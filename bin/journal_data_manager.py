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
from datetime import datetime
from typing import Dict, List, Any, Optional
from copy import deepcopy

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 文件路径
JRANK_FILE = '_data/jrank.yml'
JOURNAL_RANK_FILE = '_data/journal_rank.json'


class JournalDataManager:
    """期刊数据统一管理器"""
    
    def __init__(self):
        self.jrank_file = JRANK_FILE
        self.journal_rank_file = JOURNAL_RANK_FILE
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
    
    def run_scopus_update(self, dry_run: bool = False, only_missing: bool = False) -> bool:
        """运行橙色系指标更新脚本"""
        logger.info("🔶 运行橙色系指标更新...")
        script_path = 'bin/update_scopus_metrics.py'

        if not os.path.exists(script_path):
            logger.error(f"❌ 脚本不存在: {script_path}")
            return False

        cmd = [sys.executable, script_path]
        if dry_run:
            cmd.append('--dry-run')
        if only_missing:
            cmd.append('--only-missing')

        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            print(result.stdout)
            if result.stderr:
                print(result.stderr)
            return result.returncode == 0
        except Exception as e:
            logger.error(f"❌ 运行脚本失败: {e}")
            return False
    
    def run_publisher_update(self, dry_run: bool = False, easyscholar_key: str = None,
                             only_missing: bool = False) -> bool:
        """运行出版商+EasyScholar 更新脚本"""
        logger.info("🔷 运行出版商+EasyScholar 更新...")
        script_path = 'bin/journal_ranking_updater.py'

        if not os.path.exists(script_path):
            logger.error(f"❌ 脚本不存在: {script_path}")
            return False

        cmd = [sys.executable, script_path]
        if dry_run:
            cmd.append('--dry-run')
        if easyscholar_key:
            cmd.extend(['--easyscholar-key', easyscholar_key])
        if only_missing:
            cmd.append('--only-missing')

        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            print(result.stdout)
            if result.stderr:
                print(result.stderr)
            return result.returncode == 0
        except Exception as e:
            logger.error(f"❌ 运行脚本失败: {e}")
            return False
    
    def run_all(self, dry_run: bool = False, show_diff: bool = True,
                easyscholar_key: str = None, only_missing: bool = False):
        """运行所有更新"""
        print("\n" + "="*80)
        print("🚀 期刊数据统一更新")
        print(f"   时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*80 + "\n")

        # 保存更新前的数据
        old_data = deepcopy(self.load_data())

        # 1. 先运行橙色系指标更新（获取 orange_score 等数据）
        print("\n[1/2] 橙色系指标更新")
        print("-"*40)
        self.run_scopus_update(dry_run=dry_run, only_missing=only_missing)

        # 2. 再运行出版商更新（此时 HM score 计算可以使用 orange 数据）
        print("\n[2/2] 出版商 + EasyScholar 更新 (含 HM Score 计算)")
        print("-"*40)
        self.run_publisher_update(dry_run=dry_run, easyscholar_key=easyscholar_key,
                                  only_missing=only_missing)
        
        # 3. 对比差异
        if show_diff:
            new_data = self.load_data()
            diff = self.compare_data(old_data, new_data)
            self.print_diff(diff)
        
        print("\n✅ 更新完成!")


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

    args = parser.parse_args()
    
    manager = JournalDataManager()
    
    if args.status:
        manager.show_status()
    elif args.all:
        manager.run_all(
            dry_run=args.dry_run,
            show_diff=not args.no_diff,
            easyscholar_key=args.easyscholar_key,
            only_missing=args.only_missing
        )
    elif args.orange_only:
        old_data = deepcopy(manager.load_data())
        manager.run_scopus_update(dry_run=args.dry_run, only_missing=args.only_missing)
        if not args.no_diff:
            new_data = manager.load_data()
            diff = manager.compare_data(old_data, new_data)
            manager.print_diff(diff)
    elif args.publisher_only:
        old_data = deepcopy(manager.load_data())
        manager.run_publisher_update(
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
        manager.run_all(
            dry_run=args.dry_run,
            show_diff=not args.no_diff,
            easyscholar_key=args.easyscholar_key,
            only_missing=args.only_missing
        )


if __name__ == "__main__":
    main()
