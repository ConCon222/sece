import re
import time
import os  # 新增
import yaml
from datetime import datetime, timedelta # 新增
from urllib.parse import urljoin
from bs4 import BeautifulSoup

# === 核心库 ===
from curl_cffi import requests  # 快：用于 Elsevier, Springer, Cambridge Core
from DrissionPage import ChromiumPage, ChromiumOptions  # 稳：用于 Taylor & Francis, Wiley, SAGE

# ==========================================
# ⚙️ 配置区域
# ==========================================
JOURNALS = [
    {
        "name": "International Journal of Educational Technology in Higher Education",
        "url": "https://link.springer.com/journal/41239/collections?filter=Open",
        "tag": ["educational technology", "higher education"]
    },
    {
        "name": "Educational Psychologist",
        "url": "https://www.tandfonline.com/journals/hedp20",
        "tag": ["educational psychology"]
    },
    {
        "name": "Educational Research Review",
        "url": "https://www.sciencedirect.com/journal/educational-research-review/about/call-for-papers",
        "tag": ["review", "general education"]
    },
    {
        "name": "Computers & Education",
        "url": "https://www.sciencedirect.com/journal/computers-and-education/about/call-for-papers",
        "tag": ["educational technology"]
    },
    {
        "name": "Studies in Science Education",
        "url": "https://www.tandfonline.com/journals/rsse20",
        "tag": ["review"]
    },
    {
        "name": "British Journal of Educational Technology",
        "url": "https://bera-journals.onlinelibrary.wiley.com/hub/journal/14678535/bjet_special_issues.htm",
        "tag": ["educational technology"]
    },
    {
        "name": "International Journal of STEM Education",
        "url": "https://link.springer.com/journal/40594/collections?filter=Open",
        "tag": ["educational technology", "STEM education"]
    },
    {
        "name": "Review of Educational Research",
        "url": "https://journals.sagepub.com/home/rer",
        "tag": ["review", "general education"]
    },
    {
        "name": "International Journal of Management Education",
        "url": "https://www.sciencedirect.com/journal/the-international-journal-of-management-education/about/call-for-papers",
        "tag": ["educational management", "higher education"]
    },
    {
        "name": "The Internet and Higher Education",
        "url": "https://www.sciencedirect.com/journal/the-internet-and-higher-education/about/call-for-papers",
        "tag": ["higher education", "educational technology"]
    },
    {
        "name": "Computer Assisted Language Learning",
        "url": "https://www.tandfonline.com/journals/ncal20",
        "tag": ["language learning", "educational technology"]
    },
    {
        "name": "Educational Technology & Society",
        "url": "https://www.j-ets.net",
        "tag": ["educational technology"]
    },
    {
        "name": "ReCALL",
        "url": "https://www.cambridge.org/core/journals/recall/announcements/call-for-papers",
        "tag": ["language learning", "educational technology"]
    },
    {
        "name": "International Journal of Computer-Supported Collaborative Learning",
        "url": "https://link.springer.com/journal/11412/collections?filter=Open",
        "tag": ["educational technology"]
    },
    {
        "name": "System",
        "url": "https://www.sciencedirect.com/journal/system/about/call-for-papers",
        "tag": ["language learning", "educational technology"]
    },
    {
        "name": "Assessing Writing",
        "url": "https://www.sciencedirect.com/journal/assessing-writing/about/call-for-papers",
        "tag": ["language learning"]
    },
    {
        "name": "Journal of Science Education and Technology",
        "url": "https://link.springer.com/journal/10956/collections?filter=Open",
        "tag": ["educational technology", "STEM education"]
    },
    {
        "name": "Education and Information Technologies",
        "url": "https://link.springer.com/journal/10639/collections?filter=Open",
        "tag": ["educational technology"]
    },
    {
        "name": "Interactive Learning Environments",
        "url": "https://www.tandfonline.com/journals/nile20",
        "tag": ["educational technology"]
    },
    {
        "name": "Academy of Management Learning & Education",
        "url": "https://journals.aom.org/journal/amle",
        "tag": ["educational management", "higher education"]
    },
    {
        "name": "Language Teaching",
        "url": "https://www.cambridge.org/core/journals/language-teaching/announcements/call-for-papers",
        "tag": ["language learning"]
    },
    {
        "name": "Journal of Research on Technology in Education",
        "url": "https://www.tandfonline.com/journals/ujrt20",
        "tag": ["educational technology"]
    },
    {
        "name": "Innovations in Education and Teaching International",
        "url": "https://www.tandfonline.com/journals/riie20",
        "tag": ["general education", "higher education"]
    },
    {
        "name": "Journal of Computing in Higher Education",
        "url": "https://www.springer.com/journal/12528/collections?filter=Open",
        "tag": ["higher education", "educational technology"]
    },
    {
        "name": "Educational Researcher",
        "url": "https://journals.sagepub.com/home/edr",
        "tag": ["general education", "educational policy"]
    },
    {
        "name": "Journal of Educational Computing Research",
        "url": "https://journals.sagepub.com/home/jec",
        "tag": ["educational technology"]
    },
    {
        "name": "Learning and Instruction",
        "url": "https://www.sciencedirect.com/journal/learning-and-instruction/about/call-for-papers",
        "tag": ["general education"]
    },
    {
        "name": "IEEE Transactions on Learning Technologies",
        "url": "https://ieeexplore.ieee.org/xpl/RecentIssue.jsp?punumber=4620076",
        "tag": ["educational technology"]
    },
    {
        "name": "Metacognition and Learning",
        "url": "https://www.springer.com/journal/11409/collections?filter=Open",
        "tag": ["educational psychology", "educational technology"]
    },
    {
        "name": "Journal of Legal Education",
        "url": "https://jle.aals.org/",
        "tag": ["educational policy", "legal education"]
    },
    {
        "name": "Asia-Pacific Education Researcher",
        "url": "https://www.springer.com/journal/40299/collections?filter=Open",
        "tag": ["general education", "educational policy"]
    },
    {
        "name": "Innovation in Language Learning and Teaching",
        "url": "https://www.tandfonline.com/journals/rill20",
        "tag": ["language learning", "educational technology"]
    },
    {
        "name": "Journal of Computer Assisted Learning",
        "url": "https://onlinelibrary.wiley.com/page/journal/13652729/homepage/call-for-papers",
        "tag": ["educational technology"]
    }
]

# 修改：适配 al-folio 目录结构，自动存入 _data 文件夹
# 请确保你的项目根目录下有 _data 文件夹，或者脚本会自动创建
OUTPUT_YML_PATH = "_data/cfps.yml"

# ==========================================
# 月份映射
# ==========================================
MONTH_MAP = {
    'jan': 1, 'january': 1, 'feb': 2, 'february': 2,
    'mar': 3, 'march': 3, 'apr': 4, 'april': 4, 'may': 5,
    'jun': 6, 'june': 6, 'jul': 7, 'july': 7, 'aug': 8, 'august': 8,
    'sep': 9, 'sept': 9, 'september': 9, 'oct': 10, 'october': 10,
    'nov': 11, 'november': 11, 'dec': 12, 'december': 12,
}


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

        print("⚙️ 初始化浏览器组件 (无头模式)...")
        co = ChromiumOptions()
        co.headless(True)
        co.set_argument("--no-sandbox")
        co.set_argument("--disable-gpu")
        co.set_argument("--ignore-certificate-errors")
        co.set_user_agent(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        )
        self.browser = ChromiumPage(co)

    def __del__(self):
        try:
            self.browser.quit()
        except Exception:
            pass

    # --------------------------
    # 通用工具
    # --------------------------
    def clean_text(self, text):
        if not text:
            return "N/A"
        return re.sub(r"\s+", " ", str(text)).strip()

    def normalize_for_date_extraction(self, text):
        if not text:
            return ""
        text = re.sub(r'<[^>]+>', '', str(text))
        text = re.sub(r'(\d)(st|nd|rd|th)\b', r'\1', text, flags=re.I)
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    def extract_date(self, text):
        if not text:
            return None
        normalized = self.normalize_for_date_extraction(text)
        m = self.date_pattern.search(normalized)
        if m:
            return self.clean_text(m.group(0))
        return None

    def parse_date_to_sort_key(self, date_str):
        """
        修改：如果解析失败或为空，直接返回 '9999-99-99'
        """
        default_date = "9999-99-99"
        
        if not date_str or date_str in {"N/A", "未找到日期", ""}:
            return default_date

        normalized = self.normalize_for_date_extraction(date_str)

        try:
            # 1. ISO格式: YYYY-MM-DD
            m = re.match(r'(\d{4})-(\d{2})-(\d{2})', normalized)
            if m:
                return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"

            # 2. DD Month YYYY
            m = re.match(r'(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})', normalized)
            if m:
                day = int(m.group(1))
                month_str = m.group(2).lower()
                year = m.group(3)
                month = MONTH_MAP.get(month_str[:3], 0)
                if month:
                    return f"{year}-{month:02d}-{day:02d}"

            # 3. Month DD, YYYY
            m = re.match(r'([A-Za-z]+)\s+(\d{1,2}),?\s+(\d{4})', normalized)
            if m:
                month_str = m.group(1).lower()
                day = int(m.group(2))
                year = m.group(3)
                month = MONTH_MAP.get(month_str[:3], 0)
                if month:
                    return f"{year}-{month:02d}-{day:02d}"

            # 4. Range: 取最后一个日期
            dates_found = re.findall(r'(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})', normalized)
            if dates_found:
                day, month_str, year = dates_found[-1]
                month = MONTH_MAP.get(month_str.lower()[:3], 0)
                if month:
                    return f"{year}-{month:02d}-{int(day):02d}"
        except Exception:
            pass

        return default_date

    def fetch_page_fast(self, url, timeout=30):
        try:
            print(f"🚀 [HTTP] 正在访问: {url}")
            resp = requests.get(
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
            print(f"❌ 状态码错误 {resp.status_code}")
        except Exception as e:
            print(f"❌ 请求异常: {e}")
        return None

    # --------------------------
    # Browser 工具 (保持不变)
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

    def scroll_to_bottom(self, rounds=3, pause=1.0):
        for _ in range(rounds):
            try:
                self.browser.scroll.to_bottom()
            except Exception:
                try:
                    self.browser.run_js("window.scrollTo(0, document.body.scrollHeight);")
                except Exception:
                    pass
            time.sleep(pause)

    def get_html_browser(self, url, wait=2, scroll_rounds=2):
        print(f"🌐 [Browser] GET {url}")
        self.browser.get(url)
        time.sleep(wait)
        self.try_accept_cookies()
        time.sleep(0.8)
        if scroll_rounds > 0:
            self.scroll_to_bottom(rounds=scroll_rounds, pause=0.8)
        return self.browser.html

    # ==========================================
    # 解析器部分 (保持原样，仅做缩进调整确认)
    # ==========================================
    def _extract_text_clean(self, element):
        if not element: return ""
        html_str = str(element)
        html_str = re.sub(r'<sup[^>]*>.*?</sup>', '', html_str, flags=re.I | re.DOTALL)
        temp_soup = BeautifulSoup(html_str, 'lxml')
        return self.clean_text(temp_soup.get_text(' ', strip=True))

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

    def parse_wiley_browser(self, journal_url):
        print(f"🌐 [Browser] Wiley: {journal_url}")
        try:
            html = self.get_html_browser(journal_url, wait=3, scroll_rounds=2)
            soup = BeautifulSoup(html, "lxml")
            results = self._parse_wiley_dst_listing(soup, journal_url) + self._parse_wiley_h4_blocks(soup, journal_url)
            uniq = {}
            for r in results: uniq[(r.get("title"), r.get("link"))] = r
            return list(uniq.values())
        except Exception as e:
            print(f"❌ Wiley 异常: {e}")
            return []

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
        print(f"🌐 [Browser] T&F: {journal_url}")
        results = []
        try:
            html = self.get_html_browser(journal_url, wait=6, scroll_rounds=1)
            soup = BeautifulSoup(html, "lxml")
            target_links = []
            cfp_container = soup.select_one(".cfpContent") or soup
            for a in cfp_container.select("a[href]"):
                if "think.taylorandfrancis.com" in a.get("href", ""): target_links.append(a.get("href"))
            
            for link_url in list(dict.fromkeys(target_links)):
                tab = self.browser.new_tab(link_url)
                try:
                    try: tab.wait.doc_loaded(timeout=12)
                    except: pass
                    time.sleep(2.5)
                    try: 
                        btn = tab.ele("css:#onetrust-accept-btn-handler", timeout=1)
                        if btn: btn.click()
                    except: pass
                    results.append(self._tf_parse_detail_page_html(tab.html, link_url))
                except: pass
                finally: tab.close()
        except Exception: pass
        uniq = {}
        for r in results: uniq[(r.get("title"), r.get("link"))] = r
        return list(uniq.values())

    def parse_sage_browser(self, journal_url):
        print(f"🌐 [Browser] SAGE: {journal_url}")
        try:
            html = self.get_html_browser(journal_url, wait=2, scroll_rounds=3)
            soup = BeautifulSoup(html, "lxml")
            results = []
            for card in soup.select("div.marketing-spot"):
                title = self._extract_text_clean(card.select_one("h3.marketing-spot__title"))
                desc = self._extract_text_clean(card.select_one("div.marketing-spot__text"))
                a = card.select_one("div.marketing-spot__footer a[href]")
                link = urljoin(journal_url, a["href"]) if a else "N/A"
                if "closed" in desc.lower() or title == "N/A": continue
                
                # 简单过滤广告
                if any(x in title.lower() or x in desc.lower() for x in ["why publish", "reviewer resources", "discipline hubs"]): continue
                if not ("call" in title.lower() or "special issue" in title.lower() or "submit" in desc.lower()): continue

                deadline = self.extract_date(desc) or "未找到日期"
                results.append({"title": title, "abstract_deadline": "未找到日期", "fullpaper_deadline": deadline, "editors": "N/A", "desc": desc, "link": link})
            
            uniq = {}
            for r in results: uniq[(r["title"], r["link"])] = r
            return list(uniq.values())
        except Exception as e:
            print(f"❌ SAGE 异常: {e}")
            return []

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
    # 数据规范化 & 输出 (核心逻辑修改)
    # ==========================================
    def infer_publisher(self, journal_url, journal_name=""):
        u, n = (journal_url or "").lower(), (journal_name or "").lower()
        if "wiley" in u or "wiley" in n: return "Wiley"
        if "tandf" in u or "taylor" in n: return "Taylor & Francis"
        if "sage" in u or "sage" in n: return "SAGE"
        if "sciencedirect" in u or "elsevier" in n: return "Elsevier"
        if "springer" in u or "springer" in n: return "Springer"
        if "cambridge" in u or "cambridge" in n: return "Cambridge Core"
        return "Unknown"

    def _empty_if_na(self, s):
        s = "" if s is None else str(s).strip()
        return "" if s in {"N/A", "未找到日期"} else s

    def normalize_item_for_yaml(self, journal, item):
        fullpaper_deadline = self._empty_if_na(item.get("fullpaper_deadline", "") or item.get("deadline", ""))
        
        # 即使这里是空字符串，parse_date_to_sort_key 也会返回 '9999-99-99'
        fullpaper_deadline_sort = self.parse_date_to_sort_key(fullpaper_deadline)

        # 获取 raw_tag，如果是字符串就转成列表，如果是列表就保持原样
        raw_tag = journal.get("tag", [])
        if isinstance(raw_tag, str):
            # 如果配置的是 "tag": "A"，转为 ["A"]
            # 如果配置的是 "tag": "A, B"，转为 ["A", "B"] (可选，看你喜好，这里简单处理)
            if raw_tag:
                tag_out = [raw_tag] 
            else:
                tag_out = []
        elif isinstance(raw_tag, list):
            # 如果配置的是 "tag": ["A", "B"]，保持原样
            tag_out = raw_tag
        else:
            tag_out = []
        # === 修改结束 ===
        
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

    def export_to_yaml(self, records, path):
        # 确保目录存在
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            yaml.safe_dump(records, f, allow_unicode=True, sort_keys=False, default_flow_style=False, width=120)

    # ==========================================
    # 核心修改：合并旧数据与新数据，并清洗过期数据
    # ==========================================
    def merge_and_clean_records(self, new_records, file_path):
        existing_records = []
        
        # 1. 读取旧数据
        if os.path.exists(file_path):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    existing_records = yaml.safe_load(f) or []
                print(f"📂 读取到历史数据: {len(existing_records)} 条")
            except Exception as e:
                print(f"⚠️ 读取旧 YAML 失败: {e}")

        # 2. 合并：使用 (Title, Link) 作为唯一键
        # 只要 Title 和 Link 相同，新数据会覆盖旧数据（更新 deadline 等信息）
        # 如果新数据这次没爬到（new_records 里没有），旧数据保留在 merged_map 中
        merged_map = {}
        
        # 先放入旧数据
        for item in existing_records:
            key = (item.get("title"), item.get("link"))
            merged_map[key] = item
            
        # 再放入新数据 (覆盖旧的)
        for item in new_records:
            key = (item.get("title"), item.get("link"))
            merged_map[key] = item

        # 3. 清洗过期数据
        final_list = []
        today = datetime.now().date()
        expire_threshold = today - timedelta(days=10) # 允许过期10天
        
        print(f"🧹 执行清理: 剔除 {expire_threshold} 之前截止的条目...")

        for item in merged_map.values():
            sort_date_str = item.get("fullpaper_deadline_sort")
            
            # 如果是 9999-99-99，说明是“待定”或“长期”，必须保留
            if sort_date_str == '9999-99-99':
                final_list.append(item)
                continue
                
            try:
                deadline_date = datetime.strptime(sort_date_str, "%Y-%m-%d").date()
                if deadline_date >= expire_threshold:
                    final_list.append(item)
                else:
                    # print(f"   🗑️ 移除过期: {item.get('title')} ({sort_date_str})")
                    pass
            except ValueError:
                # 解析不了日期的，保留比较安全
                final_list.append(item)

        # 4. 排序：日期越早越靠前 (9999会排在最后)
        final_list.sort(key=lambda x: x.get("fullpaper_deadline_sort") or "9999-99-99")
        
        return final_list

    def run(self, output_yml_path=OUTPUT_YML_PATH):
        new_scraped_records = []
        print("🕷️ 开始爬取任务...")

        for journal in JOURNALS:
            j_name = journal["name"]
            j_url = journal["url"]
            data = []
            
            try:
                url_l = j_url.lower()
                if "tandfonline.com" in url_l:
                    data = self.parse_taylor_francis(j_url)
                elif "wiley.com" in url_l:
                    data = self.parse_wiley_browser(j_url)
                elif "sagepub.com" in url_l:
                    data = self.parse_sage_browser(j_url)
                elif "cambridge.org/core" in url_l:
                    html = self.fetch_page_fast(j_url)
                    if html: data = self.parse_cambridge_core_call_for_papers(html, j_url)
                else:
                    html = self.fetch_page_fast(j_url)
                    if html:
                        if "springer.com" in url_l: data = self.parse_springer(html, j_url)
                        elif "sciencedirect.com" in url_l: data = self.parse_elsevier(html, j_url)
                
                if data:
                    print(f"   ✅ {j_name}: 抓取成功 {len(data)} 条")
                    for item in data:
                        rec = self.normalize_item_for_yaml(journal, item)
                        if rec["title"] or rec["link"]:
                            new_scraped_records.append(rec)
                else:
                    print(f"   ⚠️ {j_name}: 未抓取到数据 (将保留历史数据)")

            except Exception as e:
                print(f"   ❌ {j_name} 爬取失败: {e} (将保留历史数据)")

        # 调用合并与清理逻辑
        final_records = self.merge_and_clean_records(new_scraped_records, output_yml_path)

        self.export_to_yaml(final_records, output_yml_path)
        print(f"🎉 处理完成! 最终写入: {output_yml_path} / 总记录数: {len(final_records)}")

if __name__ == "__main__":
    scraper = JournalCFPScraper()
    scraper.run()