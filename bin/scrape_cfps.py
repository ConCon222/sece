import re
import time
import os
import yaml
import random
from datetime import datetime, timedelta
from urllib.parse import urljoin
from bs4 import BeautifulSoup

# === 核心库 ===
from curl_cffi import requests
from DrissionPage import ChromiumPage, ChromiumOptions

# ==========================================
# ⚙️ 配置区域
# ==========================================
FLARESOLVERR_URL = "http://localhost:8191"  # GitHub Actions 中自动启动
FLARESOLVERR_AVAILABLE = False              # 运行时动态检测


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
            return yaml.safe_load(f)
    except FileNotFoundError:
        print(f"❌ 错误：找不到文件 {filepath}")
        return []
    except yaml.YAMLError as e:
        print(f"❌ 错误：YAML 格式解析失败: {e}")
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
]


class JournalCFPScraper:
    def __init__(self):
        self.date_pattern = re.compile(
            r"(\d{1,2})(?:st|nd|rd|th)?\s*"
            r"(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)[a-z]*\s+"
            r"(\d{4})|"
            r"(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)[a-z]*\s+"
            r"(\d{1,2})(?:st|nd|rd|th)?,?\s+(\d{4})|"
            r"(\d{4})-(\d{2})-(\d{2})|"
            r"(\d{1,2})(?:st|nd|rd|th)?\s+(\w+)\s+(\d{4})",
            re.I,
        )

        # Session 用于快速抓取 (Elsevier/Springer/Cambridge/Nature/OUP等)
        self.session = requests.Session()

        # DrissionPage 延迟初始化（仅 T&F 需要）
        self._browser = None
        self._browser_cookies_injected = False

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
                cookies = solution.get("cookies", [])
                user_agent = solution.get("userAgent", "")
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

    def extract_date(self, text):
        if not text: return None
        normalized = self.normalize_for_date_extraction(text)
        m = self.date_pattern.search(normalized)
        if m: return self.clean_text(m.group(0))
        return None

    def parse_date_to_sort_key(self, date_str):
        default_date = "9999-99-99"
        if not date_str or date_str in {"N/A", "未找到日期", ""}: return default_date
        normalized = self.normalize_for_date_extraction(date_str)
        try:
            m = re.match(r'(\d{4})-(\d{2})-(\d{2})', normalized)
            if m: return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
            m = re.match(r'(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})', normalized)
            if m:
                day, month_str, year = int(m.group(1)), m.group(2).lower(), m.group(3)
                month = MONTH_MAP.get(month_str[:3], 0)
                if month: return f"{year}-{month:02d}-{day:02d}"
            m = re.match(r'([A-Za-z]+)\s+(\d{1,2}),?\s+(\d{4})', normalized)
            if m:
                month_str, day, year = m.group(1).lower(), int(m.group(2)), m.group(3)
                month = MONTH_MAP.get(month_str[:3], 0)
                if month: return f"{year}-{month:02d}-{day:02d}"
            dates_found = re.findall(r'(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})', normalized)
            if dates_found:
                day, month_str, year = dates_found[-1]
                month = MONTH_MAP.get(month_str.lower()[:3], 0)
                if month: return f"{year}-{month:02d}-{int(day):02d}"
        except Exception: pass
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
            if resp.status_code == 200:
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
                for sib in h4.find_next_siblings():
                    if sib.name in {"h4", "hr"}: break
                    if sib.name == "div" and "border-top" in (sib.get("style") or "").lower(): break
                    if sib.name == "p":
                        txt = self._extract_text_clean(sib)
                        lower = txt.lower()
                        if "deadline" in lower:
                            dt = self.extract_date(txt)
                            if "abstract" in lower: abstract_deadline = dt or abstract_deadline
                            elif "full paper" in lower or "full-paper" in lower: fullpaper_deadline = dt or fullpaper_deadline
                            elif dt and fullpaper_deadline == "未找到日期": fullpaper_deadline = dt
                    if sib.name == "ul":
                        editor_list = [self._extract_text_clean(li) for li in sib.find_all("li") if li.get_text(strip=True)]

                if title and title != "N/A":
                    results.append({"title": title, "abstract_deadline": abstract_deadline, "fullpaper_deadline": fullpaper_deadline, "editors": "; ".join(editor_list) if editor_list else "N/A", "desc": "N/A", "link": link})
            except Exception: continue
        return results

    def parse_wiley_from_html(self, html, journal_url):
        """从 HTML 解析 Wiley（FlareSolverr 返回的 HTML）"""
        if not html: return []
        soup = BeautifulSoup(html, "lxml")
        results = self._parse_wiley_dst_listing(soup, journal_url) + self._parse_wiley_h4_blocks(soup, journal_url)
        uniq = {}
        for r in results: uniq[(r.get("title"), r.get("link"))] = r
        return list(uniq.values())

    # --- T&F (保持解析逻辑不变) ---
    def _tf_parse_detail_page_html(self, html, page_url):
        soup = BeautifulSoup(html, "lxml")
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
            link = urljoin(journal_url, a["href"]) if a else "N/A"
            if "closed" in desc.lower() or title == "N/A": continue
            if any(x in title.lower() or x in desc.lower() for x in ["why publish", "reviewer resources", "discipline hubs"]): continue
            if not ("call" in title.lower() or "special issue" in title.lower() or "submit" in desc.lower()): continue

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
    def _fetch_nature_deadline(self, url):
        """抓取单个 Nature collection 页面，提取 Submission deadline。
        列表页不含截止日期，需进入每个 collection 详情页
        （页面显示 "Submission status: Open / Submission deadline: <date>"）。
        防御式：任何失败都返回 ""，保持原有（留空）行为，绝不会让整个爬虫崩溃。
        Nature 走 curl_cffi（无 Cloudflare），故用 fetch_page_fast。"""
        try:
            html = self.fetch_page_fast(url, timeout=20)
            if not html:
                return ""
            soup = BeautifulSoup(html, "lxml")
            # 1) 结构化元素（若存在）
            for sel in ['[data-test="submission-deadline"]',
                        'time[itemprop="submissionDeadline"]',
                        '[data-test="deadline"]']:
                el = soup.select_one(sel)
                if el:
                    d = self.extract_date(self._extract_text_clean(el))
                    if d:
                        return d
            # 2) 文本兜底："Submission deadline" 后紧跟日期（对 markup 变化稳健）
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

    def parse_nature_collections(self, html, base_url):
        """
        解析 Nature 系列期刊 Collections 页面。
        实际 HTML 结构（来自抓取验证）：
          - 卡片为普通 <article>（无特定 class）
          - 标题：h3[itemprop="name headline"] > a  （a 里面有 img，需清除）
          - 链接：上面 a 的 href（相对路径，如 /collections/xxxxx）
          - 开放状态：div[data-test="open-status"] 文本为 "Open for submissions"
          - 描述：div[itemprop="description"]
          - 注意：列表页不显示截止日期，deadline 留空
        """
        if not html: return []
        soup = BeautifulSoup(html, "lxml")
        results = []

        for art in soup.find_all("article"):
            try:
                # 只保留 "Open for submissions" 的条目
                open_pill = art.find("div", {"data-test": "open-status"})
                if not open_pill:
                    continue
                if "open for submissions" not in open_pill.get_text(strip=True).lower():
                    continue

                # 标题：h3 > a，img 的 alt 也会被 get_text 提取，用 strings 过滤
                h3 = art.find("h3", itemprop=re.compile("name|headline"))
                if not h3:
                    h3 = art.find("h3")
                a = h3.find("a", href=True) if h3 else art.find("a", href=True)
                if not a:
                    continue

                # 提取 a 里的文本，跳过 img alt
                title_parts = [s.strip() for s in a.strings if s.strip() and s.strip() != "N/A"]
                title = " ".join(title_parts).strip()
                if not title:
                    continue

                href = a.get("href", "")
                link = urljoin(base_url, href) if href else base_url

                # 描述
                desc_div = art.find("div", itemprop="description")
                desc = self._extract_text_clean(desc_div) if desc_div else "N/A"

                # 列表页无截止日期 → 进入 collection 详情页抓取（防御式，失败留空）
                deadline = self._fetch_nature_deadline(link)
                time.sleep(0.4)  # 礼貌限速
                results.append({
                    "title": title,
                    "abstract_deadline": "未找到日期",
                    "fullpaper_deadline": deadline if deadline else "未找到日期",
                    "editors": "N/A",
                    "desc": desc,
                    "link": link
                })
            except Exception:
                continue

        uniq = {}
        for r in results: uniq[(r["title"], r["link"])] = r
        return list(uniq.values())

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

        uniq = {}
        for r in results:
            k = (r["title"], r["link"])
            if k not in uniq: uniq[k] = r
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

                # 发布日期（span.card__meta__date），作为 fullpaper_deadline 的参考
                date_span = card.find("span", class_="card__meta__date")
                pub_date = date_span.get_text(strip=True) if date_span else "未找到日期"

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
                    "fullpaper_deadline": pub_date,
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
        fullpaper_deadline = self._empty_if_na(item.get("fullpaper_deadline", "") or item.get("deadline", ""))
        fullpaper_deadline_sort = self.parse_date_to_sort_key(fullpaper_deadline)

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
            "abstract_deadline": self._empty_if_na(item.get("abstract_deadline")),
            "fullpaper_deadline": fullpaper_deadline,
            "fullpaper_deadline_sort": fullpaper_deadline_sort,
            "editors": self._empty_if_na(item.get("editors")),
            "link": self._empty_if_na(item.get("link")),
            "description": self._empty_if_na(item.get("desc")),
        }

    def merge_and_clean_records(self, new_records, file_path):
        existing_records = []
        if os.path.exists(file_path):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    existing_records = yaml.safe_load(f) or []
                print(f"📂 读取到历史数据: {len(existing_records)} 条")
            except Exception as e:
                print(f"⚠️ 读取旧 YAML 失败: {e}")

        # Dedup by (journal, title): the same call often appears under two URLs
        # (listing page + detail page), which the old (title, link) key kept as
        # visible duplicates. Prefer the richer record: real deadline first,
        # then the longer description.
        def _richness(rec):
            has_deadline = 1 if (rec.get("fullpaper_deadline_sort") or "9999-99-99") != "9999-99-99" else 0
            return (has_deadline, len(rec.get("description") or ""), len(rec.get("editors") or ""))

        merged_map = {}
        for item in existing_records + new_records:
            key = (item.get("journal"), (item.get("title") or "").strip().lower())
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
        )
        # Editor-recruitment / reviewer-award pages are not calls for papers.
        JUNK_URL_MARKERS = (
            "editor_recruitment", "reviewer-award", "reviewer-prize",
            "associate-editor", "editors-needed", "editor-needed", "reviewers-needed",
        )

        def _is_junk(rec):
            title = (rec.get("title") or "").strip().lower()
            link = (rec.get("link") or "").lower()
            if any(m in title for m in JUNK_TITLE_MARKERS):
                return True
            return any(m in link for m in JUNK_URL_MARKERS)

        final_list = []
        today = datetime.now().date()
        expire_threshold = today - timedelta(days=10)

        for item in merged_map.values():
            if _is_junk(item):
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
        return final_list

    # ==========================================
    # 主运行逻辑 (扩展出版商路由)
    # ==========================================
    def run(self, output_yml_path=OUTPUT_YML_PATH):
        # 启动时检测 FlareSolverr
        check_flaresolverr_health()

        new_scraped_records = []
        print("\n🕷️ 开始爬取任务 (FlareSolverr + curl_cffi 混合模式)...")
        print(f"   FlareSolverr: {'✅ 可用' if FLARESOLVERR_AVAILABLE else '⚠️ 不可用，使用 curl_cffi 回退'}\n")

        for journal in JOURNALS:
            j_name = journal["name"]
            j_url = journal["url"]
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

                # === Springer: curl_cffi ===
                elif "springer.com" in url_l and "nature" not in url_l:
                    html = self.fetch_page_fast(j_url)
                    if html:
                        data = self.parse_springer(html, j_url)

                # === Elsevier / ScienceDirect: curl_cffi ===
                elif "sciencedirect.com" in url_l:
                    html = self.fetch_page_fast(j_url)
                    if html:
                        data = self.parse_elsevier(html, j_url)

                # === Nature Portfolio: curl_cffi (SpringerNature infra, 无 CF) ===
                elif "nature.com" in url_l:
                    html = self.fetch_page_fast(j_url)
                    if html:
                        data = self.parse_nature_collections(html, j_url)

                # === Oxford University Press: Cloudflare → FlareSolverr ===
                elif "academic.oup.com" in url_l:
                    html = self.fetch_cf_site(j_url)
                    if html:
                        data = self.parse_oup(html, j_url)

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
                        # Science.org 无统一 CFP 列表页，用通用解析
                        data = self.parse_pnas(html, j_url)  # 结构相近，复用
                    else:
                        print(f"   ⚠️ Science.org 可能返回 403，跳过: {j_name}")

                # === 其他未知站点: curl_cffi，失败时尝试 FlareSolverr ===
                else:
                    html = self.fetch_page_fast(j_url)
                    if not html and FLARESOLVERR_AVAILABLE and self.needs_flaresolverr(j_url):
                        html, _, _ = self.fetch_with_flaresolverr(j_url)
                    print(f"   ⚠️ 通用出版社 (未特定解析): {j_name}")

                # 处理结果
                if data:
                    print(f"   ✅ 抓取成功: {len(data)} 条\n")
                    for item in data:
                        rec = self.normalize_item_for_yaml(journal, item)
                        if rec["title"] or rec["link"]:
                            new_scraped_records.append(rec)
                else:
                    print(f"   ⚠️ 无数据/保留历史\n")

            except Exception as e:
                print(f"   ❌ 处理异常: {e}\n")

            time.sleep(random.uniform(1, 2))

        # 合并与保存
        final_records = self.merge_and_clean_records(new_scraped_records, output_yml_path)

        os.makedirs(os.path.dirname(output_yml_path), exist_ok=True)
        with open(output_yml_path, "w", encoding="utf-8") as f:
            yaml.safe_dump(final_records, f, allow_unicode=True, sort_keys=False,
                           default_flow_style=False, width=120)

        print(f"🎉 任务结束! 总条目: {len(final_records)}")


if __name__ == "__main__":
    scraper = JournalCFPScraper()
    scraper.run()
