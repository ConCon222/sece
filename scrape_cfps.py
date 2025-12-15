# scraper.py
import os
import re
import time
import random
import requests
import yaml
from datetime import datetime, timedelta
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from curl_cffi import requests as curl_requests

# ==========================================
# 配置
# ==========================================
FLARESOLVERR_URL = "http://localhost:8191"

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
        "name": "British Journal of Educational Technology",
        "url": "https://bera-journals.onlinelibrary.wiley.com/hub/journal/14678535/bjet_special_issues.htm",
        "tag": ["educational technology"]
    },
    {
        "name": "International Journal of STEM Education",
        "url": "https://link.springer.com/journal/40594/collections?filter=Open",
        "tag": ["educational technology", "STEM education"]
    },
    # ... 添加其他期刊
]

OUTPUT_PATH = "_data/cfps.yml"

MONTH_MAP = {
    'jan': 1, 'january': 1, 'feb': 2, 'february': 2,
    'mar': 3, 'march': 3, 'apr': 4, 'april': 4, 'may': 5,
    'jun': 6, 'june': 6, 'jul': 7, 'july': 7, 'aug': 8, 'august': 8,
    'sep': 9, 'sept': 9, 'september': 9, 'oct': 10, 'october': 10,
    'nov': 11, 'november': 11, 'dec': 12, 'december': 12,
}

# Cloudflare 保护的站点
CF_PROTECTED_SITES = [
    "tandfonline.com",
    "wiley.com",
    "sagepub.com",
    "onlinelibrary.wiley",
    "bera-journals",
]


class CFPScraper:
    def __init__(self):
        self.date_pattern = re.compile(
            r"(\d{1,2})(?:st|nd|rd|th)?\s*"
            r"(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)[a-z]*\s+"
            r"(\d{4})|"
            r"(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)[a-z]*\s+"
            r"(\d{1,2})(?:st|nd|rd|th)?,?\s+(\d{4})|"
            r"(\d{4})-(\d{2})-(\d{2})",
            re.I,
        )

    # --------------------------
    # HTTP 请求
    # --------------------------
    def needs_flaresolverr(self, url):
        return any(site in url.lower() for site in CF_PROTECTED_SITES)

    def fetch_with_curl(self, url, timeout=30):
        """普通站点用 curl_cffi"""
        try:
            print(f"  🚀 [curl] {url}")
            resp = curl_requests.get(
                url,
                impersonate="chrome120",
                timeout=timeout,
                headers={"Accept-Language": "en-US,en;q=0.9"},
            )
            if resp.status_code == 200:
                return resp.text
            print(f"  ❌ 状态码: {resp.status_code}")
        except Exception as e:
            print(f"  ❌ curl 异常: {e}")
        return None

    def fetch_with_flaresolverr(self, url, max_timeout=60000):
        """Cloudflare 站点用 FlareSolverr"""
        try:
            print(f"  🛡️ [FlareSolverr] {url}")
            resp = requests.post(
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
                return data["solution"]["response"]
            print(f"  ❌ FlareSolverr 错误: {data.get('message')}")
        except Exception as e:
            print(f"  ❌ FlareSolverr 异常: {e}")
        return None

    def fetch_html(self, url):
        """自动选择抓取方式"""
        if self.needs_flaresolverr(url):
            return self.fetch_with_flaresolverr(url)
        return self.fetch_with_curl(url)

    # --------------------------
    # 工具函数
    # --------------------------
    def clean_text(self, text):
        if not text:
            return ""
        return re.sub(r"\s+", " ", str(text)).strip()

    def extract_text(self, element):
        if not element:
            return ""
        html_str = re.sub(r'<sup[^>]*>.*?</sup>', '', str(element), flags=re.I | re.DOTALL)
        soup = BeautifulSoup(html_str, 'lxml')
        return self.clean_text(soup.get_text(' ', strip=True))

    def extract_date(self, text):
        if not text:
            return None
        text = re.sub(r'(\d)(st|nd|rd|th)\b', r'\1', text, flags=re.I)
        m = self.date_pattern.search(text)
        return self.clean_text(m.group(0)) if m else None

    def parse_date_to_sort_key(self, date_str):
        if not date_str:
            return "9999-99-99"
        try:
            # YYYY-MM-DD
            m = re.match(r'(\d{4})-(\d{2})-(\d{2})', date_str)
            if m:
                return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
            # 15 January 2025
            m = re.match(r'(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})', date_str)
            if m:
                day, month_str, year = int(m.group(1)), m.group(2).lower()[:3], m.group(3)
                month = MONTH_MAP.get(month_str, 0)
                if month:
                    return f"{year}-{month:02d}-{day:02d}"
            # January 15, 2025
            m = re.match(r'([A-Za-z]+)\s+(\d{1,2}),?\s+(\d{4})', date_str)
            if m:
                month_str, day, year = m.group(1).lower()[:3], int(m.group(2)), m.group(3)
                month = MONTH_MAP.get(month_str, 0)
                if month:
                    return f"{year}-{month:02d}-{day:02d}"
        except:
            pass
        return "9999-99-99"

    # --------------------------
    # 解析器
    # --------------------------
    def parse_springer(self, html, base_url):
        soup = BeautifulSoup(html, "lxml")
        results = []
        for art in soup.select("article.app-card-collection"):
            try:
                heading = art.select_one("h2.app-card-collection__heading, h3")
                a = heading.select_one("a[href]") if heading else None
                if not a:
                    continue
                title = self.extract_text(a)
                link = urljoin(base_url, a["href"])
                desc = self.extract_text(art.select_one("div.app-card-collection__text"))
                
                deadline = None
                for dt in art.select("dt"):
                    if "deadline" in dt.get_text().lower():
                        dd = dt.find_next_sibling("dd")
                        if dd:
                            deadline = self.extract_text(dd)
                            break
                
                if deadline:
                    results.append({
                        "title": title,
                        "deadline": deadline,
                        "desc": desc,
                        "link": link
                    })
            except:
                continue
        return results

    def parse_elsevier(self, html, base_url):
        soup = BeautifulSoup(html, "lxml")
        results = []
        container = soup.select_one("ul.sub-list")
        if not container:
            return []
        for item in container.select("li"):
            try:
                h3 = item.select_one("h3")
                a = h3.select_one("a[href]") if h3 else None
                if not a:
                    continue
                title = self.extract_text(a)
                link = urljoin(base_url, a["href"])
                desc = self.extract_text(item.select_one("p.intro"))
                
                deadline_div = item.find(lambda t: t.name == "div" and "deadline" in t.get_text().lower())
                deadline = self.extract_text(deadline_div.select_one("strong")) if deadline_div else None
                
                results.append({
                    "title": title,
                    "deadline": deadline or self.extract_date(desc),
                    "desc": desc,
                    "link": link
                })
            except:
                continue
        return results

    def parse_taylor_francis(self, html, base_url):
        """T&F 首页解析 - 提取 CFP 链接"""
        soup = BeautifulSoup(html, "lxml")
        results = []
        
        # 查找 think.taylorandfrancis.com 链接
        for a in soup.select("a[href*='think.taylorandfrancis.com']"):
            link = a.get("href")
            title = self.extract_text(a)
            if title and len(title) > 5:
                # 获取详情页
                detail_html = self.fetch_with_flaresolverr(link)
                if detail_html:
                    detail = self._parse_tf_detail(detail_html, link)
                    if detail:
                        results.append(detail)
                time.sleep(random.uniform(2, 4))
        
        return results

    def _parse_tf_detail(self, html, url):
        """解析 T&F 详情页"""
        soup = BeautifulSoup(html, "lxml")
        
        title = self.extract_text(soup.select_one("h2")) or "未知标题"
        
        deadline = None
        for sec in soup.select("section.layout__deadline--title"):
            time_el = sec.select_one("time")
            label = self.extract_text(sec.select_one("h3")).lower()
            if time_el and ("manuscript" in label or "submission" in label):
                deadline = self.extract_text(time_el)
                break
        
        desc = ""
        about = soup.select_one("section.layout__about")
        if about:
            paragraphs = [self.extract_text(p) for p in about.select("p") if len(self.extract_text(p)) > 50]
            if paragraphs:
                desc = max(paragraphs, key=len)
        
        return {
            "title": title,
            "deadline": deadline,
            "desc": desc,
            "link": url
        }

    def parse_wiley(self, html, base_url):
        """Wiley 解析"""
        soup = BeautifulSoup(html, "lxml")
        results = []
        
        # DST-CFP 列表格式
        for item in soup.select("div.DST-CFP-listing-item"):
            a = item.select_one("h3 a[href]")
            if not a:
                continue
            title = self.extract_text(a)
            link = urljoin(base_url, a["href"])
            
            deadline_el = item.select_one("p.DST-CFP-listing-item__deadline")
            deadline = self.extract_date(self.extract_text(deadline_el)) if deadline_el else None
            
            results.append({
                "title": title,
                "deadline": deadline,
                "desc": "",
                "link": link
            })
        
        # h4 块格式
        for h4 in soup.select("h4"):
            a = h4.select_one("a[href]")
            if not a:
                continue
            title = self.extract_text(a)
            link = urljoin(base_url, a["href"])
            
            deadline = None
            for sib in h4.find_next_siblings():
                if sib.name == "h4":
                    break
                text = self.extract_text(sib)
                if "deadline" in text.lower():
                    deadline = self.extract_date(text)
                    break
            
            if title:
                results.append({
                    "title": title,
                    "deadline": deadline,
                    "desc": "",
                    "link": link
                })
        
        # 去重
        seen = set()
        unique = []
        for r in results:
            key = (r["title"], r["link"])
            if key not in seen:
                seen.add(key)
                unique.append(r)
        return unique

    def parse_sage(self, html, base_url):
        """SAGE 解析"""
        soup = BeautifulSoup(html, "lxml")
        results = []
        
        for card in soup.select("div.marketing-spot"):
            title = self.extract_text(card.select_one("h3.marketing-spot__title"))
            desc = self.extract_text(card.select_one("div.marketing-spot__text"))
            a = card.select_one("div.marketing-spot__footer a[href]")
            link = urljoin(base_url, a["href"]) if a else ""
            
            # 过滤无关内容
            skip = ["why publish", "reviewer", "discipline hub", "submit your article"]
            if any(x in title.lower() or x in desc.lower() for x in skip):
                continue
            if "closed" in desc.lower():
                continue
            
            deadline = self.extract_date(desc)
            
            if title and ("call" in title.lower() or "special issue" in title.lower()):
                results.append({
                    "title": title,
                    "deadline": deadline,
                    "desc": desc,
                    "link": link
                })
        
        return results

    def parse_cambridge(self, html, base_url):
        """Cambridge Core 解析"""
        soup = BeautifulSoup(html, "lxml")
        results = []
        
        for ul in soup.select("ul.overview.no-margin-bottom-for-small"):
            a = ul.select_one("li.title a[href]")
            if not a:
                continue
            title = self.extract_text(a)
            link = urljoin(base_url, a["href"])
            
            date_el = ul.select_one("li.date")
            deadline = self.extract_text(date_el) if date_el else None
            desc = self.extract_text(ul.select_one("li.description"))
            
            results.append({
                "title": title,
                "deadline": deadline,
                "desc": desc,
                "link": link
            })
        
        return results

    # --------------------------
    # 主流程
    # --------------------------
    def scrape_journal(self, journal):
        """抓取单个期刊"""
        url = journal["url"]
        html = self.fetch_html(url)
        if not html:
            return []
        
        url_lower = url.lower()
        
        if "springer.com" in url_lower:
            return self.parse_springer(html, url)
        elif "sciencedirect.com" in url_lower:
            return self.parse_elsevier(html, url)
        elif "tandfonline.com" in url_lower:
            return self.parse_taylor_francis(html, url)
        elif "wiley.com" in url_lower or "onlinelibrary.wiley" in url_lower:
            return self.parse_wiley(html, url)
        elif "sagepub.com" in url_lower:
            return self.parse_sage(html, url)
        elif "cambridge.org" in url_lower:
            return self.parse_cambridge(html, url)
        else:
            # 默认尝试 Springer 格式
            return self.parse_springer(html, url)

    def normalize_record(self, journal, item):
        """标准化记录"""
        deadline = item.get("deadline") or ""
        return {
            "journal": journal["name"],
            "tag": journal.get("tag", []),
            "title": item.get("title", ""),
            "fullpaper_deadline": deadline,
            "fullpaper_deadline_sort": self.parse_date_to_sort_key(deadline),
            "link": item.get("link", ""),
            "description": item.get("desc", ""),
        }

    def run(self):
        """运行爬虫"""
        print(f"🕷️ 开始爬取 {len(JOURNALS)} 个期刊...\n")
        
        all_records = []
        
        for idx, journal in enumerate(JOURNALS, 1):
            print(f"[{idx}/{len(JOURNALS)}] {journal['name']}")
            
            try:
                items = self.scrape_journal(journal)
                if items:
                    print(f"  ✅ 获取 {len(items)} 条")
                    for item in items:
                        record = self.normalize_record(journal, item)
                        if record["title"]:
                            all_records.append(record)
                else:
                    print(f"  ⚠️ 无数据")
            except Exception as e:
                print(f"  ❌ 异常: {e}")
            
            time.sleep(random.uniform(1, 3))
        
        # 合并历史数据
        existing = []
        if os.path.exists(OUTPUT_PATH):
            try:
                with open(OUTPUT_PATH, "r", encoding="utf-8") as f:
                    existing = yaml.safe_load(f) or []
                print(f"\n📂 历史数据: {len(existing)} 条")
            except:
                pass
        
        # 去重合并
        merged = {}
        for r in existing:
            merged[(r.get("title"), r.get("link"))] = r
        for r in all_records:
            merged[(r.get("title"), r.get("link"))] = r
        
        # 过滤过期
        today = datetime.now().date()
        cutoff = today - timedelta(days=10)
        final = []
        for r in merged.values():
            sort_date = r.get("fullpaper_deadline_sort", "9999-99-99")
            if sort_date == "9999-99-99":
                final.append(r)
            else:
                try:
                    d = datetime.strptime(sort_date, "%Y-%m-%d").date()
                    if d >= cutoff:
                        final.append(r)
                except:
                    final.append(r)
        
        # 排序
        final.sort(key=lambda x: x.get("fullpaper_deadline_sort", "9999-99-99"))
        
        # 保存
        os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
        with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
            yaml.safe_dump(final, f, allow_unicode=True, sort_keys=False)
        
        print(f"\n🎉 完成！保存 {len(final)} 条到 {OUTPUT_PATH}")


if __name__ == "__main__":
    scraper = CFPScraper()
    scraper.run()