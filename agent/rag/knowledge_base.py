#!/usr/bin/env python3
"""
RAG Knowledge Base — TF-IDF retrieval over general cybersecurity investigation docs.

Provides relevant, domain-appropriate investigation guidance to the Judge Agent
based on the content of each question.  No BOTSv3-specific answers are stored here —
only general investigator knowledge (MITRE ATT&CK context, Splunk patterns, forensic
methodology) that helps the agent figure out WHERE to look, not WHAT the answer is.
"""

import math
import os
import re
from typing import List, Tuple


# ── Chunk representation ───────────────────────────────────────────────────────

class Chunk:
    def __init__(self, title: str, content: str, source: str):
        self.title   = title
        self.content = content
        self.source  = source
        self.tokens  = _tokenize(content + " " + title)


# ── Tokenizer ──────────────────────────────────────────────────────────────────

def _tokenize(text: str) -> List[str]:
    """Lowercase, remove punctuation, split on whitespace."""
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s_:-]", " ", text)
    return [t for t in text.split() if len(t) > 1]


# ── TF-IDF retrieval ───────────────────────────────────────────────────────────

class KnowledgeBase:
    """
    Lightweight TF-IDF knowledge base with no external ML dependencies.

    Loads one or more markdown files, splits on ## headers, and retrieves
    the top-k most relevant chunks for a given query string.
    """

    def __init__(self):
        self.chunks: List[Chunk] = []
        self._idf:   dict        = {}

    # ── Loading ────────────────────────────────────────────────────────────────

    def load_markdown(self, path: str, source: str = "") -> None:
        """Load a markdown file and split on ## / ### section headers."""
        if not os.path.exists(path):
            return
        with open(path, encoding="utf-8") as f:
            text = f.read()

        src = source or os.path.basename(path)
        sections = re.split(r"\n(?=#{1,3} )", text)
        for section in sections:
            lines   = section.strip().splitlines()
            if not lines:
                continue
            title   = re.sub(r"^#+\s*", "", lines[0]).strip()
            content = "\n".join(lines[1:]).strip()
            if content:
                self.chunks.append(Chunk(title, content, src))

        self._build_idf()

    def add_text(self, title: str, content: str, source: str = "inline") -> None:
        """Add a chunk directly (for inline knowledge that doesn't live in a file)."""
        self.chunks.append(Chunk(title, content, source))
        self._build_idf()

    # ── Retrieval ──────────────────────────────────────────────────────────────

    def retrieve(self, query: str, top_k: int = 3) -> str:
        """Return the top-k most relevant chunks as a single formatted string."""
        if not self.chunks:
            return ""

        query_tokens = set(_tokenize(query))
        scored: List[Tuple[float, Chunk]] = []

        for chunk in self.chunks:
            score = self._bm25_score(query_tokens, chunk.tokens)
            if score > 0:
                scored.append((score, chunk))

        scored.sort(key=lambda x: -x[0])
        top = scored[:top_k]

        if not top:
            return ""

        parts = []
        for score, chunk in top:
            snippet = chunk.content[:800] + ("…" if len(chunk.content) > 800 else "")
            parts.append(f"### [{chunk.source}] {chunk.title}\n{snippet}")

        return "\n\n".join(parts)

    # ── Internals ──────────────────────────────────────────────────────────────

    def _build_idf(self) -> None:
        N = len(self.chunks)
        if N == 0:
            return
        df: dict = {}
        for chunk in self.chunks:
            for tok in set(chunk.tokens):
                df[tok] = df.get(tok, 0) + 1
        self._idf = {tok: math.log((N + 1) / (cnt + 1)) + 1 for tok, cnt in df.items()}

    def _bm25_score(self, query_tokens: set, doc_tokens: List[str], k1: float = 1.5, b: float = 0.75) -> float:
        """Simplified BM25 scoring."""
        avg_dl = sum(len(c.tokens) for c in self.chunks) / max(len(self.chunks), 1)
        dl     = len(doc_tokens)
        tf_map: dict = {}
        for tok in doc_tokens:
            tf_map[tok] = tf_map.get(tok, 0) + 1

        score = 0.0
        for tok in query_tokens:
            if tok not in tf_map:
                continue
            idf = self._idf.get(tok, 0)
            tf  = tf_map[tok]
            norm_tf = (tf * (k1 + 1)) / (tf + k1 * (1 - b + b * dl / avg_dl))
            score += idf * norm_tf
        return score


# ── Builder helper ─────────────────────────────────────────────────────────────

def build_siem_knowledge_base(agent_dir: str) -> KnowledgeBase:
    """
    Construct the knowledge base from all available knowledge documents.
    Call once at agent startup.
    """
    kb = KnowledgeBase()

    # 1. Rich cybersecurity analyst persona (MITRE ATT&CK, forensics methodology)
    persona_path = os.path.join(agent_dir, "judge", "cybersecurity_persona.md")
    kb.load_markdown(persona_path, source="cybersec-persona")

    # 2. Inline: general Splunk investigation cheatsheet (not dataset-specific)
    kb.add_text(
        title="Splunk SPL Investigation Cheatsheet",
        content="""
## General SPL patterns for security investigations

### Field enumeration before filtering
Use before writing complex queries against an unfamiliar sourcetype:
  index=botsv3 sourcetype="<name>" | fieldsummary | table field count distinct_count
  index=botsv3 sourcetype="<name>" | top eventName limit=20

### Raw event sampling (for unparsed / raw-text sourcetypes)
  index=botsv3 sourcetype="<name>" | head 5
Always sample raw events when field filters return 0 results.

### Cross-sourcetype pivoting
When one sourcetype doesn't have enough context, pivot to another:
  - IP address in HTTP → pivot to DNS for hostname resolution
  - Process name in Sysmon → pivot to Security log for account info
  - AWS API call → pivot to VPC flow logs for network activity

### Time-based investigation
  index=botsv3 sourcetype="<name>" | stats min(_time) as first, max(_time) as last by field | sort first
  index=botsv3 sourcetype="<name>" | timechart count by field

### Count / unique value questions
  index=botsv3 sourcetype="<name>" | stats dc(field) as unique_count
  index=botsv3 sourcetype="<name>" | stats count by field | sort -count

### Finding first/earliest occurrence
  index=botsv3 sourcetype="<name>" | stats min(_time) as first_seen by field | sort first_seen | head 1

### Extracting fields from raw text logs
  index=botsv3 sourcetype="<name>" | rex field=_raw "(?P<fieldname>pattern)"
""",
        source="spl-cheatsheet",
    )

    # 3. Inline: MITRE ATT&CK to log source mapping (general, no BOTSv3 specifics)
    kb.add_text(
        title="MITRE ATT&CK Tactic to Log Source Mapping",
        content="""
## Tactic → Primary log sources for investigation

Initial Access:
  - Web exploitation: IIS/web server logs, stream:http, suricata
  - Phishing/email: stream:smtp
  - Cloud account compromise: aws:cloudtrail (ConsoleLogin, AssumeRole)

Execution:
  - Process execution: XmlWinEventLog:Microsoft-Windows-Sysmon/Operational (EventID 1)
  - Scripting: Sysmon CommandLine field, PowerShell logs
  - Cloud execution: aws:cloudtrail (RunInstances, InvokeFunction)

Persistence:
  - Registry: WinRegistry, Sysmon EventID 12/13
  - Scheduled tasks: Sysmon EventID 1 (schtasks.exe)
  - Cloud persistence: aws:cloudtrail (CreateUser, AttachUserPolicy)

Privilege Escalation:
  - Windows: XmlWinEventLog:Security (EventID 4672, 4673)
  - Cloud: aws:cloudtrail (CreateAccessKey, PutUserPolicy, AssumeRole)

Defense Evasion:
  - AV tampering: symantec:ep:security:file, symantec:ep:agent:file
  - Process injection: Sysmon EventID 8 (CreateRemoteThread)
  - Cloud: aws:cloudtrail (DeleteTrail, StopLogging)

Credential Access:
  - Windows credential dumping: Sysmon (lsass.exe access), Security EventID 4688
  - Cloud MFA/login: aws:cloudtrail (ConsoleLogin, GetSessionToken)

Discovery:
  - Network scan: pan:traffic, stream:tcp (many connections, short duration)
  - DNS lookup patterns: stream:dns (unusual query volume/types)

Lateral Movement:
  - SMB: pan:traffic, stream:tcp (port 445)
  - Pass-the-Hash: Security EventID 4624 (Logon Type 3)

Exfiltration:
  - Large upload: aws:s3:accesslogs, stream:http (large POST/PUT)
  - DNS exfiltration: stream:dns (long TXT queries, high volume)
  - Cloud storage: aws:cloudtrail (GetObject, PutObject volume)
""",
        source="mitre-mapping",
    )

    # 4. Inline: AWS cloud data source reference (general documentation, no question-specific strategy)
    kb.add_text(
        title="AWS Log Source Reference",
        content="""
## aws:cloudtrail
Records every AWS API call made in the environment.
- Key fields: eventName, eventID, userIdentity.userName, userIdentity.type,
  sourceIPAddress, requestParameters, responseElements, errorCode
- Successful calls typically lack an errorCode field; failed ones have errorCode set
- IAM-related eventNames: CreateUser, DeleteUser, AttachUserPolicy, CreateAccessKey, AssumeRole
- S3-related eventNames: CreateBucket, DeleteBucket, PutBucketAcl, PutBucketPolicy, GetObject
- MFA information lives in: userIdentity.sessionContext.attributes.mfaAuthenticated
- Resource ARNs in: resources[].ARN or requestParameters fields

## aws:s3:accesslogs
Records every HTTP request made against an S3 bucket.
- These are RAW TEXT logs; columns are SPACE-SEPARATED and NOT auto-parsed by Splunk
- You MUST use | rex field=_raw to extract any field — direct field= filters will fail
- Fields in order: bucket-owner bucket [time] remote-ip requester request-id operation key request-uri http-status error-code bytes-sent ...
- Operation names follow AWS REST API conventions (e.g., REST.GET.OBJECT, REST.PUT.OBJECT)
- HTTP status code indicates success/failure of individual requests
- requester="-" indicates anonymous (unauthenticated) access

## aws:cloudwatchlogs:vpcflow
Records network flow data for VPC traffic.
- Key fields: srcaddr, dstaddr, srcport, dstport, protocol, bytes, packets, action
- action=ACCEPT means traffic was allowed; action=REJECT means it was blocked by security group/ACL

## aws:elb:accesslogs
Records requests handled by an Elastic Load Balancer.
- Raw text log; extract fields with rex
- Contains: client IP, request path, backend IP, response code, bytes
""",
        source="aws-log-sources",
    )

    return kb
