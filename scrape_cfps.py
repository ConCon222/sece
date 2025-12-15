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
        
        # === 增强配置：最强隐身模式 ===
        print("⚙️ 初始化 DrissionPage (增强隐身模式)...")
        co = ChromiumOptions()
        
        # 1. 基础 Headless 设置
        co.headless(True) # 在 GHA 必须为 True
        co.set_argument("--no-sandbox")
        co.set_argument("--disable-gpu")
        
        # 2. 关键：移除自动化特征
        co.set_argument("--disable-blink-features=AutomationControlled") 
        co.set_argument("--disable-infobars")
        
        # 3. 关键：伪装 User-Agent (使用标准 Win10 Chrome)
        # 绝对不能包含 "HeadlessChrome"
        ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        co.set_user_agent(ua)
        
        # 4. 关键：设置窗口大小 (Headless 默认很小，会被识别)
        co.set_argument("--window-size=1920,1080")
        co.set_argument("--start-maximized")
        
        # 5. 其他隐匿设置
        co.set_argument("--lang=en-US")
        co.set_pref("profile.default_content_setting_values.notifications", 2)
        
        # 启动
        self.browser = ChromiumPage(co)
        
        # 二次防御：通过 CDP 脚本再次覆盖 navigator.webdriver
        self.browser.run_js("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

    def __del__(self):
        try:
            self.browser.quit()
        except Exception:
            pass

    # --------------------------
    # 日期与文本处理
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

    # --------------------------
    # 核心：增强型页面访问
    # --------------------------
    def anti_detect_action(self):
        """模拟人类动作：随机鼠标移动"""
        try:
            self.browser.run_js("window.scrollTo(0, 100)")
            time.sleep(0.5)
            self.browser.run_js("window.scrollTo(0, 0)")
        except: pass

    def get_html_safe(self, url, wait=5):
        print(f"🌐 [Drission] 访问: {url}")
        try:
            self.browser.get(url)
            
            # Cloudflare 挑战检测
            title = self.browser.title.lower()
            if "just a moment" in title or "security check" in title or "cloudfare" in title:
                print("   🛡️ 检测到 Cloudflare 盾，尝试等待 10秒...")
                time.sleep(10)
                # 尝试点击任何可能的 iframe 复选框 (玄学，但在 DP 中有时有效)
                try:
                    self.browser.ele("tag:iframe").ele("css:input[type=checkbox]").click()
                except: pass
                time.sleep(5)

            # 模拟人类操作
            self.anti_detect_action()
            time.sleep(2) # 基础等待
            
            # 处理 Cookie 弹窗 (提高页面加载完整性)
            try:
                btn = self.browser.ele("text:Accept All Cookies") or \
                      self.browser.ele("text:Accept all") or \
                      self.browser.ele("text:I Agree") or \
                      self.browser.ele("id:onetrust-accept-btn-handler")
                if btn: 
                    btn.click(by_js=True)
                    time.sleep(1)
            except: pass

            # 滚动加载
            self.browser.scroll.to_bottom()
            time.sleep(1)

            return self.browser.html
        except Exception as e:
            print(f"   ❌ 浏览器异常: {e}")
            return None

    def _extract_text_clean(self, element):
        if not element: return ""
        html_str = str(element)
        html_str = re.sub(r'<sup[^>]*>.*?</sup>', '', html_str, flags=re.I | re.DOTALL)
        soup = BeautifulSoup(html_str, 'lxml')
        return self.clean_text(soup.get_text(' ', strip=True))

    # ==========================================
    # 解析逻辑 (复用 BeautifulSoup，保持稳定)
    # ==========================================
    
    # 1. Wiley
    def parse_wiley(self, html, journal_url):
        soup = BeautifulSoup(html, "lxml")
        results = []
        # 模式1: DST-CFP-listing-wrap
        wrap = soup.select_one("div.DST-CFP-listing-wrap")
        if wrap:
            for it in wrap.select("div.DST-CFP-listing-item"):
                a_title = it.select_one("h3 a[href]")
                if not a_title: continue
                title = self._extract_text_clean(a_title)
                link = urljoin(journal_url, a_title.get("href"))
                d_el = it.select_one("p.DST-CFP-listing-item__deadline")
                deadline_text = self._extract_text_clean(d_el) if d_el else ""
                dt = self.extract_date(deadline_text) or (deadline_text.split(":", 1)[1].strip() if ":" in deadline_text else "未找到日期")
                results.append({"title": title, "fullpaper_deadline": dt, "link": link})
        
        # 模式2: H4 Block
        for h4 in soup.find_all("h4"):
            try:
                a = h4.find("a", href=True)
                if not a: continue
                title = self._extract_text_clean(a)
                link = urljoin(journal_url, a.get("href"))
                deadline = "未找到日期"
                for sib in h4.find_next_siblings():
                    if sib.name in {"h4", "hr"}: break
                    txt = self._extract_text_clean(sib).lower()
                    if "deadline" in txt:
                        deadline = self.extract_date(txt) or deadline
                        break
                results.append({"title": title, "fullpaper_deadline": deadline, "link": link})
            except: continue
        return results

    # 2. Taylor & Francis
    def parse_tf(self, html, journal_url):
        soup = BeautifulSoup(html, "lxml")
        results = []
        # T&F 现在通常需要点击，但我们先试着抓取页面上的静态链接
        # 查找所有包含 "Call for papers" 的链接
        seen_links = set()
        for a in soup.find_all("a", href=True):
            txt = a.get_text().lower()
            if "call for paper" in txt or "special issue" in txt:
                link = urljoin(journal_url, a['href'])
                if link not in seen_links and "doi.org" not in link:
                    seen_links.add(link)
                    # 简单猜测标题，因为没有进入详情页
                    title = self._extract_text_clean(a)
                    if len(title) < 10: title = "Call for Papers (Check Link)"
                    results.append({"title": title, "fullpaper_deadline": "未找到日期", "link": link})
        return results

    # 3. SAGE
    def parse_sage(self, html, journal_url):
        soup = BeautifulSoup(html, "lxml")
        results = []
        for card in soup.select("div.marketing-spot"):
            title = self._extract_text_clean(card.select_one("h3.marketing-spot__title"))
            desc = self._extract_text_clean(card.select_one("div.marketing-spot__text"))
            a = card.select_one("div.marketing-spot__footer a[href]")
            link = urljoin(journal_url, a["href"]) if a else "N/A"
            if "closed" in desc.lower() or title == "N/A": continue
            if "submit" not in desc.lower() and "call" not in title.lower(): continue
            deadline = self.extract_date(desc) or "未找到日期"
            results.append({"title": title, "fullpaper_deadline": deadline, "desc": desc, "link": link})
        return results

    # 4. Elsevier
    def parse_elsevier(self, html, base_url):
        soup = BeautifulSoup(html, "lxml")
        results = []
        # 尝试查找 H3 链接
        for h3 in soup.find_all("h3"):
            a = h3.find("a", href=True)
            if not a: continue
            if "call for paper" in h3.get_text().lower() or "special issue" in h3.get_text().lower():
                title = self._extract_text_clean(a)
                link = urljoin(base_url, a['href'])
                # 尝试找 deadline
                deadline = "未找到日期"
                # 往父级找 container
                parent = h3.find_parent("li")
                if parent:
                    txt = parent.get_text()
                    deadline = self.extract_date(txt) or deadline
                results.append({"title": title, "fullpaper_deadline": deadline, "link": link})
        return results
    
    # 5. Springer / Cambridge (通常较容易)
    def parse_standard(self, html, base_url):
        # 通用解析器，尝试提取列表
        soup = BeautifulSoup(html, "lxml")
        results = []
        # Springer Collections
        for art in soup.find_all("article", class_="app-card-collection"):
            heading = art.find(["h2", "h3"])
            if heading and heading.find("a"):
                title = self._extract_text_clean(heading)
                link = urljoin(base_url, heading.find("a")['href'])
                desc = art.get_text()
                deadline = self.extract_date(desc) or "未找到日期"
                results.append({"title": title, "fullpaper_deadline": deadline, "link": link})
        return results

    # ==========================================
    # 流程控制
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
            "title": item.get("title", "N/A"),
            "abstract_deadline": "未找到日期",
            "fullpaper_deadline": fullpaper_deadline,
            "fullpaper_deadline_sort": fullpaper_deadline_sort,
            "editors": "N/A",
            "link": item.get("link", ""),
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
        for item in existing_records:
            key = (item.get("title"), item.get("link"))
            merged_map[key] = item
        for item in new_records:
            key = (item.get("title"), item.get("link"))
            merged_map[key] = item

        final_list = []
        today = datetime.now().date()
        expire_threshold = today - timedelta(days=10)
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
        print("🕷️ 开始爬取任务 (DrissionPage Enhanced Stealth)...")

        for journal in JOURNALS:
            j_name = journal["name"]
            j_url = journal["url"]
            print(f"--- 处理: {j_name} ---")
            
            try:
                html = self.get_html_safe(j_url)
                if html:
                    url_l = j_url.lower()
                    data = []
                    if "tandfonline.com" in url_l:
                        data = self.parse_tf(html, j_url)
                    elif "wiley.com" in url_l or "onlinelibrary.wiley" in url_l:
                        data = self.parse_wiley(html, j_url)
                    elif "sagepub.com" in url_l:
                        data = self.parse_sage(html, j_url)
                    elif "sciencedirect.com" in url_l:
                        data = self.parse_elsevier(html, j_url)
                    else:
                        data = self.parse_standard(html, j_url)
                    
                    if data:
                        print(f"   ✅ 抓取到 {len(data)} 条数据")
                        for item in data:
                            rec = self.normalize_item_for_yaml(journal, item)
                            new_scraped_records.append(rec)
                    else:
                        print("   ⚠️ 页面已获取，但未解析出特定CFP格式 (保留旧数据)")
                else:
                    print("   ❌ 页面加载失败 (403/超时)")
            except Exception as e:
                print(f"   ❌ 处理异常: {e}")

        final_records = self.merge_and_clean_records(new_scraped_records, output_yml_path)
        os.makedirs(os.path.dirname(output_yml_path), exist_ok=True)
        with open(output_yml_path, "w", encoding="utf-8") as f:
            yaml.safe_dump(final_records, f, allow_unicode=True, sort_keys=False, default_flow_style=False, width=120)
        print(f"🎉 任务结束! 总条目: {len(final_records)}")

if __name__ == "__main__":
    scraper = JournalCFPScraper()
    scraper.run()