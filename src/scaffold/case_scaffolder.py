# -*- coding: utf-8 -*-
"""
CaseScaffolder: 单测试用例骨架生成器 (支持 Go / Python / Java)
"""
import re
import time
from pathlib import Path
from typing import Dict, Any, Optional


class CaseScaffolder:
    """用例模板代码生成器"""

    @staticmethod
    def generate_case(
        lang: str,
        req: str,
        risk: str = "P1",
        title: str = "验证核心业务逻辑断言",
        case_id: Optional[str] = None,
        target_dir: Optional[str] = None,
    ) -> Dict[str, Any]:
        lang = lang.lower()
        if not case_id:
            safe_req = re.sub(r"[^A-Za-z0-9]", "", req).upper() or "REQ"
            case_id = f"TC-{safe_req}-{int(time.time()) % 10000:04d}"

        dest_dir = Path(target_dir or "tests").resolve()
        dest_dir.mkdir(parents=True, exist_ok=True)

        file_name = ""
        code_content = ""

        if lang == "go":
            file_name = f"tc_{case_id.lower().replace('-', '_')}_test.go"
            func_name = f"Test{case_id.replace('-', '_')}"
            code_content = f"""package tests

import (
\t"testing"

\taegis "github.com/vanguard-platform/aegis-sdk-go"
)

func {func_name}(t *testing.T) {{
\tmeta := aegis.Meta{{
\t\tID:       "{case_id}",
\t\tReq:      "{req}",
\t\tTitle:    "{title}",
\t\tRisk:     "{risk.upper()}",
\t\tPriority: "P1",
\t}}

\taegis.Case(t, meta, func(c *aegis.Context) {{
\t\tc.Step("1. 初始化测试数据与前置上下文", func() {{
\t\t\t// 构造入参与 Mock 上下文
\t\t}})

\t\tc.Step("2. 执行核心业务调用并记录证据", func() {{
\t\t\tc.AttachEvidence("case_id", "{case_id}")
\t\t}})

\t\tc.Step("3. 校验业务状态机与核心断言", func() {{
\t\t\t// 校验核心断言
\t\t}})
\t}})
}}
"""

        elif lang == "python":
            file_name = f"test_{case_id.lower().replace('-', '_')}.py"
            code_content = f"""# -*- coding: utf-8 -*-
\"\"\"
TrueOne Test-as-Code - {case_id}
Requirement: {req} | Risk: {risk} | Title: {title}
\"\"\"
import pytest
import aegis


@aegis.case(
    id="{case_id}",
    req="{req}",
    title="{title}",
    risk="{risk.upper()}",
    priority="P1",
    tags=["regression", "{risk.lower()}"]
)
def test_{case_id.lower().replace('-', '_')}():
    with aegis.step("1. 初始化测试数据与前置上下文"):
        payload = {{"id": "{case_id}", "status": "ACTIVE"}}
        assert payload["id"] == "{case_id}"

    with aegis.step("2. 执行核心业务调用并记录证据"):
        result_code = 200
        aegis.attach_evidence("payload.json", payload)
        assert result_code == 200

    with aegis.step("3. 校验业务状态机与核心断言"):
        assert True
"""

        elif lang == "java":
            class_name = f"Test{case_id.replace('-', '_')}"
            file_name = f"{class_name}.java"
            code_content = f"""package com.trueone.tests;

import com.vanguard.aegis.sdk.Aegis;
import com.vanguard.aegis.sdk.AegisCase;
import com.vanguard.aegis.sdk.AegisExtension;
import com.vanguard.aegis.sdk.RiskLevel;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;

import static org.junit.jupiter.api.Assertions.*;

@ExtendWith(AegisExtension.class)
public class {class_name} {{

    @Test
    @DisplayName("{title}")
    @AegisCase(
        id = "{case_id}",
        req = "{req}",
        title = "{title}",
        risk = RiskLevel.{risk.upper()},
        tags = {{"regression", "{risk.lower()}"}}
    )
    void testExecution() {{
        Aegis.step("1. 初始化测试数据与前置上下文", () -> {{
            assertNotNull("{case_id}");
        }});

        Aegis.step("2. 执行核心业务调用并记录证据", () -> {{
            Aegis.attachEvidence("context.json", "{{\\\"caseId\\\": \\\"{case_id}\\\"}}");
            assertTrue(true);
        }});

        Aegis.step("3. 校验业务状态机与核心断言", () -> {{
            assertEquals(1, 1);
        }});
    }}
}}
"""
        else:
            raise ValueError(f"不支持的语言栈: {lang}，可选 go, python, java")

        out_path = dest_dir / file_name
        out_path.write_text(code_content, encoding="utf-8")

        return {
            "caseId": case_id,
            "lang": lang,
            "req": req,
            "risk": risk.upper(),
            "title": title,
            "filePath": str(out_path),
            "codeContent": code_content
        }
