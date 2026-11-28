# PileMeter 堆衡

PileMeter 是一个面向工程堆体的多视角 RGB 体积测量系统。系统计划使用 VGGT
恢复相机、深度和点云，再通过标尺与地面基准将相对几何转换为真实尺度。

> 当前仓库已具备最小重建闭环：本地 VGGT 推理、点云导出、相机轨迹和 Web
> 点云查看器。标尺求解、地面拟合和体积计算仍待接入。

## 第一版目标

```text
多视角图片
  -> 输入质检
  -> VGGT 多视角重建
  -> 点云清理与可视化
  -> 标尺尺度恢复
  -> 地面拟合
  -> 高度场体积计算
  -> 质量报告
```

VGGT 输出是相对尺度几何，不能直接作为米制测量结果。系统只有在标尺和地面基准
均可靠时才应输出绝对体积。

## 当前能力

- FastAPI 健康检查接口；
- 任务状态与输入参数契约；
- 可测试的顺序流水线运行器；
- 本地 VGGT-1B 推理和深度反投影；
- ASCII/二进制 PLY 导出；
- Three.js 点云与相机轨迹查看器；
- 后端测试、GitHub Actions、Docker 与 Compose 基础配置。

## 项目结构

```text
backend/                 Python 后端与算法模块
  src/pile_meter/
    domain/              业务实体与状态机
    contracts/           稳定的序列化契约
    application/         用例与流水线编排
    reconstruction/      VGGT 等重建模型适配
    pointcloud/          点云过滤、融合和导出
    segmentation/        堆体与背景分割
    calibration/         标尺、尺度和地面平面
    volume/              高度场与体积积分
    quality/             质量门控和不确定性
    artifacts/           任务产物与 manifest
    infra/               数据库、存储和队列实现
    interfaces/          API、Worker 和 CLI 入口
frontend/                Web 前端
deploy/                  Docker 与部署配置
docs/                    架构、产物协议和路线图
models/                  本地模型权重（不提交 Git）
data/                    本地样例数据（不提交 Git）
runtime/                 本地任务产物（不提交 Git）
```

详细设计见：

- [系统架构](docs/architecture.md)
- [任务产物布局](docs/artifact-layout.md)
- [开发路线图](docs/roadmap.md)
- [坐标约定](docs/coordinate-systems.md)

## 本地启动

要求 Python 3.11+、Node.js 20+。

### 1. Python 环境

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install torch==2.13.0 --index-url https://download.pytorch.org/whl/cu130
python -m pip install -e "backend[api,reconstruction,dev]"
```

RTX 50 系列显卡需要支持 `sm_120` 的 PyTorch；CUDA 13 包约 1.9 GB。

### 2. 连接本地模型

```powershell
.\scripts\setup-vggt.ps1
```

脚本会在不入库的位置创建：

- `third_party/vggt`：VGGT 源码目录链接；
- `models/vggt/model.safetensors`：权重硬链接。跨磁盘时可加 `-CopyWeights`。

### 3. 运行重建

图片放在同一目录中，建议先使用 6～10 张有连续重叠的环绕照片：

```powershell
pile-meter reconstruct --images ".\data\my_scene\images" --max-images 6
```

输出默认写入 `runtime/reconstructions/<run_id>/`：

```text
manifest.json
predictions.npz
points_raw.ply
points_view.ply
cameras.json
```

此阶段点云是 VGGT 相对尺度，不等同于真实米制体积。

### 4. 启动 API

```powershell
pile-meter doctor
uvicorn pile_meter.interfaces.api.main:app --reload
```

API 文档：<http://127.0.0.1:8000/docs>

健康检查：<http://127.0.0.1:8000/api/v1/health>

### 5. 启动查看器

```powershell
cd frontend
npm install
npm run dev
```

前端地址：<http://127.0.0.1:5173>。页面会自动加载最近一次重建，
支持点大小、原始颜色/Z 高度着色、相机轨迹和视角复位。

### 测试

```powershell
pytest backend/tests
ruff check backend/src backend/tests
```

## Docker

```powershell
docker compose up --build
```

Web 地址：<http://127.0.0.1:8080>

## 开发原则

- API 进程保持轻量，不导入 Torch；GPU 推理由 Worker 执行。
- 算法步骤通过稳定契约传递数据，避免原始模型字典贯穿全系统。
- 每次任务使用不可变的 `job_id/run_id` 目录，重试不覆盖历史结果。
- 模型版本、配置哈希、坐标约定和 schema 版本写入 manifest。
- 未完成尺度恢复前，产物必须标记为相对尺度几何。

## 许可

项目许可证尚未确定。在补充许可证前，默认保留所有权利。
