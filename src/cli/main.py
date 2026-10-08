# -*- coding: utf-8 -*-
"""
TrueOne CLI 入口
提供 init (4层工程初始化) 与 scaffold-case (单用例生成)
"""
import argparse
import json
import os
import sys
from pathlib import Path

# 将 src 加入路径
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scaffold.project_scaffolder import ProjectScaffolder


def main():
    parser = argparse.ArgumentParser(
        prog="trueone",
        description="TrueOne Test-as-Code CLI - 面向 AI 与研发的工程化脚手架"
    )
    subparsers = parser.add_subparsers(dest="subcommand", help="子命令")

    # 1. trueone init
    init_p = subparsers.add_parser("init", help="初始化 4 层标准工程骨架 (Skills + Knowledge + QA + Tests)")
    init_p.add_argument("--app", required=True, help="应用/系统名称 (如 order-service, payment-gateway)")
    init_p.add_argument("--lang", default="go", choices=["go", "python", "java"], help="测试语言栈 (默认 go)")
    init_p.add_argument("--dir", default=".", help="目标初始化目录 (默认当前目录)")
    init_p.add_argument("--json", action="store_true", help="以 JSON 格式输出")

    args = parser.parse_args()
    if not args.subcommand:
        parser.print_help()
        sys.exit(1)

    if args.subcommand == "init":
        scaffolder = ProjectScaffolder(args.dir)
        res = scaffolder.init_project(app_name=args.app, lang=args.lang)
        if args.json:
            print(json.dumps(res, ensure_ascii=False, indent=2))
        else:
            print(f"🎉 成功为应用 [{args.app}] 初始化 TrueOne 4 层标准测试工程！")
            print(f"📁 目标目录: {res['targetDir']}")
            print("🏗️ 生成的分层结构:")
            for layer in res["layers"]:
                print(f"   • {layer}")
            print(f"📦 已自动为 tests/ 注入 trueone-sdk/{args.lang} 依赖，开箱即用！")


if __name__ == "__main__":
    main()
