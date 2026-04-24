---
name: hltv-falcons-next
description: Query Team Falcons CS2 (HLTV team 11283) confirmed next upcoming event and next specific match, including confirmed opponent team details and five active player details. Use when the user asks about Falcons, Falcons CS2, Falcons战队, Team Falcons' next event, next match, upcoming HLTV schedule, opponent roster, or asks to use the HLTV pages /team/11283/falcons#tab-matchesBox and /team/11283/falcons#tab-eventsBox as sources.
---

# HLTV Falcons Next

## Core Rule

Use current sources every time. Falcons' schedule, opponents, and rosters change frequently, so do not answer from memory. Treat HLTV as the primary source and include source links in the final answer.

## Source URLs

- Matches: `https://www.hltv.org/team/11283/falcons#tab-matchesBox`
- Events: `https://www.hltv.org/team/11283/falcons#tab-eventsBox`
- Team root: `https://www.hltv.org/team/11283/falcons`

Open match, event, opponent team, and player pages from HLTV links as needed. If HLTV blocks direct HTTP fetches with Cloudflare, use browsing/search access or ask for saved page HTML rather than guessing.

## Workflow

1. Establish freshness:
   - Browse the HLTV matches and events tab URLs.
   - Record the current query date and timezone.
   - Ignore cached model knowledge and old articles unless they directly link to the same current HLTV pages.

2. Find the next confirmed event:
   - Use the events tab's upcoming/attending events list.
   - Select the earliest future event explicitly listed for Falcons.
   - Capture event name, date range, location/prize/team count when shown, and event URL.
   - If no future event is listed, state that HLTV does not currently show a confirmed next event.

3. Find the next confirmed match:
   - Use the matches tab's upcoming matches list.
   - Select the earliest scheduled match for Falcons.
   - Treat the opponent as confirmed only when HLTV shows an opponent team name/link. If the entry says TBD, unannounced, or only shows a bracket placeholder, say the next opponent is not confirmed.
   - Capture match date/time, event, format if shown, opponent, and match URL.

4. Gather opponent details when the next match opponent is confirmed:
   - Open the opponent team page linked from the match or matches tab.
   - Use HLTV's active players/lineup section for the five-player roster.
   - Output five players only when five active players are clearly shown. Include nickname, real name if shown, nationality if shown, and HLTV player URL.
   - If the active five cannot be confirmed from HLTV, say exactly which part is missing instead of filling from memory.

5. Produce a concise answer:
   - `查询时间`: absolute date/time and timezone.
   - `下一个已确认赛事`: event name, dates, key details, HLTV URL.
   - `下一场已确认比赛`: match date/time, Falcons vs opponent, event, format if available, HLTV URL.
   - `对手信息`: team name, country/ranking if shown, HLTV URL.
   - `对手五人名单`: table with nickname, real name, nationality, player URL.
   - `来源`: direct HLTV links used.
   - Note any uncertainty caused by missing opponent, incomplete roster, or HLTV access limitations.

## Helper Script

Use `scripts/falcons_next_hltv.py` to parse HLTV HTML when direct fetch is available or when the page HTML has been saved from a browser:

```bash
python3 scripts/falcons_next_hltv.py --fetch
python3 scripts/falcons_next_hltv.py --html falcons.html --opponent-html opponent.html --json
python3 scripts/falcons_next_hltv.py --self-test
```

The script is a parser/helper, not a Cloudflare bypass. If it reports a Cloudflare challenge, continue with browser-based access or saved HTML.

## Verification

Before finalizing, check that every date is future relative to the query time, the selected event and match are the earliest confirmed entries visible on HLTV, and the opponent roster comes from the opponent's current HLTV team/player pages.
