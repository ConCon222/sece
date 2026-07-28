#!/usr/bin/env python3
"""
期刊指标更新器 - 使用 DrissionPage 获取橙色分数指标
独立运行，专门更新：橙色分数、橙色分区、Documents Published、Percentile
"""

import json
import logging
import os
import re
import sys
import tempfile
import time
from datetime import datetime
from typing import Dict, Any

import yaml

try:
    from DrissionPage import WebPage, ChromiumOptions
except ImportError:  # Allow the pure data-merging helpers to be unit-tested without Chrome.
    WebPage = None
    ChromiumOptions = None

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def _select_document_years(parsed_years, current_year=None):
    """Return counts for the actual calendar year and previous year only.

    Scopus may expose future-volume rows; choosing the two numerically largest
    years would incorrectly label those as current/last-year production.
    """
    year = int(current_year or datetime.now().year)
    by_year = {int(item_year): str(count) for item_year, count in parsed_years}
    return by_year.get(year), by_year.get(year - 1)


class ScopusDrissionCrawler:
    """使用 DrissionPage 爬取期刊橙色系指标"""
    
    def __init__(self, headless: bool = True):
        if ChromiumOptions is None or WebPage is None:
            raise RuntimeError("DrissionPage is required to crawl Scopus metrics")

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
            "docs_current_year": None,
            "docs_last_year": None,
            "citescore_rank_data": [],
            "documents_data": [],
            "success": False,
            "error": None,
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
                
                parsed_years = []
                for row in rows:
                    cells = row.eles("tag:td")
                    if not cells:
                        cells = row.eles("tag:th")

                    if len(cells) >= 2:
                        year_text = cells[0].text.strip()
                        doc_text = cells[1].text.strip()
                        year_match = re.search(r"\b(20\d{2})\b", year_text)
                        doc_text_clean = doc_text.replace(',', '')
                        doc_count_match = re.search(r'(\d+)', doc_text_clean)
                        if not year_match or not doc_count_match:
                            continue
                        parsed_years.append((int(year_match.group(1)), doc_count_match.group(1)))

                current_year = datetime.now().year
                current_count, previous_count = _select_document_years(
                    parsed_years,
                    current_year=current_year,
                )
                if current_count is not None:
                    result["docs_current_year"] = f"{current_count} ({current_year})"
                    result["documents_data"].append(
                        {"year": str(current_year), "documents": current_count}
                    )
                if previous_count is not None:
                    result["docs_last_year"] = f"{previous_count} ({current_year - 1})"
                    result["documents_data"].append(
                        {"year": str(current_year - 1), "documents": previous_count}
                    )

                if result["documents_data"]:
                    print(f"✅ 提取成功")
                else:
                    print(f"⚠️ 未提取到数据")

            except Exception as e:
                print(f"✗ 获取 Documents Published 数据失败: {e}")

            result["success"] = any(
                result.get(field) not in (None, "")
                for field in (
                    "orange_score",
                    "orange_quartile",
                    "orange_percentile",
                    "docs_current_year",
                    "docs_last_year",
                )
            )
                
        except Exception as e:
            result["error"] = str(e)
            logger.error(f"❌ 爬取失败: {e}")
        
        finally:
            # 关闭页面
            try:
                page.quit()
            except:
                pass
        
        return result


def _apply_batch(journal_list, offset, size):
    """取轮转窗口 journal_list[offset:offset+size]（超出末尾则绕回开头）。
    size 为 None/0 或 >= 总数时返回整份列表。"""
    if not size:
        return journal_list
    n = len(journal_list)
    if size >= n:
        return journal_list
    offset = (offset or 0) % n
    end = offset + size
    return journal_list[offset:end] if end <= n else journal_list[offset:] + journal_list[:end - n]


def _atomic_write_yaml(data, target_file):
    """Write YAML atomically so a killed runner cannot leave a truncated file."""
    target_dir = os.path.dirname(target_file) or "."
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=target_dir,
            prefix=f".{os.path.basename(target_file)}.",
            suffix=".tmp",
            delete=False,
        ) as temp_file:
            temp_path = temp_file.name
            yaml.dump(data, temp_file, default_flow_style=False, allow_unicode=True)
        os.replace(temp_path, target_file)
        return True
    except Exception as e:
        logger.error(f"❌ 写入 {target_file} 失败: {e}")
        if temp_path:
            try:
                os.unlink(temp_path)
            except OSError:
                pass
        return False


def _save_jrank(jrank_dict, jrank_file):
    """把 jrank_dict 原子写回 YAML（增量保存用）。"""
    return _atomic_write_yaml(list(jrank_dict.values()), jrank_file)


def _merge_scopus_metrics(journal_data, scopus_metrics):
    """Merge only values actually parsed from Scopus, preserving older metrics on failure."""
    updated = False
    field_map = {
        "orange_score": "orange_score",
        "orange_quartile": "orange_quartile",
        "orange_percentile": "orange_percentile",
        "docs_current_year": "documents_current_year",
        "docs_last_year": "documents_last_year",
    }
    for source_field, target_field in field_map.items():
        value = scopus_metrics.get(source_field)
        if value not in (None, ""):
            journal_data[target_field] = value
            updated = True

    docs_last_year = scopus_metrics.get("docs_last_year")
    if docs_last_year not in (None, ""):
        journal_data["documents_published"] = docs_last_year

    return updated


def update_scopus_metrics_in_yaml(dry_run: bool = False, only_missing: bool = False,
                                  save_every: int = 10, batch_offset: int = 0,
                                  batch_size: int = 0):
    """
    更新 jrank.yml 中的橙色系指标

    Args:
        dry_run: 是否为测试模式（不保存文件）
        only_missing: 只处理还没有 orange_score 的期刊（跳过已完成的，大幅缩短耗时）
        save_every: 每处理 N 本就写一次盘（防止超时被杀导致整轮丢失）
        batch_offset/batch_size: 轮转窗口——本轮只处理 journal_list[offset:offset+size]
                                 （绕回开头）。配合管理器的游标实现小批次滚动刷新。
    """
    journal_rank_file = '_data/journal_rank.json'
    jrank_file = '_data/jrank.yml'

    # 1. 读取期刊列表（获取 sourceid）
    try:
        with open(journal_rank_file, 'r', encoding='utf-8') as f:
            journal_list = json.load(f)
        total = len(journal_list)
        journal_list = _apply_batch(journal_list, batch_offset, batch_size)
        if batch_size and len(journal_list) < total:
            logger.info(f"📖 加载了 {total} 个期刊，本轮窗口 [{batch_offset % total}:+{batch_size}] = {len(journal_list)} 本")
        else:
            logger.info(f"📖 加载了 {total} 个期刊")
    except Exception as e:
        logger.error(f"❌ 无法读取 {journal_rank_file}: {e}")
        return False
    
    # 2. 读取现有的 jrank.yml
    try:
        with open(jrank_file, 'r', encoding='utf-8') as f:
            jrank_data = yaml.safe_load(f) or []
        logger.info(f"📖 加载了 {len(jrank_data)} 条现有数据")
    except FileNotFoundError:
        logger.error(f"❌ 文件不存在: {jrank_file}")
        return False
    except Exception as e:
        logger.error(f"❌ 无法读取 {jrank_file}: {e}")
        return False
    
    # 3. 创建期刊名称到数据的映射
    jrank_dict = {item['journal']: item for item in jrank_data}
    
    # 4. 创建爬虫实例
    try:
        crawler = ScopusDrissionCrawler(headless=True)
    except Exception as e:
        logger.error(f"❌ 无法初始化 Scopus 爬虫: {e}")
        return False
    
    # 5. 遍历期刊列表，更新橙色系指标
    updated_count = 0
    attempted_count = 0
    failed_count = 0
    save_failed = False
    for journal_info in journal_list:
        journal_name = journal_info['name']
        sourceid = journal_info.get('sourceid')
        
        if not sourceid:
            logger.info(f"⏩ 跳过 {journal_name} (无 sourceid)")
            continue

        # only_missing: 已有 orange_score 的期刊跳过浏览器导航（最贵的一步）
        if only_missing:
            existing = jrank_dict.get(journal_name, {})
            required_fields = (
                "orange_score",
                "orange_quartile",
                "orange_percentile",
                "documents_current_year",
                "documents_last_year",
            )
            if all(existing.get(field) not in (None, "") for field in required_fields):
                logger.info(f"⏩ 跳过 {journal_name} (已有橙色数据)")
                continue

        is_new_journal = journal_name not in jrank_dict
        if is_new_journal:
            # Do not add the blank entry unless at least one real metric is parsed.
            logger.info(f"➕ 准备创建新条目: {journal_name}")
            journal_data = {
                'journal': journal_name,
                'orange_score': '',
                'orange_quartile': '',
                'orange_percentile': '',
                'documents_current_year': '',
                'documents_last_year': '',
                'documents_published': ''
            }
        else:
            journal_data = jrank_dict[journal_name]
        
        logger.info(f"\n{'='*80}")
        logger.info(f"📊 处理: {journal_name} (ID: {sourceid})")
        logger.info(f"{'='*80}")
        
        try:
            # 爬取橙色系指标
            attempted_count += 1
            scopus_metrics = crawler.scrape_journal_metrics(sourceid)

            if not scopus_metrics.get("success") or not _merge_scopus_metrics(journal_data, scopus_metrics):
                failed_count += 1
                logger.error(
                    "❌ %s 未解析到任何有效 Scopus 指标，保留旧值%s",
                    journal_name,
                    f": {scopus_metrics.get('error')}" if scopus_metrics.get("error") else "",
                )
                continue

            jrank_dict[journal_name] = journal_data
            updated_count += 1
            logger.info(f"✅ {journal_name} 更新完成")

            # 增量保存：每 save_every 本写一次盘，超时被杀也能保住已爬的数据
            if not dry_run and save_every and updated_count % save_every == 0:
                if _save_jrank(jrank_dict, jrank_file):
                    logger.info(f"💾 增量保存：已写入 {updated_count} 本的进度")
                else:
                    save_failed = True

            # 延迟，避免请求过快
            time.sleep(2)

        except Exception as e:
            failed_count += 1
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
            if not _atomic_write_yaml(list(jrank_dict.values()), jrank_file):
                save_failed = True
            else:
                logger.info("\n" + "="*80)
                logger.info(f"✅ 成功更新 {jrank_file}")
                logger.info(f"📊 已更新 {updated_count} 个期刊的橙色系指标")
                logger.info("="*80)
        except Exception as e:
            save_failed = True
            logger.error(f"❌ 保存文件失败: {e}")

    if save_failed:
        return False
    if attempted_count and updated_count == 0:
        logger.error("❌ 本轮 %d 个 Scopus 请求全部失败", attempted_count)
        return False
    if failed_count:
        logger.warning("⚠️ 本轮有 %d/%d 本未获取到新指标，旧值已保留", failed_count, attempted_count)
    return True


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='更新期刊橙色系指标 (橙色分数, 橙色分区, Documents Published, Percentile)')
    parser.add_argument('--dry-run', '-n', action='store_true',
                       help='测试模式 - 不保存文件')
    parser.add_argument('--only-missing', action='store_true',
                       help='只处理还没有橙色数据的期刊（跳过已完成，避免 6h 超时）')
    parser.add_argument('--save-every', type=int, default=10,
                       help='每处理 N 本写一次盘（增量保存，默认 10）')
    parser.add_argument('--batch-offset', type=int, default=0,
                       help='轮转窗口起点（配合 --batch-size）')
    parser.add_argument('--batch-size', type=int, default=0,
                       help='本轮只处理这么多本（0=全部）；窗口超出末尾会绕回开头')
    args = parser.parse_args()
    
    logger.info("="*80)
    logger.info("期刊橙色系指标更新器 (DrissionPage)")
    logger.info("="*80)
    
    try:
        success = update_scopus_metrics_in_yaml(
            dry_run=args.dry_run,
            only_missing=args.only_missing,
            save_every=args.save_every,
            batch_offset=args.batch_offset,
            batch_size=args.batch_size,
        )
        if not success:
            sys.exit(1)
    except KeyboardInterrupt:
        logger.info("\n⚠️ 用户中断")
        sys.exit(130)
    except Exception as e:
        logger.error(f"\n❌ 发生错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
