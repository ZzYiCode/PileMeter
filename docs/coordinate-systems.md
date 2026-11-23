# 坐标约定

## 相机坐标

- 遵循 OpenCV 相机约定。
- `+X` 指向图像右侧，`+Y` 指向图像下方，`+Z` 指向相机前方。
- 外参矩阵形状为 `(S, 3, 4)`，语义为 `x_camera = R * x_world + t`，
  也写作 camera-from-world 或 world-to-camera。
- 相机中心为 `C = -R^T t`。

## VGGT 点图

`world_points` 形状为 `(S, H, W, 3)`，每个像素对应 VGGT 当前世界坐标系中的
一个三维点。该坐标系通常由网络内部选定，不保证与第一台相机的世界坐标完全
一致，因此显示相机轨迹前必须用同一组外参验证。

## 深度反投影

对像素 `(u, v)`：

```text
X_camera = (u - cx) * depth / fx
Y_camera = (v - cy) * depth / fy
Z_camera = depth
X_world = R_camera_to_world * X_camera + C
```

优先使用与深度图同一轮推理产生的内参和外参。

## 尺度

VGGT 默认输出相对尺度。标尺两端点重建距离为 `L_model`，真实长度为
`L_real` 时：

```text
s = L_real / L_model
V_absolute = s^3 * V_model
```

在 `s` 未求解并验证前，所有点云和结果必须标记为 `scale_status = relative`。
