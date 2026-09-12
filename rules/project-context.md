# 项目上下文

## 已确认事实

- 项目：3D打印；个人 CAD 建模与打印制作工作区，不是编程产品。
- 目标：通过 MCP 控制 Fusion 360，保留可修改的设计，最终制造实物。
- 沟通：中文；设计与交付尺寸默认 mm，角度默认度。
- 电脑：macOS；已确认应用路径为 `/Users/henji/Applications/Autodesk Fusion.app`，需要时可用 `open '/Users/henji/Applications/Autodesk Fusion.app'` 启动。
- 用户于 2026-09-10 确认：已安装 Fusion 360、已开启 MCP；打印机为 **拓竹 X2D，0.4 mm 喷嘴，以 PLA 为主，少量 PETG**。
- Fusion 使用内置的本地 MCP Server，默认地址为 `http://127.0.0.1:27182/mcp`；2026-09-11 本次恢复后实际监听 `http://127.0.0.1:62842/mcp`，已通过握手、工具发现、回开原生模型及截图验证。当前收纳架客户端用环境变量 `FUSION_MCP_URL` 指定此地址；62842 是本次运行值，重启后重新核对；Fusion 必须保持运行。设置入口：**Fusion → 首选项 → 常规 → API → Fusion MCP Server**。端口若在首选项中变更，客户端地址随之匹配。
- 2026-09-10 核验 Fusion 应用版本 **2705.1.15**，MCP 协议 `2025-03-26`、适配器 `MCP Server Adapter 1.0.0`。连接故障恢复后已通过握手、工具发现、文档读取、只读脚本、临时设计参数写入及独立回读；测试设计已关闭。实体建模与导出仍须按实际任务验证。`activeCommand` 查询出现 UTF-8 序列化错误，可用只读脚本读取 `app.userInterface.activeCommand` 并结合 UI 核对，不能把该错误等同于服务断开。
- 当前发现的工具：`fusion_mcp_read`、`fusion_mcp_execute`、`fusion_mcp_update`、`fusion_mcp_electronics_read`；未来按实时工具定义使用。会话工具列表未直接注册这些接口时，可通过已验证的本地 HTTP MCP 连接调用。
- 用户已授权连接失败时主动打开 Fusion，并通过 computer use 检查 / 启用上述 MCP 设置；具体重试和现场保护见 [Fusion 与 MCP](fusion-mcp.md)。
- 初始化时目录仅有 AGENTS.md、rules/ 与系统目录元数据；2026-09-11 用户明确要求初始化本地 Git 并首次提交。2026-09-12 用户调整版本管理范围：`AGENTS.md`、`rules/` 和 `.gitignore` 纳入 Git；`models/` 整个目录（含模型、切片、交付包、模型脚本及打印记录）仅保留本地，不纳入 Git 跟踪或同步。缓存、日志及本地编辑器配置也忽略。没有构建、测试框架、开发服务或启动命令，未配置远端。

## 设备与工艺基线

- 工艺：FDM / FFF 熔融挤出。默认按用户的 0.4 mm 喷嘴和 PLA 开展普通室内模型方案；耐热、长期受力、弹性或户外用途必须重新评估材料，不能仅沿用默认值。
- 用户于 2026-09-11 先确认收纳架使用 **拓竹 PLA Basic（基础款）＋拓竹增稳低温打印板（Bambu Cool Plate SuperTack）**，随后试打印改用白色 PETG；当次 AMS A4 配置显示 Generic PETG，品牌／系列未确认。槽位与装载材料是当次状态，后续操作重新读取；修订及实际参数见 [模型打印记录](../models/sink-organizer/print-notes.md)，不把这次组合当成所有模型的固定选择。
- 2026-09-11 已安装并核验官方 **Bambu Studio 2.8.2.61**，位置 `/Users/henji/Applications/BambuStudio.app`；安装包 SHA256 与官方发布值匹配。自带真实 X2D 0.4 mm、PLA Basic 与 SuperTack 配置，已完成收纳架分板切片及 GUI 预览回开；具体参数与验证边界见模型打印记录。
- 已验证的 Bambu Studio 工作方式：官方程序命令行离线切片，电脑控制工具操作已登录 GUI 进行预览、核对与交接；本次未使用 Bambu Studio 专用 MCP。电脑控制工具通过 MCP 接入不等于目标软件提供原生 MCP。Fusion 仍通过其本地 MCP 建模；Bambu Studio 的打印发送由自身既有设备连接完成。操作规则见 [验证与交付](testing.md)。
- X2D 官方资料给出的主喷嘴范围为 **256 × 256 × 260 mm**，副喷嘴及双喷嘴交集为 **235.5 × 256 × 256 mm**。此处依据 2026-04-14 官方说明，核验于 2026-09-10。
- X2D 主、副喷嘴的送料与校准条件不同。官方建议主喷嘴用于模型、副喷嘴用于支撑；实际任务需核对喷嘴分工、各自口径、装载材料及可达区域。
- 上述范围不是无条件可用的最大模型尺寸。切片时按当前 X2D 配置、禁区、支撑、裙边 / brim、擦拭塔和喷嘴分配检查；不能把双喷嘴并集当成两支喷嘴均可访问的区域。
- 层高、线宽、温度、速度、壁层、填充和支撑从当前机型、喷嘴、耗材及打印板的真实预设出发，按模型需要调整。当前没有实测的配合间隙或收缩补偿基线。

## 需要时再确认的事项

- 首次实际建模：查询 Fusion 应用版本，刷新 MCP 工具与权限、活动文档和保存状态；连接信息沿用已确认值，发生变化时再更新。
- 首次切片：Bambu Studio 版本、X2D / 喷嘴配置、打印板、材料具体系列；从本机切片器和用户设备信息确认。
- 首次双材料任务：主副喷嘴口径与材料分配、送料装置 / AMS 状态、相容性；不从“有少量 PETG”推断用户希望把它用作支撑。
- 每个模型：用途、关键尺寸、配合对象、载荷与环境、外观要求；已有事实直接复用。

## 文件约定

- AGENTS.md 是入口；rules/ 保存按需读取的长期规则和资料入口。
- 首个模型需要落盘时再建立 `models/<模型名称>/`，不预建空目录树。
- Fusion 原生文档保存参数、特征与组件；需要本地归档时保存适用的 F3D / F3Z。STEP 用于几何交换，不能代替完整的原生历史。
- 打印网格优先 3MF，接口不支持时可导出二进制 STL 并明确 mm；通过目标切片器验证。按需保存 Bambu Studio 项目 3MF，区分它和纯几何 3MF。
- 同一模型的源文件、导出件、切片项目及必要的实际预览放在模型目录中，用清晰的名称和修订号对应；不存在的产物不预留空文件。
- 多次试打印时在该模型目录维护一份简短 `print-notes.md`，仅记录源文档 / 修订、关键参数、材料与预设、姿态、验证状态、实测结果及有效修改；不另建数据库或通用日志系统。
- 私有模型、账号数据和设备凭据不得自动发布；本地路径与云端文档位置按任务需要引用。

## 长期一手资料

以下页面已于 2026-09-10 查阅。软件文档是滚动版本；实际调用前仍需匹配本机版本，不能据此宣称本机支持所有 API。

| 资料 | 使用边界 |
|---|---|
| [Autodesk Fusion MCP 官方连接指南](https://help.autodesk.com/view/ADSKMCP/ENU/?guid=ADSKMCP_FusionDesktopMcp_connecting_to_the_fusion_mcp_server_html) | Fusion 运行要求、首选项中的 MCP 开关、默认本地端口与客户端 URL |
| [Autodesk Fusion MCP 排错](https://help.autodesk.com/view/fusion360/ENU/?guid=ADSKMCP_FusionDesktopMcp_troubleshooting_html) | 连接失败、端口变更和 API 设置项缺失的原因；不自动授权升级或重启 |
| [Bambu X2D 主副挤出与打印范围](https://blog.bambulab.com/two-extruders-one-purpose-what-is-x2d-direct-drive-extrusion-and-auxiliary-extrusion/) | X2D 专属；核对主副喷嘴差异与可达范围 |
| [拓竹支撑耗材与支撑功能](https://wiki.bambulab.com/zh/software/bambu-studio/support) | 支撑类型、界面、Z 间距及阈值角度定义；界面随版本变化 |
| [拓竹 PLA / PETG 互相支撑](https://wiki.bambulab.com/zh/filament-acc/filament/h2d-pla-and-petg-mutual-support) | 官方限定的 PLA Basic、PETG HF / Basic 组合；不能泛化到所有 PLA / PETG 或直接移植其他机型预设 |
| [Prusa：为 3D 打印建模](https://help.prusa3d.com/article/modeling-with-3d-printing-in-mind_164135) | FFF 设计原则；其中机型精度、喷嘴线宽示例不是 X2D 的保证 |
| [Fusion API 单位](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/Units_UM.htm) | Design API 内部长度 cm、角度 rad；MCP 是否转换须另核对 |
| [Fusion 3D 打印与网格导出](https://help.autodesk.com/view/fusion360/ENU/?guid=SLD-3D-PRINT) | 3MF / STL 导出与网格细化；STL 不含单位 |
| [3MF 核心规范](https://github.com/3MFConsortium/spec_core/blob/master/3MF%20Core%20Specification.md) | 单位、对象、变换和可选打印信息；后缀不证明已含机型预设 |

## GitHub 调研结果与取舍

以下是查阅过的参考，**没有安装或执行**。本地规则独立编写，不把第三方 skill 的运行指令当作项目授权。许可证状态记录于 2026-09-10；引入文件前仍须核对对应修订。

| 项目 | 可参考之处 | 不直接采用的原因 |
|---|---|---|
| [EdwinjJ1/3d-print-skill](https://github.com/EdwinjJ1/3d-print-skill/blob/main/SKILL.md) | 查真实规格、网格验证、失败回到几何根因 | 强制 manifold3d；部分固定工艺数值缺少适用验证。README 声明 MIT，根目录未见独立 LICENSE |
| [flowful-ai/cad-skill](https://github.com/flowful-ai/cad-skill/blob/main/SKILL.md) | 参数化与多视图检查流程 | CadQuery 路线；声明 PolyForm Noncommercial 1.0.0。审阅文件中的体积比例薄壁估算、正体积判有效实体及悬垂近似都不足以作验收 |
| [TrillyD13/3d-printing-skill](https://github.com/TrillyD13/3d-printing-skill/blob/main/SKILL.md) | 保护硬件接口、使用真实切片预设、记录有效试打反馈 | MIT LICENSE 已查；默认 H2C / PETG，含覆写原件、依赖安装和实机流程，不能直接用于本项目 X2D / Fusion |
| [santiagomoneta/3d-printing-skills](https://github.com/santiagomoneta/3d-printing-skills) | OrcaSlicer 校准与配置资料线索 | 以 Klipper / OrcaSlicer 为主，README 声明 MIT；本次只核对项目说明，未审计脚本 |
| [Major-AI-Skills 的 Fusion skill](https://github.com/alivirgo/Major-AI-Skills/blob/master/skills/fusion-360/SKILL.md) | 参数、时间线与错误诊断的主题线索 | 泛 CAD / CAM，含未经本机核验的版本、示例与缓存删除指令；不作为 Fusion API 权威资料，许可未核验 |
