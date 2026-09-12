# 资料入口与历史调研

> 触发：查证设备、工艺、API、格式或复用第三方资源；只读取相关条目。以下日期表示历史核验，不表示本次重新核验。

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
