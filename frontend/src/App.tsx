import { useCallback, useEffect, useState } from "react";

import PointCloudViewer from "./components/PointCloudViewer";

type Reconstruction = {
  run_id: string;
  created_at: string;
  model_name: string;
  image_count: number;
  point_count: number;
  scale_status: string;
  pointcloud_url: string;
  cameras_url: string;
  manifest_url: string;
  bounds_size: number[];
};

type ColorMode = "rgb" | "height";

function formatDate(value: string): string {
  return new Intl.DateTimeFormat("zh-CN", {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(value));
}

function App() {
  const [reconstruction, setReconstruction] = useState<Reconstruction | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [loadedPoints, setLoadedPoints] = useState<number | null>(null);
  const [pointSize, setPointSize] = useState(2.2);
  const [colorMode, setColorMode] = useState<ColorMode>("rgb");
  const [showCameras, setShowCameras] = useState(true);
  const [resetSignal, setResetSignal] = useState(0);

  const loadLatest = useCallback(() => {
    const controller = new AbortController();
    setLoading(true);
    setError(null);
    fetch("/api/v1/reconstructions/latest", { signal: controller.signal })
      .then(async (response) => {
        if (response.status === 404) {
          return null;
        }
        if (!response.ok) {
          throw new Error(`API 返回 ${response.status}`);
        }
        return (await response.json()) as Reconstruction;
      })
      .then((result) => {
        setReconstruction(result);
        setLoadedPoints(null);
        if (result) {
          setError(null);
        }
      })
      .catch((reason: unknown) => {
        if (!controller.signal.aborted) {
          setError(reason instanceof Error ? reason.message : "无法读取重建结果。");
        }
      })
      .finally(() => {
        if (!controller.signal.aborted) {
          setLoading(false);
        }
      });
    return () => controller.abort();
  }, []);

  useEffect(() => loadLatest(), [loadLatest]);

  const handleViewerLoaded = useCallback((count: number) => {
    setLoadedPoints(count);
  }, []);

  const handleViewerError = useCallback((message: string) => {
    setError(message);
  }, []);

  return (
    <div className="survey-shell">
      <header className="topbar">
        <a href="/" className="wordmark" aria-label="PileMeter 首页">
          <span className="wordmark-sign">PM</span>
          <span className="wordmark-copy">
            <strong>PileMeter</strong>
            <span>堆衡 · VGGT 场重建</span>
          </span>
        </a>
        <div className="topbar-meta">
          <span className="connection-state">
            <i />
            {reconstruction ? "模型结果已连接" : "等待重建结果"}
          </span>
          <a href="/docs">API</a>
          <a href="https://github.com/ZzYiCode/PileMeter" target="_blank" rel="noreferrer">
            GitHub
          </a>
        </div>
      </header>

      <main className="workbench">
        <aside className="control-rail" aria-label="点云控制">
          <section className="rail-title">
            <p>VGGT / FIELD VIEW</p>
            <h1>多视角<br />场重建</h1>
            <span>相对尺度 · 未做体积标定</span>
          </section>

          <section className="rail-section">
            <div className="section-label">
              <span>视图</span>
              <button type="button" onClick={() => setResetSignal((value) => value + 1)}>
                复位视角
              </button>
            </div>
            <label className="range-control">
              <span>点大小</span>
              <output>{pointSize.toFixed(1)}×</output>
              <input
                type="range"
                min="0.8"
                max="7"
                step="0.1"
                value={pointSize}
                onChange={(event) => setPointSize(Number(event.target.value))}
              />
            </label>
            <div className="mode-switch" aria-label="着色模式">
              <button
                type="button"
                className={colorMode === "rgb" ? "active" : ""}
                onClick={() => setColorMode("rgb")}
              >
                原始颜色
              </button>
              <button
                type="button"
                className={colorMode === "height" ? "active" : ""}
                onClick={() => setColorMode("height")}
              >
                Z 高度
              </button>
            </div>
            <label className="toggle-control">
              <span>显示相机轨迹</span>
              <input
                type="checkbox"
                checked={showCameras}
                onChange={(event) => setShowCameras(event.target.checked)}
              />
            </label>
          </section>

          <section className="rail-section result-record">
            <div className="section-label">
              <span>本次记录</span>
              {reconstruction && <b>{formatDate(reconstruction.created_at)}</b>}
            </div>
            {reconstruction ? (
              <dl>
                <div><dt>模型</dt><dd>{reconstruction.model_name}</dd></div>
                <div><dt>输入视角</dt><dd>{reconstruction.image_count}</dd></div>
                <div><dt>显示点数</dt><dd>{(loadedPoints ?? reconstruction.point_count).toLocaleString()}</dd></div>
                <div><dt>尺度</dt><dd>{reconstruction.scale_status}</dd></div>
                <div><dt>运行 ID</dt><dd>{reconstruction.run_id}</dd></div>
              </dl>
            ) : (
              <div className="empty-record">
                <strong>{loading ? "正在检查结果…" : "还没有点云"}</strong>
                <p>先运行下面的命令，再点击刷新。</p>
                <code>pile-meter reconstruct --images .\data\your_scene</code>
              </div>
            )}
          </section>

          <button className="refresh-button" type="button" onClick={() => loadLatest()}>
            刷新重建结果
          </button>
        </aside>

        <section className="viewport-panel">
          {reconstruction ? (
            <PointCloudViewer
              pointcloudUrl={reconstruction.pointcloud_url}
              camerasUrl={reconstruction.cameras_url}
              pointSize={pointSize}
              colorMode={colorMode}
              showCameras={showCameras}
              resetSignal={resetSignal}
              onLoaded={handleViewerLoaded}
              onError={handleViewerError}
            />
          ) : (
            <div className="viewport-empty">
              <div className="empty-target" aria-hidden="true">
                <span />
                <span />
                <span />
              </div>
              <p>{loading ? "正在检查重建产物" : "等待第一组多视角图片"}</p>
              <span>运行 VGGT 后，点云会在这里出现。</span>
            </div>
          )}
          <div className="viewport-crosshair" aria-hidden="true" />
          <div className="viewport-scale" aria-hidden="true">
            <span />
            <small>VGGT WORLD</small>
          </div>
          <div className="viewport-hint">拖动旋转 · 滚轮缩放 · 右键平移</div>
          {error && (
            <div className="error-banner" role="alert">
              {error}
            </div>
          )}
        </section>
      </main>

      <footer className="status-strip">
        <span>RELATIVE GEOMETRY</span>
        <span>{reconstruction ? `RUN ${reconstruction.run_id}` : "NO ACTIVE RUN"}</span>
        <span>{reconstruction ? `EXTENT ${reconstruction.bounds_size.map((v) => v.toFixed(3)).join(" / ")}` : "0.1.0"}</span>
      </footer>
    </div>
  );
}

export default App;
