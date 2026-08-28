# 天猫国际保健行业 Agent — Ontology 底座模板（行业试点版）

这套模板把「ODPS 数据底层 + kbase 知识图谱 + 业务语义 + agent 编排」沉淀为**机器可读的本体定义**。
思路对标 Palantir Ontology：对象（Object）、链接（Link）、指标（语义属性）、工具/操作（Action/Function），
但按行业试点的规模做了裁剪——先跑通闭环，不追求大而全。

## 文件结构

| 文件 | 作用 | 起草人 | 确认人 |
|------|------|--------|--------|
| `ontology.yaml` | 对象类型 + 链接类型定义 | 建设者 | 业务 owner |
| `metrics.yaml` | 指标字典（口径唯一事实源） | 数据 owner | 业务 owner 签字 |
| `dimensions.yaml` | 维度字典（时间/类目/渠道/模式/人群） | 数据 owner | 业务 owner |
| `glossary.md` | 业务术语与黑话表 | 业务 owner | — |
| `tools.yaml` | 取数 skill / 工具注册表 | 建设者 | 数据 owner |
| `qa_evalset.yaml` | 评测问答集（质量回归的标尺） | 全员贡献 | 建设者维护 |
| `sops.md` | 分析套路 SOP（人的经验 → 可执行流程） | 业务 + 分析 | 业务 owner |
| `governance.md` | 试点期角色分工、口径变更流程 | 建设者 | 全员 |

## 试点四步走

1. **圈范围**：让每个岗位报 10 条真实高频问题，填进 `qa_evalset.yaml`（先凑 30 条，从取数工单里捞最快）。
2. **倒推定义**：从这 30 条问题倒推需要哪些对象、指标、维度，填 `ontology.yaml` / `metrics.yaml` / `dimensions.yaml`。
   问题覆盖不到的对象和指标，v1 一律不建。
3. **接工具**：把现有取数 skill 注册进 `tools.yaml`；每个对象类型在 ODPS 上绑定**一张物化宽表**
   （提前 join 好，不要让 agent 现场关联多张表）。
4. **回归评测**：每次修改任何定义文件，把评测集跑一遍再发布。

## 喂给 AI（agent 运行时）的方式

- **不要整包塞进 system prompt。** 分层加载：
  - system prompt 常驻：对象清单摘要（一行一个）+ 工具清单 + `metrics.yaml` 里的全局口径约定（conventions 区）
  - 按需检索：具体指标口径、术语解释、SOP 步骤（放 kbase 或向量库，agent 查询时召回相关片段）
- **status 门槛**：所有条目带 `status: draft | confirmed`。agent 只信 `confirmed`；
  遇到 draft 口径要在回答里声明"口径未最终确认"。
- **让 AI 参与建设的正确姿势**：把 ODPS 表 DDL + 样例数据 + 本目录的模板发给 AI，
  让它起草 draft；人只做两件事——确认口径、补充黑话。不要让人从零填模板。

## 填写约定

- `<尖括号>` 是占位符，替换为真实值
- `# TODO` 标记待补内容
- 每个条目都有 `owner`（负责人花名/工号）和 `status`
- 示例条目均为**虚构示意**（表名、口径按你们真实情况替换），但结构和坑位是按保健行业真实场景设计的
