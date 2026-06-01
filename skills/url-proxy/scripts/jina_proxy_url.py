#!/usr/bin/env python3
"""Generate Jina Reader proxy URLs."""

from __future__ import annotations

import argparse
import sys
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit


JINA_READER_PREFIX = "https://r.jina.ai/"


def normalize_url(raw_url: str) -> str:
    url = raw_url.strip()
    if not url:
        raise ValueError("URL must not be empty")
    if url.startswith(JINA_READER_PREFIX):
        return url
    parsed = urlsplit(url)
    if not parsed.scheme:
        url = f"https://{url}"
        parsed = urlsplit(url)
    return remove_tracking_query_params(parsed)


def remove_tracking_query_params(parsed_url) -> str:
    query = parse_qsl(parsed_url.query, keep_blank_values=True)
    filtered_query = [
        (key, value)
        for key, value in query
        if not key.lower().startswith("utm_")
    ]
    return urlunsplit(
        (
            parsed_url.scheme,
            parsed_url.netloc,
            parsed_url.path,
            urlencode(filtered_query, doseq=True),
            parsed_url.fragment,
        )
    )


def proxy_url(raw_url: str) -> str:
    url = normalize_url(raw_url)
    if url.startswith(JINA_READER_PREFIX):
        return url
    return f"{JINA_READER_PREFIX}{url}"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate a Jina Reader proxy URL for an inaccessible webpage."
    )
    parser.add_argument("url", nargs="+", help="Original webpage URL")
    parser.add_argument(
        "--curl",
        action="store_true",
        help="Print curl commands instead of plain proxy URLs",
    )
    args = parser.parse_args()

    for raw_url in args.url:
        try:
            output = proxy_url(raw_url)
        except ValueError as exc:
            print(str(exc), file=sys.stderr)
            return 2
        if args.curl:
            print(f"curl -L {shell_quote(output)}")
        else:
            print(output)
    return 0


def shell_quote(value: str) -> str:
    return "'" + value.replace("'", "'\"'\"'") + "'"


if __name__ == "__main__":
    raise SystemExit(main())
