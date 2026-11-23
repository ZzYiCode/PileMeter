# Data

本目录用于本地样例图片和测试场景，不提交实际采集数据。

建议每个场景包含：

```text
scene_name/
├── images/
├── calibration.json
└── metadata.json
```

后续可增加 `scripts/prepare_fixture.py` 生成小型脱敏测试集。
