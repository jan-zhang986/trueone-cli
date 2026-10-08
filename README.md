# TrueOne CLI (`trueone`)

面向 AI Agent 与研发工程师的下一代 **Test-as-Code** 质量工程命令行脚手架。

## 🎯 定位与核心价值

在大模型时代，测试的核心瓶颈在于：**AI 缺乏业务上下文、缺乏规范约束、容易盲目写出“假通过”的弱断言用例**。

`trueone-cli` 提供企业级标准化脚手架能力：
1. **4 层工程骨架秒级生成**：一键生成 `.agents/skills/` (AI 规约)、`knowledge/` (业务知识库)、`qa/` (过程对账) 与 `tests/` (原生测试)。
2. **SDK 零配置自动集成**：在初始化工程时，自动为目标语言注入 `trueone-sdk` 依赖，实现开箱即用。
3. **因果对账与代码资产盘点**：结合 Git Diff，精准捕获未被测试覆盖的代码盲区 (GAP)。

---

## 🏗️ 4 层测试工程规范架构

通过 `trueone init` 生成的标准工程遵循统一的层次规约：

```text
<app>-tests/
├── .agents/skills/          # 【主动技能层 (Skills)】—— 约束 AI 按标准 SOP 工作
│   ├── test-design/         # 1. 需求拆解与 FMEA 风险分析规约
│   ├── test-codegen/        # 2. 原生用例代码生成规约 (强制绑定 SDK)
│   ├── test-review/         # 3. 方案反思评审规约 (拦截弱断言与盲区)
│   └── test-validate/       # 4. Git Diff 变动因果对账与发布五问门禁
│
├── knowledge/               # 【被动事实层 (Knowledge)】—— 喂给 AI 的领域上下文
│   ├── ROUTING.md           # 知识总路由表
│   └── applications/{app}/  # 业务应用物理隔离
│       ├── app-overview.md  # 系统边界与架构定位
│       ├── domain/          # 核心领域状态机与业务规则字典
│       └── tech/            # 造数规则、防坑规约与异步轮询约定
│
├── qa/                      # 【过程对账层 (QA QA-as-Code)】—— 需求生命周期资产
│   └── README.md            # 以需求为单元的过程对账与盲区签注指南
│
└── tests/                   # 【物理用例层 (Tests)】—— 真实落盘的多语言代码
    ├── go.mod               # 自动依赖 trueone-sdk
    └── ...
```

---

## 🚀 快速上手

### 1. 安装与运行
```bash
# 进入 CLI 目录或配置环境变量
python3 src/cli/main.py --help
```

### 2. 初始化标准测试工程 (`trueone init`)
```bash
# 为 Go 语言业务系统初始化测试工程
python3 src/cli/main.py init --app payment-service --lang go --dir ./payment-tests

# 为 Python 业务系统初始化
python3 src/cli/main.py init --app order-service --lang python --dir ./order-tests

# 为 Java SpringBoot 业务系统初始化
python3 src/cli/main.py init --app user-service --lang java --dir ./user-tests
```

输出示例：
```text
🎉 成功为应用 [payment-service] 初始化 TrueOne 4 层标准测试工程！
📁 目标目录: /path/to/payment-tests
🏗️ 生成的分层结构:
   • .agents/skills/ (4个核心SOP技能)
   • knowledge/ (3支柱业务知识库)
   • qa/ (需求对账过程资产)
   • tests/ (已内置接入 trueone-sdk/go)
📦 已自动为 tests/ 注入 trueone-sdk/go 依赖，开箱即用！
```

---

## 🔗 相关生态组件

- **`trueone-sdk`**：多语言统一契约与事件上报 SDK (Go / Python / Java)
- **`trueone-anubis`**：云端质量工作台核心 Go 后端与 AST 对账引擎
- **`trueone-web`**：活体测试计划因果对账三联屏前端大盘
