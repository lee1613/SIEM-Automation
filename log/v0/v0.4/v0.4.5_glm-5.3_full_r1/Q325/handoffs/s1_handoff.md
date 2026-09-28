# s1 - Q325 - Round 2
_stamped by runner: rounds_remaining=3 novel_spl=2_
**Scope:** sourcetype=ms:aad:signin | source=/tenantdomains/froth.ly | fields=_indextime, _time, signinDateTimeInMillis, user
**Insight:** FOUND
**Candidate:** 51   **Confidence:** 97

## Prior rounds
- R1: Confirmed feed ms:aad:signin (220 events, source=/tenantdomains/froth.ly); identified signinDateTimeInMillis as creation time; computed max lag 3048.793s = 50.813 min -> 51; verified _time matches signinDateTimeInMillis within 1ms and all events on 2018-08-20; cross-check via _indextime-_time also gave 51.
- R2: Answered SH's three questions on completeness, single-day coverage, and literal rounded value from held evidence.

## This round
### What I ran
- `index=botsv3 sourcetype=ms:aad:signin | eval time_diff = abs(_time - signinDateTimeInMillis/1000), lag_seconds = _indextime - signinDateTimeInMillis/1000 | stats count, max(time_diff) as max_time_diff, dc(eval(strftime(_time,"%Y-%m-%d"))) as distinct_days, values(eval(strftime(_time,"%Y-%m-%d"))) as days, max(eval(lag_seconds/60)) as max_lag_minutes_exact, max(eval(round(lag_seconds/60,0))) as max_lag_minutes_rounded` -> 1 row (returned 1 of 1): count=220, max_time_diff=0.000998, distinct_days=1, days=2018-08-20, max_lag_minutes_exact=50.81321666638056, max_lag_minutes_rounded=51.
- `index=botsv3 sourcetype=ms:aad:signin | eval lag_seconds = _indextime - signinDateTimeInMillis/1000 | sort - lag_seconds | head 3 | eval lag_min=round(lag_seconds/60, 2) | stats list(lag_seconds), list(lag_min), list(user)` -> 1 row (returned 1 of 1): lag_seconds [3048.792999982834, 2822.6159999370575, 2756.140000104904], lag_min [50.81, 47.04, 45.94], user [fyodor@froth.ly, ghoppy@froth.ly, bstoll@froth.ly].

### What it means
FOUND: both open premises are settled by complete, fully-returned results. p1 (coverage): count=220 is every event in the feed; max_time_diff=0.000998s is the largest absolute difference between _time and signinDateTimeInMillis/1000 across all 220 events, so the creation-time representations are the same instant; distinct_days=1 with days=2018-08-20 shows the feed holds exactly one day, so the full-feed stats max() covers the entire asked span. p2 (selection): the exact maximum lag is 50.81321666638056 minutes and the SPL-computed rounded maximum is 51; the top-3 listing shows the next-highest events at 47.04 and 45.94 minutes, so no rival event competes. 51 is the value to submit.

## Ruled out
- signinDateTime (ISO string) as a separate creation-time source - same instant as signinDateTimeInMillis (max_time_diff 0.000998s).
- Other in-scope days - the feed contains only 2018-08-20 (distinct_days=1).

## What I'd tell my replacement
- Retired because: end of question (answer)
- Scope I owned: sourcetypes=['ms:aad:signin'] sources=[] fields=['_time', 'index time', 'createdDateTime', 'creation time']
- Rounds worked: 2/5  (iterations: 14, compactions: 0)
- SPL already run — do not repeat these, go one step further:
- index=botsv3 sourcetype=ms:aad:signin | eval lag_seconds = _indextime - _time | stats max(eval(round(lag_seconds/60, 0))) as max_lag_minutes_rounded, max(eval(lag_seconds/60)) as max_lag_minutes_exact, min(lag_seconds) as min_lag_sec
- index=botsv3 sourcetype=ms:aad:signin | eval lag_seconds = _indextime - signinDateTimeInMillis/1000 | sort - lag_seconds | head 3 | eval lag_min=round(lag_seconds/60, 2) | stats list(lag_seconds) as lag_seconds, list(lag_min) as lag_min, list(user) as user
- index=botsv3 sourcetype=ms:aad:signin | eval lag_seconds = _indextime - signinDateTimeInMillis/1000 | sort - lag_seconds | head 3 | eval signin_time=strftime(signinDateTimeInMillis/1000, "%Y-%m-%dT%H:%M:%S%Z"), index_time=strftime(_indextime, "%Y-%m-%dT%H:%M:%S%Z"), lag_min=round(lag_seconds/60, 2) | stats list(signin_time) as signin_time, list(index_time) as index_time, list(lag_seconds) as lag_seconds, list(lag_min) as lag_min, list(user) as user
- index=botsv3 sourcetype=ms:aad:signin | eval lag_seconds = _indextime - signinDateTimeInMillis/1000 | sort - lag_seconds | head 3 | eval signin_time=strftime(signinDateTimeInMillis/1000, "%Y-%m-%dT%H:%M:%S%Z"), index_time=strftime(_indextime, "%Y-%m-%dT%H:%M:%S%Z"), lag_min=round(lag_seconds/60, 2) | table signin_time, index_time, lag_seconds, lag_min, user, _time
- index=botsv3 sourcetype=ms:aad:signin | eval lag_seconds = _indextime - signinDateTimeInMillis/1000 | stats count, min(lag_seconds) as min_lag_sec, max(lag_seconds) as max_lag_sec, avg(lag_seconds) as avg_lag_sec
- index=botsv3 sourcetype=ms:aad:signin | eval lag_seconds = _indextime - signinDateTimeInMillis/1000 | stats max(eval(round(lag_seconds/60, 0))) as max_lag_minutes_rounded, max(eval(lag_seconds/60)) as max_lag_minutes_exact
- index=botsv3 sourcetype=ms:aad:signin | eval time_diff = abs(_time - signinDateTimeInMillis/1000) | stats count, max(time_diff) as max_time_diff, dc(eval(strftime(_time,"%Y-%m-%d"))) as distinct_days, values(eval(strftime(_time,"%Y-%m-%d"))) as days
- index=botsv3 sourcetype=ms:aad:signin | eval time_diff = abs(_time - signinDateTimeInMillis/1000), lag_seconds = _indextime - signinDateTimeInMillis/1000 | stats count, max(time_diff) as max_time_diff, dc(eval(strftime(_time,"%Y-%m-%d"))) as distinct_days, values(eval(strftime(_time,"%Y-%m-%d"))) as days, max(eval(lag_seconds/60)) as max_lag_minutes_exact, max(eval(round(lag_seconds/60,0))) as max_lag_minutes_rounded
