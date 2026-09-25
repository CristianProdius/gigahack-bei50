"use client";

import { useEffect, useRef, useState, type ChangeEvent, type MouseEvent, type ReactNode } from "react";
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

function Swatch({ kind }: { kind: string }) {
  return <span className={`swatch swatch-${kind}`} aria-hidden="true" />;
}

function MapCanvas({
  layers,
  selected,
  onSelect,
  placingPoint,
  onPlacePoint,
  start,
  end,
  route,
  demo,
  zoom,
  center,
}: {
  layers: Record<LayerKey, boolean>;
  selected: SelectedFeature | null;
  onSelect: (feature: SelectedFeature) => void;
  placingPoint: "start" | "end" | null;
  onPlacePoint: (point: Point) => void;
  start: Point;
  end: Point;
  route: DemoRoute | null;
  demo: boolean;
  zoom: number;
  center: Point;
}) {
  const width = 1440 / zoom;
  const height = 810 / zoom;
  const viewBox = `${center.x - width / 2} ${center.y - height / 2} ${width} ${height}`;
  function handleMapClick(event: MouseEvent<SVGSVGElement>) {
    if (!placingPoint) return;
    const svg = event.currentTarget;
    const matrix = svg.getScreenCTM();
    if (!matrix) return;
    const point = new DOMPoint(event.clientX, event.clientY).matrixTransform(matrix.inverse());
    onPlacePoint({ x: Math.round(point.x), y: Math.round(point.y) });
  }

  return (
    <svg
      className={`annotation-canvas ${placingPoint ? "is-placing-point" : ""}`}
      viewBox={viewBox}
      preserveAspectRatio="xMidYMid slice"
      role="img"
      aria-label="Demonstration vineyard annotations on a white map canvas"
      onClick={handleMapClick}
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

      {!demo && <text x="720" y="405" textAnchor="middle" fill="#69766f" fontSize="19">Map geometry will appear when the API provides georeferenced layers.</text>}

      {demo && layers.interrows && (
        <g className="map-interrows">
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

      {demo && layers.canopies && (
        <g className="map-canopies">
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

      {demo && layers.rows && (
        <g className="map-rows">
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

      {demo && layers.forbidden && (
        <path d="M922 131 L1073 171 L1100 283 L1076 345 L1028 340 L1032 259 L882 207 Z" fill="url(#forbidden-hatch)" stroke="#e25039" strokeWidth="2" />
      )}
      {demo && layers.passages && (
        <g stroke="#a4bd1f" strokeWidth="2" strokeDasharray="7 4" fill="#d4ef5b22">
          <path d="M280 480 L317 489 L305 542 L268 532 Z" />
          <path d="M1000 565 L1040 575 L1030 621 L990 609 Z" />
        </g>
      )}
      {demo && layers.waste && (
        <g>
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
      {demo && layers.route && route && (
        <g fill="none" strokeLinecap="round" strokeLinejoin="round">
          <polyline points={route.points.map((point) => `${point.x},${point.y}`).join(" ")} stroke="#377efb" strokeWidth="7" strokeOpacity=".17" filter="url(#route-shadow)" />
          <polyline points={route.points.map((point) => `${point.x},${point.y}`).join(" ")} stroke="#438bff" strokeWidth="3.5" />
        </g>
      )}
      {demo && layers.inspection && (
        <g>
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
  );
}

export default function VineyardWorkspace() {
  const [data, setData] = useState<VineyardData>(demoVineyard);
  const [layers, setLayers] = useState(initialLayerVisibility);
  const [selected, setSelected] = useState<SelectedFeature | null>({ type: "row", title: "Selected Row", vineyardId: "V001", rowId: "V001_R014", lengthM: 82.4, structure: "disrupted" });
  const [panelsVisible, setPanelsVisible] = useState(true);
  const [plannerOpen, setPlannerOpen] = useState(false);
  const [startPoint, setStartPoint] = useState<Point>(demoVineyard.organizerStart);
  const [endPoint, setEndPoint] = useState<Point>(demoVineyard.organizerStart);
  const [endCustomized, setEndCustomized] = useState(false);
  const [placingPoint, setPlacingPoint] = useState<"start" | "end" | null>(null);
  const [targetMode, setTargetMode] = useState<TargetMode>("both");
  const [route, setRoute] = useState<DemoRoute | null>(() => buildDemoRoute(demoVineyard.organizerStart, demoVineyard.organizerStart, "both"));
  const [routeBusy, setRouteBusy] = useState(false);
  const [zoom, setZoom] = useState(1);
  const [center, setCenter] = useState<Point>({ x: 720, y: 405 });
  const [fullscreen, setFullscreen] = useState(false);
  const [uploadName, setUploadName] = useState("");
  const [processing, setProcessing] = useState(false);
  const [progress, setProgress] = useState(0);
  const [message, setMessage] = useState("");
  const [apiError, setApiError] = useState("");
  const fileInput = useRef<HTMLInputElement>(null);
  const workspace = useRef<HTMLElement>(null);

  useEffect(() => {
    let alive = true;
    loadVineyard()
      .then((payload) => {
        if (!alive) return;
        setData(payload);
        if (payload.source === "api") {
          setSelected(null);
          setStartPoint(payload.organizerStart);
          setEndPoint(payload.organizerStart);
          setEndCustomized(false);
          setRoute(null);
        }
      })
      .catch((error: unknown) => { if (alive) setApiError(error instanceof Error ? error.message : "Data could not be loaded."); });
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

  async function handleFile(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (!file) return;
    event.target.value = "";
    if (!/\.tiff?$/i.test(file.name)) {
      setMessage("Choose a GeoTIFF file (.tif or .tiff).");
      return;
    }
    setUploadName(file.name);
    setMessage("");
    setProgress(0);
    setProcessing(true);
    try {
      const result = await uploadAndAnalyze(file, setProgress);
      setData(result);
      if (result.source === "api") {
        setSelected(null);
        setStartPoint(result.organizerStart);
        setEndPoint(result.organizerStart);
        setEndCustomized(false);
        setRoute(null);
      }
      setMessage(isDemoMode() ? "UI preview complete. This file has not been analyzed; connect the processing API for real results." : "Analysis complete.");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "The upload could not be processed.");
    } finally {
      setProcessing(false);
    }
  }

  function beginPlacingPoint(kind: "start" | "end") {
    setPlacingPoint(kind);
    setPlannerOpen(false);
    setMessage("");
  }

  function placePoint(point: Point) {
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
  }

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
      <MapCanvas
        layers={layers}
        selected={selected}
        onSelect={(feature) => setSelected(feature)}
        placingPoint={placingPoint}
        onPlacePoint={placePoint}
        start={startPoint}
        end={endPoint}
        route={route}
        demo={data.source === "demo"}
        zoom={zoom}
        center={center}
      />

      {!placingPoint && <header className="topbar absolute inset-x-0 top-0 z-30 flex items-center justify-between">
        <div className="brand flex items-center gap-3">
          <span className="brand-mark"><Leaf size={22} strokeWidth={2.4} /></span>
          <span>VINEYARD INSPECTOR</span>
        </div>
        <div className="top-actions flex items-center gap-3">
          <IconAction label={panelsVisible ? "Hide panels" : "Show panels"} onClick={() => setPanelsVisible((value) => !value)} pressed={!panelsVisible}>
            {panelsVisible ? <PanelLeftClose size={23} strokeWidth={1.8} /> : <PanelLeftOpen size={23} strokeWidth={1.8} />}
          </IconAction>
          <IconAction label={fullscreen ? "Exit full screen" : "Enter full screen"} onClick={toggleFullscreen} pressed={fullscreen}>
            {fullscreen ? <Minimize2 size={22} strokeWidth={1.9} /> : <Expand size={22} strokeWidth={1.9} />}
          </IconAction>
          <button type="button" className="upload-button flex items-center justify-center gap-3" aria-label="Upload GeoTIFF" onClick={() => fileInput.current?.click()}>
            <Upload size={22} strokeWidth={1.9} /> <span>Upload GeoTIFF</span>
          </button>
          <input ref={fileInput} type="file" accept=".tif,.tiff,image/tiff" className="hidden" onChange={handleFile} tabIndex={-1} aria-hidden="true" />
        </div>
      </header>}

      {panelsVisible && !placingPoint && (
        <>
          <section className="identity-block" aria-label="Vineyard status">
            <div className={`status-pill flex items-center gap-2 ${processing ? "is-processing" : ""}`}>
              <span className="status-dot" />{processing ? "Processing…" : "Analysis Complete"}
            </div>
            <h1>{data.name}</h1>
            <div className="identity-meta flex items-center gap-2"><p>Aerial inspection <span>·</span> {data.crs}</p>{data.source === "demo" && <div className="demo-tag">DEMO DATA</div>}</div>
            {uploadName && <p className="uploaded-name" title={uploadName}>{uploadName}</p>}
          </section>

          <section className="panel layers-panel" aria-labelledby="layers-heading">
            <div className="panel-title flex items-center gap-3"><Layers3 size={22} fill="white" strokeWidth={1.6} /><h2 id="layers-heading">Layers</h2></div>
            <div className="layer-list">
              {layerDefinitions.map(({ key, label, swatch }) => (
                <label key={key} className={`layer-row flex items-center ${layers[key] ? "" : "layer-disabled"}`}>
                  <input type="checkbox" checked={layers[key]} onChange={() => toggleLayer(key)} className="layer-native-check" />
                  <span className={`layer-check layer-check-${key}`} aria-hidden="true">{layers[key] && <Check size={14} strokeWidth={2.7} />}</span>
                  <span className="layer-label">{label}</span>
                  <Swatch kind={swatch} />
                </label>
              ))}
            </div>
          </section>

          <div className="right-panel-stack">
          <section className="panel summary-panel" aria-labelledby="summary-heading">
            <div className="panel-title flex items-center gap-3"><BarChart3 size={23} fill="white" strokeWidth={1.5} /><h2 id="summary-heading">Vineyard Summary</h2></div>
            <div className="summary-grid grid grid-cols-2 gap-2">
              <SummaryMetric icon={<Layers3 />} label="Blocks" value={formatValue(data.summary.blocks)} />
              <SummaryMetric icon={<Rows3 />} label="Rows" value={formatValue(data.summary.rows)} />
              <SummaryMetric icon={<Leaf />} label="Canopy Area" value={formatValue(data.summary.canopyHa, " ha")} />
              <SummaryMetric icon={<ScanLine />} label="Inter-row Area" value={formatValue(data.summary.interrowHa, " ha")} />
              <SummaryMetric icon={<Route />} label="Total Row Length" value={formatValue(data.summary.totalRowKm, " km")} compact />
              <SummaryMetric icon={<Route />} label="Route" value={formatValue(routeLengthKm, " km")} />
            </div>
          </section>

          {!plannerOpen && <section className="panel selected-panel" aria-labelledby="selected-heading">
            <div className="panel-title flex items-center gap-3"><Leaf size={23} fill="white" strokeWidth={1.3} /><h2 id="selected-heading">{selected?.title || "Selected Feature"}</h2></div>
            {selected ? (
              <div className="detail-list">
                <Detail label="Vineyard ID" value={selected.vineyardId} />
                {selected.rowId && <Detail label="Row ID" value={selected.rowId} />}
                {selected.lengthM != null && <Detail label="Length" value={`${selected.lengthM.toFixed(1)} m`} />}
                {selected.structure && <Detail label="Structure" value={selected.structure === "disrupted" ? "Disrupted" : selected.structure} alert={selected.structure === "disrupted"} />}
                {!selectedRows && <Detail label="Details" value={selected.note || "No attributes available"} />}
              </div>
            ) : <p className="empty-selection">Click an annotation to inspect it.</p>}
          </section>}
          </div>

          {plannerOpen && (
            <section className="panel route-planner" id="route-planner" aria-labelledby="planner-heading">
              <div className="panel-title planner-title flex items-center gap-3">
                <Route size={25} strokeWidth={1.6} />
                <h2 id="planner-heading">Route Planner</h2>
                <button type="button" className="collapse-button" onClick={() => setPlannerOpen(false)} aria-label="Close route planner">
                  <Minus size={20} />
                </button>
              </div>
              <div className="planner-body">
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
                </div>
            </section>
          )}

          <div className="map-controls flex flex-col gap-1" aria-label="Map controls">
            <IconAction label="Zoom in" onClick={() => setZoom((value) => Math.min(2.4, +(value + 0.2).toFixed(1)))}><Plus size={25} /></IconAction>
            <IconAction label="Zoom out" onClick={() => setZoom((value) => Math.max(0.7, +(value - 0.2).toFixed(1)))}><Minus size={25} /></IconAction>
            <IconAction label="Go to start point" title="Go to start point" onClick={() => { setCenter(startPoint); setZoom(1.5); }}><Navigation size={22} fill="white" /></IconAction>
          </div>

          <section className="legend panel flex items-center gap-4" aria-label="Map legend">
            {layerDefinitions.map((layer) => (
              <div key={layer.key} className="legend-item flex items-center gap-2"><Swatch kind={layer.swatch} /><span>{layer.legendLabel}</span></div>
            ))}
          </section>
          <button type="button" className="plan-button flex items-center justify-center gap-3" aria-expanded={plannerOpen} aria-controls="route-planner" onClick={() => setPlannerOpen((value) => !value)}>
            <Route size={24} strokeWidth={1.8} />Plan Route
          </button>
          <div className="scale" aria-label={`Map scale approximately ${Math.round(200 / zoom)} metres`}>
            <div className="scale-labels"><span>0</span><span>{Math.round(50 / zoom)}</span><span>{Math.round(100 / zoom)}</span><span>{Math.round(200 / zoom)} m</span></div>
            <div className="scale-rule"><i /><i /><i /><i /></div>
          </div>
        </>
      )}

      {placingPoint && <div className="point-picker" role="status"><span>Click anywhere on the map to set the {placingPoint === "start" ? "starting" : "end"} point</span><button type="button" onClick={() => { setPlacingPoint(null); setPlannerOpen(true); }}>Cancel</button></div>}

      {(processing || message || apiError) && (
        <div className="toast" role="status" aria-live="polite">
          {processing ? (
            <><div className="toast-top"><span>Processing {uploadName}</span><strong>{progress}%</strong></div><div className="progress-track"><div style={{ width: `${progress}%` }} /></div>{isDemoMode() && <small>Preview mode · no GeoTIFF analysis</small>}</>
          ) : (
            <><span>{apiError || message}</span><button type="button" onClick={() => { setMessage(""); setApiError(""); }} aria-label="Dismiss message"><X size={16} /></button></>
          )}
        </div>
      )}

      {!panelsVisible && <div className="hidden-panels-hint">Panels hidden · use the top control to restore</div>}
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
