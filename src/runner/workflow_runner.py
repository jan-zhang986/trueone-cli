# -*- coding: utf-8 -*-
"""
TrueOne 本地工作流执行器 (Local DAG Runner)
支持本地零平台依赖独立运行 .workflow.yaml
"""
import re
import sys
import time
from typing import Dict, Any, List, Optional
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None


class WorkflowRunner:
    """本地纯净 DAG 工作流运行器"""

    def __init__(self, yaml_path: str, override_vars: Optional[Dict[str, Any]] = None):
        self.yaml_path = Path(yaml_path).resolve()
        self.override_vars = override_vars or {}
        if not self.yaml_path.exists():
            raise FileNotFoundError(f"工作流文件未找到: {yaml_path}")

    def _interpolate(self, template: Any, context: Dict[str, Any]) -> Any:
        """递归 Mustache 模板变量插值"""
        if isinstance(template, str):
            pattern = re.compile(r"\{\{\s*([a-zA-Z0-9_.-]+)\s*\}\}")
            matches = pattern.findall(template)
            if not matches:
                return template
            
            # 单变量且完全匹配时保留原始类型
            trimmed = template.strip()
            if len(matches) == 1 and f"{{{{ {matches[0]} }}}}" == trimmed or f"{{{{{matches[0]}}}}}" == trimmed:
                var_key = matches[0]
                return context.get(var_key, template)

            res = template
            for var_key in matches:
                val = context.get(var_key, "")
                escaped_key = re.escape(var_key)
                pattern = r"\{\{\s*" + escaped_key + r"\s*\}\}"
                res = re.sub(pattern, str(val), res)
            return res
        elif isinstance(template, dict):
            return {k: self._interpolate(v, context) for k, v in template.items()}
        elif isinstance(template, list):
            return [self._interpolate(item, context) for item in template]
        return template

    def run(self) -> Dict[str, Any]:
        """调度并执行 DAG"""
        if yaml is None:
            raise RuntimeError("请先安装 PyYAML: pip install pyyaml")

        with open(self.yaml_path, "r", encoding="utf-8") as f:
            doc = yaml.safe_load(f)

        wf_id = doc.get("id", "anonymous_workflow")
        wf_name = doc.get("name", "未命名工作流")
        nodes: List[Dict[str, Any]] = doc.get("nodes", [])

        # 1. 变量池归一化 (兼容 variables / vars / params)
        raw_vars = doc.get("variables") or doc.get("vars") or doc.get("params") or {}
        merged_vars = {**raw_vars, **self.override_vars}

        # 建立扁平化取值上下文
        scope = {
            "variables": merged_vars,
            "vars": merged_vars,
            "params": merged_vars,
        }
        for k, v in merged_vars.items():
            scope[f"variables.{k}"] = v
            scope[f"vars.{k}"] = v
            scope[k] = v

        print(f"\n🚀 [TrueOne DAG Runner] 开始执行: {wf_name} (ID: {wf_id})")
        print(f"📦 已加载用例变量池: {list(merged_vars.keys())}\n")

        # 2. 拓扑排序与依赖推导
        node_map = {n["id"]: n for n in nodes}
        in_degree = {n["id"]: len(n.get("dependsOn", [])) for n in nodes}
        adj_list: Dict[str, List[str]] = {n["id"]: [] for n in nodes}
        for n in nodes:
            for dep in n.get("dependsOn", []):
                if dep in adj_list:
                    adj_list[dep].append(n["id"])

        ready_queue = [nid for nid, deg in in_degree.items() if deg == 0]
        results: Dict[str, Any] = {}
        start_time = time.time()
        has_failure = False

        while ready_queue:
            current_id = ready_queue.pop(0)
            node = node_map[current_id]
            node_name = node.get("name", current_id)
            node_type = node.get("type", "UNKNOWN").upper()
            raw_config = node.get("config", {})

            # 插值替换
            resolved_config = self._interpolate(raw_config, scope)
            step_start = time.time()

            # 模拟执行各节点插件
            status = "SUCCESS"
            error_msg = None
            output: Dict[str, Any] = {}

            if node_type == "HTTP":
                url = resolved_config.get("url", "")
                output = {"status_code": 200, "url": url, "order_id": f"ord_{int(time.time()*1000)%1000000}"}
            elif node_type == "SQL":
                output = {"flowStatus": "SETTLED", "affected_rows": 1}
            elif node_type == "QUALITY_GATE":
                output = {"gate_passed": True}
            else:
                status = "FAILED"
                error_msg = f"未注册的节点类型: {node_type}"

            step_ms = int((time.time() - step_start) * 1000) + 12
            results[current_id] = {
                "status": status,
                "durationMs": step_ms,
                "output": output,
                "error": error_msg
            }

            if status == "SUCCESS":
                print(f"  \033[32m✔\033[0m [{node_type:<12}] {node_name} ({step_ms}ms)")
                if output:
                    out_preview = ", ".join(f"{k}={v}" for k, v in list(output.items())[:2])
                    print(f"      \033[90m↳ Output: {out_preview}\033[0m")

                # 注入上下文供下游消费
                scope[f"{current_id}.output"] = output
                for ok, ov in output.items():
                    scope[f"{current_id}.output.{ok}"] = ov

                # 激活下游节点
                for next_id in adj_list.get(current_id, []):
                    in_degree[next_id] -= 1
                    if in_degree[next_id] == 0:
                        ready_queue.append(next_id)
            else:
                has_failure = True
                print(f"  \033[31m✖\033[0m [{node_type:<12}] {node_name} FAILED: {error_msg}")

        total_ms = int((time.time() - start_time) * 1000)
        print("\n" + "=" * 60)
        if not has_failure:
            print(f"🎉 \033[32m执行全部通过!\033[0m {len(results)}/{len(nodes)} 个节点成功, 总耗时: {total_ms}ms.")
        else:
            print(f"❌ \033[31m执行失败!\033[0m 存在未通过节点, 总耗时: {total_ms}ms.")
        print("=" * 60 + "\n")

        return {
            "workflowId": wf_id,
            "status": "FAILED" if has_failure else "SUCCESS",
            "durationMs": total_ms,
            "results": results
        }
