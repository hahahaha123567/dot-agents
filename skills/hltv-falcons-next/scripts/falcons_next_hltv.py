#!/usr/bin/env python3
"""Parse Team Falcons' next HLTV event, match, opponent roster, and ratings.

The script can fetch pages when HLTV allows it, but it intentionally does not
try to bypass Cloudflare challenges. Use --html/--opponent-html with saved page
HTML when direct HTTP access is blocked.
"""

from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from typing import Dict, Iterable, List, Optional, Tuple


BASE = "https://www.hltv.org"
FALCONS_TEAM_URL = f"{BASE}/team/11283/falcons"
MATCHES_URL = FALCONS_TEAM_URL + "#tab-matchesBox"
EVENTS_URL = FALCONS_TEAM_URL + "#tab-eventsBox"
STATS_PLAYER_URL = f"{BASE}/stats/players"


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


def parse_players(page_html: str, limit: int = 5) -> List[Dict[str, Optional[str]]]:
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
        if len(players) == limit:
            break
    return players


def parse_match_lineups(page_html: str) -> Tuple[List[Dict[str, Optional[str]]], List[Dict[str, Optional[str]]]]:
    start = page_html.lower().find("lineups")
    end = page_html.lower().find("map stats", start if start != -1 else 0)
    if start == -1:
        return [], []
    lineup_html = page_html[start : end if end != -1 else start + 50000]
    players = parse_players(lineup_html, limit=10)
    if len(players) < 10:
        return [], []
    return players[:5], players[5:10]


def player_id_slug(player_url: str) -> Optional[Tuple[str, str]]:
    parsed = urllib.parse.urlparse(player_url)
    match = re.search(r"/player/(\d+)/([^/?#]+)", parsed.path)
    if not match:
        return None
    return match.group(1), match.group(2)


def player_stats_url(player: Dict[str, Optional[str]], start_date: str, end_date: str) -> Optional[str]:
    player_url = player.get("player_url")
    if not player_url:
        return None
    parsed = player_id_slug(player_url)
    if not parsed:
        return None
    player_id, slug = parsed
    query = urllib.parse.urlencode({"startDate": start_date, "endDate": end_date})
    return f"{STATS_PLAYER_URL}/{player_id}/{slug}?{query}"


def parse_rating_from_stats(page_html: str) -> Optional[float]:
    text = strip_tags(page_html)
    patterns = [
        r"\bRating\s*(?:3\.0|2\.0)?\s*([0-9]+(?:\.[0-9]+)?)\b",
        r"\b([0-9]+(?:\.[0-9]+)?)\s*Rating\s*(?:3\.0|2\.0)?\b",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.I)
        if match:
            try:
                return float(match.group(1))
            except ValueError:
                return None
    return None


def rating_period(days: int, now: dt.datetime) -> Dict[str, str]:
    end_date = now.date()
    start_date = end_date - dt.timedelta(days=days)
    return {
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "days": str(days),
    }


def stats_html_path(stats_dir: str, player: Dict[str, Optional[str]]) -> Optional[str]:
    player_url = player.get("player_url")
    nickname = player.get("nickname")
    if not player_url:
        return None
    parsed = player_id_slug(player_url)
    candidates = []
    if parsed:
        player_id, slug = parsed
        candidates.extend([f"{player_id}.html", f"{player_id}-{slug}.html", f"{slug}.html"])
    if nickname:
        candidates.append(f"{nickname}.html")
    for candidate in candidates:
        path = os.path.join(stats_dir, candidate)
        if os.path.exists(path):
            return path
    return None


def attach_stats(
    players: List[Dict[str, Optional[str]]],
    start_date: str,
    end_date: str,
    html_dir: Optional[str] = None,
    fetch: bool = False,
) -> List[Dict[str, Optional[object]]]:
    enriched: List[Dict[str, Optional[object]]] = []
    for player in players:
        item: Dict[str, Optional[object]] = dict(player)
        url = player_stats_url(player, start_date, end_date)
        item["stats_url"] = url
        item["rating"] = None
        if html_dir:
            path = stats_html_path(html_dir, player)
            if path:
                stats_html = read_file(path)
                if is_cloudflare_challenge(stats_html):
                    item["stats_error"] = "Stats page returned a Cloudflare challenge."
                else:
                    item["rating"] = parse_rating_from_stats(stats_html)
            else:
                item["stats_error"] = f"No saved stats HTML found in {html_dir}."
        elif fetch and url:
            try:
                stats_html = fetch_url(url)
                if is_cloudflare_challenge(stats_html):
                    item["stats_error"] = "Stats page returned a Cloudflare challenge."
                else:
                    item["rating"] = parse_rating_from_stats(stats_html)
            except RuntimeError as exc:
                item["stats_error"] = str(exc)[:500]
        enriched.append(item)
    return enriched


def compare_ratings(
    falcons_players: List[Dict[str, Optional[object]]],
    opponent_players: List[Dict[str, Optional[object]]],
) -> List[Dict[str, Optional[object]]]:
    comparison: List[Dict[str, Optional[object]]] = []
    for index, (falcon, opponent) in enumerate(zip(falcons_players, opponent_players), start=1):
        falcon_rating = falcon.get("rating")
        opponent_rating = opponent.get("rating")
        diff: Optional[float] = None
        leader: Optional[str] = None
        if isinstance(falcon_rating, (int, float)) and isinstance(opponent_rating, (int, float)):
            diff = round(float(falcon_rating) - float(opponent_rating), 2)
            if diff > 0:
                leader = str(falcon.get("nickname") or "Falcons")
            elif diff < 0:
                leader = str(opponent.get("nickname") or "Opponent")
            else:
                leader = "tie"
        comparison.append(
            {
                "position": index,
                "falcons_player": falcon.get("nickname"),
                "falcons_rating": falcon_rating,
                "opponent_player": opponent.get("nickname"),
                "opponent_rating": opponent_rating,
                "rating_diff_falcons_minus_opponent": diff,
                "higher_rating": leader,
            }
        )
    return comparison


def summarize(
    team_html: str,
    opponent_html: Optional[str],
    *,
    match_html: Optional[str] = None,
    include_stats: bool = False,
    fetch_stats: bool = False,
    falcons_stats_dir: Optional[str] = None,
    opponent_stats_dir: Optional[str] = None,
    rating_days: int = 90,
) -> Dict[str, object]:
    if is_cloudflare_challenge(team_html):
        return {
            "ok": False,
            "blocked": True,
            "message": "HLTV returned a Cloudflare challenge. Use browser-based access or saved page HTML.",
            "sources": [MATCHES_URL, EVENTS_URL],
        }

    queried_at = dt.datetime.now(dt.timezone.utc)
    period = rating_period(rating_days, queried_at)
    matches = parse_matches(team_html)
    events = parse_events(team_html)
    result: Dict[str, object] = {
        "ok": True,
        "queried_at_utc": queried_at.isoformat(timespec="seconds"),
        "sources": [MATCHES_URL, EVENTS_URL],
        "next_event": select_next_future(events, queried_at),
        "next_match": select_next_future(matches, queried_at),
    }
    match_falcons_players: List[Dict[str, Optional[str]]] = []
    match_opponent_players: List[Dict[str, Optional[str]]] = []
    if match_html:
        if is_cloudflare_challenge(match_html):
            result["match_lineup_error"] = "Match page returned a Cloudflare challenge."
        else:
            match_falcons_players, match_opponent_players = parse_match_lineups(match_html)
            if not match_falcons_players or not match_opponent_players:
                result["match_lineup_error"] = "Could not identify both five-player lineups from match page."

    falcons_players = match_falcons_players or parse_players(team_html)
    if falcons_players:
        result["falcons_players"] = falcons_players
    if opponent_html:
        if is_cloudflare_challenge(opponent_html):
            result["opponent_roster_error"] = "Opponent page returned a Cloudflare challenge."
        else:
            result["opponent_players"] = match_opponent_players or parse_players(opponent_html)
    elif match_opponent_players:
        result["opponent_players"] = match_opponent_players
    if include_stats:
        result["rating_period"] = period
        if len(falcons_players) == 5:
            result["falcons_players"] = attach_stats(
                falcons_players,
                period["start_date"],
                period["end_date"],
                html_dir=falcons_stats_dir,
                fetch=fetch_stats,
            )
        else:
            result["falcons_stats_error"] = "Could not identify five active Falcons players."

        opponent_players = result.get("opponent_players")
        if isinstance(opponent_players, list) and len(opponent_players) == 5:
            result["opponent_players"] = attach_stats(
                opponent_players,  # type: ignore[arg-type]
                period["start_date"],
                period["end_date"],
                html_dir=opponent_stats_dir,
                fetch=fetch_stats,
            )
        elif "opponent_players" in result:
            result["opponent_stats_error"] = "Could not identify five active opponent players."

        updated_falcons = result.get("falcons_players")
        updated_opponent = result.get("opponent_players")
        if isinstance(updated_falcons, list) and isinstance(updated_opponent, list):
            result["rating_comparison"] = compare_ratings(updated_falcons, updated_opponent)  # type: ignore[arg-type]
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
    falcons_stats = """
    <html><body>
      <div>Rating 3.0</div><div>1.20</div>
    </body></html>
    """
    opponent_stats = """
    <html><body>
      <div>Rating 3.0</div><div>1.10</div>
    </body></html>
    """
    result = summarize(sample, opponent)
    assert result["ok"] is True
    assert result["next_match"]["opponent"] == "Vitality"  # type: ignore[index]
    assert result["next_event"]["event"] == "IEM Sample 2026"  # type: ignore[index]
    assert len(result["opponent_players"]) == 5  # type: ignore[arg-type]
    assert parse_rating_from_stats(falcons_stats) == 1.20
    assert parse_rating_from_stats(opponent_stats) == 1.10
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fetch", action="store_true", help="Fetch the Falcons HLTV team page directly.")
    parser.add_argument("--html", help="Path to saved Falcons HLTV team page HTML.")
    parser.add_argument("--match-url", help="Fetch the confirmed HLTV match page directly for lineup order.")
    parser.add_argument("--match-html", help="Path to saved confirmed HLTV match page HTML for lineup order.")
    parser.add_argument("--opponent-url", help="Fetch an opponent HLTV team page directly.")
    parser.add_argument("--opponent-html", help="Path to saved opponent HLTV team page HTML.")
    parser.add_argument("--with-player-stats", action="store_true", help="Include both lineups' player stats rating comparison.")
    parser.add_argument(
        "--fetch-player-stats",
        action="store_true",
        help="Fetch player stats pages directly. Implies --with-player-stats.",
    )
    parser.add_argument("--falcons-stats-html-dir", help="Directory with saved Falcons player stats pages.")
    parser.add_argument("--opponent-stats-html-dir", help="Directory with saved opponent player stats pages.")
    parser.add_argument("--rating-days", type=int, default=90, help="Number of days for stats date filter.")
    parser.add_argument("--json", action="store_true", help="Emit JSON only.")
    parser.add_argument("--self-test", action="store_true", help="Run parser self-test with embedded sample HTML.")
    args = parser.parse_args(argv)

    if args.self_test:
        return self_test()

    if not args.fetch and not args.html:
        parser.error("Provide --fetch or --html.")

    try:
        team_html = fetch_url(FALCONS_TEAM_URL) if args.fetch else read_file(args.html)
        match_html = None
        if args.match_url:
            match_html = fetch_url(args.match_url)
        elif args.match_html:
            match_html = read_file(args.match_html)
        opponent_html = None
        if args.opponent_url:
            opponent_html = fetch_url(args.opponent_url)
        elif args.opponent_html:
            opponent_html = read_file(args.opponent_html)
        result = summarize(
            team_html,
            opponent_html,
            match_html=match_html,
            include_stats=(
                args.with_player_stats
                or args.fetch_player_stats
                or bool(args.falcons_stats_html_dir)
                or bool(args.opponent_stats_html_dir)
            ),
            fetch_stats=args.fetch_player_stats,
            falcons_stats_dir=args.falcons_stats_html_dir,
            opponent_stats_dir=args.opponent_stats_html_dir,
            rating_days=args.rating_days,
        )
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
    if "rating_comparison" in result:
        print("\nRating comparison:")
        print(json.dumps(result.get("rating_comparison"), ensure_ascii=False, indent=2))
    if "rating_period" in result:
        print("\nRating period:")
        print(json.dumps(result.get("rating_period"), ensure_ascii=False, indent=2))
    if "falcons_stats_error" in result:
        print(f"\nFalcons stats error: {result['falcons_stats_error']}")
    if "opponent_stats_error" in result:
        print(f"\nOpponent stats error: {result['opponent_stats_error']}")
    if "opponent_roster_error" in result:
        print(f"\nOpponent roster error: {result['opponent_roster_error']}")
    print("\nSources:")
    for source in result.get("sources", []):  # type: ignore[assignment]
        print(f"- {source}")


if __name__ == "__main__":
    sys.exit(main())
