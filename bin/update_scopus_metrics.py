#!/usr/bin/env python3
"""
期刊指标更新器 - 使用 DrissionPage 获取橙色分数指标
独立运行，专门更新：橙色分数、橙色分区、Documents Published、Percentile
"""

import json
import yaml
import time
import logging
from DrissionPage import WebPage, ChromiumOptions
from typing import Dict, Any, Optional
import re

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class ScopusDrissionCrawler:
    """使用 DrissionPage 爬取期刊橙色系指标"""
    
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.base_url = "https://www.scopus.com/sourceid"
        
        # 配置浏览器选项
        self.options = ChromiumOptions()
        
        # 1. 关键：设置无头模式的特定参数以防被检测
        if headless:
            self.options.headless()
            # 某些反爬虫检测无头浏览器的 user-agent，手动强制覆盖
            self.options.set_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        # 2. 配置代理 (如果本地 IP 被封)
        # 格式: http://username:password@ip:port 或 http://ip:port
        # self.options.set_proxy('http://127.0.0.1:7890') 
        
        # 3. 自动处理一些反爬特征
        self.options.auto_port()  # 自动寻找可用端口
        self.options.set_argument('--no-sandbox')
        self.options.set_argument('--disable-gpu')
        
        # DrissionPage 默认已经处理了很多 WebDriver 特征，通常不需要像 Selenium 那样做很多 mask
    
    def calculate_orange_quartile(self, percentile: float) -> str:
        """
        根据 Percentile 计算橙色分区
        Q1: 100-75
        Q2: 74-50
        Q3: 49-25
        Q4: 24-0
        """
        if percentile >= 75:
            return "Q1"
        elif percentile >= 50:
            return "Q2"
        elif percentile >= 25:
            return "Q3"
        else:
            return "Q4"
    
    def scrape_journal_metrics(self, source_id: int) -> Dict[str, Any]:
        """
        爬取单个期刊的 Scopus 指标
        
        Args:
            source_id: Scopus 期刊 ID
            
        Returns:
            {
                'citescore': '17.6',
                'sjr_quartile': 'Q1',
                'sjr_percentile': '95',
                'documents_published': '133'
            }
        """
        result = {
        "source_id": source_id,
        "orange_score": None,
        "orange_quartile": None,
        "orange_percentile": None,
        "documents_published": None,
        "docs_current_year": None,  # 新增：当年发文量
        "docs_last_year": None,     # 新增：去年发文量
        "citescore_rank_data": [],
        "documents_data": [],
        "success": False,
        "error": None
    }
        
        # 创建 WebPage 实例，应用配置
        page = WebPage(chromium_options=self.options)
        
        try:
            # 1. 访问 Scopus 期刊页面 (tabs=0 显示 CiteScore)
            url = f"{self.base_url}/{source_id}#tabs=0"
            logger.info(f"正在访问: {url}")
            page.get(url, timeout=30)
            
            # 等待页面加载
            page.wait.ele_displayed('#rpResult', timeout=20)
            time.sleep(2)
            
            # 2. 抓取 CiteScore
            try:
                citescore_element = page.ele('#rpResult')
                if citescore_element:
                    result['orange_score'] = citescore_element.text.strip()
                    logger.info(f"   ✅ 橙色分数: {result['orange_score']}")
            except Exception as e:
                logger.warning(f"   ⚠️ 无法获取橙色分数: {e}")
            
            # 3. 抓取 Percentile (用于计算 SJR Quartile)
            try:
                page.wait.ele_displayed('#rpCategoryDropDown', timeout=15)
                # 查找分类表格
                table = page.ele('#CSCategoryTBody')
                if table:
                    rows = table.eles('tag:tr')
                    if rows:
                        # 取第一个分类的 Percentile
                        first_row = rows[0]
                        cells = first_row.eles('tag:td')
                        if len(cells) >= 3:
                            percentile_text = cells[2].text.strip()
                            # 提取数字：如 "95th" -> "95"
                            percentile_match = re.search(r'(\d+)', percentile_text)
                            if percentile_match:
                                percentile = int(percentile_match.group(1))
                                result['orange_percentile'] = str(percentile)
                                result['orange_quartile'] = self.calculate_orange_quartile(percentile)
                                logger.info(f"   ✅ Percentile: {percentile}th -> 橙色分区: {result['orange_quartile']}")
            except Exception as e:
                logger.warning(f"   ⚠️ 无法获取 Percentile: {e}")
            
            # ... (前面代码保持不变) ...

            # 4. 导航到 Content Coverage 标签页 (#tabs=2) 获取 Documents Published 数据
            print("\n=== 步骤 3: 获取 Documents Published 数据 (当年 & 去年) ===")
            try:
                # 确保 result 字典里有这两个字段 (建议在函数开头初始化时加上)
                result["docs_current_year"] = "0"
                result["docs_last_year"] = "0"

                print("正在导航到 Content Coverage 标签页 (#tabs=2)...")
                content_coverage_url = f"https://www.scopus.com/sourceid/{source_id}#tabs=2"
                page.get(content_coverage_url, timeout=30)
                time.sleep(3) # 等待渲染
                
                page.wait.ele_displayed("#contentCoverage", timeout=20)
                
                # 获取表格
                table = page.ele('#contentCoverage')
                rows = []
                if table:
                    rows = table.eles('tag:tr')
                
                print(f"找到 {len(rows)} 行数据")
                
                # 遍历前两行：第0行通常是当年(Header)，第1行通常是去年
                for i, row in enumerate(rows):
                    if i > 1: break # 我们只需要前两年，拿到后就退出循环

                    cells = row.eles("tag:td")
                    if not cells: 
                         cells = row.eles("tag:th")

                    if len(cells) >= 2:
                        # 提取年份和数量
                        year_text = cells[0].text.strip()
                        doc_text = cells[1].text.strip()
                        
                        # 使用正则提取纯数字 (处理 "176 documents" -> "176")
                        doc_count_match = re.search(r'(\d+)', doc_text)
                        doc_count = doc_count_match.group(1) if doc_count_match else "0"

                        print(f"解析第 {i} 行 -> 年份: {year_text} | 数量: {doc_count}")

                        # 逻辑判断：第0行视为“最新/当年”，第1行视为“去年”
                        if i == 0:
                            result["docs_current_year"] = f"{doc_count} ({year_text})"
                            result["documents_data"].append({"year": year_text, "documents": doc_count})
                        elif i == 1:
                            result["docs_last_year"] = f"{doc_count} ({year_text})"
                            result["documents_data"].append({"year": year_text, "documents": doc_count})

                if result["documents_data"]:
                    print(f"✅ 提取成功")
                else:
                    print(f"⚠️ 未提取到数据")

            except Exception as e:
                print(f"✗ 获取 Documents Published 数据失败: {e}")
            
            # ... (后面代码保持不变) ...
                
        except Exception as e:
            logger.error(f"❌ 爬取失败: {e}")
        
        finally:
            # 关闭页面
            try:
                page.quit()
            except:
                pass
        
        return result


def update_scopus_metrics_in_yaml(dry_run: bool = False):
    """
    更新 jrank.yml 中的橙色系指标
    
    Args:
        dry_run: 是否为测试模式（不保存文件）
    """
    journal_rank_file = '_data/journal_rank.json'
    jrank_file = '_data/jrank.yml'
    
    # 1. 读取期刊列表（获取 sourceid）
    try:
        with open(journal_rank_file, 'r', encoding='utf-8') as f:
            journal_list = json.load(f)
        logger.info(f"📖 加载了 {len(journal_list)} 个期刊")
    except Exception as e:
        logger.error(f"❌ 无法读取 {journal_rank_file}: {e}")
        return
    
    # 2. 读取现有的 jrank.yml
    try:
        with open(jrank_file, 'r', encoding='utf-8') as f:
            jrank_data = yaml.safe_load(f) or []
        logger.info(f"📖 加载了 {len(jrank_data)} 条现有数据")
    except FileNotFoundError:
        logger.error(f"❌ 文件不存在: {jrank_file}")
        return
    except Exception as e:
        logger.error(f"❌ 无法读取 {jrank_file}: {e}")
        return
    
    # 3. 创建期刊名称到数据的映射
    jrank_dict = {item['journal']: item for item in jrank_data}
    
    # 4. 创建爬虫实例
    crawler = ScopusDrissionCrawler(headless=True)
    
    # 5. 遍历期刊列表，更新橙色系指标
    updated_count = 0
    for journal_info in journal_list:
        journal_name = journal_info['name']
        sourceid = journal_info.get('sourceid')
        
        if not sourceid:
            logger.info(f"⏩ 跳过 {journal_name} (无 sourceid)")
            continue
        
        if journal_name not in jrank_dict:
            # 自动创建期刊条目
            logger.info(f"➕ 创建新条目: {journal_name}")
            jrank_dict[journal_name] = {
                'journal': journal_name,
                'orange_score': '',
                'orange_quartile': '',
                'orange_percentile': '',
                'documents_current_year': '',
                'documents_last_year': '',
                'documents_published': ''
            }
        
        logger.info(f"\n{'='*80}")
        logger.info(f"📊 处理: {journal_name} (ID: {sourceid})")
        logger.info(f"{'='*80}")
        
        try:
            # 爬取橙色系指标
            scopus_metrics = crawler.scrape_journal_metrics(sourceid)
            
            # 更新 jrank_dict 中的数据
            if scopus_metrics['orange_score']:
                jrank_dict[journal_name]['orange_score'] = scopus_metrics['orange_score']
            if scopus_metrics['orange_quartile']:
                jrank_dict[journal_name]['orange_quartile'] = scopus_metrics['orange_quartile']
            if scopus_metrics['orange_percentile']:
                jrank_dict[journal_name]['orange_percentile'] = scopus_metrics['orange_percentile']
            
            # 使用 split 后的字段
            if scopus_metrics['docs_current_year']:
                jrank_dict[journal_name]['documents_current_year'] = scopus_metrics['docs_current_year']
            if scopus_metrics['docs_last_year']:
                jrank_dict[journal_name]['documents_last_year'] = scopus_metrics['docs_last_year']
                # 保留 documents_published 用于兼容（如果需要），或者可以删除
                jrank_dict[journal_name]['documents_published'] = scopus_metrics['docs_last_year']
            
            updated_count += 1
            logger.info(f"✅ {journal_name} 更新完成")
            
            # 延迟，避免请求过快
            time.sleep(2)
            
        except Exception as e:
            logger.error(f"❌ {journal_name} 更新失败: {e}")
    
    # 6. 保存更新后的数据
    if dry_run:
        logger.info("\n" + "="*80)
        logger.info("🧪 DRY-RUN 模式：不保存文件")
        logger.info(f"📊 已更新 {updated_count} 个期刊的橙色系指标")
        logger.info("="*80)
    elif updated_count == 0:
        logger.info("\n" + "="*80)
        logger.info("ℹ️ 没有数据更新，跳过保存")
        logger.info("="*80)
    else:
        try:
            # 转换回列表
            updated_jrank_data = list(jrank_dict.values())
            
            with open(jrank_file, 'w', encoding='utf-8') as f:
                yaml.dump(updated_jrank_data, f, default_flow_style=False, allow_unicode=True)
            
            logger.info("\n" + "="*80)
            logger.info(f"✅ 成功更新 {jrank_file}")
            logger.info(f"📊 已更新 {updated_count} 个期刊的橙色系指标")
            logger.info("="*80)
        except Exception as e:
            logger.error(f"❌ 保存文件失败: {e}")


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='更新期刊橙色系指标 (橙色分数, 橙色分区, Documents Published, Percentile)')
    parser.add_argument('--dry-run', '-n', action='store_true', 
                       help='测试模式 - 不保存文件')
    args = parser.parse_args()
    
    logger.info("="*80)
    logger.info("期刊橙色系指标更新器 (DrissionPage)")
    logger.info("="*80)
    
    try:
        update_scopus_metrics_in_yaml(dry_run=args.dry_run)
    except KeyboardInterrupt:
        logger.info("\n⚠️ 用户中断")
    except Exception as e:
        logger.error(f"\n❌ 发生错误: {e}")


if __name__ == "__main__":
    main()
