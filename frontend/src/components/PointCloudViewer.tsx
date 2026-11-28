import { useEffect, useRef, useState } from "react";
import * as THREE from "three";
import { OrbitControls } from "three/examples/jsm/controls/OrbitControls.js";
import { PLYLoader } from "three/examples/jsm/loaders/PLYLoader.js";

type ColorMode = "rgb" | "height";

type PointCloudViewerProps = {
  pointcloudUrl: string;
  camerasUrl: string;
  pointSize: number;
  colorMode: ColorMode;
  showCameras: boolean;
  resetSignal: number;
  onLoaded: (pointCount: number) => void;
  onError: (message: string) => void;
};

type LoadedCloud = {
  geometry: THREE.BufferGeometry;
  material: THREE.PointsMaterial;
  points: THREE.Points;
  baseSize: number;
  originalColors: Float32Array;
  sceneScale: number;
};

function heightColors(geometry: THREE.BufferGeometry): Float32Array {
  const positions = geometry.getAttribute("position");
  geometry.computeBoundingBox();
  const bounds = geometry.boundingBox;
  if (!bounds) {
    return new Float32Array(positions.count * 3);
  }

  const low = new THREE.Color("#153d3a");
  const middle = new THREE.Color("#49a294");
  const high = new THREE.Color("#f2a65a");
  const colors = new Float32Array(positions.count * 3);
  const range = Math.max(bounds.max.z - bounds.min.z, 1e-6);

  for (let index = 0; index < positions.count; index += 1) {
    const ratio = (positions.getZ(index) - bounds.min.z) / range;
    const color =
      ratio < 0.5
        ? low.clone().lerp(middle, ratio * 2)
        : middle.clone().lerp(high, (ratio - 0.5) * 2);
    colors[index * 3] = color.r;
    colors[index * 3 + 1] = color.g;
    colors[index * 3 + 2] = color.b;
  }
  return colors;
}

export default function PointCloudViewer({
  pointcloudUrl,
  camerasUrl,
  pointSize,
  colorMode,
  showCameras,
  resetSignal,
  onLoaded,
  onError,
}: PointCloudViewerProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const sceneRef = useRef<THREE.Scene | null>(null);
  const cameraRef = useRef<THREE.PerspectiveCamera | null>(null);
  const rendererRef = useRef<THREE.WebGLRenderer | null>(null);
  const controlsRef = useRef<OrbitControls | null>(null);
  const cloudRef = useRef<LoadedCloud | null>(null);
  const cameraGroupRef = useRef<THREE.Group | null>(null);
  const resetViewRef = useRef<() => void>(() => undefined);
  const [loadVersion, setLoadVersion] = useState(0);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) {
      return;
    }

    const scene = new THREE.Scene();
    scene.background = new THREE.Color("#0b1513");
    const camera = new THREE.PerspectiveCamera(45, 1, 0.001, 10000);
    camera.position.set(2, 1.5, 2);

    let renderer: THREE.WebGLRenderer;
    try {
      renderer = new THREE.WebGLRenderer({ antialias: true, powerPreference: "high-performance" });
    } catch {
      onError("当前浏览器无法创建 WebGL 画布。请启用硬件加速后重试。");
      return;
    }
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.outputColorSpace = THREE.SRGBColorSpace;
    container.appendChild(renderer.domElement);

    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.075;
    controls.screenSpacePanning = true;

    sceneRef.current = scene;
    cameraRef.current = camera;
    rendererRef.current = renderer;
    controlsRef.current = controls;

    const resize = () => {
      const width = container.clientWidth;
      const height = container.clientHeight;
      if (width === 0 || height === 0) {
        return;
      }
      renderer.setSize(width, height, false);
      camera.aspect = width / height;
      camera.updateProjectionMatrix();
    };
    const observer = new ResizeObserver(resize);
    observer.observe(container);
    resize();

    let animationFrame = 0;
    const render = () => {
      controls.update();
      renderer.render(scene, camera);
      animationFrame = requestAnimationFrame(render);
    };
    render();

    return () => {
      cancelAnimationFrame(animationFrame);
      observer.disconnect();
      controls.dispose();
      cloudRef.current?.geometry.dispose();
      cloudRef.current?.material.dispose();
      renderer.dispose();
      renderer.domElement.remove();
      sceneRef.current = null;
      cameraRef.current = null;
      rendererRef.current = null;
      controlsRef.current = null;
      cloudRef.current = null;
      cameraGroupRef.current = null;
    };
  }, [onError]);

  useEffect(() => {
    const scene = sceneRef.current;
    const camera = cameraRef.current;
    const controls = controlsRef.current;
    if (!scene || !camera || !controls || !pointcloudUrl) {
      return;
    }

    let cancelled = false;
    fetch(pointcloudUrl)
      .then((response) => {
        if (!response.ok) {
          throw new Error(`点云请求失败：HTTP ${response.status}`);
        }
        return response.arrayBuffer();
      })
      .then((buffer) => {
        if (cancelled) {
          return;
        }
        const geometry = new PLYLoader().parse(buffer);
        geometry.computeBoundingBox();
        const positions = geometry.getAttribute("position");
        const bounds = geometry.boundingBox;
        if (!positions || !bounds) {
          throw new Error("PLY 文件不含有效的顶点坐标。");
        }

        if (cloudRef.current) {
          scene.remove(cloudRef.current.points);
          cloudRef.current.geometry.dispose();
          cloudRef.current.material.dispose();
        }

        let originalColor = geometry.getAttribute("color") as THREE.BufferAttribute | undefined;
        if (!originalColor) {
          const fallback = new Float32Array(positions.count * 3).fill(0.72);
          originalColor = new THREE.BufferAttribute(fallback, 3);
          geometry.setAttribute("color", originalColor);
        }
        geometry.setAttribute("color", new THREE.BufferAttribute(originalColor.array.slice(), 3));

        const size = bounds.getSize(new THREE.Vector3());
        const sceneScale = Math.max(size.x, size.y, size.z, 1e-6);
        const material = new THREE.PointsMaterial({
          size: sceneScale * 0.0016,
          sizeAttenuation: true,
          vertexColors: true,
        });
        const points = new THREE.Points(geometry, material);
        scene.add(points);

        const loaded: LoadedCloud = {
          geometry,
          material,
          points,
          baseSize: material.size,
          originalColors: Float32Array.from(originalColor.array),
          sceneScale,
        };
        cloudRef.current = loaded;

        resetViewRef.current = () => {
          const center = bounds.getCenter(new THREE.Vector3());
          camera.near = Math.max(sceneScale / 2000, 0.000001);
          camera.far = sceneScale * 100;
          camera.position.set(
            center.x + sceneScale * 1.15,
            center.y + sceneScale * 0.8,
            center.z + sceneScale * 1.15,
          );
          controls.target.copy(center);
          camera.updateProjectionMatrix();
          controls.update();
        };
        resetViewRef.current();
        onLoaded(positions.count);
        setLoadVersion((value) => value + 1);
      })
      .catch((error: unknown) => {
        if (!cancelled) {
          onError(error instanceof Error ? error.message : "点云加载失败。");
        }
      });

    return () => {
      cancelled = true;
    };
  }, [onError, onLoaded, pointcloudUrl]);

  useEffect(() => {
    const cloud = cloudRef.current;
    if (!cloud) {
      return;
    }
    const colors =
      colorMode === "height"
        ? heightColors(cloud.geometry)
        : cloud.originalColors;
    cloud.geometry.setAttribute("color", new THREE.BufferAttribute(colors.slice(), 3));
    cloud.material.vertexColors = true;
    cloud.material.needsUpdate = true;
  }, [colorMode, loadVersion]);

  useEffect(() => {
    const cloud = cloudRef.current;
    if (cloud) {
      cloud.material.size = cloud.baseSize * pointSize;
      cloud.material.needsUpdate = true;
    }
  }, [pointSize, loadVersion]);

  useEffect(() => {
    if (resetSignal > 0) {
      resetViewRef.current();
    }
  }, [resetSignal]);

  useEffect(() => {
    const scene = sceneRef.current;
    const cloud = cloudRef.current;
    if (!scene || !cloud || !camerasUrl || !showCameras) {
      if (cameraGroupRef.current) {
        cameraGroupRef.current.visible = false;
      }
      return;
    }

    let cancelled = false;
    fetch(camerasUrl)
      .then((response) => response.json())
      .then((payload: { camera_centers: number[][] }) => {
        if (cancelled) {
          return;
        }
        if (cameraGroupRef.current) {
          scene.remove(cameraGroupRef.current);
        }
        const group = new THREE.Group();
        const centers = payload.camera_centers.map(
          ([x, y, z]) => new THREE.Vector3(x, y, z),
        );
        if (centers.length > 0) {
          const markerGeometry = new THREE.BufferGeometry().setFromPoints(centers);
          const markerMaterial = new THREE.PointsMaterial({
            color: "#ef7b43",
            size: cloud.sceneScale * 0.012,
            sizeAttenuation: true,
          });
          group.add(new THREE.Points(markerGeometry, markerMaterial));

          if (centers.length > 1) {
            const lineGeometry = new THREE.BufferGeometry().setFromPoints(centers);
            const lineMaterial = new THREE.LineDashedMaterial({
              color: "#ef7b43",
              dashSize: cloud.sceneScale * 0.015,
              gapSize: cloud.sceneScale * 0.01,
              transparent: true,
              opacity: 0.72,
            });
            const line = new THREE.Line(lineGeometry, lineMaterial);
            line.computeLineDistances();
            group.add(line);
          }
        }
        cameraGroupRef.current = group;
        scene.add(group);
      })
      .catch(() => {
        if (!cancelled) {
          onError("相机轨迹加载失败。");
        }
      });

    return () => {
      cancelled = true;
    };
  }, [camerasUrl, loadVersion, onError, showCameras]);

  return <div ref={containerRef} className="pointcloud-viewer" aria-label="VGGT 点云视口" />;
}
