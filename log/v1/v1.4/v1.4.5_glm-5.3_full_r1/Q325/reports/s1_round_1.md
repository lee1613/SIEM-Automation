# s1 - Q325 - Round 1
_stamped by runner: rounds_remaining=4 novel_spl=6_
**Scope:** sourcetype=ms:aad:signin | source=/tenantdomains/froth.ly | fields=_indextime, signinDateTimeInMillis, _time, user
**Insight:** FOUND
**Candidate:** 51   **Confidence:** 95

## Prior rounds
- (Round 1) Confirmed feed ms:aad:signin exists: 220 events, all 2018-08-20, source=/tenantdomains/froth.ly.

## This round
### What I ran
- get_sourcetype_fields ms:aad:signin -> 220 events, 15 distinct signinDateTimeInMillis values; creation-time candidates: signinDateTimeInMillis, signinDateTime.
- sample_events (2 raw) -> JSON with signinDateTimeInMillis=1534778205572 and signinDateTime="2018-08-20T15:16:45.5720566Z"; _time matches signinDateTime.
- `index=botsv3 sourcetype=ms:aad:signin | eval lag_seconds = _indextime - signinDateTimeInMillis/1000 | stats count, min(lag_seconds), max(lag_seconds), avg(lag_seconds)` -> 220 events; min 156.375s, max 3048.793s, avg 846.853s.
- `... | stats max(eval(round(lag_seconds/60,0))) as max_lag_minutes_rounded, max(eval(lag_seconds/60)) as max_lag_minutes_exact` -> 51 and 50.81321666638056.
- `... | eval time_diff = abs(_time - signinDateTimeInMillis/1000) | stats count, max(time_diff), dc(day)` -> 220 events, max diff 0.000998s, all on 2018-08-20.
- Cross-check `| eval lag_seconds = _indextime - _time | stats max(round(lag/60,0))` -> 51 (exact 50.81320133).
- Top-3 lag events (aggregated table) -> max: signin 2018-08-20T11:54:28Z, indexed 12:45:17Z, 3048.793s = 50.81 min (fyodor@froth.ly); next 47.04 and 45.94 min.

### What it means
FOUND: the feed's event creation time is signinDateTimeInMillis (epoch ms; _time equals it within 1ms across all 220 events, and the raw JSON's signinDateTime string is the same instant). Index time is _indextime. Computing lag = _indextime - signinDateTimeInMillis/1000 over every event of the only day in this feed (2018-08-20) gives a maximum of 3048.793 seconds = 50.813 minutes, which rounds to 51. The result is identical when _time is used as the creation-time representation, so the answer does not depend on that choice. All arithmetic was done inside SPL (eval + stats max/round); no manual rounding.

## Ruled out
- signinDateTime (ISO string) as a separate creation-time source - it is the same instant as signinDateTimeInMillis; both yield max 50.813 min.
- Other days in scope - the feed contains only 2018-08-20 (dc(day)=1), so "the entire day" is fully covered by the 220 events.

_Iteration cap reached: 10/10 iterations used this round — cut off, not finished._
