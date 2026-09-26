"use client";

import { forwardRef, memo, useCallback, useEffect, useRef, useState, type ReactNode } from "react";
import Image from "next/image";
import Brand from "./Brand";
import UploadScreen, { type VineyardIdentity } from "./UploadScreen";
import { useMapViewport, type MapHandle } from "./useMapViewport";
import {
  BarChart3,
  Check,
  Expand,
  Leaf,
  Layers3,
  Minimize2,
  Minus,
  Navigation,
  PanelLeftClose,
  PanelLeftOpen,
  Plus,
  Route,
  Rows3,
  ScanLine,
  Upload,
  X,
} from "lucide-react";
import {
  demoVineyard,
  initialLayerVisibility,
  layerDefinitions,
  targetCount,
  type LayerKey,
  type Point,
  type SelectedFeature,
  type TargetMode,
  type VineyardData,
} from "@/lib/vineyard-data";
import { isDemoMode, loadVineyard, uploadAndAnalyze } from "@/lib/vineyard-api";
import { buildDemoRoute, inspectionPoints, wasteBoxes, type DemoRoute } from "@/lib/demo-route";

type RowShape = { id: string; vineyardId: string; x1: number; y1: number; x2: number; y2: number; lengthM: number };
const exitDurationMs = 900;

function usePresence(visible: boolean) {
  const [presence, setPresence] = useState<{ rendered: boolean; motion: "initial" | "enter" | "exit" }>({ rendered: visible, motion: "initial" });

  useEffect(() => {
    let firstFrame = 0;
    let revealFrame = 0;
    let timeout = 0;

    if (visible) {
      // Paint newly mounted panels in their hidden position before revealing them.
      // Keep the current position when reversing an unfinished exit transition.
      setPresence((current) => current.rendered ? current : { rendered: true, motion: "initial" });
      firstFrame = window.requestAnimationFrame(() => {
        revealFrame = window.requestAnimationFrame(() => setPresence({ rendered: true, motion: "enter" }));
      });
    } else {
      setPresence((current) => current.rendered ? { ...current, motion: "exit" } : current);
      timeout = window.setTimeout(() => setPresence({ rendered: false, motion: "initial" }), exitDurationMs);
    }

    return () => {
      window.cancelAnimationFrame(firstFrame);
      window.cancelAnimationFrame(revealFrame);
      window.clearTimeout(timeout);
    };
  }, [visible]);

  return presence;
}

const rowShapes: RowShape[] = [
  ...Array.from({ length: 10 }, (_, i) => ({
    id: `V001_R${String(i + 1).padStart(3, "0")}`,
    vineyardId: "V001",
    x1: 390 + i * 23,
    y1: 86 + i * 7,
    x2: 292 + i * 23,
    y2: 470 + i * 7,
    lengthM: 77.4 + i * 0.7,
  })),
  ...Array.from({ length: 19 }, (_, i) => ({
    id: `V001_R${String(i + 11).padStart(3, "0")}`,
    vineyardId: "V001",
    x1: 570 + i * 20,
    y1: 193 + i * 3,
    x2: 484 + i * 20,
    y2: 610 + i * 3,
    lengthM: i === 3 ? 82.4 : 78.1 + i * 0.52,
  })),
  ...Array.from({ length: 7 }, (_, i) => ({
    id: `V002_R${String(i + 1).padStart(3, "0")}`,
    vineyardId: "V002",
    x1: 957 + i * 20,
    y1: 239 + i * 6,
    x2: 930 + i * 20,
    y2: 575 + i * 7,
    lengthM: 66.2 + i * 0.6,
  })),
];

function formatValue(value: number | null, unit = "") {
  return value === null ? "—" : `${value}${unit}`;
}

function IconAction({
  label,
  children,
  onClick,
  pressed,
  title,
}: {
  label: string;
  children: ReactNode;
  onClick: () => void;
  pressed?: boolean;
  title?: string;
}) {
  return (
    <button
      type="button"
      className="round-action grid place-items-center"
      onClick={onClick}
      aria-label={label}
      aria-pressed={pressed}
      title={title || label}
    >
      {children}
    </button>
  );
}

function PanelCollapse({ label, collapsed, controls, onClick }: { label: string; collapsed: boolean; controls: string; onClick: () => void }) {
  return (
    <button type="button" className="panel-collapse" aria-label={`${collapsed ? "Expand" : "Collapse"} ${label}`} aria-controls={controls} aria-expanded={!collapsed} onClick={onClick}>
      <svg className="panel-toggle-icon" width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" aria-hidden="true">
        <path d="M3 8H13" />
        <path className="panel-toggle-vertical" d="M8 3V13" />
      </svg>
    </button>
  );
}

function PanelHeader({ icon, title, headingId, label, collapsed, controls, onToggle }: { icon: ReactNode; title: string; headingId: string; label: string; collapsed: boolean; controls: string; onToggle: () => void }) {
  return <div className="panel-title">{icon}<h2 id={headingId}>{title}</h2><PanelCollapse label={label} collapsed={collapsed} controls={controls} onClick={onToggle} /></div>;
}

function PanelBody({ id, collapsed, className = "", children }: { id: string; collapsed: boolean; className?: string; children: ReactNode }) {
  return (
    <div className="panel-content" id={id} aria-hidden={collapsed} inert={collapsed}>
      <div className="panel-content-inner"><div className={className}>{children}</div></div>
    </div>
  );
}

function Swatch({ kind }: { kind: string }) {
  return <span className={`swatch swatch-${kind}`} aria-hidden="true" />;
}

type MapCanvasProps = {
  layers: Record<LayerKey, boolean>;
  selected: SelectedFeature | null;
  onSelect: (feature: SelectedFeature) => void;
  placingPoint: "start" | "end" | null;
  onPlacePoint: (point: Point) => void;
  start: Point;
  end: Point;
  route: DemoRoute | null;
  demo: boolean;
  onRest: (zoom: number) => void;
};

const MapCanvas = memo(forwardRef<MapHandle, MapCanvasProps>(function MapCanvas({ layers, selected, onSelect, placingPoint, onPlacePoint, start, end, route, demo, onRest }, ref) {
  const { canvas, camera, handlers } = useMapViewport(ref, placingPoint, onPlacePoint, onRest);
  return (
    <div ref={canvas} className={`map-viewport ${placingPoint ? "is-placing-point" : ""}`} {...handlers}>
      <div ref={camera} className="map-camera">
    <svg
      className="annotation-canvas"
      viewBox="0 0 1440 810"
      preserveAspectRatio="xMidYMid slice"
      role="img"
      aria-label="Demonstration vineyard annotations on a dark map canvas"
    >
      <defs>
        <pattern id="forbidden-hatch" width="8" height="8" patternTransform="rotate(38)" patternUnits="userSpaceOnUse">
          <rect width="8" height="8" fill="#f35a431b" />
          <path d="M0 0 V8" stroke="#ef563d" strokeWidth="2" />
        </pattern>
        <filter id="route-shadow" x="-20%" y="-20%" width="140%" height="140%">
          <feGaussianBlur stdDeviation="2" />
        </filter>
      </defs>

      {!demo && <text x="720" y="405" textAnchor="middle" fill="#c9d7ca" fontSize="19">Map geometry will appear when the API provides georeferenced layers.</text>}

      {demo && (
        <g className="map-layer map-interrows" data-visible={layers.interrows}>
          {rowShapes.filter((_, index) => index % 2 === 0).map((row) => (
            <path
              key={`area-${row.id}`}
              d={`M ${row.x1 + 7} ${row.y1} L ${row.x1 + 21} ${row.y1 + 4} L ${row.x2 + 21} ${row.y2 + 4} L ${row.x2 + 7} ${row.y2} Z`}
              fill="#bfc8c5"
              fillOpacity="0.32"
              stroke="#a5b3ae"
              strokeOpacity="0.55"
              strokeWidth="1"
              onClick={(event) => {
                if (placingPoint) return;
                event.stopPropagation();
                onSelect({ type: "interrow", title: "Inter-row Area", vineyardId: row.vineyardId, rowId: row.id, note: "Mixed cover · demo annotation" });
              }}
              className="map-feature"
            />
          ))}
        </g>
      )}

      {demo && (
        <g className="map-layer map-canopies" data-visible={layers.canopies}>
          {rowShapes.map((row) =>
            Array.from({ length: 18 }, (_, index) => {
              const t = (index + 0.5) / 18;
              const x = row.x1 + (row.x2 - row.x1) * t;
              const y = row.y1 + (row.y2 - row.y1) * t;
              return (
                <ellipse
                  key={`${row.id}-vine-${index}`}
                  cx={x}
                  cy={y}
                  rx="4.5"
                  ry="10.5"
                  transform={`rotate(14 ${x} ${y})`}
                  fill="#248a4540"
                  stroke="#0b9b4e"
                  strokeWidth="1.45"
                  className="map-feature"
                  onClick={(event) => {
                    if (placingPoint) return;
                    event.stopPropagation();
                    onSelect({ type: "canopy", title: "Canopy", vineyardId: row.vineyardId, rowId: row.id, note: `Individual vine ${index + 1} · demo annotation` });
                  }}
                />
              );
            }),
          )}
        </g>
      )}

      {demo && (
        <g className="map-layer map-rows" data-visible={layers.rows}>
          {rowShapes.map((row) => {
            const active = selected?.type === "row" && selected.rowId === row.id;
            return (
              <g key={row.id}>
                <path d={`M${row.x1} ${row.y1} L${row.x2} ${row.y2}`} stroke={active ? "#f1bb24" : "#b3aa21"} strokeWidth={active ? "4" : "2"} strokeDasharray="6 5" />
                <path
                  d={`M${row.x1} ${row.y1} L${row.x2} ${row.y2}`}
                  stroke="transparent"
                  strokeWidth="17"
                  className="map-feature"
                  onClick={(event) => {
                    if (placingPoint) return;
                    event.stopPropagation();
                    onSelect({ type: "row", title: "Selected Row", vineyardId: row.vineyardId, rowId: row.id, lengthM: row.lengthM, structure: row.id === "V001_R014" ? "disrupted" : "regular" });
                  }}
                />
              </g>
            );
          })}
        </g>
      )}

      {demo && (
        <path className="map-layer" data-visible={layers.forbidden} d="M922 131 L1073 171 L1100 283 L1076 345 L1028 340 L1032 259 L882 207 Z" fill="url(#forbidden-hatch)" stroke="#e25039" strokeWidth="2" />
      )}
      {demo && (
        <g className="map-layer" data-visible={layers.passages} stroke="#a4bd1f" strokeWidth="2" strokeDasharray="7 4" fill="#d4ef5b22">
          <path d="M280 480 L317 489 L305 542 L268 532 Z" />
          <path d="M1000 565 L1040 575 L1030 621 L990 609 Z" />
        </g>
      )}
      {demo && (
        <g className="map-layer" data-visible={layers.waste}>
          {wasteBoxes.map((box, index) => (
            <rect
              key={index}
              data-target-id={box.id}
              x={box.x}
              y={box.y}
              width={box.w}
              height={box.h}
              transform={`rotate(${box.r} ${box.x + box.w / 2} ${box.y + box.h / 2})`}
              fill="#f168454a"
              stroke="#e34b32"
              strokeWidth="2"
              className="map-feature"
              onClick={(event) => {
                if (placingPoint) return;
                event.stopPropagation();
                onSelect({ type: "waste", title: "Waste", vineyardId: "V001", note: `Detected item ${index + 1} · demo annotation` });
              }}
            />
          ))}
        </g>
      )}
      {demo && route && (
        <g className="map-layer map-route" data-visible={layers.route} fill="none" strokeLinecap="round" strokeLinejoin="round">
          <polyline points={route.points.map((point) => `${point.x},${point.y}`).join(" ")} stroke="#377efb" strokeWidth="7" strokeOpacity=".17" filter="url(#route-shadow)" />
          <polyline points={route.points.map((point) => `${point.x},${point.y}`).join(" ")} stroke="#438bff" strokeWidth="3.5" />
        </g>
      )}
      {demo && (
        <g className="map-layer" data-visible={layers.inspection}>
          {inspectionPoints.map((point, index) => (
            <circle
              key={point.id}
              data-target-id={point.id}
              cx={point.point.x}
              cy={point.point.y}
              r="7.5"
              fill="#ff9826"
              stroke="white"
              strokeWidth="2.3"
              className="map-feature"
              onClick={(event) => {
                if (placingPoint) return;
                event.stopPropagation();
                onSelect({ type: "inspection", title: "Inspection Point", vineyardId: "V001", rowId: rowShapes[Math.min(index + 10, rowShapes.length - 1)].id, note: `${point.id} · demo annotation` });
              }}
            />
          ))}
        </g>
      )}

      {demo && <g transform={`translate(${start.x} ${start.y})`} className="map-endpoint">
        <circle r="13" fill="#0d1623" stroke="white" strokeWidth="2" />
        <circle r="7" fill="#438bff" stroke="white" strokeWidth="2" />
        <rect x="13" y="-11" width={Math.hypot(start.x - end.x, start.y - end.y) < 1 ? 82 : 55} height="22" rx="11" fill="#263130" stroke="#48544d" />
        <text x={Math.hypot(start.x - end.x, start.y - end.y) < 1 ? 54 : 40} y="4.5" textAnchor="middle" fontSize="12" fill="white" fontWeight="700">{Math.hypot(start.x - end.x, start.y - end.y) < 1 ? "Start / End" : "Start"}</text>
      </g>}
      {demo && Math.hypot(start.x - end.x, start.y - end.y) >= 1 && <g transform={`translate(${end.x} ${end.y})`} className="map-endpoint">
        <circle r="13" fill="#233b27" stroke="white" strokeWidth="2" />
        <circle r="7" fill="#cdf954" stroke="white" strokeWidth="2" />
        <rect x="13" y="-11" width="48" height="22" rx="11" fill="#263130" stroke="#48544d" />
        <text x="37" y="4.5" textAnchor="middle" fontSize="12" fill="white" fontWeight="700">End</text>
      </g>}
    </svg>
      </div>
    </div>
  );
}));

export default function VineyardWorkspace() {
  const [introPhase, setIntroPhase] = useState<"waiting" | "showing" | "logo-leaving" | "screen-leaving" | "done">("waiting");
  const [logoLoaded, setLogoLoaded] = useState(false);
  const [data, setData] = useState<VineyardData>(demoVineyard);
  const [layers, setLayers] = useState(initialLayerVisibility);
  const [selected, setSelected] = useState<SelectedFeature | null>({ type: "row", title: "Selected Row", vineyardId: "V001", rowId: "V001_R014", lengthM: 82.4, structure: "disrupted" });
  const [panelsVisible, setPanelsVisible] = useState(true);
  const [plannerOpen, setPlannerOpen] = useState(false);
  const [collapsedPanels, setCollapsedPanels] = useState({ layers: false, summary: false, selected: false, planner: false, legend: false });
  const [startPoint, setStartPoint] = useState<Point>(demoVineyard.organizerStart);
  const [endPoint, setEndPoint] = useState<Point>(demoVineyard.organizerStart);
  const [endCustomized, setEndCustomized] = useState(false);
  const [placingPoint, setPlacingPoint] = useState<"start" | "end" | null>(null);
  const [targetMode, setTargetMode] = useState<TargetMode>("both");
  const [route, setRoute] = useState<DemoRoute | null>(() => buildDemoRoute(demoVineyard.organizerStart, demoVineyard.organizerStart, "both"));
  const [routeBusy, setRouteBusy] = useState(false);
  const [zoom, setZoom] = useState(1);
  const map = useRef<MapHandle>(null);
  const [fullscreen, setFullscreen] = useState(false);
  const [uploadName, setUploadName] = useState("");
  const [uploadOpen, setUploadOpen] = useState(true);
  const [uploadError, setUploadError] = useState("");
  const [vineyardIdentity, setVineyardIdentity] = useState<VineyardIdentity>({ name: "", id: "" });
  const [processing, setProcessing] = useState(false);
  const [progress, setProgress] = useState(0);
  const [message, setMessage] = useState("");
  const [apiError, setApiError] = useState("");
  const [noticeSnapshot, setNoticeSnapshot] = useState("");
  const uploadTrigger = useRef<HTMLButtonElement>(null);
  const workspace = useRef<HTMLElement>(null);
  const datasetRevision = useRef(0);
  const lastPointKind = useRef<"start" | "end">("start");
  const siteReady = introPhase === "done";
  const sceneReady = introPhase === "screen-leaving" || siteReady;
  const mapReady = sceneReady && !uploadOpen;
  const chromeVisible = siteReady && !uploadOpen && !placingPoint;
  const uploadPresence = usePresence(sceneReady && uploadOpen);
  const uploadActive = siteReady && uploadOpen;
  const panelsActive = panelsVisible && chromeVisible;
  const headerPresence = usePresence(chromeVisible);
  const panelsPresence = usePresence(panelsActive);
  const selectedPresence = usePresence(panelsActive && !plannerOpen);
  const plannerPresence = usePresence(panelsActive && plannerOpen);
  const pickerPresence = usePresence(Boolean(placingPoint) && !uploadOpen);
  const toastPresence = usePresence(Boolean(message || apiError) && !uploadOpen);
  const hintPresence = usePresence(!panelsVisible && chromeVisible);

  useEffect(() => {
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
      setIntroPhase("done");
      return;
    }
    if (!logoLoaded) return;

    let firstFrame = 0;
    let revealFrame = 0;
    let leaveLogo = 0;
    let revealSite = 0;
    let finish = 0;
    firstFrame = window.requestAnimationFrame(() => {
      revealFrame = window.requestAnimationFrame(() => {
        setIntroPhase("showing");
        leaveLogo = window.setTimeout(() => setIntroPhase("logo-leaving"), 2300);
        revealSite = window.setTimeout(() => setIntroPhase("screen-leaving"), 3500);
        finish = window.setTimeout(() => setIntroPhase("done"), 4600);
      });
    });
    return () => {
      window.cancelAnimationFrame(firstFrame);
      window.cancelAnimationFrame(revealFrame);
      window.clearTimeout(leaveLogo);
      window.clearTimeout(revealSite);
      window.clearTimeout(finish);
    };
  }, [logoLoaded]);

  function togglePanel(panel: keyof typeof collapsedPanels) {
    setCollapsedPanels((current) => ({ ...current, [panel]: !current[panel] }));
  }

  useEffect(() => {
    if (message || apiError) setNoticeSnapshot(apiError || message);
  }, [message, apiError]);

  useEffect(() => {
    let alive = true;
    const revision = datasetRevision.current;
    loadVineyard()
      .then((payload) => {
        if (!alive || datasetRevision.current !== revision) return;
        setData(payload);
        if (payload.source === "api") {
          setSelected(null);
          setStartPoint(payload.organizerStart);
          setEndPoint(payload.organizerStart);
          setEndCustomized(false);
          setRoute(null);
        }
      })
      .catch((error: unknown) => { if (alive && datasetRevision.current === revision) setApiError(error instanceof Error ? error.message : "Data could not be loaded."); });
    return () => { alive = false; };
  }, []);

  useEffect(() => {
    const onChange = () => setFullscreen(Boolean(document.fullscreenElement));
    document.addEventListener("fullscreenchange", onChange);
    return () => document.removeEventListener("fullscreenchange", onChange);
  }, []);

  useEffect(() => {
    if (!message) return;
    const timeout = window.setTimeout(() => setMessage(""), 4500);
    return () => window.clearTimeout(timeout);
  }, [message]);

  useEffect(() => {
    if (!placingPoint) return;
    const cancelOnEscape = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        setPlacingPoint(null);
        setPlannerOpen(true);
      }
    };
    document.addEventListener("keydown", cancelOnEscape);
    return () => document.removeEventListener("keydown", cancelOnEscape);
  }, [placingPoint]);

  const visibleTargets = targetCount(data, targetMode);
  const routeLengthKm = route ? +(route.lengthM / 1000).toFixed(1) : null;

  function toggleLayer(key: LayerKey) {
    setLayers((current) => ({ ...current, [key]: !current[key] }));
  }

  async function toggleFullscreen() {
    try {
      if (document.fullscreenElement) await document.exitFullscreen();
      else await workspace.current?.requestFullscreen();
    } catch {
      setMessage("Full screen is unavailable in this browser.");
    }
  }

  const closeUpload = useCallback(() => {
    if (!processing) setUploadOpen(false);
  }, [processing]);

  useEffect(() => {
    if (uploadOpen || !siteReady) return;
    const timeout = window.setTimeout(() => uploadTrigger.current?.focus({ preventScroll: true }), exitDurationMs);
    return () => window.clearTimeout(timeout);
  }, [uploadOpen, siteReady]);

  function openUpload() {
    setUploadError("");
    setMessage("");
    setPlacingPoint(null);
    setUploadOpen(true);
  }

  async function handleUpload(file: File, identity: VineyardIdentity) {
    if (processing) return;
    if (!/\.tiff?$/i.test(file.name)) {
      setUploadError("Choose a GeoTIFF file (.tif or .tiff).");
      return;
    }
    if (file.size === 0) {
      setUploadError("This file is empty. Choose another GeoTIFF map.");
      return;
    }
    datasetRevision.current += 1;
    setApiError("");
    setUploadName(file.name);
    setUploadError("");
    setMessage("");
    setProgress(0);
    setProcessing(true);
    try {
      const result = await uploadAndAnalyze(file, setProgress, identity);
      setData({ ...result, name: identity.name });
      setVineyardIdentity(identity);
      map.current?.reset();
      setZoom(1);
      if (result.source === "api") {
        setSelected(null);
        setStartPoint(result.organizerStart);
        setEndPoint(result.organizerStart);
        setEndCustomized(false);
        setRoute(null);
      }
      setUploadOpen(false);
    } catch (error) {
      setUploadError(error instanceof Error ? error.message : "The upload could not be processed. Try again.");
    } finally {
      setProcessing(false);
    }
  }

  function beginPlacingPoint(kind: "start" | "end") {
    lastPointKind.current = kind;
    setPlacingPoint(kind);
    setPlannerOpen(false);
    setMessage("");
  }

  const placePoint = useCallback((point: Point) => {
    if (placingPoint === "start") {
      setStartPoint(point);
      if (!endCustomized) setEndPoint(point);
    } else if (placingPoint === "end") {
      setEndPoint(point);
      setEndCustomized(true);
    }
    setRoute(null);
    setPlacingPoint(null);
    setPlannerOpen(true);
    setMessage(placingPoint === "start" ? "Starting point selected. Build the route to update it." : "End point selected. Build the route to update it.");
  }, [placingPoint, endCustomized]);

  function changeTargetMode(mode: TargetMode) {
    setTargetMode(mode);
    setRoute(null);
  }

  function handleBuildRoute() {
    if (data.source === "api") {
      setMessage("Route computation is waiting for the backend route endpoint.");
      return;
    }
    setRouteBusy(true);
    setMessage("");
    window.setTimeout(() => {
      setRouteBusy(false);
      const result = buildDemoRoute(startPoint, endPoint, targetMode);
      if (!result) {
        setMessage("Choose start and end points outside the forbidden zone.");
        return;
      }
      setRoute(result);
      setLayers((current) => ({ ...current, route: true }));
      setMessage(`Demo route visits all ${result.targetIds.length} selected targets. Real geospatial routing requires the processing API.`);
    }, 180);
  }

  const selectedRows = selected?.type === "row";

  return (
    <main className="workspace" ref={workspace}>
      <div className={`app-stage ${mapReady ? "is-revealing" : ""}`} aria-hidden={!siteReady || uploadOpen} inert={!siteReady || uploadOpen}>
      <MapCanvas
        ref={map}
        layers={layers}
        selected={selected}
        onSelect={setSelected}
        placingPoint={placingPoint}
        onPlacePoint={placePoint}
        start={startPoint}
        end={endPoint}
        route={route}
        demo={data.source === "demo"}
        onRest={setZoom}
      />

      {headerPresence.rendered && <header className="topbar absolute inset-x-0 top-0 z-30 flex items-center justify-between" data-motion={headerPresence.motion} aria-hidden={!chromeVisible} inert={!chromeVisible}>
        <Brand />
        <div className="top-actions flex items-center gap-3">
          <IconAction label={panelsVisible ? "Hide panels" : "Show panels"} onClick={() => setPanelsVisible((value) => !value)} pressed={!panelsVisible}>
            {panelsVisible ? <PanelLeftClose size={23} strokeWidth={1.8} /> : <PanelLeftOpen size={23} strokeWidth={1.8} />}
          </IconAction>
          <IconAction label={fullscreen ? "Exit full screen" : "Enter full screen"} onClick={toggleFullscreen} pressed={fullscreen}>
            {fullscreen ? <Minimize2 size={22} strokeWidth={1.9} /> : <Expand size={22} strokeWidth={1.9} />}
          </IconAction>
          <button ref={uploadTrigger} type="button" className="upload-button flex items-center justify-center gap-3" aria-label="Upload map" onClick={openUpload}>
            <Upload size={22} strokeWidth={1.9} /> <span>Upload Map</span>
          </button>
        </div>
      </header>}

      {panelsPresence.rendered && (
        <>
          <section className="identity-block" aria-label="Vineyard information" data-motion={panelsPresence.motion} aria-hidden={!panelsActive} inert={!panelsActive}>
            <h1>{data.name}</h1>
            <div className="identity-meta flex items-center gap-2"><p>Aerial inspection <span>·</span> {data.crs}{vineyardIdentity.id && <><span>·</span>{vineyardIdentity.id}</>}</p>{data.source === "demo" && <div className="demo-tag">DEMO DATA</div>}</div>
            {uploadName && <p className="uploaded-name" title={uploadName}>{uploadName}</p>}
          </section>

          <section className="panel layers-panel" aria-labelledby="layers-heading" data-motion={panelsPresence.motion} data-collapsed={collapsedPanels.layers} aria-hidden={!panelsActive} inert={!panelsActive}>
            <PanelHeader icon={<Layers3 size={22} fill="white" strokeWidth={1.6} />} title="Layers" headingId="layers-heading" label="layers" collapsed={collapsedPanels.layers} controls="layers-content" onToggle={() => togglePanel("layers")} />
            <PanelBody id="layers-content" collapsed={collapsedPanels.layers} className="layer-list">
              {layerDefinitions.map(({ key, label, swatch }) => (
                <label key={key} className={`layer-row flex items-center ${layers[key] ? "" : "layer-disabled"}`}>
                  <input type="checkbox" checked={layers[key]} onChange={() => toggleLayer(key)} className="layer-native-check" />
                  <span className={`layer-check layer-check-${key}`} aria-hidden="true">{layers[key] && <Check size={14} strokeWidth={2.7} />}</span>
                  <span className="layer-label">{label}</span>
                  <Swatch kind={swatch} />
                </label>
              ))}
            </PanelBody>
          </section>

          <aside className="right-panels" aria-label="Vineyard panels" aria-hidden={!panelsActive} inert={!panelsActive}>
          <section className="panel summary-panel" aria-labelledby="summary-heading" data-motion={panelsPresence.motion} data-collapsed={collapsedPanels.summary} aria-hidden={!panelsActive} inert={!panelsActive}>
            <PanelHeader icon={<BarChart3 size={22} fill="white" strokeWidth={1.5} />} title="Vineyard Summary" headingId="summary-heading" label="vineyard summary" collapsed={collapsedPanels.summary} controls="summary-content" onToggle={() => togglePanel("summary")} />
            <PanelBody id="summary-content" collapsed={collapsedPanels.summary} className="summary-grid grid grid-cols-2 gap-2">
              <SummaryMetric icon={<Layers3 />} label="Blocks" value={formatValue(data.summary.blocks)} />
              <SummaryMetric icon={<Rows3 />} label="Rows" value={formatValue(data.summary.rows)} />
              <SummaryMetric icon={<Leaf />} label="Canopy Area" value={formatValue(data.summary.canopyHa, " ha")} />
              <SummaryMetric icon={<ScanLine />} label="Inter-row Area" value={formatValue(data.summary.interrowHa, " ha")} />
              <SummaryMetric icon={<Route />} label="Total Row Length" value={formatValue(data.summary.totalRowKm, " km")} compact />
              <SummaryMetric icon={<Route />} label="Route" value={formatValue(routeLengthKm, " km")} />
            </PanelBody>
          </section>

          {selectedPresence.rendered && <section className="panel selected-panel" aria-labelledby="selected-heading" data-motion={selectedPresence.motion} data-collapsed={collapsedPanels.selected} aria-hidden={!(panelsActive && !plannerOpen)} inert={!(panelsActive && !plannerOpen)}>
            <PanelHeader icon={<Leaf size={22} fill="white" strokeWidth={1.3} />} title={selected?.title || "Selected Feature"} headingId="selected-heading" label="selected feature" collapsed={collapsedPanels.selected} controls="selected-content" onToggle={() => togglePanel("selected")} />
            <PanelBody id="selected-content" collapsed={collapsedPanels.selected}>
            {selected ? (
              <div className="detail-list">
                <Detail label="Vineyard ID" value={selected.vineyardId} />
                {selected.rowId && <Detail label="Row ID" value={selected.rowId} />}
                {selected.lengthM != null && <Detail label="Length" value={`${selected.lengthM.toFixed(1)} m`} />}
                {selected.structure && <Detail label="Structure" value={selected.structure === "disrupted" ? "Disrupted" : selected.structure} alert={selected.structure === "disrupted"} />}
                {!selectedRows && <Detail label="Details" value={selected.note || "No attributes available"} />}
              </div>
            ) : <p className="empty-selection">Click an annotation to inspect it.</p>}
            </PanelBody>
          </section>}

          </aside>

          {plannerPresence.rendered && (
            <section className="panel route-planner" id="route-planner" aria-labelledby="planner-heading" data-motion={plannerPresence.motion} data-collapsed={collapsedPanels.planner} aria-hidden={!(panelsActive && plannerOpen)} inert={!(panelsActive && plannerOpen)}>
              <PanelHeader icon={<Route size={22} strokeWidth={1.6} />} title="Route Planner" headingId="planner-heading" label="route planner" collapsed={collapsedPanels.planner} controls="planner-content" onToggle={() => togglePanel("planner")} />
              <PanelBody id="planner-content" collapsed={collapsedPanels.planner} className="planner-body">
                  <p className="field-label">Route Endpoints</p>
                  <div className="segmented two flex gap-1">
                    <button type="button" className="choice endpoint-choice flex items-center justify-center gap-2" onClick={() => beginPlacingPoint("start")}>Select Starting Point</button>
                    <button type="button" className="choice endpoint-choice flex items-center justify-center gap-2" title="End follows start until you select it" onClick={() => beginPlacingPoint("end")}>Select End Point</button>
                  </div>
                  <p className="field-label targets-label">Route Targets</p>
                  <div className="segmented three flex gap-1">
                    <Choice active={targetMode === "inspection"} onClick={() => changeTargetMode("inspection")} label="Inspection" />
                    <Choice active={targetMode === "waste"} onClick={() => changeTargetMode("waste")} label="Waste" />
                    <Choice active={targetMode === "both"} onClick={() => changeTargetMode("both")} label="Both" />
                  </div>
                  <button type="button" className="build-button flex items-center justify-center gap-3" onClick={handleBuildRoute} disabled={routeBusy}>
                    <Route size={24} strokeWidth={1.8} />{routeBusy ? "Building Route…" : "Build Optimal Route"}
                  </button>
                  <p className="route-caption">{route ? route.targetIds.length : visibleTargets} targets <span>·</span> {route ? (route.returnsToStart ? "Returns to start" : "Ends at selected point") : "Ready to build"}</p>
              </PanelBody>
            </section>
          )}

          <div className="map-controls flex flex-col gap-1" aria-label="Map controls" data-motion={panelsPresence.motion} aria-hidden={!panelsActive} inert={!panelsActive}>
            <IconAction label="Zoom in" onClick={() => map.current?.zoomBy(0.2)}><Plus size={25} /></IconAction>
            <IconAction label="Zoom out" onClick={() => map.current?.zoomBy(-0.2)}><Minus size={25} /></IconAction>
            <IconAction label="Go to start point" title="Go to start point" onClick={() => map.current?.flyTo(startPoint, 1.5)}><Navigation size={22} fill="white" /></IconAction>
          </div>

          <section className="legend panel flex items-center gap-4" aria-label="Map legend" data-motion={panelsPresence.motion} data-collapsed={collapsedPanels.legend} aria-hidden={!panelsActive} inert={!panelsActive}>
            <span className="legend-collapsed-label" aria-hidden={!collapsedPanels.legend}>Legend</span>
            <div className="legend-content flex items-center" id="legend-content" aria-hidden={collapsedPanels.legend} inert={collapsedPanels.legend}>
            {layerDefinitions.slice(0, 6).map((layer) => (
              <div key={layer.key} className="legend-item flex items-center gap-2" data-visible={layers[layer.key]} aria-hidden={!layers[layer.key]}><Swatch kind={layer.swatch} /><span>{layer.key === "interrows" ? "Inter-row Area" : layer.key === "inspection" ? "Inspection Point" : layer.key === "route" ? "Route" : layer.key === "canopies" ? "Canopy" : layer.key === "rows" ? "Row" : layer.label}</span></div>
            ))}
            </div>
            <PanelCollapse label="map legend" collapsed={collapsedPanels.legend} controls="legend-content" onClick={() => togglePanel("legend")} />
          </section>
          <button type="button" className="plan-button flex items-center justify-center gap-3" data-motion={panelsPresence.motion} aria-hidden={!panelsActive} inert={!panelsActive} aria-expanded={plannerOpen} aria-controls="route-planner" onClick={() => setPlannerOpen((value) => !value)}>
            <Route size={24} strokeWidth={1.8} />Plan Route
          </button>
          <div className="scale" aria-label={`Map scale approximately ${Math.round(200 / zoom)} metres`} data-motion={panelsPresence.motion} aria-hidden={!panelsActive}>
            <div className="scale-labels"><span>0</span><span>{Math.round(50 / zoom)}</span><span>{Math.round(100 / zoom)}</span><span>{Math.round(200 / zoom)} m</span></div>
            <div className="scale-rule"><i /><i /><i /><i /></div>
          </div>
        </>
      )}

      {pickerPresence.rendered && <div className="point-picker" role="status" data-motion={pickerPresence.motion} aria-hidden={!placingPoint} inert={!placingPoint}><span>Click anywhere on the map to set the {(placingPoint || lastPointKind.current) === "start" ? "starting" : "end"} point</span><button type="button" onClick={() => { setPlacingPoint(null); setPlannerOpen(true); }}>Cancel</button></div>}

      {toastPresence.rendered && (
        <div className="toast" role="status" aria-live="polite" data-motion={toastPresence.motion} aria-hidden={!(processing || message || apiError)} inert={!(processing || message || apiError)}>
          {processing ? (
            <><div className="toast-top"><span>Processing {uploadName}</span><strong>{progress}%</strong></div><div className="progress-track"><div style={{ width: `${progress}%` }} /></div>{isDemoMode() && <small>Preview mode · no GeoTIFF analysis</small>}</>
          ) : (
            <><span>{apiError || message || noticeSnapshot}</span><button type="button" onClick={() => { setMessage(""); setApiError(""); }} aria-label="Dismiss message"><X size={16} /></button></>
          )}
        </div>
      )}

      {hintPresence.rendered && <div className="hidden-panels-hint" data-motion={hintPresence.motion} aria-hidden={panelsVisible}>Panels hidden · use the top control to restore</div>}
      </div>
      {uploadPresence.rendered && <UploadScreen active={uploadActive} motion={uploadPresence.motion} busy={processing} progress={progress} filename={uploadName} error={uploadError} demo={isDemoMode()} identity={vineyardIdentity} onUpload={handleUpload} onClose={closeUpload} />}
      {introPhase !== "done" && (
        <div className="intro-screen" data-phase={introPhase} role="status" aria-label="Loading TRASHOPOLY">
          <Image className="intro-logo" src="/brand/trashopoly-logo.png" alt="TRASHOPOLY — Smart Vineyard Routing" width={2021} height={778} loading="eager" fetchPriority="high" unoptimized onLoad={() => setLogoLoaded(true)} onError={() => setIntroPhase("done")} />
        </div>
      )}
    </main>
  );
}

function Choice({ active, onClick, label }: { active: boolean; onClick: () => void; label: string }) {
  return <button type="button" className={`choice flex items-center justify-center gap-2 ${active ? "is-active" : ""}`} onClick={onClick} aria-pressed={active}><span className="choice-radio" /><span>{label}</span></button>;
}

function SummaryMetric({ icon, label, value, compact = false }: { icon: ReactNode; label: string; value: string; compact?: boolean }) {
  return <div className={`metric flex items-center gap-3 ${compact ? "metric-compact" : ""}`}><span className="metric-icon">{icon}</span><div><span className="metric-label">{label}</span><strong>{value}</strong></div></div>;
}

function Detail({ label, value, alert }: { label: string; value: string; alert?: boolean }) {
  return <div className="detail-row flex items-center justify-between gap-2"><span>{label}</span><strong className={alert ? "alert-value" : ""}>{value}{alert && <span className="alert-symbol">▲</span>}</strong></div>;
}
