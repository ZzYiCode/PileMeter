# 任务产物布局

## 目录

```text
runtime/
└── jobs/
    └── {job_id}/
        └── runs/
            └── {run_id}/
                ├── manifest.json
                ├── predictions.npz
                ├── points_raw.ply
                ├── points_view.ply
                ├── cameras.json
                ├── previews/
                ├── artifacts.json
                └── report.json
```

## manifest.json

每次运行必须记录：

- `schema_version`
- `job_id`、`run_id`
- 模型名称、权重版本或哈希
- 输入图片顺序和尺寸
- 预处理方式
- 坐标约定
- 算法配置哈希
- 代码版本
- 状态、开始时间和结束时间
- 尺度状态：`relative` 或 `metric`

## 产物类型

| 文件 | 内容 |
| --- | --- |
| `predictions.npz` | 深度、置信度、内参、外参、点图和输入变换 |
| `points_raw.ply` | 过滤后的完整观测点云，保留下游计算所需信息 |
| `points_view.ply` | 为浏览器降采样的显示副本 |
| `cameras.json` | 相机位姿、时间戳和来源图片 |
| `artifacts.json` | 产物索引、媒体类型、大小和校验和 |
| `report.json` | 质量指标、警告和最终状态 |

## 不可变规则

已经开始执行的运行目录不可原地覆盖。参数变化、代码变化或重试都应创建新的
`run_id`，并通过数据库或索引关联到同一 `job_id`。
