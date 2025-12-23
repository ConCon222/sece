#!/usr/bin/env python3
"""
Journal Ranking Data Updater - Enhanced Version
Collects journal ranking data from multiple sources using FlareSolverr
"""

import json
import yaml
import requests
import time
import re
import os
import sys
import argparse
from datetime import datetime
import logging
from typing import Dict, List, Optional, Any
from urllib.parse import urlparse
import random
from dotenv import load_dotenv

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# FlareSolverr configuration
FLARESOLVERR_URL = "http://127.0.0.1:8191"
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15'
]

class FlareSolverrClient:
    """Client for FlareSolverr to bypass anti-bot protection (Enhanced for Wiley)"""
    
    def __init__(self, base_url: str = FLARESOLVERR_URL):
        self.base_url = base_url
        self.session = None
        
    def create_session(self) -> Optional[str]:
        """Create a new FlareSolverr session"""
        try:
            # 销毁旧 session 以防残留
            if self.session:
                self.destroy_session()
                
            session_id = f"journal_session_{int(time.time())}"
            response = requests.post(f"{self.base_url}/v1", json={
                "cmd": "sessions.create",
                "session": session_id,
                # 显式指定浏览器参数，尝试模拟真实环境
                "userAgent": random.choice(USER_AGENTS) 
            }, timeout=30)
            
            data = response.json()
            if data.get("status") == "ok":
                self.session = session_id
                logger.info(f"Created FlareSolverr session: {self.session}")
                return self.session
            else:
                logger.error(f"Failed to create session: {data}")
                return None
        except Exception as e:
            logger.error(f"Error creating FlareSolverr session: {e}")
            return None
    
    def get_page(self, url: str) -> Optional[str]:
        """Get page content using FlareSolverr with Retry Logic"""
        # 增加最大超时时间到 3 分钟 (180000ms)
        # Wiley 的五秒盾有时候会卡很久
        max_timeout = 180000 
        
        for attempt in range(2): # 尝试 2 次
            if not self.session:
                if not self.create_session():
                    return None
            
            try:
                logger.info(f"   🔄 Requesting page (Attempt {attempt+1}): {url}")
                
                # 注意：Python 的 requests timeout 必须比 FlareSolverr 的 maxTimeout 大
                # 这里设为 190秒，给 FlareSolverr 留出 180秒 处理时间
                response = requests.post(f"{self.base_url}/v1", json={
                    "cmd": "request.get",
                    "url": url,
                    "maxTimeout": max_timeout,
                    "session": self.session,
                    # 只要 HTML 下载完就算成功，不需要等所有图片加载完 (networkidle0有时会卡死)
                    "returnOnlyHtml": True 
                }, timeout=190) 
                
                if response.status_code == 500:
                    logger.warning(f"   ⚠️ FlareSolverr 500 Error (Timeout?). Destroying session and retrying...")
                    self.destroy_session() # 销毁当前 session，下次循环会重建
                    continue

                response.raise_for_status()
                data = response.json()
                
                if data.get("status") == "ok":
                    solution = data.get("solution", {})
                    html = solution.get("response")
                    
                    # 简单检查是否真的拿到了内容，而不是 blocked 页面
                    if "Just a moment" in html and len(html) < 5000:
                         logger.warning("   ⚠️ Still stuck on Cloudflare challenge.")
                         self.destroy_session()
                         continue
                         
                    return html
                else:
                    logger.error(f"FlareSolverr request failed: {data}")
                    self.destroy_session() # 失败就销毁，保持环境干净
                    
            except Exception as e:
                logger.error(f"Error fetching page {url}: {e}")
                self.destroy_session()
                
        return None
    
    def destroy_session(self):
        """Destroy the FlareSolverr session"""
        if self.session:
            try:
                requests.post(f"{self.base_url}/v1", json={
                    "cmd": "sessions.destroy",
                    "session": self.session
                }, timeout=10)
                logger.info(f"Destroyed FlareSolverr session: {self.session}")
            except Exception as e:
                logger.error(f"Error destroying session: {e}")
            finally:
                self.session = None

class EasyScholarCrawler:
    """Crawler for EasyScholar API - 紫色分区、红色分区、紫色分数"""
    
    def __init__(self, secret_key: str):
        self.api_url = "https://www.easyscholar.cc/open/getPublicationRank"
        self.secret_key = secret_key
        
    def get_journal_rank(self, journal_name: str) -> Dict[str, Any]:
        """
        获取期刊排名数据
        
        Args:
            journal_name: 期刊名称
            
        Returns:
            {
                'jcr_quartile': 'Q1',      # 紫色分区
                'cas_division': '教育学2区',# 红色分区
                'impact_factor': '5.4'     # 紫色分数
            }
        """
        try:
            logger.info(f"   🔍 [EasyScholar] 查询期刊: {journal_name}")
            
            response = requests.get(
                self.api_url,
                params={
                    'secretKey': self.secret_key,
                    'publicationName': journal_name
                },
                timeout=30
            )
            response.raise_for_status()
            data = response.json()
            
            if data.get('code') == 200:
                official_rank = data.get('data', {}).get('officialRank', {}).get('select', {})
                
                result = {
                    'purple_quartile': official_rank.get('ssci', ''),      # SSCI/SCI分区
                    'red_division': official_rank.get('sciUp', ''),     # 中科院分区
                    'purple_score': official_rank.get('sciif', '')     # Impact Factor
                }
                
                logger.info(f"   ✅ [EasyScholar] 紫色分区={result['purple_quartile']}, "
                          f"红色分区={result['red_division']}, 紫色分数={result['purple_score']}")
                
                # 必须的 0.5 秒延迟
                time.sleep(0.5)
                
                return result
            else:
                logger.warning(f"   ⚠️ [EasyScholar] API 错误: {data.get('msg')}")
                time.sleep(0.5)  # 即使失败也延迟
                return {}
                
        except Exception as e:
            logger.error(f"   ❌ [EasyScholar] 调用失败: {e}")
            time.sleep(0.5)  # 确保总是延迟
            return {}


class PublisherCrawler:
    """Base class for publisher crawlers"""
    
    def __init__(self, flaresolverr_client: FlareSolverrClient):
        self.client = flaresolverr_client
    
    def extract_metrics(self, url: str) -> Dict[str, Any]:
        """Extract metrics from publisher page - to be implemented by subclasses"""
        return {}

class WileyCrawler(PublisherCrawler):
    """Crawler for Wiley journals - 优化版"""
    
    def extract_metrics(self, url: str) -> Dict[str, Any]:
        """Extract metrics from Wiley journal-metrics page"""
        # 确保 URL 指向 metrics 页面
        if "journal-metrics" not in url:
            # 处理类似 /journal/1234/ 的 URL
            if "/journal/" in url:
                url = url.replace("/journal/", "/journal-metrics/")
            # 如果结尾不是 metrics
            if not url.endswith("journal-metrics") and "journal-metrics" not in url:
                url = f"{url.rstrip('/')}/journal-metrics"
        
        logger.info(f"Fetching Wiley data from: {url}")
        html = self.client.get_page(url)
        if not html:
            return {}
        
        metrics = {
            'acceptance_rate': '',
            'first_decision_time': '',
            'review_time': '', # 这个指标在你提供的HTML中不存在，作为预留
            'acceptance_time': '',
            'publication_time': '',
            'publisher': 'Wiley'
        }
        
        try:
            # 使用 re.DOTALL 让 . 可以匹配换行符
            # 使用 re.IGNORECASE 忽略大小写
            
            # 1. Extract Acceptance rate
            # HTML: <span class="label">Acceptance rate: </span></h4><p> 11%</p>
            # 逻辑: 找到 "Acceptance rate"，跳过中间所有字符直到遇到 <p>，然后提取数字
            ar_match = re.search(r'Acceptance\s+rate.*?<p>\s*(\d+(?:\.\d+)?)%', html, re.DOTALL | re.IGNORECASE)
            if ar_match:
                metrics['acceptance_rate'] = f"{ar_match.group(1)}%"
            
            # 2. Extract Submission to first decision
            # HTML: <span class="label">Submission to first decision <span> (median) </span>: </span></h4><p> 29 days </p>
            # 逻辑: 这里的 .*? 会自动跳过中间的 <span> (median) </span> 结构
            sfd_match = re.search(r'Submission\s+to\s+first\s+decision.*?<p>\s*(\d+)\s*days', html, re.DOTALL | re.IGNORECASE)
            if sfd_match:
                metrics['first_decision_time'] = f"{sfd_match.group(1)} days"
            
            # 3. Extract Submission to decision after review
            # 注意：你提供的 HTML 中没有这一项，但如果其他 Wiley 期刊有，这个正则可以匹配
            sdar_match = re.search(r'Submission\s+to\s+decision\s+after\s+review.*?<p>\s*(\d+)\s*days', html, re.DOTALL | re.IGNORECASE)
            if sdar_match:
                metrics['review_time'] = f"{sdar_match.group(1)} days"
            
            # 4. Extract Submission to acceptance
            # HTML: <span class="label">Submission to acceptance <span> (median) </span>: </span></h4><p> 214 days </p>
            sa_match = re.search(r'Submission\s+to\s+acceptance.*?<p>\s*(\d+)\s*days', html, re.DOTALL | re.IGNORECASE)
            if sa_match:
                metrics['acceptance_time'] = f"{sa_match.group(1)} days"
            
            # 5. Extract Acceptance to publication
            # HTML: <span class="label">Acceptance to publication <span> (median) </span>: </span></h4><p> 15 days </p>
            ap_match = re.search(r'Acceptance\s+to\s+publication.*?<p>\s*(\d+)\s*days', html, re.DOTALL | re.IGNORECASE)
            if ap_match:
                metrics['publication_time'] = f"{ap_match.group(1)} days"
            
            logger.info(f"Extracted Wiley metrics: {metrics}")
            
        except Exception as e:
            logger.error(f"Error parsing Wiley HTML: {e}")
        
        return metrics
    
class TaylorFrancisCrawler(PublisherCrawler):
    """Crawler for Taylor & Francis journals - 最终防贪婪匹配版"""
    
    def extract_metrics(self, url: str) -> Dict[str, Any]:
        """Extract metrics from Taylor & Francis about-this-journal page"""
        if "about-this-journal" not in url:
            base_url = url.split('#')[0].rstrip('/')
            url = f"{base_url}/about-this-journal"
        
        # 加上锚点方便日志排查
        if "#aims-and-scope" not in url:
            url = f"{url}#aims-and-scope"
        
        logger.info(f"Fetching Taylor & Francis data from: {url}")
        html = self.client.get_page(url)
        if not html:
            return {}
        
        metrics = {
            'acceptance_rate': '',
            'first_decision_time': '',
            'review_time': '',
            'publication_time': '',
            'acceptance_time': '',
            'publisher': 'Taylor & Francis'
        }
        
        try:
            # 核心修正：使用 (?:(?!<strong>).)*? 代替 .*?
            # 作用：在寻找关键词时，禁止跨越下一个 <strong> 标签，防止匹配到上面错误的数字。
            
            # 1. Acceptance rate
            ar_match = re.search(r'<strong>\s*(\d+(?:\.\d+)?)\s*%?\s*</strong>(?:(?!<strong>).)*?acceptance\s+rate', html, re.DOTALL | re.IGNORECASE)
            if ar_match and float(ar_match.group(1)) > 0:
                metrics['acceptance_rate'] = f"{ar_match.group(1)}%"
            
            # 2. Submission to first decision (截图里是0，会被过滤掉)
            sfd_match = re.search(r'<strong>\s*(\d+)\s*</strong>(?:(?!<strong>).)*?submission\s+to\s+first\s+decision', html, re.DOTALL | re.IGNORECASE)
            if sfd_match and sfd_match.group(1) != '0':
                metrics['first_decision_time'] = f"{sfd_match.group(1)} days"
            
            # 3. Submission to post-review decision (截图里是50)
            # 之前的代码会因为贪婪匹配错误地抓成 0，现在会正确抓到 50
            sprd_match = re.search(r'<strong>\s*(\d+)\s*</strong>(?:(?!<strong>).)*?submission\s+to\s+first\s+post-review\s+decision', html, re.DOTALL | re.IGNORECASE)
            if sprd_match and sprd_match.group(1) != '0':
                metrics['review_time'] = f"{sprd_match.group(1)} days"
            
            # 4. Acceptance to online publication (截图里是30)
            ap_match = re.search(r'<strong>\s*(\d+)\s*</strong>(?:(?!<strong>).)*?acceptance\s+to\s+online\s+publication', html, re.DOTALL | re.IGNORECASE)
            if ap_match and ap_match.group(1) != '0':
                metrics['publication_time'] = f"{ap_match.group(1)} days"

            # 5. Submission to acceptance (截图里没有)
            sa_match = re.search(r'<strong>\s*(\d+)\s*</strong>(?:(?!<strong>).)*?submission\s+to\s+acceptance', html, re.DOTALL | re.IGNORECASE)
            if sa_match and sa_match.group(1) != '0':
                 metrics['acceptance_time'] = f"{sa_match.group(1)} days"

            logger.info(f"Extracted Taylor & Francis metrics: {metrics}")
            
        except Exception as e:
            logger.error(f"Error parsing Taylor & Francis HTML: {e}")
        
        return metrics

class SpringerCrawler(PublisherCrawler):
    """Crawler for Springer journals - 优化版"""
    
    def extract_metrics(self, url: str) -> Dict[str, Any]:
        """Extract metrics from Springer journal page"""
        logger.info(f"Fetching Springer data from: {url}")
        html = self.client.get_page(url)
        if not html:
            return {}
        
        metrics = {
            'first_decision_time': '',
            'publisher': 'Springer'
        }
        
        try:
            # 使用 re.DOTALL 跨行匹配
            # 策略：利用 Springer 特有的 data-test 属性定位，忽略中间的 HTML 标签结构
            
            # 1. Extract Submission to first decision
            # HTML: <dd data-test="metrics-speed-value"> \n <span class="u-text-bold">19 days</span> \n </dd>
            # 逻辑：找到 metrics-speed-value，不管中间隔了多少标签(<span>等)，直接找后面的数字 + days
            speed_match = re.search(r'data-test="metrics-speed-value".*?(\d+)\s*days', html, re.DOTALL | re.IGNORECASE)
            if speed_match:
                metrics['first_decision_time'] = f"{speed_match.group(1)} days"
            
            logger.info(f"Extracted Springer metrics: {metrics}")
            
        except Exception as e:
            logger.error(f"Error parsing Springer HTML: {e}")
        
        return metrics

class SageCrawler(PublisherCrawler):
    """Crawler for SAGE journals - 优化版"""
    
    def extract_metrics(self, url: str) -> Dict[str, Any]:
        """Extract metrics from SAGE journal page"""
        logger.info(f"Fetching SAGE data from: {url}")
        html = self.client.get_page(url)
        if not html:
            return {}
        
        metrics = {
            'first_decision_time': '',
            'publication_time': '',
            'acceptance_rate': '',
            'publisher': 'SAGE'
        }
        
        try:
            # 使用 re.DOTALL 忽略换行符影响
            # 使用 re.IGNORECASE 忽略大小写
            
            # 1. Extract First decision -> 映射到 first_decision_time
            # HTML: First decision:</div><div ...>77<span>days*</span>
            # 逻辑: 找到 "First decision:"，跳过中间乱七八糟的标签，找到数字，且确保后面跟着 days
            fd_match = re.search(r'First\s+decision:.*?(\d+)\s*<span[^>]*>days', html, re.DOTALL | re.IGNORECASE)
            if fd_match:
                metrics['first_decision_time'] = f"{fd_match.group(1)} days"
            
            # 2. Extract Acceptance to publication
            # HTML: Acceptance to publication:</div><div ...>39<span>days*</span>
            ap_match = re.search(r'Acceptance\s+to\s+publication:.*?(\d+)\s*<span[^>]*>days', html, re.DOTALL | re.IGNORECASE)
            if ap_match:
                metrics['publication_time'] = f"{ap_match.group(1)} days"
            
            # 3. Extract Acceptance rate
            # HTML: Acceptance rate:</div><div ...>5.0<span class="percentage">%</span>
            # 逻辑: 匹配整数或小数 (如 5 或 5.0)，且后面跟着 %
            ar_match = re.search(r'Acceptance\s+rate:.*?(\d+(?:\.\d+)?)\s*<span[^>]*>%', html, re.DOTALL | re.IGNORECASE)
            if ar_match:
                metrics['acceptance_rate'] = f"{ar_match.group(1)}%"
            
            logger.info(f"Extracted SAGE metrics: {metrics}")
            
        except Exception as e:
            logger.error(f"Error parsing SAGE HTML: {e}")
        
        return metrics

import re
from typing import Dict, Any

class ElsevierCrawler(PublisherCrawler):
    """Crawler for Elsevier journals - 优化版"""
    
    def extract_metrics(self, url: str) -> Dict[str, Any]:
        """Extract metrics from Elsevier insights page"""
        logger.info(f"Fetching Elsevier data from: {url}")
        html = self.client.get_page(url)
        if not html:
            return {}
        
        # 字段初始化 - 使用下划线命名与其他爬虫保持一致
        metrics = {
            'acceptance_rate': '',
            'first_decision_time': '',
            'review_time': '',
            'acceptance_time': '',
            'publication_time': '', 
            'publisher': 'Elsevier'
        }
        
        def clean_value(raw_value: str) -> str:
            """清洗 Elsevier 特有的脏数据，如 '8<!-- --> days' -> '8 days'"""
            if not raw_value:
                return ''
            # 1. 移除 HTML 注释 <!-- -->
            cleaned = re.sub(r'<!--.*?-->', '', raw_value)
            # 2. 合并多余空格
            cleaned = re.sub(r'\s+', ' ', cleaned)
            # 3. 去除首尾空格
            return cleaned.strip()

        # 标签 -> 字段名的映射表（使用下划线命名）
        LABEL_MAPPING = {
            'submission to first decision': 'first_decision_time',
            'first decision': 'first_decision_time',
            'submission to first decision (median)': 'first_decision_time',
            'submission to decision after review': 'review_time',
            'submission to acceptance': 'acceptance_time',
            'acceptance to online publication': 'publication_time',
            'acceptance to publication': 'publication_time',
            'acceptance rate': 'acceptance_rate',
        }

        try:
            # ===== 核心正则：匹配 metric-box 内的 值+标签 =====
            # 结构：<li class="metric-box..."><span class="text-xl">值</span>...<div class="text-s">标签</div>
            pattern = r'<li[^>]*class="metric-box[^"]*"[^>]*>.*?' \
                      r'<span[^>]*class="text-xl"[^>]*>(.*?)</span>.*?' \
                      r'<div[^>]*class="text-s"[^>]*>(.*?)</div>'
            
            matches = re.findall(pattern, html, re.DOTALL | re.IGNORECASE)
            
            for raw_value, raw_label in matches:
                cleaned_value = clean_value(raw_value)
                cleaned_label = clean_value(raw_label).lower()
                
                # 在映射表中查找对应字段
                for label_key, field_name in LABEL_MAPPING.items():
                    if label_key in cleaned_label:
                        metrics[field_name] = cleaned_value
                        logger.debug(f"Matched: '{cleaned_label}' -> {field_name} = {cleaned_value}")
                        break
            
            logger.info(f"Extracted Elsevier metrics: {metrics}")
            
        except Exception as e:
            import traceback
            logger.error(f"Error parsing Elsevier HTML: {e}")
            logger.error(traceback.format_exc())
        
        return metrics

class JournalRankingUpdater:
    def __init__(self, flaresolverr_url: str = FLARESOLVERR_URL, easyscholar_key: str = None):
        self.flaresolverr_client = FlareSolverrClient(flaresolverr_url)
        
        # Initialize EasyScholar crawler if key is provided
        if easyscholar_key:
            self.easyscholar_crawler = EasyScholarCrawler(easyscholar_key)
            logger.info("EasyScholar API initialized")
        else:
            self.easyscholar_crawler = None
            logger.warning("⚠️ No EasyScholar API key provided - 紫色分区、红色分区、紫色分数 will not be updated from EasyScholar")
        
        # Initialize publisher crawlers
        self.publisher_crawlers = {
            'wiley': WileyCrawler(self.flaresolverr_client),
            'taylor_francis': TaylorFrancisCrawler(self.flaresolverr_client),
            'springer': SpringerCrawler(self.flaresolverr_client),
            'sage': SageCrawler(self.flaresolverr_client),
            'elsevier': ElsevierCrawler(self.flaresolverr_client)
        }
        
        # Map publishers to crawlers
        self.publisher_map = {
            'wiley.com': 'wiley',
            'onlinelibrary.wiley.com': 'wiley',
            'tandfonline.com': 'taylor_francis',
            'springer.com': 'springer',
            'link.springer.com': 'springer',
            'sagepub.com': 'sage',
            'journals.sagepub.com': 'sage',
            'sciencedirect.com': 'elsevier',
            'elsevier.com': 'elsevier'
        }
    
    def load_journal_data(self):
        """Load journal data from journal_rank.json and jrank.yml"""
        journal_rank_file = '_data/journal_rank.json'
        jrank_file = '_data/jrank.yml'
        
        # Check if journal_rank.json exists
        if not os.path.exists(journal_rank_file):
            logger.error(f"Required file not found: {journal_rank_file}")
            logger.error("Please ensure journal_rank.json exists in the _data directory")
            return [], []
        
        try:
            with open(journal_rank_file, 'r', encoding='utf-8') as f:
                journal_list = json.load(f)
                logger.info(f"Loaded {len(journal_list)} journals from {journal_rank_file}")
            
            # Try to load existing data from jrank.yml
            try:
                with open(jrank_file, 'r', encoding='utf-8') as f:
                    existing_data = yaml.safe_load(f) or []
                    logger.info(f"Loaded {len(existing_data)} existing entries from {jrank_file}")
            except FileNotFoundError:
                logger.info(f"{jrank_file} not found, will create new file")
                existing_data = []
                
            return journal_list, existing_data
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in {journal_rank_file}: {e}")
            return [], []
        except Exception as e:
            logger.error(f"Error loading journal data: {e}")
            return [], []
    
    def get_publisher_from_url(self, url: str) -> Optional[str]:
        """Determine publisher from URL"""
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            
            # Remove www. prefix if present
            if domain.startswith('www.'):
                domain = domain[4:]
            
            # Check for known publisher domains
            for publisher_domain, publisher_key in self.publisher_map.items():
                if publisher_domain in domain:
                    return publisher_key
            
            # Special cases
            if 'springer' in domain:
                return 'springer'
            elif 'wiley' in domain:
                return 'wiley'
            elif 'tandf' in domain:
                return 'taylor_francis'
            elif 'sage' in domain:
                return 'sage'
            elif 'elsevier' in domain or 'sciencedirect' in domain:
                return 'elsevier'
            
            return None
        except Exception as e:
            logger.error(f"Error determining publisher from URL {url}: {e}")
            return None
    
    def update_journal_rankings(self, dry_run: bool = False):
        """Main function to update all journal rankings"""
        if dry_run:
            logger.info("Running in DRY-RUN mode - data will NOT be saved")
        
        journal_list, existing_data = self.load_journal_data()
        
        # Create a dictionary for quick lookup of existing data
        existing_dict = {item['journal']: item for item in existing_data}
        
        updated_count = 0
        
        for journal_info in journal_list:
            journal_name = journal_info['name']
            url = journal_info.get('url', '')
            sourceid = journal_info.get('sourceid')
            tags = journal_info.get('tag', [])
            
            logger.info(f"Processing {journal_name}...")
            
            # 获取现有数据或创建新条目（保留所有现有字段）
            if journal_name in existing_dict:
                journal_data = existing_dict[journal_name].copy()
                # 更新 tag（如果有新的）
                if tags and not journal_data.get('tag'):
                    journal_data['tag'] = tags
            else:
                # 新期刊，创建基础条目
                journal_data = {
                    'journal': journal_name,
                    'publisher': '',
                    'tag': tags,
                    'purple_quartile': '',
                    'orange_quartile': '',
                    'orange_percentile': '',
                    'red_division': '',
                    'orange_score': '',
                    'documents_published': '',
                    'purple_score': '',
                    'acceptance_rate': '',
                    'first_decision_time': '',
                    'review_time': '',
                    'acceptance_time': '',
                    'publication_time': '',
                    'hm_score': ''
                }
            
            # Determine publisher from URL
            if url:
                publisher_key = self.get_publisher_from_url(url)
                if publisher_key:
                    journal_data['publisher'] = publisher_key
            
            # Get publisher-specific metrics
            if url and journal_data.get('publisher'):
                publisher_key = journal_data['publisher']
                if publisher_key in self.publisher_crawlers:
                    try:
                        publisher_metrics = self.publisher_crawlers[publisher_key].extract_metrics(url)
                        # Update only if we got data
                        for key, value in publisher_metrics.items():
                            if value:
                                journal_data[key] = value
                    except Exception as e:
                        logger.error(f"Error getting publisher metrics for {journal_name}: {e}")
            
            # Get EasyScholar data (紫色分区、红色分区、紫色分数) - 优先级最高
            if self.easyscholar_crawler:
                try:
                    easyscholar_data = self.easyscholar_crawler.get_journal_rank(journal_name)
                    
                    # 更新 3 个字段（EasyScholar 数据优先级最高，会覆盖之前的值）
                    if easyscholar_data.get('purple_quartile'):
                        journal_data['purple_quartile'] = easyscholar_data['purple_quartile']
                    if easyscholar_data.get('red_division'):
                        journal_data['red_division'] = easyscholar_data['red_division']
                    if easyscholar_data.get('purple_score'):
                        journal_data['purple_score'] = easyscholar_data['purple_score']
                        
                except Exception as e:
                    logger.error(f"Error getting EasyScholar data for {journal_name}: {e}")
            
            # Calculate HM score
            journal_data['hm_score'] = self.calculate_hm_score(journal_data)
            
            # 更新到 existing_dict
            existing_dict[journal_name] = journal_data
            updated_count += 1
            
            # Add delay to avoid rate limiting
            time.sleep(random.uniform(2, 5))
        
        # Save updated data (skip if dry-run or no updates)
        if dry_run:
            logger.info("DRY-RUN: Skipping file save. Would have updated %d journals", updated_count)
            logger.info("DRY-RUN: Sample data (first journal):")
            if existing_dict:
                first_journal = list(existing_dict.values())[0]
                logger.info(yaml.dump([first_journal], default_flow_style=False, allow_unicode=True))
        elif updated_count == 0:
            logger.info("ℹ️ 没有数据更新，跳过保存")
        else:
            try:
                # 转换回列表（保留所有期刊数据）
                updated_data = list(existing_dict.values())
                with open('_data/jrank.yml', 'w', encoding='utf-8') as f:
                    yaml.dump(updated_data, f, default_flow_style=False, allow_unicode=True)
                logger.info("Successfully updated jrank.yml with %d journals", len(updated_data))
            except Exception as e:
                logger.error(f"Error saving updated data: {e}")
        
        # Clean up FlareSolverr session
        self.flaresolverr_client.destroy_session()
    
    def calculate_hm_score(self, journal_data):
        """Calculate HM (Haoming) custom score based on multiple factors
        
        计算公式:
        - 紫色分区 (purple_quartile): 20分 (Q1=20, Q2=15, Q3=10, Q4=5)
        - 紫色分数 (purple_score): 直接加
        - 橙色分数 (orange_score): 除以2直接加
        - 橙色百分位 (orange_percentile): 20分 (按百分比计算)
        - 接受率 (acceptance_rate): 反向加分 (100-rate)/10，默认4分
        - 发文量 (documents_last_year): >200加10分, >100加5分, >50加3分
        """
        score = 0
        
        # 1. 紫色分区 scoring (20分满分)
        jcr = journal_data.get('purple_quartile', '').upper()
        if 'Q1' in jcr:
            score += 20
        elif 'Q2' in jcr:
            score += 15
        elif 'Q3' in jcr:
            score += 10
        elif 'Q4' in jcr:
            score += 5
            
        # 2. 紫色分数 - 乘以2直接加
        try:
            purple_score = float(journal_data.get('purple_score', 0) or 0)
            score += purple_score * 2
        except (ValueError, TypeError):
            pass
            
        # 3. 橙色分数 - 直接加
        try:
            orange_score = float(journal_data.get('orange_score', 0) or 0)
            score += orange_score
        except (ValueError, TypeError):
            pass
            
        # 4. 橙色百分位 scoring (20分满分，按百分比计算)
        try:
            orange_percentile = float(journal_data.get('orange_percentile', 0) or 0)
            score += orange_percentile * 0.2  # 99 -> 19.8, 50 -> 10
        except (ValueError, TypeError):
            pass
            
        # 5. 接受率 - 直接加分，默认4分
        try:
            acceptance_rate = journal_data.get('acceptance_rate', '')
            if acceptance_rate and '%' in str(acceptance_rate):
                rate = float(str(acceptance_rate).replace('%', ''))
                # 接受率直接加: 10% -> 10分, 20% -> 20分
                score += rate
            else:
                # 没有接受率数据，默认加4分
                score += 4
        except (ValueError, TypeError):
            score += 4
            
        # 6. 发文量加分 (documents_last_year)
        try:
            docs_last_year = journal_data.get('documents_last_year', '')
            if docs_last_year:
                # 格式可能是 "127 (2024)" 或纯数字
                docs_str = str(docs_last_year).split('(')[0].strip()
                docs_count = int(docs_str)
                if docs_count > 200:
                    score += 10
                elif docs_count > 100:
                    score += 5
                elif docs_count > 50:
                    score += 3
        except (ValueError, TypeError):
            pass
            
        return round(score, 1)  # 四舍五入到小数点后1位

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Update journal ranking data using FlareSolverr and EasyScholar API')
    parser.add_argument('--flaresolverr', '-f', type=str, default=FLARESOLVERR_URL,
                       help=f'FlareSolverr URL (default: {FLARESOLVERR_URL})')
    parser.add_argument('--easyscholar-key', '-e', type=str, 
                       help='EasyScholar API secret key (can also use EASYSCHOLAR_KEY env variable)')
    parser.add_argument('--debug', '-d', action='store_true', help='Enable debug logging')
    parser.add_argument('--dry-run', '-n', action='store_true', 
                       help='Dry run - collect data but don\'t save')
    args = parser.parse_args()
    
    # Set logging level
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Get EasyScholar key from args or environment variable
    easyscholar_key = args.easyscholar_key or os.environ.get('EASYSCHOLAR_KEY')
    
    # Create and run updater
    updater = JournalRankingUpdater(args.flaresolverr, easyscholar_key=easyscholar_key)
    
    try:
        logger.info("Starting journal ranking update...")
        updater.update_journal_rankings(dry_run=args.dry_run)
        logger.info("Journal ranking update completed successfully")
    except KeyboardInterrupt:
        logger.info("Update interrupted by user")
        # Clean up session
        updater.flaresolverr_client.destroy_session()
        sys.exit(1)
    except Exception as e:
        logger.error(f"Update failed with error: {e}")
        # Clean up session
        updater.flaresolverr_client.destroy_session()
        sys.exit(1)

if __name__ == "__main__":
    main()
