# VGGT Adapter

该目录负责 VGGT 模型与 PileMeter 业务契约之间的适配，后续应包含：

- 模型权重和推理运行时加载；
- 固定图片排序、letterbox/pad 与原始像素映射；
- 相机、深度、置信度和点图输出；
- 深度反投影；
- 深度分支与点图分支的质量对照；
- `predictions.npz`、点云和相机轨迹导出。

API 或其他算法模块不得直接导入 `torch` 或依赖 VGGT 输出字典。
