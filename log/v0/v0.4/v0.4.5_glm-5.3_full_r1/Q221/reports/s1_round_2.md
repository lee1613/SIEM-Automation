# s1 - Q221 - Round 2
_stamped by runner: rounds_remaining=1 novel_spl=0_
**Insight:** NOT_FOUND
**Candidate:** none   **Confidence:** None

## This round
### What I ran

### What it means
Intention: The GetUser denial (requestParameters=null) renders "user web_admin" cleanly while CreateAccessKey (also requestParameters=null) renders "user nullweb_admin" — so nullity of parameters alone doesn't explain the prefix. I need to (a) check real AWS error-message format externally, (b) read both ListAccessKeys raw events and the burst structure, and (c) find where "nullweb_admin" appears across the whole dataset. These are independent, so I'll run them together.
