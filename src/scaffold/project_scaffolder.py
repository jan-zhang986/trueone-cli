# -*- coding: utf-8 -*-
"""
TrueOne Scaffolder
负责创建收敛在 tests/ 目录下的 4 层标准化工程骨架 (完全隔离，零侵入研发主仓代码)
"""
import os
import shutil
from pathlib import Path
from typing import Dict, Any, Optional

TEMPLATE_ROOT = Path(__file__).parent / "templates"


class ProjectScaffolder:
    """TrueOne 项目骨架生成器 (收敛在 tests 域内)"""

    def __init__(self, target_dir: str):
        base_path = Path(target_dir).resolve()
        # 如果传入的不是 tests 目录，则自动收敛在其 tests/ 子目录下，杜绝污染工程根目录
        if base_path.name == "tests":
            self.tests_root = base_path
            self.project_root = base_path.parent
        else:
            self.tests_root = base_path / "tests"
            self.project_root = base_path

    def init_project(self, app_name: str, lang: str = "go") -> Dict[str, Any]:
        """
        初始化标准 4 层结构工程，全部自包含并收敛在 tests/ 目录下
        """
        lang = lang.lower()
        skills_dir = self.tests_root / ".agents" / "skills"
        knowledge_dir = self.tests_root / "knowledge" / "applications" / app_name
        qa_dir = self.tests_root / "qa"

        # 1. 创建 tests 内部分层目录树
        for d in [skills_dir, knowledge_dir / "domain" / "product", knowledge_dir / "tech", qa_dir]:
            d.mkdir(parents=True, exist_ok=True)

        # 2. 拷贝 / 生成核心 Skills 到 tests/.agents/skills/
        src_skills = TEMPLATE_ROOT / "skills"
        if src_skills.exists():
            for skill_name in ["test-design", "test-codegen", "test-review", "test-validate", "e2e-dag-workflow"]:
                dest = skills_dir / skill_name
                dest.mkdir(parents=True, exist_ok=True)
                src_file = src_skills / skill_name / "SKILL.md"
                if src_file.exists():
                    shutil.copy(src_file, dest / "SKILL.md")

        # 2.1 创建 workflows 目录并生成黄金 DAG 用例样例
        wf_dir = self.tests_root / "workflows"
        wf_dir.mkdir(parents=True, exist_ok=True)
        sample_wf = wf_dir / "order_sample.workflow.yaml"
        if not sample_wf.exists():
            sample_wf.write_text("""id: order_reconciliation_workflow
name: "订单交易与账本核销全链路核对"
module: "交易履约引擎"
priority: "P0"
description: "通过网关下单、数据库流水双向校验及资金安全门禁，确保交易履约资金不发生单边账"

variables:
  userId: "usr_9527_vip"
  merchantId: "mch_8888"
  currency: "CNY"
  expectedDeduction: 99.00
  safetyLimit: 1000.00

nodes:
  - id: create_order
    name: "创建商品订单"
    type: HTTP
    dependsOn: []
    config:
      url: "/api/v1/orders"
      method: "POST"
      body:
        userId: "{{ variables.userId }}"
        amount: "{{ variables.expectedDeduction }}"
      extract:
        orderId: "data.order_id"
      assertions:
        - field: "status_code"
          operator: "equals"
          expected: 200

  - id: verify_ledger_entry
    name: "核对账本记账流水"
    type: SQL
    dependsOn: ["create_order"]
    config:
      datasource: "finance_ledger_db"
      sql: "SELECT amount, status FROM t_ledger_flow WHERE order_id = '{{ create_order.output.orderId }}';"
      extract:
        flowStatus: "status"
      assertions:
        - field: "status"
          operator: "equals"
          expected: "SETTLED"

  - id: financial_safety_gate
    name: "资金安全准入门禁"
    type: QUALITY_GATE
    dependsOn: ["verify_ledger_entry"]
    config:
      rule: "FINANCIAL_CONSISTENCY"
      condition: "{{ verify_ledger_entry.output.flowStatus }} == 'SETTLED'"
""", encoding="utf-8")

        # 3. 生成知识库核心引导文件到 tests/knowledge/
        (self.tests_root / "knowledge" / "ROUTING.md").write_text(
            f"# Knowledge Routing\n\n- [{app_name}](applications/{app_name}/app-overview.md)\n",
            encoding="utf-8"
        )
        (knowledge_dir / "app-overview.md").write_text(
            f"# {app_name} 系统架构与业务边界\n\n## 1. 核心定位\n## 2. 领域状态机\n## 3. 防资损底线\n",
            encoding="utf-8"
        )

        # 4. 生成 QA 迭代接续指南到 tests/qa/
        (qa_dir / "README.md").write_text(
            "# QA 迭代过程对账资产目录\n\n以需求 ID 为子目录，如 `qa/REQ-001/requirement.md`。\n",
            encoding="utf-8"
        )

        # 5. 生成默认带 SDK 依赖的测试项目工程配置到 tests/ 根部
        created_files = []
        if lang == "go":
            # 只有当父目录不是 Go 模块时，才在 tests/ 生成独立的 go.mod；若父目录已有 go.mod，则复用主工程模块体系，杜绝 nested module 破坏包导入
            parent_mod = self.project_root / "go.mod"
            if not parent_mod.exists():
                go_mod_path = self.tests_root / "go.mod"
                if not go_mod_path.exists():
                    go_mod_content = f"""module {app_name}-tests

go 1.22

require (
    github.com/vanguard-platform/aegis-sdk-go v1.0.0
)

// 本地开发模式映射
replace github.com/vanguard-platform/aegis-sdk-go => /Users/zhangjian/vanguard-platform/trueone-sdk/go
"""
                    go_mod_path.write_text(go_mod_content, encoding="utf-8")
                    created_files.append(str(go_mod_path))

        elif lang == "python":
            req_path = self.tests_root / "requirements.txt"
            if not req_path.exists():
                req_content = """# TrueOne SDK 依赖
pytest>=7.0.0
# 本地开发模式
-e /Users/zhangjian/vanguard-platform/trueone-sdk/python
"""
                req_path.write_text(req_content, encoding="utf-8")
                created_files.append(str(req_path))

        elif lang == "java":
            pom_path = self.tests_root / "pom.xml"
            if not pom_path.exists():
                pom_content = f"""<project xmlns="http://maven.apache.org/POM/4.0.0">
  <modelVersion>4.0.0</modelVersion>
  <groupId>com.trueone</groupId>
  <artifactId>{app_name}-tests</artifactId>
  <version>1.0.0</version>
  <dependencies>
    <dependency>
      <groupId>io.aegis</groupId>
      <artifactId>aegis-sdk-java</artifactId>
      <version>1.0.0</version>
      <scope>test</scope>
    </dependency>
  </dependencies>
</project>
"""
                pom_path.write_text(pom_content, encoding="utf-8")
                created_files.append(str(pom_path))

        return {
            "projectRoot": str(self.project_root),
            "testsRoot": str(self.tests_root),
            "appName": app_name,
            "language": lang,
            "layers": [
                "tests/.agents/skills/ (4个核心SOP技能)",
                "tests/knowledge/ (3支柱业务知识库)",
                "tests/qa/ (需求对账过程资产)",
                f"tests/ (已内置接入 trueone-sdk/{lang})"
            ],
            "createdFiles": created_files
        }
