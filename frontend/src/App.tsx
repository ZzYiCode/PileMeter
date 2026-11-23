import { useEffect, useState } from "react";

type Health = {
  status: string;
  service: string;
  version: string;
  environment: string;
  scale_status: string;
  capabilities: Record<string, boolean>;
};

const pipeline = [
  ["01", "Input", "拍摄检查与任务管理"],
  ["02", "Reconstruct", "VGGT 相机、深度与点图"],
  ["03", "Point cloud", "置信度过滤与 PLY 导出"],
  ["04", "Measure", "尺度、基底与体积积分"],
];

function App() {
  const [health, setHealth] = useState<Health | null>(null);
  const [apiState, setApiState] = useState<"loading" | "online" | "offline">(
    "loading",
  );

  useEffect(() => {
    const controller = new AbortController();

    fetch("/api/v1/health", { signal: controller.signal })
      .then((response) => {
        if (!response.ok) {
          throw new Error(`API returned ${response.status}`);
        }
        return response.json() as Promise<Health>;
      })
      .then((payload) => {
        setHealth(payload);
        setApiState("online");
      })
      .catch(() => {
        if (!controller.signal.aborted) {
          setApiState("offline");
        }
      });

    return () => controller.abort();
  }, []);

  return (
    <main>
      <nav className="nav">
        <a className="brand" href="/" aria-label="PileMeter home">
          <span className="brand-mark">PM</span>
          <span>
            <strong>PileMeter</strong>
            <small>堆衡</small>
          </span>
        </a>
        <div className={`status status-${apiState}`}>
          <span className="status-dot" />
          API {apiState}
        </div>
      </nav>

      <section className="hero">
        <div className="eyebrow">Multi-view stockpile measurement</div>
        <h1>
          从多视角影像
          <br />
          到可信体积。
        </h1>
        <p className="lede">
          PileMeter 将 VGGT 重建、点云处理、尺度标定和体积积分组织成一条可追踪、
          可验证的测量流水线。
        </p>
        <div className="hero-actions">
          <a className="primary-action" href="/docs">
            查看 API
          </a>
          <span className="metric-note">当前阶段：相对尺度重建骨架</span>
        </div>
      </section>

      <section className="pipeline-section" aria-labelledby="pipeline-title">
        <div className="section-heading">
          <span>Pipeline</span>
          <h2 id="pipeline-title">测量流程</h2>
        </div>
        <div className="pipeline-grid">
          {pipeline.map(([index, name, description]) => (
            <article className="pipeline-card" key={index}>
              <span className="card-index">{index}</span>
              <h3>{name}</h3>
              <p>{description}</p>
              <span className="card-state">
                {index === "01" || index === "03" ? "Scaffolded" : "Planned"}
              </span>
            </article>
          ))}
        </div>
      </section>

      <section className="system-grid">
        <article className="system-card">
          <span className="card-label">Runtime</span>
          <dl>
            <div>
              <dt>Service</dt>
              <dd>{health?.service ?? "Waiting for API"}</dd>
            </div>
            <div>
              <dt>Version</dt>
              <dd>{health?.version ?? "0.1.0"}</dd>
            </div>
            <div>
              <dt>Environment</dt>
              <dd>{health?.environment ?? "local"}</dd>
            </div>
            <div>
              <dt>Scale</dt>
              <dd>{health?.scale_status ?? "relative"}</dd>
            </div>
          </dl>
        </article>

        <article className="system-card constraints">
          <span className="card-label">Engineering boundary</span>
          <h3>先重建，后测量</h3>
          <p>
            VGGT 提供一致的相对几何。只有标尺与地面基准通过质量门控后，结果才可标记为米制体积。
          </p>
          <ul>
            <li>API 与 GPU Worker 分离</li>
            <li>任务产物不可变</li>
            <li>每次运行记录模型与配置版本</li>
          </ul>
        </article>
      </section>

      <footer>
        <span>PileMeter · 堆衡</span>
        <span>RGB multi-view geometry for engineering measurement</span>
      </footer>
    </main>
  );
}

export default App;
