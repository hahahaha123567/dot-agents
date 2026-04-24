#!/usr/bin/env python3
"""Parse Team Falcons' next HLTV event, match, and opponent roster.

The script can fetch pages when HLTV allows it, but it intentionally does not
try to bypass Cloudflare challenges. Use --html/--opponent-html with saved page
HTML when direct HTTP access is blocked.
"""

from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from typing import Dict, Iterable, List, Optional


BASE = "https://www.hltv.org"
FALCONS_TEAM_URL = f"{BASE}/team/11283/falcons"
MATCHES_URL = FALCONS_TEAM_URL + "#tab-matchesBox"
EVENTS_URL = FALCONS_TEAM_URL + "#tab-eventsBox"


def normalize_space(value: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(value or "")).strip()


def strip_tags(value: str) -> str:
    value = re.sub(r"<script\b.*?</script>", " ", value, flags=re.I | re.S)
    value = re.sub(r"<style\b.*?</style>", " ", value, flags=re.I | re.S)
    return normalize_space(re.sub(r"<[^>]+>", " ", value))


def absolute_url(path: str) -> str:
    return urllib.parse.urljoin(BASE, html.unescape(path))


def slug_title(path: str) -> str:
    slug = path.rstrip("/").split("/")[-1]
    return normalize_space(slug.replace("-", " ")).title()


def around(text: str, start: int, end: int, radius: int = 3500) -> str:
    return text[max(0, start - radius) : min(len(text), end + radius)]


def anchor_block(page_html: str, link: re.Match[str], radius: int = 2200) -> str:
    close = page_html.find("</a>", link.end())
    if close != -1 and close - link.start() < 12000:
        return page_html[link.start() : close + 4]
    return around(page_html, link.start(), link.end(), radius=radius)


def read_file(path: str) -> str:
    with open(path, "r", encoding="utf-8") as fh:
        return fh.read()


def fetch_url(url: str, timeout: int = 25) -> str:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            charset = resp.headers.get_content_charset() or "utf-8"
            return resp.read().decode(charset, errors="replace")
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {exc.code} while fetching {url}\n{body[:5000]}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Failed to fetch {url}: {exc}") from exc


def is_cloudflare_challenge(page_html: str) -> bool:
    lowered = page_html.lower()
    return (
        "just a moment..." in lowered
        or "cf-mitigated" in lowered
        or "enable javascript and cookies to continue" in lowered
        or "/cdn-cgi/challenge-platform/" in lowered
    )


def parse_data_unix(block: str) -> Optional[str]:
    match = re.search(r'data-unix=["\'](\d{10,13})["\']', block)
    if not match:
        return None
    millis = int(match.group(1))
    if millis < 10_000_000_000:
        millis *= 1000
    return dt.datetime.fromtimestamp(millis / 1000, tz=dt.timezone.utc).isoformat()


def class_text(block: str, class_fragment: str) -> List[str]:
    values = []
    pattern = re.compile(
        r'<[^>]+class=["\'][^"\']*' + re.escape(class_fragment) + r'[^"\']*["\'][^>]*>(.*?)</[^>]+>',
        re.I | re.S,
    )
    for match in pattern.finditer(block):
        text = strip_tags(match.group(1))
        if text:
            values.append(text)
    return values


def extract_titles(block: str) -> List[str]:
    values = []
    for attr in ("title", "alt"):
        for raw in re.findall(attr + r'=["\']([^"\']+)["\']', block, flags=re.I):
            value = normalize_space(raw)
            if value and value not in values:
                values.append(value)
    return values


def extract_team_names(block: str) -> List[str]:
    candidates: List[str] = []
    for fragment in ("matchTeamName", "teamName", "team-name", "team"):
        candidates.extend(class_text(block, fragment))
    candidates.extend(extract_titles(block))

    cleaned = []
    ignored = {
        "team logo",
        "falcons logo",
        "team falcons",
        "falcons",
        "counter-strike",
        "cs2",
    }
    for candidate in candidates:
        value = normalize_space(candidate)
        if not value or value.lower() in ignored:
            continue
        if re.search(r"\b\d{1,2}:\d{2}\b", value):
            continue
        if value not in cleaned:
            cleaned.append(value)
    return cleaned


def select_opponent(block: str) -> Optional[str]:
    for name in extract_team_names(block):
        if name.lower() != "falcons":
            return name

    text = strip_tags(block)
    patterns = [
        r"Falcons\s+(?:vs\.?|versus|-)\s+([A-Za-z0-9 ._'\-]+)",
        r"([A-Za-z0-9 ._'\-]+)\s+(?:vs\.?|versus|-)\s+Falcons",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.I)
        if match:
            value = normalize_space(match.group(1))
            if value and value.lower() not in {"tbd", "to be decided"}:
                return value
    return None


def extract_event_name(block: str, href: str) -> Optional[str]:
    candidates = []
    for fragment in ("matchEventName", "matchEvent", "event-name", "eventName"):
        candidates.extend(class_text(block, fragment))
    for candidate in candidates:
        if candidate and candidate.lower() not in {"event", "events"}:
            return candidate
    return slug_title(href)


def iter_links(page_html: str, path_re: str) -> Iterable[re.Match[str]]:
    pattern = re.compile(r'<a\b[^>]*href=["\'](' + path_re + r')["\'][^>]*>', re.I)
    return pattern.finditer(page_html)


def parse_matches(page_html: str) -> List[Dict[str, Optional[str]]]:
    matches: List[Dict[str, Optional[str]]] = []
    seen = set()
    for link in iter_links(page_html, r"/matches/\d+/[^\"']+"):
        href = html.unescape(link.group(1))
        if href in seen:
            continue
        seen.add(href)
        block = anchor_block(page_html, link, radius=3500)
        text = strip_tags(block)
        if "falcons" not in text.lower():
            continue

        opponent = select_opponent(block)
        event_name = extract_event_name(block, href)
        matches.append(
            {
                "match_url": absolute_url(href),
                "match_title": slug_title(href),
                "datetime_utc": parse_data_unix(block),
                "event": event_name,
                "opponent": opponent,
                "opponent_confirmed": bool(opponent and opponent.lower() not in {"tbd", "tba", "to be decided"}),
                "text": text[:700],
            }
        )
    return sort_by_datetime(matches)


def parse_events(page_html: str) -> List[Dict[str, Optional[str]]]:
    events: List[Dict[str, Optional[str]]] = []
    seen = set()
    for link in iter_links(page_html, r"/events/\d+/[^\"']+"):
        href = html.unescape(link.group(1))
        if href in seen:
            continue
        seen.add(href)
        block = anchor_block(page_html, link, radius=2200)
        text = strip_tags(block)
        title = extract_event_name(block, href)
        date_text = None
        date_candidates = class_text(block, "eventdate") + class_text(block, "date")
        if date_candidates:
            date_text = date_candidates[0]
        events.append(
            {
                "event_url": absolute_url(href),
                "event": title,
                "datetime_utc": parse_data_unix(block),
                "date_text": date_text,
                "text": text[:700],
            }
        )
    return sort_by_datetime(events)


def sort_by_datetime(items: List[Dict[str, Optional[str]]]) -> List[Dict[str, Optional[str]]]:
    def key(item: Dict[str, Optional[str]]) -> str:
        return item.get("datetime_utc") or "9999-12-31T23:59:59+00:00"

    return sorted(items, key=key)


def parse_iso_datetime(value: Optional[str]) -> Optional[dt.datetime]:
    if not value:
        return None
    try:
        parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=dt.timezone.utc)
    return parsed.astimezone(dt.timezone.utc)


def select_next_future(
    items: List[Dict[str, Optional[str]]], now: dt.datetime
) -> Optional[Dict[str, Optional[str]]]:
    future_items = [
        item
        for item in items
        if (item_time := parse_iso_datetime(item.get("datetime_utc"))) is not None and item_time > now
    ]
    if not future_items:
        return None
    return sort_by_datetime(future_items)[0]


def parse_players(page_html: str) -> List[Dict[str, Optional[str]]]:
    players: List[Dict[str, Optional[str]]] = []
    seen = set()
    links = list(iter_links(page_html, r"/player/\d+/[^\"']+"))
    for index, link in enumerate(links):
        href = html.unescape(link.group(1))
        if href in seen:
            continue
        seen.add(href)
        next_start = links[index + 1].start() if index + 1 < len(links) else min(len(page_html), link.end() + 1200)
        block = page_html[link.start() : next_start]
        slug = href.rstrip("/").split("/")[-1]
        link_text_match = re.search(re.escape(link.group(0)) + r"(.*?)</a>", page_html[link.start() :], flags=re.I | re.S)
        nickname = strip_tags(link_text_match.group(1)) if link_text_match else ""
        if not nickname or len(nickname) > 40:
            nickname = slug

        titles = extract_titles(block)
        nationality = None
        for title in titles:
            if title.lower() not in {nickname.lower(), slug.lower(), "player picture"}:
                nationality = title
                break

        full_name = None
        name_candidates = class_text(block, "playerRealname") + class_text(block, "realname") + class_text(block, "player-name")
        for candidate in name_candidates:
            if candidate.lower() != nickname.lower():
                full_name = candidate
                break

        players.append(
            {
                "nickname": nickname,
                "real_name": full_name,
                "nationality": nationality,
                "player_url": absolute_url(href),
            }
        )
        if len(players) == 5:
            break
    return players


def summarize(team_html: str, opponent_html: Optional[str]) -> Dict[str, object]:
    if is_cloudflare_challenge(team_html):
        return {
            "ok": False,
            "blocked": True,
            "message": "HLTV returned a Cloudflare challenge. Use browser-based access or saved page HTML.",
            "sources": [MATCHES_URL, EVENTS_URL],
        }

    queried_at = dt.datetime.now(dt.timezone.utc)
    matches = parse_matches(team_html)
    events = parse_events(team_html)
    result: Dict[str, object] = {
        "ok": True,
        "queried_at_utc": queried_at.isoformat(timespec="seconds"),
        "sources": [MATCHES_URL, EVENTS_URL],
        "next_event": select_next_future(events, queried_at),
        "next_match": select_next_future(matches, queried_at),
    }
    if opponent_html:
        if is_cloudflare_challenge(opponent_html):
            result["opponent_roster_error"] = "Opponent page returned a Cloudflare challenge."
        else:
            result["opponent_players"] = parse_players(opponent_html)
    return result


def self_test() -> int:
    now = dt.datetime.now(dt.timezone.utc)
    past_unix = int((now - dt.timedelta(days=7)).timestamp() * 1000)
    future_event_unix = int((now + dt.timedelta(days=3)).timestamp() * 1000)
    future_match_unix = int((now + dt.timedelta(days=4)).timestamp() * 1000)
    sample = """
    <html><body>
      <section id="matchesBox">
        <a class="upcomingMatch" href="/matches/2379999/falcons-vs-old-team">
          <div class="matchTime" data-unix="{past_unix}">12:00</div>
          <div class="matchEventName">Past Event</div>
          <div class="matchTeamName">Falcons</div>
          <div class="matchTeamName">Old Team</div>
        </a>
        <a class="upcomingMatch" href="/matches/2380001/falcons-vs-vitality">
          <div class="matchTime" data-unix="{future_match_unix}">12:00</div>
          <div class="matchEventName">IEM Sample 2026</div>
          <div class="matchTeamName">Falcons</div>
          <div class="matchTeamName">Vitality</div>
        </a>
      </section>
      <section id="eventsBox">
        <a class="event-box" href="/events/9000/past-event">
          <span class="event-name">Past Event</span>
          <span class="eventdate" data-unix="{past_unix}">Past</span>
        </a>
        <a class="event-box" href="/events/9001/iem-sample-2026">
          <span class="event-name">IEM Sample 2026</span>
          <span class="eventdate" data-unix="{future_event_unix}">Future</span>
        </a>
      </section>
    </body></html>
    """.format(
        past_unix=past_unix,
        future_event_unix=future_event_unix,
        future_match_unix=future_match_unix,
    )
    opponent = """
    <html><body>
      <div class="players-table">
        <a href="/player/1/apex">apEX</a><span class="playerRealname">Dan Madesclaire</span><img title="France">
        <a href="/player/2/zywoo">ZywOo</a><span class="playerRealname">Mathieu Herbaut</span><img title="France">
        <a href="/player/3/flamez">flameZ</a><span class="playerRealname">Shahar Shushan</span><img title="Israel">
        <a href="/player/4/mezii">mezii</a><span class="playerRealname">William Merriman</span><img title="United Kingdom">
        <a href="/player/5/ropz">ropz</a><span class="playerRealname">Robin Kool</span><img title="Estonia">
      </div>
    </body></html>
    """
    result = summarize(sample, opponent)
    assert result["ok"] is True
    assert result["next_match"]["opponent"] == "Vitality"  # type: ignore[index]
    assert result["next_event"]["event"] == "IEM Sample 2026"  # type: ignore[index]
    assert len(result["opponent_players"]) == 5  # type: ignore[arg-type]
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fetch", action="store_true", help="Fetch the Falcons HLTV team page directly.")
    parser.add_argument("--html", help="Path to saved Falcons HLTV team page HTML.")
    parser.add_argument("--opponent-url", help="Fetch an opponent HLTV team page directly.")
    parser.add_argument("--opponent-html", help="Path to saved opponent HLTV team page HTML.")
    parser.add_argument("--json", action="store_true", help="Emit JSON only.")
    parser.add_argument("--self-test", action="store_true", help="Run parser self-test with embedded sample HTML.")
    args = parser.parse_args(argv)

    if args.self_test:
        return self_test()

    if not args.fetch and not args.html:
        parser.error("Provide --fetch or --html.")

    try:
        team_html = fetch_url(FALCONS_TEAM_URL) if args.fetch else read_file(args.html)
        opponent_html = None
        if args.opponent_url:
            opponent_html = fetch_url(args.opponent_url)
        elif args.opponent_html:
            opponent_html = read_file(args.opponent_html)
        result = summarize(team_html, opponent_html)
    except RuntimeError as exc:
        challenge = is_cloudflare_challenge(str(exc))
        result = {
            "ok": False,
            "blocked": challenge,
            "message": str(exc)[:900],
            "sources": [MATCHES_URL, EVENTS_URL],
        }

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print_human(result)
    return 0 if result.get("ok") else 2


def print_human(result: Dict[str, object]) -> None:
    if not result.get("ok"):
        print("Unable to parse HLTV data.")
        print(result.get("message", "Unknown error"))
        print("Sources:")
        for source in result.get("sources", []):  # type: ignore[assignment]
            print(f"- {source}")
        return

    print(f"Queried at UTC: {result.get('queried_at_utc')}")
    print("\nNext confirmed event:")
    print(json.dumps(result.get("next_event"), ensure_ascii=False, indent=2))
    print("\nNext confirmed match:")
    print(json.dumps(result.get("next_match"), ensure_ascii=False, indent=2))
    if "opponent_players" in result:
        print("\nOpponent players:")
        print(json.dumps(result.get("opponent_players"), ensure_ascii=False, indent=2))
    if "opponent_roster_error" in result:
        print(f"\nOpponent roster error: {result['opponent_roster_error']}")
    print("\nSources:")
    for source in result.get("sources", []):  # type: ignore[assignment]
        print(f"- {source}")


if __name__ == "__main__":
    sys.exit(main())
