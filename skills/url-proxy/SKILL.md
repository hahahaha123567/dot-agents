---
name: url-proxy
description: Generate Jina Reader proxy URLs for webpages that are inaccessible from the local machine, browser, curl, or normal web fetch. Use when the user asks to turn blocked, unreachable, paywall-like, JavaScript-heavy, or hard-to-fetch webpage URLs into r.jina.ai addresses, or when Codex needs a readable proxy URL for scraping, summarizing, archiving, or opening a page through Jina Reader.
---

# URL Proxy

## Workflow

Use Jina Reader by prepending the original URL with:

```text
https://r.jina.ai/
```

For example:

```text
https://example.com/article?utm_source=dlvr.it&utm_medium=twitter
```

becomes:

```text
https://r.jina.ai/https://example.com/article
```

## Rules

- Return the proxy URL directly when the user only asks for an address
- Before generating the proxy URL, remove tracking-only query parameters such as `utm_source`, `utm_medium`, `utm_campaign`, `utm_term`, `utm_content`, and other `utm_*` parameters
- Preserve all non-tracking query parameters after normalizing a missing scheme to `https://`
- Do not wrap a URL that already starts with `https://r.jina.ai/`
- Use this only for public webpages and documents that Jina Reader can fetch
- Tell the user if the target appears to require login, private network access, or user-specific cookies, because Jina Reader cannot access those
- When fetching content is needed, open or curl the generated `https://r.jina.ai/<original-url>` URL

## Script

Use `scripts/jina_proxy_url.py` for deterministic conversion:

```bash
python3 scripts/jina_proxy_url.py 'https://example.com/article'
python3 scripts/jina_proxy_url.py example.com/article
python3 scripts/jina_proxy_url.py --curl 'https://example.com/article'
```

The `--curl` option prints a ready-to-run command for reading the proxied page.
