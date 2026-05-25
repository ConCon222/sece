#!/usr/bin/env python3
"""
Fetch journal cover images for publication preview thumbnails.
Downloads covers from publisher websites and saves them to assets/img/publication_preview/.
"""

import os
import sys
import time
import re
from pathlib import Path
from urllib.parse import urljoin

from curl_cffi import requests as cffi_requests
from bs4 import BeautifulSoup

PROJ_ROOT = Path(__file__).resolve().parent.parent
IMG_DIR = PROJ_ROOT / "assets" / "img" / "publication_preview"
IMG_DIR.mkdir(parents=True, exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
}

# ── Journal cover sources ─────────────────────────────────────────
# Each entry: (output_filename, fetcher_function, args)
# Filenames match what we'll put in the BibTeX `preview` field.

def fetch_url(url, **kwargs):
    """Fetch URL using curl_cffi (handles TLS fingerprinting)."""
    try:
        r = cffi_requests.get(url, headers=HEADERS, timeout=30, impersonate="chrome", **kwargs)
        r.raise_for_status()
        return r
    except Exception as e:
        print(f"  ✗ Failed to fetch {url}: {e}")
        return None


def download_image(url, filename, referer=None):
    """Download an image from URL and save to publication_preview dir."""
    out_path = IMG_DIR / filename
    if out_path.exists():
        print(f"  ✓ Already exists: {filename}")
        return True

    headers = {**HEADERS}
    if referer:
        headers["Referer"] = referer

    try:
        r = cffi_requests.get(url, headers=headers, timeout=30, impersonate="chrome")
        r.raise_for_status()
        content_type = r.headers.get("content-type", "")
        if "image" not in content_type and len(r.content) < 1000:
            print(f"  ✗ Not an image ({content_type}, {len(r.content)} bytes): {url}")
            return False
        out_path.write_bytes(r.content)
        size_kb = len(r.content) / 1024
        print(f"  ✓ Saved {filename} ({size_kb:.1f} KB)")
        return True
    except Exception as e:
        print(f"  ✗ Download failed for {filename}: {e}")
        return False


# ── Publisher-specific fetchers ─────────────────────────────────────

def fetch_springer_cover(journal_id, filename):
    """Fetch Springer journal cover via media CDN."""
    print(f"\n[Springer] Journal {journal_id} → {filename}")

    # Try the hires cover URL pattern
    urls_to_try = [
        f"https://media.springer.com/full/springer-static/cover-hires/journal/{journal_id}",
        f"https://media.springer.com/full/springer-static/cover/journal/{journal_id}",
    ]

    for url in urls_to_try:
        if download_image(url, filename):
            return True

    # Fallback: scrape the journal page for cover image
    page_url = f"https://link.springer.com/journal/{journal_id}"
    r = fetch_url(page_url)
    if r:
        soup = BeautifulSoup(r.text, "html.parser")
        # Look for cover image
        for img in soup.find_all("img"):
            src = img.get("src", "")
            if "cover" in src.lower() or "journal" in src.lower():
                full_url = urljoin(page_url, src)
                if download_image(full_url, filename, referer=page_url):
                    return True

    return False


def fetch_elsevier_cover(journal_slug, filename):
    """Fetch Elsevier/ScienceDirect journal cover."""
    print(f"\n[Elsevier] {journal_slug} → {filename}")

    page_url = f"https://www.sciencedirect.com/journal/{journal_slug}"
    r = fetch_url(page_url)
    if not r:
        return False

    soup = BeautifulSoup(r.text, "html.parser")

    # Look for journal cover image
    for img in soup.find_all("img"):
        src = img.get("src", "")
        alt = img.get("alt", "").lower()
        if "cover" in src.lower() or "cover" in alt or "journal" in alt:
            full_url = urljoin(page_url, src)
            if download_image(full_url, filename, referer=page_url):
                return True

    # Try og:image
    og_img = soup.find("meta", property="og:image")
    if og_img and og_img.get("content"):
        if download_image(og_img["content"], filename, referer=page_url):
            return True

    return False


def fetch_sage_cover(journal_code, filename):
    """Fetch SAGE journal cover."""
    print(f"\n[SAGE] {journal_code} → {filename}")

    page_url = f"https://journals.sagepub.com/home/{journal_code}"
    r = fetch_url(page_url)
    if not r:
        return False

    soup = BeautifulSoup(r.text, "html.parser")

    # SAGE typically has cover images in specific patterns
    for img in soup.find_all("img"):
        src = img.get("src", "")
        if "cover" in src.lower() or journal_code.lower() in src.lower():
            full_url = urljoin(page_url, src)
            if download_image(full_url, filename, referer=page_url):
                return True

    # Try og:image
    og_img = soup.find("meta", property="og:image")
    if og_img and og_img.get("content"):
        url = og_img["content"]
        if download_image(url, filename, referer=page_url):
            return True

    return False


def fetch_tandfonline_cover(journal_id, filename):
    """Fetch Taylor & Francis journal cover."""
    print(f"\n[T&F] {journal_id} → {filename}")

    page_url = f"https://www.tandfonline.com/toc/{journal_id}/current"
    r = fetch_url(page_url)
    if not r:
        # Try alternative URL pattern
        page_url = f"https://www.tandfonline.com/journals/{journal_id}"
        r = fetch_url(page_url)
    if not r:
        return False

    soup = BeautifulSoup(r.text, "html.parser")

    # Look for cover image
    for img in soup.find_all("img"):
        src = img.get("src", "")
        alt = img.get("alt", "").lower()
        cls = " ".join(img.get("class", []))
        if "cover" in src.lower() or "cover" in alt or "cover" in cls:
            full_url = urljoin(page_url, src)
            if download_image(full_url, filename, referer=page_url):
                return True

    # Try og:image
    og_img = soup.find("meta", property="og:image")
    if og_img and og_img.get("content"):
        url = og_img["content"]
        if url and "logo" not in url.lower():
            if download_image(url, filename, referer=page_url):
                return True

    return False


def fetch_mdpi_cover(journal_name, filename):
    """Fetch MDPI journal cover/logo."""
    print(f"\n[MDPI] {journal_name} → {filename}")

    page_url = f"https://www.mdpi.com/journal/{journal_name}"
    r = fetch_url(page_url)
    if not r:
        return False

    soup = BeautifulSoup(r.text, "html.parser")

    for img in soup.find_all("img"):
        src = img.get("src", "")
        alt = img.get("alt", "").lower()
        if "cover" in src.lower() or "cover" in alt or journal_name.lower() in alt:
            full_url = urljoin(page_url, src)
            if download_image(full_url, filename, referer=page_url):
                return True

    # Try og:image
    og_img = soup.find("meta", property="og:image")
    if og_img and og_img.get("content"):
        if download_image(og_img["content"], filename, referer=page_url):
            return True

    return False


def fetch_nature_cover(journal_id, filename):
    """Fetch Nature/Palgrave journal cover."""
    print(f"\n[Nature] {journal_id} → {filename}")

    page_url = f"https://www.nature.com/{journal_id}"
    r = fetch_url(page_url)
    if not r:
        return False

    soup = BeautifulSoup(r.text, "html.parser")

    for img in soup.find_all("img"):
        src = img.get("src", "")
        alt = img.get("alt", "").lower()
        if "cover" in src.lower() or "cover" in alt:
            full_url = urljoin(page_url, src)
            if download_image(full_url, filename, referer=page_url):
                return True

    # Try og:image
    og_img = soup.find("meta", property="og:image")
    if og_img and og_img.get("content"):
        if download_image(og_img["content"], filename, referer=page_url):
            return True

    return False


def fetch_acl_cover(venue, filename):
    """Fetch ACL Anthology venue cover/logo."""
    print(f"\n[ACL] {venue} → {filename}")

    page_url = f"https://aclanthology.org/venues/{venue}/"
    r = fetch_url(page_url)
    if not r:
        return False

    soup = BeautifulSoup(r.text, "html.parser")

    # Try og:image first
    og_img = soup.find("meta", property="og:image")
    if og_img and og_img.get("content"):
        if download_image(og_img["content"], filename, referer=page_url):
            return True

    for img in soup.find_all("img"):
        src = img.get("src", "")
        if venue.lower() in src.lower() or "logo" in src.lower():
            full_url = urljoin(page_url, src)
            if download_image(full_url, filename, referer=page_url):
                return True

    return False


def fetch_generic_cover(url, filename):
    """Fetch cover from a generic URL by finding og:image or cover images."""
    print(f"\n[Generic] {url} → {filename}")

    r = fetch_url(url)
    if not r:
        return False

    soup = BeautifulSoup(r.text, "html.parser")

    # Try og:image first
    og_img = soup.find("meta", property="og:image")
    if og_img and og_img.get("content"):
        img_url = og_img["content"]
        if not img_url.startswith("http"):
            img_url = urljoin(url, img_url)
        if download_image(img_url, filename, referer=url):
            return True

    # Look for cover images
    for img in soup.find_all("img"):
        src = img.get("src", "")
        alt = img.get("alt", "").lower()
        if "cover" in src.lower() or "cover" in alt:
            full_url = urljoin(url, src)
            if download_image(full_url, filename, referer=url):
                return True

    return False


# ── Main ─────────────────────────────────────────────────────────

def main():
    results = {}

    # ─ Journal articles ─

    # 1. Education and Information Technologies (Springer, journal 10639)
    results["eait"] = fetch_springer_cover("10639", "eait.jpg")
    time.sleep(1)

    # 2. Sustainability (MDPI)
    results["sustainability"] = fetch_mdpi_cover("sustainability", "sustainability.jpg")
    time.sleep(1)

    # 3. Humanities and Social Sciences Communications (Nature/Palgrave)
    results["palcomms"] = fetch_nature_cover("palcomms", "palcomms.jpg")
    time.sleep(1)

    # 4. Data in Brief (Elsevier)
    results["dib"] = fetch_elsevier_cover("data-in-brief", "dib.jpg")
    time.sleep(1)

    # 5. Journal of Educational Computing Research (SAGE)
    results["jecr"] = fetch_sage_cover("JER", "jecr.jpg")
    time.sleep(1)

    # 6. International Journal of Human-Computer Interaction (T&F)
    results["ijhci"] = fetch_tandfonline_cover("hihc20", "ijhci.jpg")
    time.sleep(1)

    # 7. Computer Assisted Language Learning (T&F)
    results["call"] = fetch_tandfonline_cover("ncal20", "call.jpg")
    time.sleep(1)

    # 8. 中国教育信息化 (Chinese journal) - try Wanfang or CNKI
    results["glxxht"] = fetch_generic_cover(
        "https://navi.cnki.net/knavi/journals/JYXX/detail",
        "glxxht.jpg"
    )
    time.sleep(1)

    # ─ Conference proceedings ─

    # 9. ISLS (International Society of the Learning Sciences)
    results["isls"] = fetch_generic_cover("https://www.isls.org/", "isls.jpg")
    time.sleep(1)

    # 10. AIED (Springer LNAI proceedings)
    results["aied"] = fetch_generic_cover(
        "https://link.springer.com/conference/aied",
        "aied.jpg"
    )
    time.sleep(1)

    # 11. EMNLP (ACL Anthology)
    results["emnlp"] = fetch_acl_cover("emnlp", "emnlp.jpg")
    time.sleep(1)

    # 12. CITERS
    results["citers"] = fetch_generic_cover(
        "https://citers2025.cite.hku.hk/",
        "citers.jpg"
    )

    # ─ Summary ─
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    succeeded = sum(1 for v in results.values() if v)
    failed = sum(1 for v in results.values() if not v)
    for name, ok in results.items():
        status = "✓" if ok else "✗"
        print(f"  {status} {name}")
    print(f"\nTotal: {succeeded} succeeded, {failed} failed")

    # List what's in the directory now
    print(f"\nFiles in {IMG_DIR}:")
    for f in sorted(IMG_DIR.iterdir()):
        size = f.stat().st_size / 1024
        print(f"  {f.name} ({size:.1f} KB)")


if __name__ == "__main__":
    main()
