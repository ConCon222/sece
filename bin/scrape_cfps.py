import re
import time
import os
import yaml
import random
import calendar
import tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
from urllib.parse import parse_qs, urlencode, urljoin, urlsplit, urlunsplit
from bs4 import BeautifulSoup

# === 核心库 ===
from curl_cffi import requests
from DrissionPage import ChromiumPage, ChromiumOptions

# ==========================================
# ⚙️ 配置区域
# ==========================================
FLARESOLVERR_URL = os.environ.get("FLARESOLVERR_URL", "http://localhost:8191").rstrip("/")
FLARESOLVERR_AVAILABLE = False              # 运行时动态检测
NATURE_MAX_PAGES = max(1, int(os.environ.get("NATURE_MAX_PAGES", "120")))
NATURE_DETAIL_WORKERS = max(1, min(8, int(os.environ.get("NATURE_DETAIL_WORKERS", "4"))))


def check_flaresolverr_health():
    """检测 FlareSolverr 是否可用，结果写入全局变量"""
    global FLARESOLVERR_AVAILABLE
    try:
        import requests as std_requests
        resp = std_requests.get(f"{FLARESOLVERR_URL}/health", timeout=5)
        if resp.status_code == 200 and "ok" in resp.text.lower():
            FLARESOLVERR_AVAILABLE = True
            print("✅ FlareSolverr 已就绪")
        else:
            FLARESOLVERR_AVAILABLE = False
            print("⚠️ FlareSolverr 健康检查未返回 ok，将对 CF 站点使用 curl_cffi 回退")
    except Exception as e:
        FLARESOLVERR_AVAILABLE = False
        print(f"⚠️ FlareSolverr 不可用 ({e})，将对 CF 站点使用 curl_cffi 回退")
    return FLARESOLVERR_AVAILABLE


# 从 JSON 加载期刊列表（yaml.safe_load 兼容 JSON）
def load_journals(filepath="_data/journal_cfp.json"):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            journals = yaml.safe_load(f) or []
        if not isinstance(journals, list):
            raise ValueError(f"{filepath} 顶层必须是列表")

        cleaned = []
        seen = set()
        for index, journal in enumerate(journals, start=1):
            if not isinstance(journal, dict):
                raise ValueError(f"{filepath} 第 {index} 项不是对象")
            item = journal.copy()
            item["name"] = str(item.get("name") or "").strip()
            item["url"] = str(item.get("url") or "").strip()
            if item.get("cfp_url"):
                item["cfp_url"] = str(item["cfp_url"]).strip()
            if not item["name"] or not item["url"]:
                raise ValueError(f"{filepath} 第 {index} 项缺少 name/url")
            parsed = urlsplit(item["url"])
            if parsed.scheme not in {"http", "https"} or not parsed.netloc:
                raise ValueError(f"{filepath} 第 {index} 项 URL 非法: {item['url']}")
            key = (item["name"].casefold(), item["url"])
            if key in seen:
                raise ValueError(f"{filepath} 存在重复期刊配置: {item['name']}")
            seen.add(key)
            cleaned.append(item)
        return cleaned
    except FileNotFoundError:
        print(f"❌ 错误：找不到文件 {filepath}")
        return []
    except yaml.YAMLError as e:
        print(f"❌ 错误：YAML 格式解析失败: {e}")
        return []
    except ValueError as e:
        print(f"❌ 错误：期刊配置无效: {e}")
        return []


# 初始化变量
JOURNALS = load_journals()
OUTPUT_YML_PATH = "_data/cfps.yml"

MONTH_MAP = {
    'jan': 1, 'january': 1, 'feb': 2, 'february': 2,
    'mar': 3, 'march': 3, 'apr': 4, 'april': 4, 'may': 5,
    'jun': 6, 'june': 6, 'jul': 7, 'july': 7, 'aug': 8, 'august': 8,
    'sep': 9, 'sept': 9, 'september': 9, 'oct': 10, 'october': 10,
    'nov': 11, 'november': 11, 'dec': 12, 'december': 12,
}

# Cloudflare / bot-protection 保护的站点列表
CF_PROTECTED_SITES = [
    "tandfonline.com",
    "wiley.com",
    "onlinelibrary.wiley",
    "sagepub.com",
    "bera-journals",
    "academic.oup.com",       # Oxford — Cloudflare
    "journals.uchicago.edu",  # UChicago Press — Cloudflare
    "pnas.org",               # PNAS — Cloudflare
    "link.springer.com",      # 2026-06: idp.springer.com cookie/JS 门
    "sciencedirect.com",      # Elsevier — curl_cffi 在云 IP 上 403
    "nature.com",             # 2026-06-10 前后铺了同一个 idp 门
]


class JournalCFPScraper:
    def __init__(self):
        self.date_pattern = re.compile(
            r"\b(?:"
            r"\d{4}-\d{1,2}-\d{1,2}|"
            r"\d{1,2}[/-]\d{1,2}[/-]\d{4}|"
            r"\d{1,2}(?:st|nd|rd|th)?\s+"
            r"(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)[a-z]*\s+\d{4}|"
            r"(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)[a-z]*\s+"
            r"\d{1,2}(?:st|nd|rd|th)?,?\s+\d{4}|"
            r"(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)[a-z]*\s+\d{4}"
            r")\b",
            re.I,
        )

        # Session 用于快速抓取 (Elsevier/Springer/Cambridge/Nature/OUP等)
        self.session = requests.Session()

        # DrissionPage 延迟初始化（仅 T&F 需要）
        self._browser = None
        self._browser_cookies_injected = False
        self._nature_scan_complete = False
        self._known_deadlines_by_link = {}

    @property
    def browser(self):
        """延迟初始化浏览器，只在需要时启动"""
        if self._browser is None:
            print("⚙️ 初始化 DrissionPage 浏览器...")
            co = ChromiumOptions()
            co.headless(True)
            co.set_argument("--no-sandbox")
            co.set_argument("--disable-gpu")
            co.set_argument("--disable-blink-features=AutomationControlled")
            co.set_argument("--disable-infobars")
            co.set_user_agent("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
            co.set_argument("--window-size=1920,1080")
            co.set_argument("--start-maximized")
            co.set_argument("--lang=en-US")
            self._browser = ChromiumPage(co)
            self._browser.run_js("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        return self._browser

    def __del__(self):
        try:
            if self._browser:
                self._browser.quit()
        except Exception:
            pass

    # ==========================================
    # FlareSolverr 集成
    # ==========================================
    def needs_flaresolverr(self, url):
        """判断是否需要 FlareSolverr"""
        return any(site in url.lower() for site in CF_PROTECTED_SITES)

    def _is_error_or_challenge_page(self, html, status_code=None):
        """Reject HTTP errors, bot challenges, and publisher error pages."""
        if status_code is not None:
            try:
                if int(status_code) >= 400:
                    return True
            except (TypeError, ValueError):
                pass
        if not html:
            return True
        text = str(html)
        sample = text[:12000].lower()
        markers = (
            "<title>just a moment",
            "cf-chl-",
            "attention required",
            "access denied",
            "captcha-delivery",
            "incapsula incident",
            "404 error",
            "<title>page not found",
        )
        return any(marker in sample for marker in markers)

    @staticmethod
    def _canonical_link(link):
        """Normalize links for validation and de-duplication."""
        if not link:
            return ""
        try:
            parsed = urlsplit(str(link).strip())
            if parsed.scheme not in {"http", "https"} or not parsed.netloc:
                return ""
            path = re.sub(r"/+$", "", parsed.path) or "/"
            return urlunsplit((parsed.scheme.lower(), parsed.netloc.lower(), path, parsed.query, ""))
        except (TypeError, ValueError):
            return ""

    def _is_non_cfp_candidate(self, title, link, context=""):
        """Reject clearly non-submission pages before they enter persistent data."""
        title_l = self.clean_text(title).casefold()
        context_l = self.clean_text(context).casefold()
        link_l = self._canonical_link(link).casefold()
        if not title_l or not link_l:
            return True

        junk_title_markers = (
            "call for editor-in-chief",
            "call for guest editor",
            "guest editor opportunity",
            "special issues collection",
            "published and upcoming special issues",
            "virtual special issue",
            "learn about our special collections",
            "see jrai's website",
            "tools, tips, and journal insights",
            "early career reviewer",
            "75th anniversary collection",
            "call for reviewers",
            "reviewer recruitment",
            "painting special issue",
            "new special issue",
            "special issue 2024",
        )
        junk_url_markers = (
            "/doi/",
            "/doi/toc/",
            "/toc/",
            "editor_recruitment",
            "editor-recruitment",
            "reviewer-award",
            "reviewer-prize",
            "associate-editor",
            "editors-needed",
            "editor-needed",
            "reviewers-needed",
        )
        published_markers = (
            "has published",
            "now published",
            "read the special issue",
            "read this special issue",
        )
        return (
            any(marker in title_l for marker in junk_title_markers)
            or any(marker in link_l for marker in junk_url_markers)
            or any(marker in context_l for marker in published_markers)
        )

    def fetch_with_flaresolverr(self, url, max_timeout=60000):
        """
        使用 FlareSolverr 获取页面
        返回: (html, cookies, user_agent) 或 (None, None, None)
        """
        import requests as std_requests  # 用标准 requests 调用 FlareSolverr API

        try:
            print(f"   🛡️ [FlareSolverr] 正在过盾: {url}")
            resp = std_requests.post(
                f"{FLARESOLVERR_URL}/v1",
                json={
                    "cmd": "request.get",
                    "url": url,
                    "maxTimeout": max_timeout
                },
                timeout=120
            )
            data = resp.json()

            if data.get("status") == "ok":
                solution = data.get("solution", {})
                html = solution.get("response", "")
                status_code = solution.get("status")
                cookies = solution.get("cookies", [])
                user_agent = solution.get("userAgent", "")
                if self._is_error_or_challenge_page(html, status_code):
                    print(f"   ❌ [FlareSolverr] 返回错误/挑战页 (HTTP {status_code or 'unknown'})")
                    return None, None, None
                print(f"   ✅ [FlareSolverr] 成功! 获取 {len(html)} 字节, {len(cookies)} 个 cookies")
                return html, cookies, user_agent
            else:
                print(f"   ❌ [FlareSolverr] 失败: {data.get('message')}")
                return None, None, None

        except Exception as e:
            print(f"   ❌ [FlareSolverr] 异常: {e}")
            return None, None, None

    def fetch_cf_site(self, url):
        """
        CF 保护站点的统一入口：
        - FlareSolverr 可用时优先使用
        - 不可用时回退到 curl_cffi（部分站点仍可绕过）
        返回: html 字符串或 None
        """
        if FLARESOLVERR_AVAILABLE:
            html, _, _ = self.fetch_with_flaresolverr(url)
            return html
        else:
            print(f"   ↩️ [curl_cffi 回退] {url}")
            return self.fetch_page_fast(url)

    def inject_cookies_to_browser(self, url, cookies, user_agent=None):
        """将 FlareSolverr 获取的 cookies 注入到 DrissionPage"""
        try:
            from urllib.parse import urlparse
            domain = urlparse(url).netloc
            base_url = f"https://{domain}"

            print(f"   🍪 注入 cookies 到浏览器 (域: {domain})...")
            self.browser.get(base_url)
            time.sleep(2)

            for cookie in cookies:
                try:
                    cookie_script = f"""
                    document.cookie = "{cookie['name']}={cookie['value']}; domain={cookie.get('domain', domain)}; path={cookie.get('path', '/')}";
                    """
                    self.browser.run_js(cookie_script)
                except Exception as e:
                    print(f"   ⚠️ Cookie 注入失败: {cookie.get('name')}: {e}")

            self._browser_cookies_injected = True
            print(f"   ✅ 成功注入 {len(cookies)} 个 cookies")
            return True

        except Exception as e:
            print(f"   ❌ Cookies 注入失败: {e}")
            return False

    # --------------------------
    # 通用工具 (保持不变)
    # --------------------------
    def clean_text(self, text):
        if not text: return "N/A"
        return re.sub(r"\s+", " ", str(text)).strip()

    def normalize_for_date_extraction(self, text):
        if not text: return ""
        text = re.sub(r'<[^>]+>', '', str(text))
        text = re.sub(r'(\d)(st|nd|rd|th)\b', r'\1', text, flags=re.I)
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    def extract_dates(self, text):
        if not text:
            return []
        normalized = self.normalize_for_date_extraction(text)
        return [self.clean_text(match.group(0)) for match in self.date_pattern.finditer(normalized)]

    def extract_date(self, text):
        dates = self.extract_dates(text)
        return dates[0] if dates else None

    def _single_date_to_sort_key(self, value):
        normalized = self.normalize_for_date_extraction(value)
        try:
            match = re.fullmatch(r'(\d{4})-(\d{1,2})-(\d{1,2})', normalized)
            if match:
                parsed = datetime(int(match.group(1)), int(match.group(2)), int(match.group(3)))
                return parsed.strftime("%Y-%m-%d")

            match = re.fullmatch(r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})', normalized)
            if match:
                # Publisher pages in this project use day-first numeric dates.
                parsed = datetime(int(match.group(3)), int(match.group(2)), int(match.group(1)))
                return parsed.strftime("%Y-%m-%d")

            match = re.fullmatch(r'(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})', normalized)
            if match:
                day, month_text, year = int(match.group(1)), match.group(2).lower(), int(match.group(3))
                month = MONTH_MAP.get(month_text[:3])
                if month:
                    return datetime(year, month, day).strftime("%Y-%m-%d")

            match = re.fullmatch(r'([A-Za-z]+)\s+(\d{1,2}),?\s+(\d{4})', normalized)
            if match:
                month_text, day, year = match.group(1).lower(), int(match.group(2)), int(match.group(3))
                month = MONTH_MAP.get(month_text[:3])
                if month:
                    return datetime(year, month, day).strftime("%Y-%m-%d")

            match = re.fullmatch(r'([A-Za-z]+)\s+(\d{4})', normalized)
            if match:
                month = MONTH_MAP.get(match.group(1).lower()[:3])
                year = int(match.group(2))
                if month:
                    # Month-only deadlines sort at the end of that month rather
                    # than remaining TBA forever.
                    return f"{year:04d}-{month:02d}-{calendar.monthrange(year, month)[1]:02d}"
        except (TypeError, ValueError):
            return None
        return None

    def parse_date_to_sort_key(self, date_str):
        default_date = "9999-99-99"
        if not date_str or date_str in {"N/A", "未找到日期", ""}:
            return default_date
        # Date ranges and paragraphs containing both abstract/full-paper
        # deadlines must sort by the final (usually full-paper) date.
        for candidate in reversed(self.extract_dates(date_str)):
            sort_key = self._single_date_to_sort_key(candidate)
            if sort_key:
                return sort_key
        return default_date

    def fetch_page_fast(self, url, timeout=30):
        """非 Cloudflare 站点用 curl_cffi"""
        try:
            print(f"   🚀 [curl_cffi] 正在访问: {url}")
            resp = self.session.get(
                url,
                impersonate="chrome120",
                timeout=timeout,
                headers={
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    "Accept-Language": "en-US,en;q=0.9",
                },
            )
            if resp.status_code == 200 and not self._is_error_or_challenge_page(resp.text, resp.status_code):
                return resp.text
            print(f"   ❌ 状态码错误 {resp.status_code}")
        except Exception as e:
            print(f"   ❌ 请求异常: {e}")
        return None

    # --------------------------
    # Browser 工具
    # --------------------------
    def try_accept_cookies(self):
        selectors = ["css:#onetrust-accept-btn-handler", "text:Accept All Cookies", "text:Accept all", "text:Accept", "text:I Agree"]
        for sel in selectors:
            try:
                ele = self.browser.ele(sel, timeout=1)
                if ele:
                    ele.click()
                    time.sleep(1)
                    break
            except Exception:
                pass

    def get_html_browser_safe(self, url, wait=5, scroll_rounds=2):
        """使用 DrissionPage 获取页面（已注入 cookies 后使用）"""
        print(f"   🌐 [DrissionPage] GET {url}")
        try:
            self.browser.get(url)
            time.sleep(wait)

            self.try_accept_cookies()
            time.sleep(0.8)

            if scroll_rounds > 0:
                for _ in range(scroll_rounds):
                    try:
                        self.browser.scroll.to_bottom()
                        time.sleep(0.8)
                    except: pass

            return self.browser.html
        except Exception as e:
            print(f"   ❌ 浏览器加载异常: {e}")
            return None

    # ==========================================
    # 解析器部分
    # ==========================================
    def _extract_text_clean(self, element):
        if not element: return ""
        html_str = str(element)
        html_str = re.sub(r'<sup[^>]*>.*?</sup>', '', html_str, flags=re.I | re.DOTALL)
        temp_soup = BeautifulSoup(html_str, 'lxml')
        return self.clean_text(temp_soup.get_text(' ', strip=True))

    # --- Wiley (保持不变) ---
    def _parse_wiley_dst_listing(self, soup, journal_url):
        wrap = soup.select_one("div.DST-CFP-listing-wrap")
        if not wrap: return []
        results = []
        for it in wrap.select("div.DST-CFP-listing-item"):
            a_title = it.select_one("h3 a[href]")
            if not a_title: continue
            title = self._extract_text_clean(a_title)
            link = urljoin(journal_url, a_title.get("href"))
            a_more = it.select_one("a.DST-CFP-listing-item__more[href]")
            if a_more and a_more.get("href"): link = urljoin(journal_url, a_more.get("href"))

            d_el = it.select_one("p.DST-CFP-listing-item__deadline")
            deadline_text = self._extract_text_clean(d_el) if d_el else ""
            dt = self.extract_date(deadline_text)
            deadline = dt or (self.clean_text(deadline_text.split(":", 1)[1]) if ":" in deadline_text else "未找到日期")
            if self._is_non_cfp_candidate(title, link, deadline_text):
                continue
            results.append({"title": title, "abstract_deadline": "未找到日期", "fullpaper_deadline": deadline, "editors": "N/A", "desc": "N/A", "link": link})
        return results

    def _parse_wiley_h4_blocks(self, soup, journal_url):
        results = []
        for h4 in soup.find_all("h4"):
            try:
                a_tags = h4.find_all("a", href=True)
                if not a_tags: continue
                candidates = []
                for a in a_tags:
                    t = self._extract_text_clean(a)
                    if t and len(t) >= 3: candidates.append((len(t), t, a.get("href")))
                if not candidates: continue
                candidates.sort(reverse=True, key=lambda x: x[0])
                _, title, href = candidates[0]
                link = urljoin(journal_url, href)

                abstract_deadline, fullpaper_deadline, editor_list = "未找到日期", "未找到日期", []
                block_texts = []
                for sib in h4.find_next_siblings():
                    if sib.name in {"h4", "hr"}: break
                    if sib.name == "div" and "border-top" in (sib.get("style") or "").lower(): break
                    sibling_text = self._extract_text_clean(sib)
                    if sibling_text:
                        block_texts.append(sibling_text)
                    if sib.name == "p":
                        # Some Wiley pages put abstract and full-paper deadlines
                        # in separate <strong> nodes inside the same paragraph.
                        segments = sib.find_all(["strong", "b"]) or [sib]
                        for segment in segments:
                            txt = self._extract_text_clean(segment)
                            lower = txt.lower()
                            if "deadline" not in lower:
                                continue
                            dates = self.extract_dates(txt)
                            dt = dates[-1] if dates else None
                            if "abstract" in lower:
                                abstract_deadline = dt or abstract_deadline
                            elif "full paper" in lower or "full-paper" in lower or "manuscript" in lower:
                                fullpaper_deadline = dt or fullpaper_deadline
                            elif dt and fullpaper_deadline == "未找到日期":
                                fullpaper_deadline = dt
                    if sib.name == "ul":
                        editor_list = [self._extract_text_clean(li) for li in sib.find_all("li") if li.get_text(strip=True)]

                context = " ".join(block_texts)
                has_submission_evidence = bool(
                    re.search(r"\b(call for papers?|submission deadline|deadline for .{0,40}submissions?|submit (?:an? )?(?:abstract|paper|manuscript))\b", context, re.I)
                    or re.search(r"(call[-_/]?for[-_/]?papers?|special[-_/]?issues?|cfp)", link, re.I)
                )
                if title and title != "N/A" and has_submission_evidence and not self._is_non_cfp_candidate(title, link, context):
                    results.append({"title": title, "abstract_deadline": abstract_deadline, "fullpaper_deadline": fullpaper_deadline, "editors": "; ".join(editor_list) if editor_list else "N/A", "desc": "N/A", "link": link})
            except Exception: continue
        return results

    def parse_wiley_from_html(self, html, journal_url):
        """从 HTML 解析 Wiley（FlareSolverr 返回的 HTML）"""
        if not html: return []
        soup = BeautifulSoup(html, "lxml")
        results = self._parse_wiley_dst_listing(soup, journal_url) + self._parse_wiley_h4_blocks(soup, journal_url)
        uniq = {}
        for r in results:
            if not self._is_non_cfp_candidate(r.get("title"), r.get("link")):
                uniq[(r.get("title"), self._canonical_link(r.get("link")))] = r
        return list(uniq.values())

    # --- T&F (保持解析逻辑不变) ---
    def _tf_parse_detail_page_html(self, html, page_url):
        if self._is_error_or_challenge_page(html):
            return None
        soup = BeautifulSoup(html, "lxml")
        page_text = self.clean_text(soup.get_text(" ", strip=True))
        has_deadline_section = bool(soup.select("section.layout__deadline--title"))
        has_submission_evidence = bool(
            re.search(
                r"\b(call for papers?|call for submissions?|submission deadline|"
                r"deadline for .{0,50}submissions?|submit (?:your|a|an)?\s*(?:paper|article|manuscript|abstract))\b",
                page_text,
                re.I,
            )
        )
        if not has_deadline_section and not has_submission_evidence:
            return None

        title = "未知标题"
        hero_h2 = soup.select_one("section.layout__hero h2")
        if hero_h2: title = self._extract_text_clean(hero_h2)
        else:
            h2 = soup.find("h2")
            if h2: title = self._extract_text_clean(h2)

        abstract_deadline, fullpaper_deadline, editors, desc = "未找到日期", "未找到日期", "N/A", "N/A"
        for sec in soup.select("section.layout__deadline--title"):
            val = self._extract_text_clean(sec.select_one("time"))
            label = self._extract_text_clean(sec.select_one("h3")).lower()
            dt = self.extract_date(val) or val
            if "abstract" in label: abstract_deadline = dt or abstract_deadline
            elif "manuscript" in label or "full" in label or "paper" in label: fullpaper_deadline = dt or fullpaper_deadline

        ed_sec = soup.select_one("section.layout__editors")
        if ed_sec:
            people = []
            for p in ed_sec.select("p"):
                name = self._extract_text_clean(p.select_one("strong"))
                aff = self._extract_text_clean(p.select_one("em"))
                if name and name != "N/A": people.append(f"{name} ({aff})" if aff and aff != "N/A" else name)
            if people: editors = "; ".join(people)

        about = soup.select_one("section.layout__about") or soup.select_one("main#main-content")
        if about:
            ps = [self._extract_text_clean(p) for p in about.select("p") if len(self._extract_text_clean(p)) >= 80]
            if ps: desc = max(ps, key=len)

        if self._is_non_cfp_candidate(title, page_url, page_text):
            return None
        return {"title": title, "abstract_deadline": abstract_deadline, "fullpaper_deadline": fullpaper_deadline, "editors": editors, "desc": desc, "link": page_url}

    def parse_taylor_francis(self, journal_url):
        """
        T&F 解析：
        1. FlareSolverr/curl_cffi 获取主页 HTML + cookies
        2. 从 HTML 中提取 think.taylorandfrancis.com 链接
        3. 对每个详情页，用 FlareSolverr 单独获取
        """
        results = []
        try:
            html = self.fetch_cf_site(journal_url)
            if not html:
                print(f"   ⚠️ T&F 主页获取失败")
                return []

            soup = BeautifulSoup(html, "lxml")
            target_links = []
            cfp_container = soup.select_one(".cfpContent") or soup
            for a in cfp_container.select("a[href]"):
                href = a.get("href", "")
                if "think.taylorandfrancis.com" in href:
                    anchor_context = f"{self._extract_text_clean(a)} {href}"
                    if re.search(
                        r"(special_issues|article_collections|call[-_/ ]?for[-_/ ]?papers?|/cfp(?:/|$))",
                        anchor_context,
                        re.I,
                    ):
                        target_links.append(href)

            unique_links = list(dict.fromkeys(target_links))
            print(f"   🔎 T&F 发现 {len(unique_links)} 个详情页链接")

            for link_url in unique_links:
                try:
                    if FLARESOLVERR_AVAILABLE:
                        detail_html, _, _ = self.fetch_with_flaresolverr(link_url, max_timeout=45000)
                    else:
                        detail_html = self.fetch_page_fast(link_url)
                    if detail_html:
                        result = self._tf_parse_detail_page_html(detail_html, link_url)
                        if result:
                            results.append(result)
                    time.sleep(random.uniform(2, 4))
                except Exception as e:
                    print(f"   ⚠️ T&F 子页面处理失败: {e}")

        except Exception as e:
            print(f"   ❌ T&F 异常: {e}")

        uniq = {}
        for r in results: uniq[(r.get("title"), r.get("link"))] = r
        return list(uniq.values())

    # --- SAGE (支持 journals.sagepub.com 和 uk.sagepub.com) ---
    def parse_sage_from_html(self, html, journal_url):
        """从 HTML 解析 SAGE (marketing-spot 卡片格式)"""
        if not html: return []
        soup = BeautifulSoup(html, "lxml")
        results = []
        for card in soup.select("div.marketing-spot"):
            title = self._extract_text_clean(card.select_one("h3.marketing-spot__title"))
            desc = self._extract_text_clean(card.select_one("div.marketing-spot__text"))
            a = card.select_one("div.marketing-spot__footer a[href]")
            if not a:
                continue
            link = urljoin(journal_url, a["href"])
            if "closed" in desc.lower() or title == "N/A": continue
            if any(x in title.lower() or x in desc.lower() for x in ["why publish", "reviewer resources", "discipline hubs"]): continue
            if not ("call" in title.lower() or "special issue" in title.lower() or "submit" in desc.lower()): continue
            if self._is_non_cfp_candidate(title, link, desc):
                continue

            deadline = self.extract_date(desc) or "未找到日期"
            results.append({"title": title, "abstract_deadline": "未找到日期", "fullpaper_deadline": deadline, "editors": "N/A", "desc": desc, "link": link})

        # Fallback: uk.sagepub.com 使用不同结构
        if not results:
            results = self._parse_sage_uk_fallback(soup, journal_url)

        uniq = {}
        for r in results: uniq[(r["title"], r["link"])] = r
        return list(uniq.values())

    def _parse_sage_uk_fallback(self, soup, journal_url):
        """uk.sagepub.com 页面的回退解析器"""
        results = []
        # 尝试通用文章卡片
        for card in soup.find_all(["article", "div"], class_=re.compile(r"issue|special|cfp|call", re.I)):
            try:
                h = card.find(["h2", "h3", "h4"])
                if not h: continue
                title = self._extract_text_clean(h)
                if not title or title == "N/A": continue
                a = h.find("a", href=True) or card.find("a", href=True)
                link = urljoin(journal_url, a["href"]) if a else journal_url
                text = card.get_text(" ", strip=True)
                if not re.search(r'call|special issue|submit', text, re.I): continue
                if self._is_non_cfp_candidate(title, link, text): continue
                deadline = self.extract_date(text) or "未找到日期"
                desc_p = card.find("p")
                desc = self._extract_text_clean(desc_p) if desc_p else "N/A"
                results.append({"title": title, "abstract_deadline": "未找到日期", "fullpaper_deadline": deadline, "editors": "N/A", "desc": desc, "link": link})
            except Exception:
                continue
        return results

    # --- Elsevier (保持不变) ---
    def parse_elsevier(self, html, base_url):
        soup = BeautifulSoup(html, "lxml")
        results = []
        header = soup.find(["h2", "h3"], string=re.compile("Call for papers", re.I))
        container = header.find_next("ul", class_="sub-list") if header else soup.find("ul", class_="sub-list")
        if not container: return []
        for item in container.find_all("li"):
            try:
                h3 = item.find("h3")
                if not h3: continue
                title = self._extract_text_clean(h3.find("a"))
                link = urljoin(base_url, h3.find("a")["href"])
                desc = "N/A"
                intro = item.find("p", class_="intro")
                if intro: desc = self._extract_text_clean(intro)
                d_div = item.find(lambda t: t.name == "div" and "Submission deadline" in t.get_text())
                deadline = self._extract_text_clean(d_div.find("strong")) if d_div and d_div.find("strong") else (self._extract_text_clean(d_div) if d_div else "未找到日期")
                editors = self._extract_text_clean(item.find("p", class_="summary")) if item.find("p", class_="summary") else "N/A"
                results.append({"title": title, "abstract_deadline": "未找到日期", "fullpaper_deadline": deadline, "editors": editors, "desc": desc, "link": link})
            except: continue
        return results

    # --- Springer (保持不变) ---
    def parse_springer(self, html, base_url):
        soup = BeautifulSoup(html, "lxml")
        results = []
        for art in soup.find_all("article", class_="app-card-collection"):
            try:
                heading = art.find(["h2", "h3"], class_=re.compile("heading"))
                title = self._extract_text_clean(heading.find("a")) if heading else "N/A"
                link = urljoin(base_url, heading.find("a")["href"]) if heading else "N/A"
                desc = self._extract_text_clean(art.find("div", class_="app-card-collection__text"))
                deadline = "未找到日期"
                for dt in art.find_all("dt"):
                    if "deadline" in dt.get_text().lower() and dt.find_next_sibling("dd"):
                        deadline = self._extract_text_clean(dt.find_next_sibling("dd"))
                        break
                if deadline != "未找到日期":
                    results.append({"title": title, "abstract_deadline": "未找到日期", "fullpaper_deadline": deadline, "editors": "N/A", "desc": desc, "link": link})
            except: continue
        return results

    # --- Cambridge Core (保持不变) ---
    def parse_cambridge_core_call_for_papers(self, html, base_url):
        soup = BeautifulSoup(html, "lxml")
        results = []
        for ov in (soup.select_one("#maincontent") or soup).select("ul.overview.no-margin-bottom-for-small"):
            a = ov.select_one("li.title a[href]")
            if not a: continue
            title = self._extract_text_clean(a)
            link = urljoin(base_url, a["href"])
            date_el = ov.select_one("li.date")
            deadline = self._extract_text_clean(date_el) if date_el else "未找到日期"
            desc = self._extract_text_clean(ov.select_one("li.description"))
            results.append({"title": title, "abstract_deadline": "未找到日期", "fullpaper_deadline": deadline, "editors": "N/A", "desc": desc, "link": link})
        uniq = {}
        for r in results: uniq[(r["title"], r["link"])] = r
        return list(uniq.values())

    # ==========================================
    # 新增解析器
    # ==========================================

    # --- Nature Portfolio ---
    def _fetch_nature_html(self, url, allow_flaresolverr=True):
        """Nature usually works with curl; only fall back to FlareSolverr when needed."""
        try:
            # Use an independent request per worker; sharing curl_cffi.Session
            # across the deadline thread pool is not guaranteed to be safe.
            response = requests.get(
                url,
                impersonate="chrome",
                timeout=35,
                headers={
                    "User-Agent": self.ua,
                    "Accept-Language": "en-US,en;q=0.9",
                },
            )
            if response.status_code == 200 and not self._is_error_or_challenge_page(response.text, response.status_code):
                return response.text
        except Exception as exc:
            print(f"   ⚠️ Nature 快速请求失败 {url}: {exc}")
        return self.fetch_cf_site(url) if allow_flaresolverr else None

    def _fetch_nature_deadline(self, url):
        """Fetch one Nature collection page and extract its submission deadline."""
        cached = self._known_deadlines_by_link.get(self._canonical_link(url))
        if cached:
            return cached
        try:
            html = self._fetch_nature_html(url, allow_flaresolverr=False)
            if not html:
                return ""
            soup = BeautifulSoup(html, "lxml")
            for sel in ['[data-test="submission-deadline"]',
                        'time[itemprop="submissionDeadline"]',
                        '[data-test="deadline"]']:
                el = soup.select_one(sel)
                if el:
                    d = self.extract_date(self._extract_text_clean(el))
                    if d:
                        return d
            page_text = soup.get_text(" ", strip=True)
            m = re.search(
                r'Submission deadline[:\s]*'
                r'(\d{1,2}\s+[A-Za-z]+\s+\d{4}|[A-Za-z]+\s+\d{1,2},?\s+\d{4}|\d{4}-\d{2}-\d{2})',
                page_text, re.I)
            if m:
                return self.extract_date(m.group(1)) or self.clean_text(m.group(1))
        except Exception as e:
            print(f"   ⚠️ Nature deadline 抓取失败 {url}: {e}")
        return ""

    def _parse_nature_listing(self, html, base_url):
        """Parse open collection cards from one Nature listing page."""
        if not html:
            return []
        soup = BeautifulSoup(html, "lxml")
        results = []
        for art in soup.find_all("article"):
            try:
                open_pill = art.find("div", {"data-test": "open-status"})
                if not open_pill or "open for submissions" not in open_pill.get_text(strip=True).lower():
                    continue
                h3 = art.find("h3", itemprop=re.compile("name|headline"))
                if not h3:
                    h3 = art.find("h3")
                a = h3.find("a", href=True) if h3 else art.find("a", href=True)
                if not a:
                    continue
                title_parts = [s.strip() for s in a.strings if s.strip() and s.strip() != "N/A"]
                title = " ".join(title_parts).strip()
                if not title:
                    continue
                href = a.get("href", "")
                link = urljoin(base_url, href) if href else base_url
                desc_div = art.find("div", itemprop="description")
                desc = self._extract_text_clean(desc_div) if desc_div else "N/A"
                results.append({
                    "title": title,
                    "abstract_deadline": "未找到日期",
                    "fullpaper_deadline": "未找到日期",
                    "editors": "N/A",
                    "desc": desc,
                    "link": link
                })
            except Exception:
                continue

        uniq = {}
        for r in results:
            uniq[self._canonical_link(r["link"])] = r
        return list(uniq.values())

    def _nature_page_url(self, base_url, page_number):
        parts = urlsplit(base_url)
        query = parse_qs(parts.query, keep_blank_values=True)
        query["page"] = [str(page_number)]
        return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query, doseq=True), ""))

    def _nature_last_page(self, html):
        soup = BeautifulSoup(html or "", "lxml")
        pages = [1]
        for anchor in soup.select('a[href*="page="]'):
            try:
                query = parse_qs(urlsplit(anchor.get("href", "")).query)
                pages.extend(int(value) for value in query.get("page", []) if str(value).isdigit())
            except (TypeError, ValueError):
                continue
        return max(pages)

    def parse_nature_collections(self, html, base_url):
        """Scan every collection page, then fetch deadlines for open calls only."""
        self._nature_scan_complete = False
        if not html:
            return []

        detected_last_page = self._nature_last_page(html)
        last_page = min(detected_last_page, NATURE_MAX_PAGES)
        listing_html = [html]
        completed_pages = True
        for page_number in range(2, last_page + 1):
            page_html = self._fetch_nature_html(self._nature_page_url(base_url, page_number))
            if not page_html:
                completed_pages = False
                print(f"   ⚠️ Nature 列表第 {page_number}/{detected_last_page} 页获取失败")
                continue
            listing_html.append(page_html)

        if detected_last_page > NATURE_MAX_PAGES:
            completed_pages = False
            print(f"   ⚠️ Nature 分页超过安全上限 {NATURE_MAX_PAGES}，本次不替换历史记录")

        by_link = {}
        for page_html in listing_html:
            for item in self._parse_nature_listing(page_html, base_url):
                by_link[self._canonical_link(item["link"])] = item

        missing_deadline_items = []
        for key, item in by_link.items():
            cached = self._known_deadlines_by_link.get(key)
            if cached:
                item["fullpaper_deadline"] = cached
            else:
                missing_deadline_items.append(item)

        if missing_deadline_items:
            print(f"   🔎 Nature 全分页发现 {len(by_link)} 个开放专题，补抓 {len(missing_deadline_items)} 个截止日期")
            with ThreadPoolExecutor(max_workers=NATURE_DETAIL_WORKERS) as pool:
                future_to_item = {
                    pool.submit(self._fetch_nature_deadline, item["link"]): item
                    for item in missing_deadline_items
                }
                for future in as_completed(future_to_item):
                    item = future_to_item[future]
                    try:
                        deadline = future.result()
                    except Exception as exc:
                        print(f"   ⚠️ Nature 截止日期任务失败 {item['link']}: {exc}")
                        deadline = ""
                    if deadline:
                        item["fullpaper_deadline"] = deadline

        self._nature_scan_complete = completed_pages and len(listing_html) == last_page
        return list(by_link.values())

    # --- Oxford University Press ---
    def parse_oup(self, html, base_url):
        """
        解析 Oxford Academic (academic.oup.com) 期刊主页上的 CFP 区块。
        实际 HTML 结构（FlareSolverr 抓取验证）：
          - CFP 内容放在 div.featurePanel 里（期刊首页的特色展示区）
          - 标题：h2 > a[href]，文本为 "Call for Papers"，href 指向完整 CFP 页
          - 描述：紧随 h2 的 <p> 元素
          - 截止日期：含 "deadline" 的 <p> 元素，如 "Abstract submission deadline: Sep 15, 2025."
          - 注意：大多数期刊主页无 CFP（featurePanel 内容为其他），直接返回空列表
        """
        if not html: return []
        soup = BeautifulSoup(html, "lxml")
        results = []

        for panel in soup.find_all("div", class_="featurePanel"):
            panel_text = panel.get_text(" ", strip=True)
            if not re.search(r'call.for.paper|special.issue|submission', panel_text, re.I):
                continue
            try:
                # 找 h2 > a（"Call for Papers" 链接）
                h2 = panel.find("h2")
                a = h2.find("a", href=True) if h2 else panel.find("a", href=True)
                if not a:
                    continue
                link = urljoin(base_url, a.get("href", ""))

                # 标题：h2 文字 or a 文字
                title_text = self._extract_text_clean(h2) if h2 else self._extract_text_clean(a)

                # 找描述和截止日期
                abstract_deadline = "未找到日期"
                fullpaper_deadline = "未找到日期"
                desc_parts = []
                inner = panel.find("div", class_="featurePanelInner") or panel
                for sib in (h2.find_next_siblings() if h2 else inner.find_all("p")):
                    txt = sib.get_text(" ", strip=True) if hasattr(sib, 'get_text') else str(sib).strip()
                    if not txt: continue
                    lower = txt.lower()
                    if "abstract" in lower and "deadline" in lower:
                        dt = self.extract_date(txt)
                        if dt: abstract_deadline = dt
                    elif "deadline" in lower or "due" in lower:
                        dt = self.extract_date(txt)
                        if dt: fullpaper_deadline = dt
                    else:
                        desc_parts.append(txt)

                # 如果 abstract_deadline 有值但 fullpaper_deadline 没有，反过来也存
                if abstract_deadline != "未找到日期" and fullpaper_deadline == "未找到日期":
                    fullpaper_deadline = abstract_deadline

                desc = " ".join(desc_parts)[:300] if desc_parts else "N/A"
                results.append({
                    "title": title_text,
                    "abstract_deadline": abstract_deadline,
                    "fullpaper_deadline": fullpaper_deadline,
                    "editors": "N/A",
                    "desc": desc,
                    "link": link
                })
            except Exception:
                continue

        # Explicit CFP detail pages (configured with cfp_url) do not contain a
        # featurePanel. Parse the document itself instead of silently returning 0.
        if not results:
            page_text = self.clean_text(soup.get_text(" ", strip=True))
            if re.search(r"\b(call for papers?|special issue call|submission deadline)\b", page_text, re.I):
                headings = [
                    self._extract_text_clean(node)
                    for node in soup.find_all(["h1", "h2", "h3"])
                    if self._extract_text_clean(node)
                ]
                specific_headings = [
                    value for value in headings
                    if not re.fullmatch(r"(special issue\s*[-–—]?\s*)?call for papers?(?:\s*\d{4})?", value, re.I)
                ]
                title = specific_headings[0] if specific_headings else (headings[0] if headings else "Call for Papers")
                abstract_deadline = "未找到日期"
                fullpaper_deadline = "未找到日期"
                # Avoid container <div>s: they repeat all descendant dates and
                # can make the final publication date look like a deadline.
                for node in soup.find_all(["p", "li", "tr"]):
                    text = self._extract_text_clean(node)
                    if not text or not re.search(r"\b(deadline|due)\b", text, re.I):
                        continue
                    dates = self.extract_dates(text)
                    if not dates:
                        continue
                    if "abstract" in text.lower():
                        abstract_deadline = dates[-1]
                    elif re.search(r"full|manuscript|paper|article", text, re.I):
                        fullpaper_deadline = dates[-1]
                if fullpaper_deadline == "未找到日期" and abstract_deadline != "未找到日期":
                    fullpaper_deadline = abstract_deadline
                if not self._is_non_cfp_candidate(title, base_url, page_text):
                    results.append({
                        "title": title,
                        "abstract_deadline": abstract_deadline,
                        "fullpaper_deadline": fullpaper_deadline,
                        "editors": "N/A",
                        "desc": "N/A",
                        "link": base_url,
                    })

        uniq = {}
        for r in results:
            k = (r["title"], r["link"])
            if k not in uniq: uniq[k] = r
        return list(uniq.values())

    def parse_generic_cfp_page(self, html, base_url):
        """Conservative fallback for journals without a publisher adapter."""
        if self._is_error_or_challenge_page(html):
            return []
        soup = BeautifulSoup(html, "lxml")
        results = []
        for anchor in soup.select("a[href]"):
            try:
                if anchor.find_parent(["nav", "header", "footer"]):
                    continue
                href = anchor.get("href", "")
                link = urljoin(base_url, href)
                anchor_text = self._extract_text_clean(anchor)
                container = anchor.find_parent(["article", "li", "p", "section", "div"]) or anchor.parent
                context = self._extract_text_clean(container)
                semantic_text = f"{anchor_text} {context} {href}"
                has_call_language = bool(
                    re.search(
                        r"\b(call for papers?|call for submissions?|"
                        r"submission deadline|deadline for .{0,50}submissions?)\b",
                        semantic_text,
                        re.I,
                    )
                    or (
                        re.search(r"\bspecial issues?\b", semantic_text, re.I)
                        and re.search(r"\b(open call|submit|submission|deadline|due)\b", semantic_text, re.I)
                    )
                    or re.search(r"(call[-_/]?for[-_/]?papers?|callforpapers|/cfp(?:/|$))", href, re.I)
                )
                if not has_call_language:
                    continue

                title = anchor_text
                if title.casefold() in {"read more", "learn more", "view", "details", "download"} or len(title) < 5:
                    heading = container.find(["h1", "h2", "h3", "h4"]) if container else None
                    title = self._extract_text_clean(heading) if heading else title
                if self._is_non_cfp_candidate(title, link, context):
                    continue

                abstract_deadline = "未找到日期"
                fullpaper_deadline = "未找到日期"
                for segment in container.find_all(["p", "li", "strong", "b"], recursive=True) if container else []:
                    text = self._extract_text_clean(segment)
                    dates = self.extract_dates(text)
                    if not dates:
                        continue
                    if "abstract" in text.lower():
                        abstract_deadline = dates[-1]
                    elif re.search(r"deadline|due|submission", text, re.I):
                        fullpaper_deadline = dates[-1]
                if fullpaper_deadline == "未找到日期":
                    dates = self.extract_dates(context)
                    if dates:
                        fullpaper_deadline = dates[-1]

                results.append({
                    "title": title,
                    "abstract_deadline": abstract_deadline,
                    "fullpaper_deadline": fullpaper_deadline,
                    "editors": "N/A",
                    "desc": context[:300] if context else "N/A",
                    "link": link,
                })
            except Exception:
                continue

        uniq = {}
        for item in results:
            uniq[self._canonical_link(item["link"])] = item
        return list(uniq.values())

    # --- University of Chicago Press ---
    def parse_uchicago(self, html, base_url):
        """
        解析 UChicago Press Journals 期刊主页 (/journal/[code])。
        实际情况（FlareSolverr 抓取验证）：
          - UChicago Atypon 平台上的期刊主页不在页面上列出 CFP 信息
          - 目前已测试 AJS/AJE/JOP/ET/BJPS 均无 CFP 内容
          - 本方法保留以备将来期刊增加 CFP 展示，当前通常返回空列表
        """
        if not html: return []
        soup = BeautifulSoup(html, "lxml")
        results = []

        # 404 检测
        body_text = soup.get_text(" ", strip=True)
        if "404 Not Found" in body_text[:200]:
            print(f"   ⚠️ UChicago 页面返回 404 (URL 可能需要从 /journals/ 改为 /journal/)")
            return []

        # 尝试找 CFP 相关内容（未来可能出现的结构）
        for block in soup.find_all(["div", "section", "article"],
                                   class_=re.compile(r"call|cfp|special|announcement", re.I)):
            try:
                h = block.find(["h2", "h3", "h4"])
                if not h: continue
                title = self._extract_text_clean(h)
                if not title or len(title) < 5: continue
                a = h.find("a", href=True) or block.find("a", href=True)
                link = urljoin(base_url, a["href"]) if a else base_url
                text = block.get_text(" ", strip=True)
                deadline = self.extract_date(text) or "未找到日期"
                desc_p = block.find("p")
                desc = self._extract_text_clean(desc_p) if desc_p else "N/A"
                results.append({"title": title, "abstract_deadline": "未找到日期",
                                 "fullpaper_deadline": deadline, "editors": "N/A",
                                 "desc": desc, "link": link})
            except Exception:
                continue

        return results

    # --- APA (American Psychological Association) ---
    def parse_apa(self, html, base_url):
        """
        解析 APA (apa.org) 期刊页面的 Special Issues / Call for Papers 部分
        """
        if not html: return []
        soup = BeautifulSoup(html, "lxml")
        results = []

        # 方案1: 专用 CFP/Special Issue 区域
        for section in soup.find_all(["section", "div"],
                                     class_=re.compile(r"special.issue|call.for.paper|cfp|submissions?", re.I)):
            for item in section.find_all(["article", "div", "li"],
                                         class_=re.compile(r"item|card|entry|call", re.I)):
                try:
                    h = item.find(["h2", "h3", "h4"])
                    title = self._extract_text_clean(h) if h else "N/A"
                    if not title or title == "N/A": continue
                    a = item.find("a", href=True)
                    link = urljoin(base_url, a["href"]) if a else base_url
                    text = item.get_text(" ", strip=True)
                    deadline = self.extract_date(text) or "未找到日期"
                    desc_p = item.find("p")
                    desc = self._extract_text_clean(desc_p) if desc_p else "N/A"
                    results.append({"title": title, "abstract_deadline": "未找到日期",
                                    "fullpaper_deadline": deadline, "editors": "N/A",
                                    "desc": desc, "link": link})
                except Exception:
                    continue

        # 方案2: 定位 "Call for Papers" 标题段落后的内容
        if not results:
            cfp_header = soup.find(
                ["h1", "h2", "h3", "h4"],
                string=re.compile(r"call.for.papers?|special.issues?", re.I)
            )
            if cfp_header:
                container = cfp_header.find_parent(["section", "div", "article"]) or cfp_header
                for item in container.find_all(["li", "article", "div"], recursive=False):
                    try:
                        text = item.get_text(" ", strip=True)
                        if len(text) < 20: continue
                        a = item.find("a", href=True)
                        deadline = self.extract_date(text) or "未找到日期"
                        title = self._extract_text_clean(a) if a else text[:100]
                        if not title: continue
                        results.append({"title": title, "abstract_deadline": "未找到日期",
                                        "fullpaper_deadline": deadline, "editors": "N/A",
                                        "desc": "N/A",
                                        "link": urljoin(base_url, a["href"]) if a else base_url})
                    except Exception:
                        continue

        uniq = {}
        for r in results:
            k = (r["title"], r["link"])
            if k not in uniq: uniq[k] = r
        return list(uniq.values())

    # --- PNAS ---
    def parse_pnas(self, html, base_url):
        """
        解析 PNAS /author-center/call-for-papers 页面。
        实际 HTML 结构（FlareSolverr 抓取验证）：
          - 每条 CFP 在 div.card--row-reversed 里
          - 标题：h3.article-title.card__title > a（href 为相对路径）
          - 发布日期：span.card__meta__date（注意：这是帖子发布日期，不是截止日期）
          - 描述：h3 后的第一个 div
        """
        if not html: return []
        soup = BeautifulSoup(html, "lxml")
        results = []

        for card in soup.find_all("div", class_="card--row-reversed"):
            try:
                h3 = card.find("h3", class_="card__title") or card.find("h3")
                if not h3: continue
                a = h3.find("a", href=True)
                if not a: continue

                title = a.get_text(" ", strip=True)
                if not title: continue
                link = urljoin(base_url, a.get("href", ""))

                # 描述：h3 之后第一个有内容的 div
                desc = "N/A"
                for sib in h3.find_next_siblings("div"):
                    txt = sib.get_text(" ", strip=True)
                    if txt and len(txt) > 10:
                        desc = txt[:300]
                        break

                results.append({
                    "title": title,
                    "abstract_deadline": "未找到日期",
                    # card__meta__date is the announcement publication date,
                    # not a submission deadline.
                    "fullpaper_deadline": "未找到日期",
                    "editors": "N/A",
                    "desc": desc,
                    "link": link
                })
            except Exception:
                continue

        uniq = {}
        for r in results:
            k = (r["title"], r["link"])
            if k not in uniq: uniq[k] = r
        return list(uniq.values())

    # ==========================================
    # 数据输出与合并 (完全保持不变)
    # ==========================================
    def infer_publisher(self, journal_url, journal_name=""):
        u, n = (journal_url or "").lower(), (journal_name or "").lower()
        if "wiley" in u or "wiley" in n: return "Wiley"
        if "tandf" in u or "taylor" in n or "tandfonline" in u: return "Taylor & Francis"
        if "sage" in u or "sagepub" in u: return "SAGE"
        if "sciencedirect" in u or "elsevier" in n: return "Elsevier"
        if "springer" in u and "nature" not in u: return "Springer"
        if "nature.com" in u: return "Nature Portfolio"
        if "cambridge" in u: return "Cambridge Core"
        if "academic.oup" in u or "oup" in n: return "Oxford University Press"
        if "uchicago" in u: return "University of Chicago Press"
        if "apa.org" in u: return "APA"
        if "pnas.org" in u: return "PNAS"
        if "science.org" in u: return "AAAS"
        return "Unknown"

    def _empty_if_na(self, s):
        s = "" if s is None else str(s).strip()
        return "" if s in {"N/A", "未找到日期"} else s

    def normalize_item_for_yaml(self, journal, item):
        abstract_deadline = self._empty_if_na(item.get("abstract_deadline"))
        fullpaper_deadline = self._empty_if_na(item.get("fullpaper_deadline", "") or item.get("deadline", ""))
        fullpaper_deadline_sort = self.parse_date_to_sort_key(fullpaper_deadline or abstract_deadline)

        raw_tag = journal.get("tag", [])
        if isinstance(raw_tag, str):
            tag_out = [raw_tag] if raw_tag else []
        elif isinstance(raw_tag, list):
            tag_out = raw_tag
        else:
            tag_out = []

        return {
            "journal": self._empty_if_na(journal.get("name")),
            "publisher": journal.get("publisher") or self.infer_publisher(journal.get("url"), journal.get("name")),
            "tag": tag_out,
            "title": self._empty_if_na(item.get("title")),
            "abstract_deadline": abstract_deadline,
            "fullpaper_deadline": fullpaper_deadline,
            "fullpaper_deadline_sort": fullpaper_deadline_sort,
            "editors": self._empty_if_na(item.get("editors")),
            "link": self._empty_if_na(item.get("link")),
            "description": self._empty_if_na(item.get("desc")),
        }

    def merge_and_clean_records(self, new_records, file_path, replace_journals=None):
        replace_journals = set(replace_journals or [])
        existing_records = []
        if os.path.exists(file_path):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    existing_records = yaml.safe_load(f) or []
                if not isinstance(existing_records, list):
                    raise ValueError("顶层必须是列表")
                print(f"📂 读取到历史数据: {len(existing_records)} 条")
            except Exception as e:
                raise RuntimeError(f"读取旧 YAML 失败，为避免覆盖已停止写入: {e}") from e

        # Only a verified full scan may replace all historical records for a
        # journal. Failed/partial scans continue to preserve the last good data.
        existing_for_merge = [
            item for item in existing_records
            if item.get("journal") not in replace_journals
        ]

        def _richness(rec):
            has_deadline = 1 if (rec.get("fullpaper_deadline_sort") or "9999-99-99") != "9999-99-99" else 0
            return (has_deadline, len(rec.get("description") or ""), len(rec.get("editors") or ""))

        merged_map = {}
        for raw_item in existing_for_merge + new_records:
            item = dict(raw_item)
            sort_source = item.get("fullpaper_deadline") or item.get("abstract_deadline")
            item["fullpaper_deadline_sort"] = self.parse_date_to_sort_key(sort_source)
            canonical_link = self._canonical_link(item.get("link"))
            title_key = self.clean_text(item.get("title")).casefold()
            key = (item.get("journal"), canonical_link or title_key)
            if key in merged_map and _richness(merged_map[key]) > _richness(item):
                continue
            merged_map[key] = item

        # Drop mis-scraped entries: when a publisher detail page 404s/redirects,
        # parsers can capture the error page's heading as the title (e.g.
        # "404 Error. Page not found.", "What happened?"). These markers are
        # unambiguous junk and would otherwise leak into the CFP table & recommender.
        JUNK_TITLE_MARKERS = (
            "404 error", "page not found", "what happened", "access denied",
            "403 forbidden", "just a moment", "are you a robot",
            "attention required", "页面不存在", "页面未找到",
            "about the role",
            "call for editor", "call for guest editor", "guest editor opportunity",
            "special issues collection", "published and upcoming special issues",
            "virtual special issue", "learn about our special collections",
            "see jrai's website", "tools, tips, and journal insights",
            "painting special issue", "new special issue",
            "special issue 2024",
        )
        # Editor-recruitment / reviewer-award pages are not calls for papers.
        JUNK_URL_MARKERS = (
            "editor_recruitment", "reviewer-award", "reviewer-prize",
            "associate-editor", "editors-needed", "editor-needed", "reviewers-needed",
        )

        def _is_junk(rec):
            title = (rec.get("title") or "").strip().lower()
            link = (rec.get("link") or "").lower()
            context = rec.get("description") or ""
            if self._is_non_cfp_candidate(title, link, context):
                return True
            if any(m in title for m in JUNK_TITLE_MARKERS):
                return True
            return any(m in link for m in JUNK_URL_MARKERS)

        final_list = []
        today = datetime.now().date()
        expire_threshold = today - timedelta(days=10)

        for item in merged_map.values():
            if _is_junk(item):
                continue
            if not item.get("journal") or not item.get("title") or not self._canonical_link(item.get("link")):
                continue
            sort_date_str = item.get("fullpaper_deadline_sort")
            if sort_date_str == '9999-99-99':
                final_list.append(item)
                continue
            try:
                deadline_date = datetime.strptime(sort_date_str, "%Y-%m-%d").date()
                if deadline_date >= expire_threshold:
                    final_list.append(item)
            except ValueError:
                final_list.append(item)

        final_list.sort(key=lambda x: x.get("fullpaper_deadline_sort") or "9999-99-99")
        if len(existing_records) >= 20 and len(final_list) < int(len(existing_records) * 0.4):
            raise RuntimeError(
                f"CFP 质量门未通过: {len(existing_records)} 条骤降至 {len(final_list)} 条"
            )
        return final_list

    # ==========================================
    # 主运行逻辑 (扩展出版商路由)
    # ==========================================
    def run(self, output_yml_path=OUTPUT_YML_PATH):
        # 启动时检测 FlareSolverr
        check_flaresolverr_health()

        new_scraped_records = []
        replace_journals = set()
        if os.path.exists(output_yml_path):
            try:
                with open(output_yml_path, "r", encoding="utf-8") as existing_file:
                    existing = yaml.safe_load(existing_file) or []
                if not isinstance(existing, list):
                    raise ValueError("顶层必须是列表")
                today = datetime.now().date()
                for item in existing:
                    link = self._canonical_link(item.get("link"))
                    deadline = self._empty_if_na(item.get("fullpaper_deadline"))
                    sort_key = item.get("fullpaper_deadline_sort") or self.parse_date_to_sort_key(deadline)
                    if not link or not deadline or sort_key == "9999-99-99":
                        continue
                    try:
                        if datetime.strptime(sort_key, "%Y-%m-%d").date() < today - timedelta(days=10):
                            continue
                    except ValueError:
                        continue
                    self._known_deadlines_by_link[link] = deadline
            except Exception as exc:
                raise RuntimeError(f"读取旧 CFP 数据失败，为避免覆盖已停止抓取: {exc}") from exc

        print("\n🕷️ 开始爬取任务 (FlareSolverr + curl_cffi 混合模式)...")
        print(f"   FlareSolverr: {'✅ 可用' if FLARESOLVERR_AVAILABLE else '⚠️ 不可用，使用 curl_cffi 回退'}\n")

        for journal in JOURNALS:
            j_name = journal["name"]
            j_url = journal["url"].strip()
            url_l = j_url.lower()
            data = []

            print(f"📖 处理: {j_name}")

            try:
                # === T&F: CF 站点 ===
                if "tandfonline.com" in url_l:
                    data = self.parse_taylor_francis(j_url)

                # === Wiley: CF 站点 ===
                elif ("wiley.com" in url_l or "onlinelibrary.wiley" in url_l
                      or "bera-journals" in url_l or "rai.onlinelibrary" in url_l
                      or "anthrosource" in url_l or "ila.onlinelibrary" in url_l):
                    html = self.fetch_cf_site(j_url)
                    if html:
                        data = self.parse_wiley_from_html(html, j_url)

                # === SAGE: CF 站点 (journals.sagepub.com 和 uk.sagepub.com) ===
                elif "sagepub.com" in url_l:
                    html = self.fetch_cf_site(j_url)
                    if html:
                        data = self.parse_sage_from_html(html, j_url)

                # === Cambridge Core: curl_cffi ===
                elif "cambridge.org" in url_l:
                    html = self.fetch_page_fast(j_url)
                    if html:
                        data = self.parse_cambridge_core_call_for_papers(html, j_url)

                # === Springer: FlareSolverr（2026-06 起 link.springer.com 加了
                #     idp.springer.com cookie/JS 门，curl_cffi 只能拿到 3KB 挑战页）===
                elif "springer.com" in url_l and "nature" not in url_l:
                    html = self.fetch_cf_site(j_url)
                    # IDP 重定向偶尔未完成就返回（落在期刊主页快照），重试一次
                    if html and "collections/" not in html:
                        print("   🔁 Springer 重定向未完成，重试一次")
                        html = self.fetch_cf_site(j_url)
                    if html:
                        data = self.parse_springer(html, j_url)

                # === Elsevier / ScienceDirect: FlareSolverr（curl_cffi 在 CI 上 403；
                #     经 FlareSolverr 可正常停留在 /about/call-for-papers 并解析）===
                elif "sciencedirect.com" in url_l:
                    html = self.fetch_cf_site(j_url)
                    if html:
                        data = self.parse_elsevier(html, j_url)

                # === Nature Portfolio: FlareSolverr（2026-06-10 前后 nature.com 也
                #     上了与 link.springer.com 相同的 idp cookie/JS 门，
                #     curl_cffi 只能拿到 3KB 挑战页）===
                elif "nature.com" in url_l:
                    html = self._fetch_nature_html(j_url)
                    if html and "collections" not in html:
                        print("   🔁 Nature 重定向未完成，重试一次")
                        html = self._fetch_nature_html(j_url)
                    if html:
                        data = self.parse_nature_collections(html, j_url)
                        if self._nature_scan_complete:
                            replace_journals.add(j_name)

                # === Oxford University Press: Cloudflare → FlareSolverr ===
                elif "academic.oup.com" in url_l:
                    target_url = journal.get("cfp_url") or j_url
                    html = self.fetch_cf_site(target_url)
                    if html:
                        data = self.parse_oup(html, target_url)

                # === University of Chicago Press: Cloudflare → FlareSolverr ===
                elif "uchicago.edu" in url_l:
                    html = self.fetch_cf_site(j_url)
                    if html:
                        data = self.parse_uchicago(html, j_url)

                # === APA: Imperva 保护，FlareSolverr 可能也无法绕过 ===
                elif "apa.org" in url_l:
                    html = self.fetch_cf_site(j_url)
                    if html and len(html) > 5000:  # Imperva 拦截页通常极短
                        data = self.parse_apa(html, j_url)
                    else:
                        print(f"   ⚠️ APA 被 Imperva 拦截，跳过: {j_name}")

                # === PNAS: Cloudflare → FlareSolverr ===
                elif "pnas.org" in url_l:
                    html = self.fetch_cf_site(j_url)
                    if html:
                        data = self.parse_pnas(html, j_url)

                # === AAAS / Science.org: curl_cffi，403 时跳过 ===
                elif "science.org" in url_l:
                    html = self.fetch_page_fast(j_url)
                    if html:
                        data = self.parse_generic_cfp_page(html, j_url)
                    else:
                        print(f"   ⚠️ Science.org 可能返回 403，跳过: {j_name}")

                # === 其他未知站点: curl_cffi，失败时尝试 FlareSolverr ===
                else:
                    html = self.fetch_page_fast(j_url)
                    if not html and FLARESOLVERR_AVAILABLE and self.needs_flaresolverr(j_url):
                        html, _, _ = self.fetch_with_flaresolverr(j_url)
                    if html:
                        data = self.parse_generic_cfp_page(html, j_url)
                    print(f"   ℹ️ 通用 CFP 解析器: {j_name}")

                # 处理结果
                if data:
                    print(f"   ✅ 抓取成功: {len(data)} 条\n")
                    for item in data:
                        rec = self.normalize_item_for_yaml(journal, item)
                        if rec["title"] and self._canonical_link(rec["link"]):
                            new_scraped_records.append(rec)
                else:
                    print(f"   ⚠️ 无数据/保留历史\n")

            except Exception as e:
                print(f"   ❌ 处理异常: {e}\n")

            time.sleep(random.uniform(1, 2))

        # 合并与保存
        final_records = self.merge_and_clean_records(
            new_scraped_records,
            output_yml_path,
            replace_journals=replace_journals,
        )

        output_dir = os.path.dirname(output_yml_path) or "."
        os.makedirs(output_dir, exist_ok=True)
        fd, temporary_path = tempfile.mkstemp(prefix=".cfps-", suffix=".yml", dir=output_dir)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                yaml.safe_dump(final_records, f, allow_unicode=True, sort_keys=False,
                               default_flow_style=False, width=120)
                f.flush()
                os.fsync(f.fileno())
            os.replace(temporary_path, output_yml_path)
        finally:
            if os.path.exists(temporary_path):
                os.unlink(temporary_path)

        print(f"🎉 任务结束! 总条目: {len(final_records)}")


if __name__ == "__main__":
    if not JOURNALS:
        raise SystemExit("期刊配置为空或无效，已停止以避免覆盖 CFP 数据")
    scraper = JournalCFPScraper()
    scraper.run()
