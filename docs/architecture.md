# 系统架构

## 架构选择

PileMeter 第一版采用单仓库、模块化单体和 API/Worker 双进程结构。
算法先在进程内通过接口协作，不拆分为多个网络微服务。

```text
React Web
    |
    v
FastAPI API  ---- metadata ----> SQLite / PostgreSQL
    |
    v
Task Queue（后续接入）
    |
    v
Worker 进程
    |
    +-- 输入质检
    +-- VGGT 重建适配
    +-- 点云清理与导出
    +-- 标尺与尺度求解
    +-- 地面拟合
    +-- 高度场体积计算
    +-- 质量门控
```

大文件保存在文件系统或对象存储中，数据库只保存任务状态、指标和产物索引。

## 模块边界

| 模块 | 职责 |
| --- | --- |
| `domain` | 任务状态、业务实体与状态转换 |
| `contracts` | API、流水线和持久化共用的数据结构 |
| `application` | 用例、步骤编排、重试和失败处理 |
| `reconstruction` | VGGT 推理、坐标转换和深度反投影 |
| `pointcloud` | 点云清理、融合、降采样及 PLY/GLB 导出 |
| `calibration` | 标尺检测、绝对尺度和地面平面 |
| `volume` | footprint、高度场和体积积分 |
| `quality` | 图像质量、覆盖率和不确定性门控 |
| `artifacts` | manifest、产物布局、校验和 |
| `infra` | 数据库、文件/对象存储和任务队列 |
| `interfaces` | HTTP API、Worker 和 CLI |

## 数据流

```text
JobCreate
  -> Job
  -> ReconstructionRequest
  -> ReconstructionResult
  -> PointCloudBundle
  -> CalibrationResult
  -> VolumeResult
  -> MeasurementReport
```

大型数组通过 `.npz`、`.ply` 和 `.glb` 文件传递；结构化摘要通过 Pydantic
契约传递。禁止让 VGGT 原始预测字典直接进入 API 或体积算法。

## 进程边界

- API 进程不得导入 Torch、Open3D 等重型依赖。
- Worker 负责 GPU 推理和长时间计算，可独立扩容或部署到 GPU 主机。
- 前端只消费 API 和可下载产物，不直接访问模型目录。
- 体积算法与 VGGT 解耦，后续可以替换为 COLMAP 或其他重建器。

## 并发与一致性

- 每个测量任务拥有 `job_id`，每次执行拥有 `run_id`。
- 任务产物目录不可变；重试创建新的 `run_id`。
- Worker 领取任务时使用租约和心跳，避免重复消费。
- 产物写入采用临时文件加原子重命名。
- 同一配置和输入的重复运行应产生相同的数据结构，允许模型本身带来的数值波动。

## 当前实现状态

当前版本只实现健康检查、任务模型、流水线运行器、PLY 导出和前端状态页。
任务队列、数据库、VGGT 推理和体积计算将在后续里程碑接入。
