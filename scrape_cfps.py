import re
import time
import os
import yaml
import random
from datetime import datetime, timedelta
from urllib.parse import urljoin
from bs4 import BeautifulSoup

# === 核心库 ===
# 如果报错 no module named 'curl_cffi'，请 pip install curl_cffi
from curl_cffi import requests

# ==========================================
# ⚙️ 配置区域
# ==========================================
OUTPUT_YML_PATH = "_data/cfps.yml"

JOURNALS = [
    # ... (保持你原有的期刊列表不变，这里为了节省篇幅略去，直接复制你原来的列表即可) ...
    # 为了演示，我放几个关键的例子，请务必把你完整的 JOURNALS 列表贴回来！
    {
        "name": "International Journal of Educational Technology in Higher Education",
        "url": "https://link.springer.com/journal/41239/collections?filter=Open",
        "tag": ["educational technology", "higher education"]
    },
    {
        "name": "Computers & Education",
        "url": "https://www.sciencedirect.com/journal/computers-and-education/about/call-for-papers",
        "tag": ["educational technology"]
    },
    {
        "name": "British Journal of Educational Technology",
        "url": "https://bera-journals.onlinelibrary.wiley.com/hub/journal/14678535/bjet_special_issues.htm",
        "tag": ["educational technology"]
    },
    {
        "name": "Review of Educational Research",
        "url": "https://journals.sagepub.com/home/rer",
        "tag": ["review", "general education"]
    },
    {
        "name": "Educational Psychologist",
        "url": "https://www.tandfonline.com/journals/hedp20",
        "tag": ["educational psychology"]
    },
     # ... 请确保把所有期刊列表粘贴回这里 ...
]

# 假设你已经把完整的 JOURNALS 列表填在上面了，下面是逻辑部分

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
        # 即使不用浏览器，也定义一个 session 可能会复用连接
        self.session = requests.Session()

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
        default_date = "9999-99-99"
        if not date_str or date_str in {"N/A", "未找到日期", ""}:
            return default_date
        
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
        except Exception:
            pass
        return default_date

    def fetch_page(self, url, timeout=30):
        """
        统一使用 curl_cffi 获取页面。
        """
        try:
            print(f"🚀 [HTTP] 正在访问: {url}")
            # 随机延迟，减少并发触发WAF的概率
            time.sleep(random.uniform(1, 3))
            
            resp = self.session.get(
                url,
                impersonate="chrome110",  # 尝试 chrome110，有时比最新版更稳定
                timeout=timeout,
                headers={
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
                    "Accept-Language": "en-US,en;q=0.9",
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36",
                    "Referer": "https://www.google.com/" 
                },
                allow_redirects=True
            )
            if resp.status_code in [200, 301, 302]:
                return resp.text
            elif resp.status_code == 403:
                print(f"❌ 403 Forbidden: 被 WAF 拦截 (Cloudflare/Akamai)")
            elif resp.status_code == 500:
                print(f"❌ 500 Server Error")
            else:
                print(f"❌ 状态码错误 {resp.status_code}")
        except Exception as e:
            print(f"❌ 请求异常: {e}")
        return None

    def _extract_text_clean(self, element):
        if not element: return ""
        html_str = str(element)
        html_str = re.sub(r'<sup[^>]*>.*?</sup>', '', html_str, flags=re.I | re.DOTALL)
        temp_soup = BeautifulSoup(html_str, 'lxml')
        return self.clean_text(temp_soup.get_text(' ', strip=True))

    # ==========================================
    # 针对不同出版社的静态解析器 (全部去除了 Browser 依赖)
    # ==========================================

    def parse_wiley_static(self, html, journal_url):
        soup = BeautifulSoup(html, "lxml")
        results = []
        
        # 模式1: DST-CFP-listing-wrap (新版页面)
        wrap = soup.select_one("div.DST-CFP-listing-wrap")
        if wrap:
            for it in wrap.select("div.DST-CFP-listing-item"):
                a_title = it.select_one("h3 a[href]")
                if not a_title: continue
                title = self._extract_text_clean(a_title)
                link = urljoin(journal_url, a_title.get("href"))
                d_el = it.select_one("p.DST-CFP-listing-item__deadline")
                deadline_text = self._extract_text_clean(d_el) if d_el else ""
                dt = self.extract_date(deadline_text)
                deadline = dt or (self.clean_text(deadline_text.split(":", 1)[1]) if ":" in deadline_text else "未找到日期")
                results.append({"title": title, "abstract_deadline": "未找到日期", "fullpaper_deadline": deadline, "editors": "N/A", "desc": "N/A", "link": link})

        # 模式2: 传统的 h4/h3 标题块 (旧版页面)
        for h_tag in soup.find_all(["h3", "h4"]):
            try:
                a_tag = h_tag.find("a", href=True)
                if not a_tag: continue
                title = self._extract_text_clean(a_tag)
                if len(title) < 5: continue 
                
                link = urljoin(journal_url, a_tag.get("href"))
                deadline = "未找到日期"
                
                # 向下查找直到下一个标题
                for sib in h_tag.find_next_siblings():
                    if sib.name in ["h3", "h4", "hr", "section"]: break
                    text = self._extract_text_clean(sib).lower()
                    if "deadline" in text:
                        dt = self.extract_date(text)
                        if dt: 
                            deadline = dt
                            break
                
                if title != "N/A":
                    results.append({"title": title, "abstract_deadline": "未找到日期", "fullpaper_deadline": deadline, "editors": "N/A", "desc": "N/A", "link": link})
            except: continue
            
        return results

    def parse_taylor_francis_static(self, html, journal_url):
        # T&F 静态抓取很难，因为内容往往在 iframe 或 JS 里。
        # 但我们尝试抓取主页上的 "Call for papers" 链接区域
        soup = BeautifulSoup(html, "lxml")
        results = []
        
        # 寻找包含 "Call for papers" 的链接
        # T&F 常见结构: <a href="...">Call for papers</a>
        candidates = []
        for a in soup.find_all("a", href=True):
            if "call for paper" in a.get_text().lower():
                candidates.append(urljoin(journal_url, a['href']))
        
        # 如果找到了具体的 CFP 列表页，需要再请求一次那个列表页
        # 这里为了简化，我们只记录找到了 "Call for Papers" 的入口，或者尝试解析当前页
        # 如果当前页就是列表页 (通常 URL 包含 calls-for-papers)
        
        container = soup.select_one(".cfpContent") # T&F 某些页面的容器
        if container:
             for a in container.select("a[href]"):
                link = urljoin(journal_url, a.get("href"))
                title = self._extract_text_clean(a)
                if len(title) > 10:
                    results.append({"title": title, "abstract_deadline": "未找到日期", "fullpaper_deadline": "未找到日期", "editors": "N/A", "desc": "T&F Link", "link": link})
        
        # 简单的兜底：如果没解析出具体条目，但没报错，就不返回数据（保留历史）
        return results

    def parse_sage_static(self, html, journal_url):
        soup = BeautifulSoup(html, "lxml")
        results = []
        # SAGE Marketing Spots
        for card in soup.select("div.marketing-spot"):
            title = self._extract_text_clean(card.select_one("h3.marketing-spot__title"))
            desc = self._extract_text_clean(card.select_one("div.marketing-spot__text"))
            a = card.select_one("div.marketing-spot__footer a[href]")
            link = urljoin(journal_url, a["href"]) if a else "N/A"
            
            if "closed" in desc.lower() or title == "N/A": continue
            if any(x in title.lower() for x in ["why publish", "reviewer resources"]): continue
            if not ("call" in title.lower() or "special issue" in title.lower() or "submit" in desc.lower()): continue

            deadline = self.extract_date(desc) or "未找到日期"
            results.append({"title": title, "abstract_deadline": "未找到日期", "fullpaper_deadline": deadline, "editors": "N/A", "desc": desc, "link": link})
        return results

    def parse_elsevier(self, html, base_url):
        soup = BeautifulSoup(html, "lxml")
        results = []
        # Elsevier 结构经常变，这里保留原本逻辑
        header = soup.find(["h2", "h3"], string=re.compile("Call for papers", re.I))
        container = header.find_next("ul", class_="sub-list") if header else soup.find("ul", class_="sub-list")
        if not container: return []
        for item in container.find_all("li"):
            try:
                h3 = item.find("h3")
                if not h3: continue
                title = self._extract_text_clean(h3.find("a"))
                link = urljoin(base_url, h3.find("a")["href"])
                d_div = item.find(lambda t: t.name == "div" and "Submission deadline" in t.get_text())
                deadline = self._extract_text_clean(d_div.find("strong")) if d_div and d_div.find("strong") else "未找到日期"
                results.append({"title": title, "abstract_deadline": "未找到日期", "fullpaper_deadline": deadline, "editors": "N/A", "desc": "N/A", "link": link})
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
                deadline = "未找到日期"
                for dt in art.find_all("dt"):
                    if "deadline" in dt.get_text().lower() and dt.find_next_sibling("dd"):
                        deadline = self._extract_text_clean(dt.find_next_sibling("dd"))
                        break
                if deadline != "未找到日期":
                    results.append({"title": title, "abstract_deadline": "未找到日期", "fullpaper_deadline": deadline, "editors": "N/A", "desc": "N/A", "link": link})
            except: continue
        return results

    def parse_cambridge(self, html, base_url):
        soup = BeautifulSoup(html, "lxml")
        results = []
        for ov in (soup.select_one("#maincontent") or soup).select("ul.overview"):
            a = ov.select_one("li.title a[href]")
            if not a: continue
            title = self._extract_text_clean(a)
            link = urljoin(base_url, a["href"])
            date_el = ov.select_one("li.date")
            deadline = self._extract_text_clean(date_el) if date_el else "未找到日期"
            results.append({"title": title, "abstract_deadline": "未找到日期", "fullpaper_deadline": deadline, "editors": "N/A", "desc": "N/A", "link": link})
        return results

    # ==========================================
    # 数据输出与合并
    # ==========================================
    def infer_publisher(self, url, name):
        u, n = (url or "").lower(), (name or "").lower()
        if "wiley" in u: return "Wiley"
        if "tandf" in u: return "Taylor & Francis"
        if "sage" in u: return "SAGE"
        if "sciencedirect" in u: return "Elsevier"
        if "springer" in u: return "Springer"
        if "cambridge" in u: return "Cambridge Core"
        return "Unknown"

    def normalize_item_for_yaml(self, journal, item):
        fullpaper_deadline = item.get("fullpaper_deadline", "")
        fullpaper_deadline_sort = self.parse_date_to_sort_key(fullpaper_deadline)
        
        raw_tag = journal.get("tag", [])
        tag_out = [raw_tag] if isinstance(raw_tag, str) else raw_tag

        return {
            "journal": journal.get("name"),
            "publisher": self.infer_publisher(journal.get("url"), journal.get("name")),
            "tag": tag_out,
            "title": item.get("title"),
            "abstract_deadline": item.get("abstract_deadline", ""),
            "fullpaper_deadline": fullpaper_deadline,
            "fullpaper_deadline_sort": fullpaper_deadline_sort,
            "editors": item.get("editors", "N/A"),
            "link": item.get("link"),
            "description": item.get("desc", "N/A"),
        }

    def merge_and_clean_records(self, new_records, file_path):
        existing_records = []
        if os.path.exists(file_path):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    existing_records = yaml.safe_load(f) or []
            except Exception: pass

        merged_map = {}
        # 先载入旧数据
        for item in existing_records:
            key = (item.get("title"), item.get("link"))
            merged_map[key] = item
        # 新数据覆盖旧数据
        for item in new_records:
            key = (item.get("title"), item.get("link"))
            merged_map[key] = item

        final_list = []
        today = datetime.now().date()
        expire_threshold = today - timedelta(days=10) # 过期10天不显示

        for item in merged_map.values():
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

    def run(self, output_yml_path=OUTPUT_YML_PATH):
        new_scraped_records = []
        print("🕷️ 开始爬取任务 (Pure Requests Mode)...")

        for journal in JOURNALS:
            j_name = journal["name"]
            j_url = journal["url"]
            data = []
            
            try:
                html = self.fetch_page(j_url)
                if html:
                    url_l = j_url.lower()
                    if "tandfonline.com" in url_l:
                        data = self.parse_taylor_francis_static(html, j_url)
                    elif "wiley.com" in url_l or "onlinelibrary.wiley" in url_l:
                        data = self.parse_wiley_static(html, j_url)
                    elif "sagepub.com" in url_l:
                        data = self.parse_sage_static(html, j_url)
                    elif "cambridge.org" in url_l:
                        data = self.parse_cambridge(html, j_url)
                    elif "springer.com" in url_l:
                        data = self.parse_springer(html, j_url)
                    elif "sciencedirect.com" in url_l:
                        data = self.parse_elsevier(html, j_url)
                    else:
                        print(f"   ⚠️ 未知出版社，跳过: {j_name}")

                    if data:
                        print(f"   ✅ {j_name}: 抓取成功 {len(data)} 条")
                        for item in data:
                            rec = self.normalize_item_for_yaml(journal, item)
                            if rec["title"] and rec["link"]:
                                new_scraped_records.append(rec)
                    else:
                        print(f"   ⚠️ {j_name}: 解析结果为空 (内容可能被 JS 渲染或无新CFP)")
                else:
                    print(f"   ❌ {j_name}: 无法获取页面内容")

            except Exception as e:
                print(f"   ❌ {j_name} 处理异常: {e}")

        final_records = self.merge_and_clean_records(new_scraped_records, output_yml_path)
        
        os.makedirs(os.path.dirname(output_yml_path), exist_ok=True)
        with open(output_yml_path, "w", encoding="utf-8") as f:
            yaml.safe_dump(final_records, f, allow_unicode=True, sort_keys=False, default_flow_style=False, width=120)
        
        print(f"🎉 处理完成! 最终写入: {output_yml_path} / 总记录数: {len(final_records)}")

if __name__ == "__main__":
    scraper = JournalCFPScraper()
    scraper.run()