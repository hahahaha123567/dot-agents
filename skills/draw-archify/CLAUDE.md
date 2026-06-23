# Draw Archify

Claude Code 入口说明：用于工程图表，不用于生成插画或图片风格转换。

## 与其他 draw skill 的区别

| Skill | 适用场景 | 产物 | 不适合 |
| --- | --- | --- | --- |
| `draw-archify` | 架构图、流程图、时序图、数据流图、生命周期图、Mermaid 结构重绘 | 独立 HTML，内联 SVG，可导出 PNG/JPEG/WebP/SVG | 情绪化插画、文章封面、手绘总结图 |
| `draw-crochet-doll-image` | 指定图片或对象转温馨钩针玩偶、毛线公仔 | 柔软纱线质感、可见针织细节的怀旧毛公仔 | 工程图表、系统拓扑 |
| `draw-hand-drawn-infographic` | 把文章、观点、会议内容总结成 3-6 点视觉信息图 | 16:9 手绘卡通信息图 | 精确系统拓扑、API 调用链 |
| `draw-orange-line-illustration` | 单一观点、隐喻、封面或文章配图 | 黑线白底、一个橙色重点的概念插画 | 多信息点总结、童趣彩色风格 |
| `draw-folk-doodle-image` | 将图片或场景转成童趣民间涂鸦平面插图 | 可爱、彩色、白纸背景的风格化图片 | 工程图表、克制 editorial 概念图 |

## Claude 使用要点

- 用户要“架构图 / 流程图 / 时序图 / 数据流图 / 状态机 / Mermaid 重画”时选本 skill
- 优先读 `SKILL.md` 中的图类型选择表，再按对应 schema 和 example 生成 JSON
- 需要验证布局时运行对应 renderer，不直接修改 renderer
