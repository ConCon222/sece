#!/usr/bin/env python3
"""
期刊数据统一管理器
功能：统一调度更新脚本、数据对比、输出控制
"""

import json
import yaml
import os
import sys
import argparse
import subprocess
import logging
import tempfile
from datetime import datetime
from typing import Dict, List, Any, Optional
from copy import deepcopy

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 文件路径
JRANK_FILE = '_data/jrank.yml'
JOURNAL_RANK_FILE = '_data/journal_rank.json'
CURSOR_FILE = '_data/.rank_cursor'  # 轮转游标：记录下一轮窗口起点（随仓库提交，跨运行保留）
META_FILE = '_data/jrank_meta.yml'  # 最近一次完整成功更新的信息，供页面和审计使用


class JournalDataManager:
    """期刊数据统一管理器"""
    
    def __init__(self):
        self.jrank_file = JRANK_FILE
        self.journal_rank_file = JOURNAL_RANK_FILE
        self.cursor_file = CURSOR_FILE
        self.meta_file = META_FILE
        self.original_data = None
        self.current_data = None
    
    def load_data(self) -> List[Dict]:
        """加载当前 jrank.yml 数据"""
        try:
            with open(self.jrank_file, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f) or []
            logger.info(f"📖 加载了 {len(data)} 个期刊数据")
            return data
        except FileNotFoundError:
            logger.warning(f"⚠️ 文件不存在: {self.jrank_file}")
            return []
        except Exception as e:
            logger.error(f"❌ 加载数据失败: {e}")
            return []
    
    def load_journal_list(self) -> List[Dict]:
        """加载 journal_rank.json 期刊列表"""
        try:
            with open(self.journal_rank_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            logger.info(f"📖 加载了 {len(data)} 个期刊配置")
            return data
        except Exception as e:
            logger.error(f"❌ 加载期刊列表失败: {e}")
            return []

    def read_cursor(self) -> int:
        """读取轮转游标（下一轮窗口起点）。文件不存在或损坏则从 0 开始。"""
        try:
            with open(self.cursor_file, 'r', encoding='utf-8') as f:
                return int((f.read() or '0').strip())
        except Exception:
            return 0

    def _atomic_write_text(self, path: str, content: str) -> bool:
        """Atomically replace a small state file."""
        target_dir = os.path.dirname(path) or "."
        temp_path = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=target_dir,
                prefix=f".{os.path.basename(path)}.",
                suffix=".tmp",
                delete=False,
            ) as temp_file:
                temp_path = temp_file.name
                temp_file.write(content)
            os.replace(temp_path, path)
            return True
        except Exception as e:
            logger.error(f"❌ 写入状态文件 {path} 失败: {e}")
            if temp_path:
                try:
                    os.unlink(temp_path)
                except OSError:
                    pass
            return False

    def write_cursor(self, offset: int) -> bool:
        return self._atomic_write_text(self.cursor_file, str(int(offset)))

    def write_success_metadata(self, batch_offset: int, batch_size: int, journal_count: int) -> bool:
        """Record only a fully successful two-stage update."""
        completed_at = datetime.now().astimezone()
        metadata = {
            "last_successful_update": completed_at.date().isoformat(),
            "last_successful_update_at": completed_at.isoformat(timespec="seconds"),
            "batch_offset": int(batch_offset),
            "batch_size": int(batch_size),
            "journal_count": int(journal_count),
        }
        content = yaml.safe_dump(metadata, allow_unicode=True, sort_keys=False)
        return self._atomic_write_text(self.meta_file, content)
    
    def save_data(self, data: List[Dict]) -> bool:
        """保存数据到 jrank.yml"""
        if not data:
            logger.warning("⚠️ 数据为空，跳过保存")
            return False
        
        try:
            with open(self.jrank_file, 'w', encoding='utf-8') as f:
                yaml.dump(data, f, default_flow_style=False, allow_unicode=True)
            logger.info(f"✅ 成功保存 {len(data)} 个期刊数据")
            return True
        except Exception as e:
            logger.error(f"❌ 保存数据失败: {e}")
            return False
    
    def compare_data(self, old_data: List[Dict], new_data: List[Dict]) -> Dict:
        """对比新旧数据差异"""
        old_dict = {item.get('journal', ''): item for item in old_data}
        new_dict = {item.get('journal', ''): item for item in new_data}
        
        diff = {
            'added': [],      # 新增的期刊
            'removed': [],    # 删除的期刊
            'modified': [],   # 修改的期刊
            'unchanged': []   # 未变的期刊
        }
        
        # 检查新增和修改
        for name, new_item in new_dict.items():
            if name not in old_dict:
                diff['added'].append(name)
            else:
                old_item = old_dict[name]
                changes = self._compare_items(old_item, new_item)
                if changes:
                    diff['modified'].append({
                        'journal': name,
                        'changes': changes
                    })
                else:
                    diff['unchanged'].append(name)
        
        # 检查删除
        for name in old_dict:
            if name not in new_dict:
                diff['removed'].append(name)
        
        return diff
    
    def _compare_items(self, old_item: Dict, new_item: Dict) -> List[Dict]:
        """对比两个期刊条目的差异"""
        changes = []
        all_keys = set(old_item.keys()) | set(new_item.keys())
        
        for key in all_keys:
            old_val = old_item.get(key, '')
            new_val = new_item.get(key, '')
            
            # 转换为字符串比较
            old_str = str(old_val) if old_val else ''
            new_str = str(new_val) if new_val else ''
            
            if old_str != new_str:
                changes.append({
                    'field': key,
                    'old': old_str,
                    'new': new_str
                })
        
        return changes
    
    def print_diff(self, diff: Dict):
        """打印数据差异报告"""
        print("\n" + "="*80)
        print("📊 数据变更报告")
        print("="*80)
        
        if diff['added']:
            print(f"\n🆕 新增期刊 ({len(diff['added'])} 个):")
            for name in diff['added']:
                print(f"   + {name}")
        
        if diff['removed']:
            print(f"\n🗑️ 删除期刊 ({len(diff['removed'])} 个):")
            for name in diff['removed']:
                print(f"   - {name}")
        
        if diff['modified']:
            print(f"\n✏️ 修改期刊 ({len(diff['modified'])} 个):")
            for mod in diff['modified']:
                print(f"\n   📌 {mod['journal']}:")
                for change in mod['changes']:
                    field = change['field']
                    old_val = change['old'] or '(空)'
                    new_val = change['new'] or '(空)'
                    print(f"      {field}: {old_val} → {new_val}")
        
        print(f"\n📈 汇总: 新增 {len(diff['added'])} | 删除 {len(diff['removed'])} | "
              f"修改 {len(diff['modified'])} | 未变 {len(diff['unchanged'])}")
        print("="*80 + "\n")
        
    def show_status(self):
        """显示当前数据状态"""
        data = self.load_data()
        journal_list = self.load_journal_list()
        
        print("\n" + "="*80)
        print("📊 期刊数据状态")
        print("="*80)
        
        print(f"\n📂 数据文件:")
        print(f"   - {self.journal_rank_file}: {len(journal_list)} 个期刊配置")
        print(f"   - {self.jrank_file}: {len(data)} 个期刊数据")
        
        if data:
            # 统计字段覆盖率
            fields = ['purple_quartile', 'orange_quartile', 'red_division', 
                     'orange_score', 'purple_score', 'acceptance_rate',
                     'first_decision_time', 'hm_score']
            
            print(f"\n📈 字段覆盖率:")
            for field in fields:
                count = sum(1 for item in data if item.get(field))
                pct = (count / len(data) * 100) if data else 0
                bar = "█" * int(pct / 5) + "░" * (20 - int(pct / 5))
                print(f"   {field:25} [{bar}] {pct:5.1f}% ({count}/{len(data)})")
            
            print(f"\n📋 期刊列表:")
            for item in data:
                name = item.get('journal', 'Unknown')
                purple_q = item.get('purple_quartile', '-')
                score = item.get('hm_score', '-')
                print(f"   • {name[:40]:40} | 紫色分区: {purple_q:4} | HM分: {score}")
        
        print("="*80 + "\n")
    
    def run_scopus_update(self, dry_run: bool = False, only_missing: bool = False,
                          batch_offset: int = 0, batch_size: int = 0) -> bool:
        """运行橙色系指标更新脚本"""
        logger.info("🔶 运行橙色系指标更新...")
        script_path = 'bin/update_scopus_metrics.py'

        if not os.path.exists(script_path):
            logger.error(f"❌ 脚本不存在: {script_path}")
            return False

        cmd = [sys.executable, '-u', script_path]
        if dry_run:
            cmd.append('--dry-run')
        if only_missing:
            cmd.append('--only-missing')
        if batch_size:
            cmd.extend(['--batch-offset', str(batch_offset), '--batch-size', str(batch_size)])

        try:
            # Inherit stdout/stderr so Actions shows progress while the crawler runs.
            result = subprocess.run(cmd)
            return result.returncode == 0
        except Exception as e:
            logger.error(f"❌ 运行脚本失败: {e}")
            return False
    
    def run_publisher_update(self, dry_run: bool = False, easyscholar_key: str = None,
                             only_missing: bool = False, batch_offset: int = 0,
                             batch_size: int = 0) -> bool:
        """运行出版商+EasyScholar 更新脚本"""
        logger.info("🔷 运行出版商+EasyScholar 更新...")
        script_path = 'bin/journal_ranking_updater.py'

        if not os.path.exists(script_path):
            logger.error(f"❌ 脚本不存在: {script_path}")
            return False

        cmd = [sys.executable, '-u', script_path]
        if dry_run:
            cmd.append('--dry-run')
        if easyscholar_key:
            cmd.extend(['--easyscholar-key', easyscholar_key])
        if only_missing:
            cmd.append('--only-missing')
        if batch_size:
            cmd.extend(['--batch-offset', str(batch_offset), '--batch-size', str(batch_size)])

        try:
            # Inherit stdout/stderr so Actions shows progress while the crawler runs.
            result = subprocess.run(cmd)
            return result.returncode == 0
        except Exception as e:
            logger.error(f"❌ 运行脚本失败: {e}")
            return False
    
    def run_all(self, dry_run: bool = False, show_diff: bool = True,
                easyscholar_key: str = None, only_missing: bool = False,
                batch_size: int = 0) -> bool:
        """运行所有更新

        batch_size > 0 时启用「轮转窗口」：本轮只处理从游标开始的 batch_size 本，
        Scopus 与出版商用同一窗口；两步都跑完后游标前移 batch_size（绕回开头）。
        这样录用率/审稿周期/IF 等会变的数据也能随轮转定期刷新，而每轮都不超时。
        """
        print("\n" + "="*80)
        print("🚀 期刊数据统一更新")
        print(f"   时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*80 + "\n")

        # 轮转窗口：读取游标，确定本轮处理哪一段
        batch_offset = 0
        total = len(self.load_journal_list())
        if not total:
            logger.error("❌ 期刊配置为空，停止更新")
            return False
        if batch_size and total:
            batch_offset = self.read_cursor() % total
            end = batch_offset + batch_size
            wrap = '…(绕回开头)' if end > total else ''
            print(f"🔄 轮转窗口: 本轮处理第 {batch_offset} ~ {min(end, total)} 本{wrap} / 共 {total} 本\n")

        # 保存更新前的数据
        old_data = deepcopy(self.load_data())

        # 1. 先运行橙色系指标更新（获取 orange_score 等数据）
        print("\n[1/2] 橙色系指标更新")
        print("-"*40)
        scopus_ok = self.run_scopus_update(
            dry_run=dry_run,
            only_missing=only_missing,
            batch_offset=batch_offset,
            batch_size=batch_size,
        )

        # 2. 再运行出版商更新（此时 HM score 计算可以使用 orange 数据）
        print("\n[2/2] 出版商 + EasyScholar 更新 (含 HM Score 计算)")
        print("-"*40)
        publisher_ok = self.run_publisher_update(
            dry_run=dry_run,
            easyscholar_key=easyscholar_key,
            only_missing=only_missing,
            batch_offset=batch_offset,
            batch_size=batch_size,
        )

        success = scopus_ok and publisher_ok
        if not scopus_ok:
            logger.error("❌ Scopus 子进程失败")
        if not publisher_ok:
            logger.error("❌ 出版商子进程失败")

        # Only a fully successful two-stage run may advance the cursor or update
        # the "last successful" metadata. Partial data remains on disk for CI to commit.
        if success and not dry_run:
            if not self.write_success_metadata(batch_offset, batch_size, total):
                success = False
            if success and batch_size:
                new_offset = (batch_offset + batch_size) % total
                if self.write_cursor(new_offset):
                    print(f"\n🔄 游标前移: 下一轮从第 {new_offset} 本开始")
                else:
                    success = False

        # 3. 对比差异
        if show_diff:
            new_data = self.load_data()
            diff = self.compare_data(old_data, new_data)
            self.print_diff(diff)
        
        if success:
            print("\n✅ 更新完成!")
        else:
            print("\n❌ 更新未完整成功；游标未推进，已抓取的数据仍可保留。")
        return success


def main():
    parser = argparse.ArgumentParser(
        description='期刊数据统一管理器',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python bin/journal_data_manager.py --all              # 运行所有更新
  python bin/journal_data_manager.py --orange-only      # 仅更新橙色系指标
  python bin/journal_data_manager.py --publisher-only   # 仅更新出版商数据
  python bin/journal_data_manager.py --status           # 查看数据状态
  python bin/journal_data_manager.py --dry-run --diff   # 测试模式+显示差异
        """
    )
    
    # 运行模式
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument('--all', '-a', action='store_true',
                           help='运行所有更新脚本')
    mode_group.add_argument('--orange-only', action='store_true',
                           help='仅运行橙色系指标更新')
    mode_group.add_argument('--publisher-only', action='store_true',
                           help='仅运行出版商+EasyScholar更新')
    mode_group.add_argument('--status', '-s', action='store_true',
                           help='显示当前数据状态')
    mode_group.add_argument('--diff', action='store_true',
                           help='对比当前数据与初始状态')
    
    # 可选参数
    parser.add_argument('--dry-run', '-n', action='store_true',
                       help='测试模式，不保存数据')
    parser.add_argument('--easyscholar-key', '-e', type=str,
                       help='EasyScholar API key')
    parser.add_argument('--no-diff', action='store_true',
                       help='不显示差异报告')
    parser.add_argument('--only-missing', action='store_true',
                       help='只处理缺数据的期刊（跳过已完成，避免 6h 超时）')
    parser.add_argument('--batch-size', type=int, default=0,
                       help='轮转窗口：本轮只处理这么多本（从游标开始，绕回开头），跑完游标前移。0=全部')

    args = parser.parse_args()
    
    manager = JournalDataManager()
    success = True
    
    if args.status:
        manager.show_status()
    elif args.all:
        success = manager.run_all(
            dry_run=args.dry_run,
            show_diff=not args.no_diff,
            easyscholar_key=args.easyscholar_key,
            only_missing=args.only_missing,
            batch_size=args.batch_size
        )
    elif args.orange_only:
        old_data = deepcopy(manager.load_data())
        success = manager.run_scopus_update(dry_run=args.dry_run, only_missing=args.only_missing)
        if not args.no_diff:
            new_data = manager.load_data()
            diff = manager.compare_data(old_data, new_data)
            manager.print_diff(diff)
    elif args.publisher_only:
        old_data = deepcopy(manager.load_data())
        success = manager.run_publisher_update(
            dry_run=args.dry_run,
            easyscholar_key=args.easyscholar_key,
            only_missing=args.only_missing
        )
        if not args.no_diff:
            new_data = manager.load_data()
            diff = manager.compare_data(old_data, new_data)
            manager.print_diff(diff)
    elif args.diff:
        # 仅载入当前数据并显示状态
        manager.show_status()
    else:
        # 默认运行所有更新
        logger.info("未指定参数，默认运行所有更新...")
        success = manager.run_all(
            dry_run=args.dry_run,
            show_diff=not args.no_diff,
            easyscholar_key=args.easyscholar_key,
            only_missing=args.only_missing,
            batch_size=args.batch_size
        )

    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()
