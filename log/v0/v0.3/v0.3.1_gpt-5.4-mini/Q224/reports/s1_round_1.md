# s1 - Q224 - Round 1
_stamped by runner: rounds_remaining=7 novel_spl=3_
**Scope:** sourcetype=stream:dns | source=none | fields=query, subdomain, len(subdomain)
**Insight:** FOUND
**Candidate:** 3.00  **Confidence:** 98

## Prior rounds
- Confirmed DNS telemetry lives in `stream:dns` and exposes `query`, `queries`, and `name` fields.
- Established `query` is the best field for queried FQDNs; `stream:dns` is the correct feed for DNS question analysis.
- Narrowed to `brewertalk.com` using lowercased query values and regex anchored on the domain.
- Verified only one third-level label appears under `brewertalk.com` in DNS telemetry: `www`.

## This round
### What I ran
- `index=botsv3 sourcetype=stream:dns | eval q=lower(query) | search q="brewertalk.com" OR q="*.brewertalk.com" | regex q="(^|\.)brewertalk\.com$" | rex field=q "^(?<subdomain>[^.]+)\.brewertalk\.com$" | dedup subdomain | eval sub_len=len(subdomain) | stats avg(sub_len) as avg_len values(subdomain) as subdomains count as distinct_count` -> returned `avg_len=3`, `subdomains=www`, `distinct_count=2` (1 result)
- `index=botsv3 sourcetype=stream:dns | eval q=lower(query) | search q="brewertalk.com" OR q="*.brewertalk.com" | regex q="(^|\.)brewertalk\.com$" | rex field=q "^(?<subdomain>[^.]+)\.brewertalk\.com$" | stats count as hits by subdomain | sort subdomain` -> returned `subdomain=www`, `hits=107` (1 result)
### What it means
The only distinct third-level subdomain observed in DNS queries to `brewertalk.com` is `www`. Its character length is 3, so the average over the distinct subdomains is `3.00`.

## Ruled out
- Additional brewertalk.com third-level subdomains - not present in DNS telemetry; only `www` matched.

## Open questions for SH
- None; the DNS-only computation is complete.