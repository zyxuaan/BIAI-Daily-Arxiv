#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import argparse

def main():
    parser = argparse.ArgumentParser(description="测试ArXiv Summary网站管理工具 (使用本地代理)")
    parser.add_argument('--proxy', default='http://127.0.0.1:7890', help='HTTP代理地址 (默认: http://127.0.0.1:7890)')
    parser.add_argument('--data-dir', default='./data', help='数据目录路径 (默认: ./data)')
    parser.add_argument('--github-dir', default='./.github', help='GitHub配置目录路径 (默认: ./.github)')
    parser.add_argument('--days', type=int, default=30, help='保留摘要文件的天数 (默认: 30)')
    parser.add_argument('--skip-clean', action='store_true', help='跳过清理旧文件')
    args = parser.parse_args()
    
    # 设置代理环境变量
    if args.proxy:
        print(f"设置HTTP/HTTPS代理: {args.proxy}")
        os.environ['HTTP_PROXY'] = args.proxy
        os.environ['HTTPS_PROXY'] = args.proxy
    
    # 运行site_manager的main函数
    print("正在导入site_manager模块...")
    try:
        from src.site_manager import main as site_manager_main
        
        # 构建参数列表以传递给site_manager.main
        sys_argv_backup = sys.argv.copy()
        sys.argv = [sys.argv[0]]  # 保留程序名
        
        # 添加data-dir参数
        if args.data_dir:
            sys.argv.extend(['--data-dir', args.data_dir])
        
        # 添加github-dir参数
        if args.github_dir:
            sys.argv.extend(['--github-dir', args.github_dir])
        
        # 添加days参数
        if args.days:
            sys.argv.extend(['--days', str(args.days)])
        
        # 添加skip-clean标志
        if args.skip_clean:
            sys.argv.append('--skip-clean')
        
        print(f"运行site_manager，参数: {sys.argv[1:]}")
        site_manager_main()
        
        # 恢复原始参数
        sys.argv = sys_argv_backup
        
    except ImportError as e:
        print(f"导入site_manager失败: {e}")
        return 1
    except Exception as e:
        print(f"运行site_manager时出错: {e}")
        return 1
    
    print("测试完成!")
    return 0

if __name__ == "__main__":
    sys.exit(main())