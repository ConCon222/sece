#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scrape_aims.py — collect each journal's "Aims & Scope" text into _data/jaims.yml.

Why: the venue recommender (CFP/JR pages) matches a pasted title+abstract
against journal names + tags only — journals carry almost no topical text.
Feeding real aims & scope makes both the local keyword match and the
optional AI re-rank far more accurate.

Sources, per publisher (derived from _data/journal_rank.json URLs):
  - Springer        link.springer.com/journal/{id}/aims-and-scope   (direct)
  - Taylor&Francis  tandfonline.com/journals/{code}/about-this-journal  (FlareSolverr)
  - Wiley           .../journal/{issn}/aims-and-scope, fallback overview (FlareSolverr)
  - SAGE            journals.sagepub.com/description/{code}, fallback home (FlareSolverr)
  - Elsevier        sciencedirect.com/journal/{slug}/about/aims-and-scope (FlareSolverr)
  - Cambridge/OUP/others: journal page → aims section, fallback og:description

Data preservation: an empty/failed fetch never overwrites an existing
non-empty aims entry (same rule as the rankings pipeline).

Usage:
  python bin/scrape_aims.py            # all journals
  python bin/scrape_aims.py --direct-only   # skip FlareSolverr publishers (local testing)
  python bin/scrape_aims.py --limit 10
"""

import argparse
import json
import os
import re
import sys
import time
import random
from html import unescape
from urllib.parse import urlparse

import requests
import yaml

MASTER_JSON = "_data/journal_rank.json"
OUTPUT_YML = "_data/jaims.yml"
FLARESOLVERR_URL = os.environ.get("FLARESOLVERR_URL", "http://localhost:8191").rstrip("/")
if not FLARESOLVERR_URL.endswith("/v1"):
    FLARESOLVERR_URL += "/v1"
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")
MAX_AIMS_CHARS = 1500

# Domains that sit behind Cloudflare → must go through FlareSolverr (CI).
CF_DOMAINS = ("tandfonline.com", "sagepub.com", "wiley.com", "sciencedirect.com")


def log(msg):
    print(msg, flush=True)


def clean_text(seg: str) -> str:
    seg = re.sub(r"<script.*?</script>|<style.*?</style>", " ", seg, flags=re.S | re.I)
    seg = re.sub(r"<[^>]+>", " ", seg)
    seg = re.sub(r"\s+", " ", unescape(seg)).strip()
    return seg[:MAX_AIMS_CHARS]


def fetch_direct(url: str, timeout=25):
    try:
        r = requests.get(url, headers={"User-Agent": UA, "Accept-Language": "en"},
                         timeout=timeout, allow_redirects=True)
        if r.status_code == 200 and len(r.text) > 2000:
            return r.text
    except Exception as e:
        log(f"    direct fetch failed: {e}")
    return None


def fetch_flaresolverr(url: str, timeout_ms=60000):
    try:
        r = requests.post(FLARESOLVERR_URL, json={
            "cmd": "request.get", "url": url, "maxTimeout": timeout_ms,
        }, timeout=timeout_ms / 1000 + 15)
        data = r.json()
        if data.get("status") == "ok":
            html = data.get("solution", {}).get("response", "")
            if len(html) > 2000:
                return html
    except Exception as e:
        log(f"    flaresolverr fetch failed: {e}")
    return None


def is_cf(url: str) -> bool:
    return any(d in url for d in CF_DOMAINS)


def fetch(url: str, allow_flaresolverr=True):
    if is_cf(url):
        return fetch_flaresolverr(url) if allow_flaresolverr else None
    return fetch_direct(url)


# ---------- aims-page derivation ----------

def aims_candidates(url: str):
    """Return candidate URLs (in priority order) for the aims & scope text."""
    host = urlparse(url).netloc.lower()
    out = []
    if "link.springer.com" in host:
        m = re.search(r"/journal/(\d+)", url)
        if m:
            out.append(f"https://link.springer.com/journal/{m.group(1)}/aims-and-scope")
    elif "tandfonline.com" in host:
        m = re.search(r"/journals/([a-z0-9]+)", url, re.I)
        if m:
            out.append(f"https://www.tandfonline.com/journals/{m.group(1)}/about-this-journal")
    elif "wiley.com" in host:
        m = re.search(r"/journal/(\d{8,9}[\dxX]?)", url)
        if m:
            base = f"https://{urlparse(url).netloc}"
            out.append(f"{base}/journal/{m.group(1)}/aims-and-scope")
            out.append(f"{base}/journal/{m.group(1)}")
    elif "sagepub.com" in host:
        m = re.search(r"/home/([a-z0-9]+)", url, re.I)
        if m:
            out.append(f"https://journals.sagepub.com/description/{m.group(1)}")
            out.append(f"https://journals.sagepub.com/home/{m.group(1)}")
    elif "sciencedirect.com" in host:
        m = re.search(r"/journal/([a-z0-9-]+)", url, re.I)
        if m:
            out.append(f"https://www.sciencedirect.com/journal/{m.group(1)}/about/aims-and-scope")
    out.append(url)  # last resort: the master URL itself
    return out


# ---------- aims extraction ----------

AIMS_HEADING = r"(?:Aims (?:and|&(?:amp;)?)\s*[Ss]cope|About (?:the|this) [Jj]ournal|Journal [Oo]verview)"

def extract_aims(html: str):
    # 1) heading-anchored section (most publishers)
    m = re.search(AIMS_HEADING + r"\s*</h\d>(.*?)(?:<h\d|</section>|</article>)", html, re.S)
    if m:
        t = clean_text(m.group(1))
        if len(t) > 120:
            return t
    # 2) heading inside div blocks (Wiley/SAGE markup variants)
    m = re.search(AIMS_HEADING + r"\s*</(?:div|span|strong|b)>(.*?)(?:<h\d|</section>)", html, re.S)
    if m:
        t = clean_text(m.group(1))
        if len(t) > 120:
            return t
    # 3) og:description / meta description fallback
    for pat in (r'<meta property="og:description" content="([^"]{120,})"',
                r'<meta name="description" content="([^"]{120,})"'):
        m = re.search(pat, html)
        if m:
            return clean_text(m.group(1))
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--direct-only", action="store_true",
                    help="skip Cloudflare publishers (no FlareSolverr; for local runs)")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--force", action="store_true", help="re-fetch even if aims already stored")
    args = ap.parse_args()

    with open(MASTER_JSON, encoding="utf-8") as f:
        journals = json.load(f)

    existing = {}
    if os.path.exists(OUTPUT_YML):
        with open(OUTPUT_YML, encoding="utf-8") as f:
            existing = yaml.safe_load(f) or {}
    log(f"📂 master journals: {len(journals)} | existing aims: {len(existing)}")

    done = fail = skip = 0
    for i, j in enumerate(journals):
        name, url = j.get("name"), j.get("url", "")
        if not name or not url:
            continue
        if args.limit and done + fail >= args.limit:
            break
        if not args.force and existing.get(name, {}).get("aims"):
            skip += 1
            continue
        if args.direct_only and is_cf(url):
            skip += 1
            continue

        log(f"[{i+1}/{len(journals)}] {name}")
        aims = None
        for cand in aims_candidates(url):
            html = fetch(cand, allow_flaresolverr=not args.direct_only)
            if not html:
                continue
            aims = extract_aims(html)
            if aims:
                existing[name] = {"aims": aims, "source": cand}
                log(f"    ✅ {len(aims)} chars from {cand}")
                break
        if aims:
            done += 1
        else:
            fail += 1
            log("    ❌ no aims found")
        time.sleep(random.uniform(1.0, 2.5))

    with open(OUTPUT_YML, "w", encoding="utf-8") as f:
        yaml.safe_dump(existing, f, allow_unicode=True, sort_keys=True,
                       default_flow_style=False, width=120)
    log(f"\n🎉 fetched={done} failed={fail} skipped={skip} | total stored={len(existing)} → {OUTPUT_YML}")


if __name__ == "__main__":
    main()
