# -*- coding: utf-8 -*-
"""
TrueOne Scaffolder
负责创建 4 层标准化工程骨架 (Skills + Knowledge + QA + Tests)
"""
import os
import shutil
from pathlib import Path
from typing import Dict, Any, Optional

TEMPLATE_ROOT = Path(__file__).parent / "templates"


class ProjectScaffolder:
    """TrueOne 项目骨架生成器"""

    def __init__(self, target_dir: str):
        self.target_dir = Path(target_dir).resolve()

    def init_project(self, app_name: str, lang: str = "go") -> Dict[str, Any]:
        """
        初始化标准 4 层结构工程，并默认注入对应语言的 TrueOne SDK 依赖
        """
        lang = lang.lower()
        skills_dir = self.target_dir / ".agents" / "skills"
        knowledge_dir = self.target_dir / "knowledge" / "applications" / app_name
        qa_dir = self.target_dir / "qa"
        tests_dir = self.target_dir / "tests"

        # 1. 创建目录树
        for d in [skills_dir, knowledge_dir / "domain" / "product", knowledge_dir / "tech", qa_dir, tests_dir]:
            d.mkdir(parents=True, exist_ok=True)

        # 2. 拷贝 / 生成 4 个核心 Skills
        src_skills = TEMPLATE_ROOT / "skills"
        if src_skills.exists():
            for skill_name in ["test-design", "test-codegen", "test-review", "test-validate"]:
                dest = skills_dir / skill_name
                dest.mkdir(parents=True, exist_ok=True)
                src_file = src_skills / skill_name / "SKILL.md"
                if src_file.exists():
                    shutil.copy(src_file, dest / "SKILL.md")

        # 3. 生成知识库核心引导文件 (ROUTING & INDEX & APP)
        (self.target_dir / "knowledge" / "ROUTING.md").write_text(
            f"# Knowledge Routing\n\n- [{app_name}](applications/{app_name}/app-overview.md)\n",
            encoding="utf-8"
        )
        (knowledge_dir / "app-overview.md").write_text(
            f"# {app_name} 系统架构与业务边界\n\n## 1. 核心定位\n## 2. 领域状态机\n## 3. 防资损底线\n",
            encoding="utf-8"
        )

        # 4. 生成 QA 迭代接续指南
        (qa_dir / "README.md").write_text(
            "# QA 迭代过程对账资产目录\n\n以需求 ID 为子目录，如 `qa/REQ-001/requirement.md`。\n",
            encoding="utf-8"
        )

        # 5. 生成默认带 SDK 依赖的测试项目工程
        created_files = []
        if lang == "go":
            go_mod_content = f"""module {app_name}-tests

go 1.22

require (
    github.com/vanguard/aegis-sdk-go v1.0.0
)

// 本地开发模式映射
replace github.com/vanguard/aegis-sdk-go => /Users/zhangjian/vanguard-platform/trueone-sdk/go
"""
            (tests_dir / "go.mod").write_text(go_mod_content, encoding="utf-8")
            created_files.append(str(tests_dir / "go.mod"))

        elif lang == "python":
            req_content = """# TrueOne SDK 依赖
pytest>=7.0.0
# 本地开发模式
-e /Users/zhangjian/vanguard-platform/trueone-sdk/python
"""
            (tests_dir / "requirements.txt").write_text(req_content, encoding="utf-8")
            created_files.append(str(tests_dir / "requirements.txt"))

        elif lang == "java":
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
            (tests_dir / "pom.xml").write_text(pom_content, encoding="utf-8")
            created_files.append(str(tests_dir / "pom.xml"))

        return {
            "targetDir": str(self.target_dir),
            "appName": app_name,
            "language": lang,
            "layers": [
                ".agents/skills/ (4个核心SOP技能)",
                "knowledge/ (3支柱业务知识库)",
                "qa/ (需求对账过程资产)",
                f"tests/ (已内置接入 trueone-sdk/{lang})"
            ],
            "createdFiles": created_files
        }
