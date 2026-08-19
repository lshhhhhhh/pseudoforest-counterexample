# 对审查的逐条回应与处置（含第三轮勘误）

最后更新: 2026-08-18（第三轮之后）。**canonical 版本 = 公开仓库
github.com/lshhhhhhh/pseudoforest-counterexample**；本研究目录的论文文件
（PAPER_DRAFT.md、paper/）在每轮修订后由仓库同步；如有出入以仓库为准。

## 第三轮审查（发布/同步/审计闭环）的处置

**R3-1 审计脚本失败时可能仍退出码 0 — 接受，已修。**
`theoremB_audit.py` 末尾新增硬断言：`feasible != total` 时抛
AssertionError（非零退出），不再只打印候选行；full-order 运行同时断言
total == A000109[n]。

**R3-2 分片无聚合断言、裸 wait 不传播失败 — 接受，已修。**
新增独立聚合器 `theoremB_aggregate.py`：逐阶断言（i）分片编号恰为
0..mod−1 或恰一个 full log；（ii）Σtotal == A000109[n]；（iii）
Σfeasible == Σmodel_verified == Σtotal；违例非零退出，通过则写
SUMMARY.md。驱动脚本改为逐 pid `wait` 并传播失败，收尾强制跑聚合器。

**R3-3 "重跑已完成"陈述不实 — 接受，已更正；现已真正完成。**
最终状态（2026-08-19，聚合器通过后更新）：**n=4..17 全部 149,960,273 个
三角剖分经审计脚本重跑完毕**——每实例 SAT 求解 + 模型解码 + min(d+,d-)≤1
直接度数验证；n=4..16 在本地（Windows，环境见 ENVIRONMENT.txt 与
ENVIRONMENT_RUN.txt），n=17 在 GCP c2d-highcpu-16（Debian 12，64 幂等
分片，单个 2 小时窗口完成，环境见 ENVIRONMENT_RUN_pf-audit-n17-1.txt）。
聚合器断言全部通过（分片集完备、Σtotal=A000109 逐阶吻合、
feasible=model_verified=total），SUMMARY.md 已入库 verification/theoremB/。

**R3-4 本地未同步却声称已同步 — 接受，已更正并修复。**
事故复盘：MD 补丁脚本在部分模式失配时先退出后落盘，导致前两次运行中
已匹配的替换全部丢失，最终本地 MD 只有 2/11 处生效；而我依据脚本自报
写下了"已同步"。本轮已（i）用带**落盘后终态 grep 验证**的补丁重新应用
全部 9 处缺失修订并逐条核验通过；（ii）research 目录 paper/（main.tex、
main.pdf、图）直接由仓库 canonical 版本覆盖同步；（iii）审计脚本副本
同步入 research/scripts。教训已入 PRINCIPLES（补丁自报成功不算数，
必须对落盘文件做终态验证）。

**R3-5 plantri 路径硬编码 — 接受，已修。**
`theoremB_audit.py` 支持 `PLANTRI` 环境变量与 `--plantri PATH` 参数，
缺失时给出明确报错与下载地址；ENVIRONMENT.txt 记录版本（plantri 5.5）、
补丁（CPUTIME 1→0）、构建命令与二进制 SHA256。plantri 源码依其许可不再
重分发，提供官方下载地址。

## 第二轮审查的处置（数学正文——远端已确认修对）

**M1 嵌套树定义不一致 — 已修**（区域为点、曲线为边，全文统一；
Proposition 6.2 的二染色论证字面成立）。
**M2 定理 B 审计包 — 六子项全部落实**（严格解析、退出码检查、逐实例
模型直接度数验证、日志入库、verifier 描述精确化、ENVIRONMENT.txt）。
完成状态见 R3-3。
**I1 "58 最优" — 已弱化**到 Γ′−v 子类。
**I2 "恰六个" — 已增引** Aldred–Bau–Holton–McKay, SIAM J. Discrete
Math. 13 (2000) 25–32；[HM] 仅支撑最小阶。
**I3 复核措辞 — 已修**（三层证据分类；"不信任任何组件"收紧）。
**次要 1–7 — 全部落实**（Whitney 措辞、脚本 27 注释、图 F_i、flip 定义
与日志归档、[RW] 引用、TODO 仅存工作版、SAT 文献拆分）。

## 第一轮（敌意子代理）审查的处置

计数错误 149,951,159 → 149,960,273（定位到日志累计加法错，n=4..12 重扫
修正）；"(unique)" 38 点图与 Tait 框架措辞；[CK]/[CKW] 互换；十二项
minor。全部落实于 v0.3/v0.3.1。

## 三轮审查的总图

三轮结论一致：**定理 A 的数学无致命漏洞**。第一轮修数值与引用；第二轮
修定义一致性与审计包设计；第三轮修发布纪律（失败传播、聚合断言、同步
真实性、可移植性）。数学、工程、发布三层各被一轮独立打穿一次——全部
修复均有落盘验证。
