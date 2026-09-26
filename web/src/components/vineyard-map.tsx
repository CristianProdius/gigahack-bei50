"use client";

import { useEffect, useRef, useState, type ReactNode } from "react";
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
  RefreshCw,
  Route,
  Rows3,
  ScanLine,
  X,
} from "lucide-react";
import { toLonLatCollection } from "@/lib/geo";

const SIRET3_XYZ =
  "https://api.imagery.hotosm.org/raster/collections/openaerialmap/items/683060c4025981aa411253c8/tiles/WebMercatorQuad/{z}/{x}/{y}?assets=visual";

/** Official start in WGS84 (data/challenge/02_route/start.geojson). */
const OFFICIAL_START: [number, number] = [28.7073776, 47.1230335];

type Status = "loading" | "ready" | "error" | "empty";
type WalkMode = "inspector" | "farmer" | "both";
type Totals = {
  vineyard: number;
  row: number;
  waste: number;
  nBlocks?: string;
  nRows?: string;
  canopyHa?: string;
  interrowHa?: string;
  rowLengthM?: string;
  inspectorM?: string;
  farmerM?: string;
};

type LayerKey =
  | "vineyard"
  | "interrow"
  | "row"
  | "waste"
  | "forbidden"
  | "passage"
  | "inspection"
  | "inspector"
  | "farmer";

type Selected = {
  title: string;
  kind: string;
  vineyardId?: string;
  rowId?: string;
  lengthM?: number;
  structure?: string;
  cover?: string;
  note?: string;
};

const LAYER_MAP: Record<LayerKey, string[]> = {
  vineyard: ["vineyard-fill", "vineyard-pt"],
  interrow: ["interrow-fill"],
  row: ["row-line"],
  waste: ["waste-fill"],
  forbidden: ["forbidden-fill"],
  passage: ["passage-fill"],
  inspection: ["inspection-pt"],
  inspector: ["inspector-line"],
  farmer: ["farmer-line"],
};

const LAYER_DEFS: Array<{ key: LayerKey; label: string; swatch: string; legend: string }> = [
  { key: "vineyard", label: "Canopies", swatch: "canopy", legend: "Canopy" },
  { key: "row", label: "Rows", swatch: "row", legend: "Row" },
  { key: "interrow", label: "Inter-row Areas", swatch: "interrow", legend: "Inter-row" },
  { key: "waste", label: "Waste", swatch: "waste", legend: "Waste" },
  { key: "inspection", label: "Inspection Points", swatch: "inspection", legend: "Inspection" },
  { key: "inspector", label: "Inspector walk", swatch: "inspector", legend: "Inspector" },
  { key: "farmer", label: "Farmer walk", swatch: "farmer", legend: "Farmer" },
  { key: "forbidden", label: "Forbidden", swatch: "forbidden", legend: "Forbidden" },
  { key: "passage", label: "Passages", swatch: "passage", legend: "Passage" },
];

type Fc = { type?: string; features?: Array<{ properties?: Record<string, unknown>; geometry?: { type?: string } }> };

async function fetchJson(url: string): Promise<Fc | null> {
  const r = await fetch(url);
  if (!r.ok) return null;
  return r.json();
}

function isSampleFeature(f: { properties?: Record<string, unknown> }) {
  return f.properties?.sample === true || f.properties?.sample === "true";
}

function parseCsv(text: string): Totals {
  const lines = text.trim().split(/\r?\n/);
  if (lines.length < 2) return { vineyard: 0, row: 0, waste: 0 };
  const header = lines[0].split(",");
  const idx = (name: string) => header.indexOf(name);
  const kindI = idx("kind");
  const nI = idx("n_parts");
  const areaI = idx("area_m2");
  const lenI = idx("length_m");
  const out: Totals = { vineyard: 0, row: 0, waste: 0 };
  for (const line of lines.slice(1)) {
    const cols = line.split(",");
    const kind = cols[kindI] || "";
    if (kind === "n_blocks") out.nBlocks = cols[nI];
    if (kind === "n_rows") out.nRows = cols[nI];
    if (kind === "canopy_union" && cols[areaI]) out.canopyHa = (Number(cols[areaI]) / 10000).toFixed(4);
    if (kind === "interrow_union" && cols[areaI]) out.interrowHa = (Number(cols[areaI]) / 10000).toFixed(4);
    if (kind === "total_row_length") out.rowLengthM = cols[lenI];
    if (kind === "vineyard") out.vineyard += 1;
    if (kind === "row") out.row += 1;
    if (kind === "waste") out.waste += 1;
  }
  return out;
}

function fmtM(value?: string) {
  if (value == null || value === "") return "—";
  const n = Number(value);
  if (Number.isNaN(n)) return value;
  return `${n.toLocaleString("en-US", { maximumFractionDigits: 1 })} m`;
}

function fmtHa(value?: string) {
  if (value == null || value === "") return "—";
  return `${value} ha`;
}

function fmtKmFromM(value?: string) {
  if (value == null || value === "") return "—";
  const n = Number(value);
  if (Number.isNaN(n)) return "—";
  return `${(n / 1000).toFixed(2)} km`;
}

function applyLayerVisibility(map: import("maplibre-gl").Map, layers: Record<LayerKey, boolean>) {
  for (const [key, ids] of Object.entries(LAYER_MAP) as Array<[LayerKey, string[]]>) {
    const vis = layers[key] ? "visible" : "none";
    for (const id of ids) {
      if (map.getLayer(id)) map.setLayoutProperty(id, "visibility", vis);
    }
  }
}

function selectedFromClick(layerId: string, props: Record<string, unknown>): Selected {
  const kind = String(props.kind || layerId);
  const vineyardId = props.vineyard_id ? String(props.vineyard_id) : undefined;
  const rowId = props.row_id ? String(props.row_id) : undefined;
  const structure = props.row_structure ? String(props.row_structure) : undefined;
  const cover = props.interrow_cover ? String(props.interrow_cover) : undefined;
  const lengthM = props.length_m != null && props.length_m !== "" ? Number(props.length_m) : undefined;
  const titles: Record<string, string> = {
    vineyard: "Canopy",
    row: "Selected Row",
    interrow_area: "Inter-row Area",
    waste: "Waste",
    inspection: "Inspection Point",
    start: "Official start",
    forbidden: "Forbidden zone",
    passage: "Authorized passage",
  };
  let title = titles[kind] || kind;
  if (kind === "route") title = layerId.includes("farmer") ? "Farmer walk" : "Inspector walk";
  let note: string | undefined;
  if (kind === "start") note = "47.1230335 N, 28.7073776 E";
  if (props.area_m2 != null) note = `${props.area_m2} m²`;
  if (cover) note = cover;
  return { title, kind, vineyardId, rowId, structure, cover, lengthM, note };
}

export function VineyardMap() {
  const mapEl = useRef<HTMLDivElement | null>(null);
  const workspace = useRef<HTMLElement | null>(null);
  const mapRef = useRef<import("maplibre-gl").Map | undefined>(undefined);
  const [status, setStatus] = useState<Status>("loading");
  const [error, setError] = useState("");
  const [selected, setSelected] = useState<Selected | null>(null);
  const [reload, setReload] = useState(0);
  const [layers, setLayers] = useState<Record<LayerKey, boolean>>({
    vineyard: true,
    interrow: true,
    row: true,
    waste: true,
    forbidden: true,
    passage: true,
    inspection: true,
    inspector: true,
    farmer: true,
  });
  const [totals, setTotals] = useState<Totals>({ vineyard: 0, row: 0, waste: 0 });
  const [sampleMode, setSampleMode] = useState(true);
  const [panelsVisible, setPanelsVisible] = useState(true);
  const [plannerOpen, setPlannerOpen] = useState(false);
  const [walkMode, setWalkMode] = useState<WalkMode>("both");
  const [fullscreen, setFullscreen] = useState(false);
  const [message, setMessage] = useState("");
  const [mapZoom, setMapZoom] = useState(16.6);

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
    let cancelled = false;
    let map: import("maplibre-gl").Map | undefined;
    let ro: ResizeObserver | undefined;

    async function boot() {
      setStatus("loading");
      setError("");
      try {
        const maplibre = await import("maplibre-gl");
        if (!mapEl.current || cancelled) return;
        maplibre.config.WORKER_URL = `${window.location.origin}/maplibre-gl-worker.mjs`;

        const [packed, sample, inspectorRaw, farmerRaw, csvText] = await Promise.all([
          fetchJson("/layers/layers.geojson"),
          fetchJson("/layers/sample.geojson"),
          fetchJson("/layers/route.geojson"),
          fetchJson("/layers/route-farmer.geojson"),
          fetch("/layers/measurements.csv").then((r) => (r.ok ? r.text() : "")),
        ]);
        if (!packed && !sample) throw new Error("no layer GeoJSON in /layers/");

        const packedFc = toLonLatCollection(packed || { features: [] });
        const sampleFc = toLonLatCollection(sample || { features: [] });
        const packedFeats = packedFc.features || [];
        const hasRealCanopy = packedFeats.some((f) => f.properties?.kind === "vineyard");
        const sampleFcFeatures = sampleFc.features || [];
        const sampleData = {
          type: "FeatureCollection",
          features: hasRealCanopy ? packedFeats : [...sampleFcFeatures, ...packedFeats],
        };
        const inspector = toLonLatCollection(inspectorRaw || { features: [] });
        const farmer = toLonLatCollection(farmerRaw || { features: [] });
        setSampleMode(!hasRealCanopy || sampleData.features.some(isSampleFeature));

        const feats = sampleData.features as Array<{ properties?: { kind?: string } }>;
        const parsed = csvText ? parseCsv(csvText) : { vineyard: 0, row: 0, waste: 0 };
        const inspectorM = inspector.features?.[0]?.properties?.length_m;
        const farmerM = farmer.features?.[0]?.properties?.length_m;
        setTotals({
          vineyard: parsed.vineyard || feats.filter((f) => f.properties?.kind === "vineyard").length,
          row: parsed.row || feats.filter((f) => f.properties?.kind === "row").length,
          waste: parsed.waste || feats.filter((f) => f.properties?.kind === "waste").length,
          nBlocks: parsed.nBlocks,
          nRows: parsed.nRows,
          canopyHa: parsed.canopyHa,
          interrowHa: parsed.interrowHa,
          rowLengthM: parsed.rowLengthM,
          inspectorM: inspectorM != null ? String(inspectorM) : undefined,
          farmerM: farmerM != null ? String(farmerM) : undefined,
        });
        setStatus(feats.length ? "ready" : "empty");

        map = new maplibre.Map({
          container: mapEl.current,
          style: {
            version: 8,
            sources: {
              osm: {
                type: "raster",
                tiles: ["https://tile.openstreetmap.org/{z}/{x}/{y}.png"],
                tileSize: 256,
                attribution: "© OpenStreetMap",
              },
              siret3: {
                type: "raster",
                tiles: [SIRET3_XYZ],
                tileSize: 256,
                attribution: "Sireț3 © 3DATA COLLECT / OIN, CC BY 4.0",
              },
            },
            layers: [
              { id: "osm", type: "raster", source: "osm" },
              { id: "siret3", type: "raster", source: "siret3", paint: { "raster-opacity": 0.92 } },
            ],
          },
          center: OFFICIAL_START,
          zoom: 16.6,
          attributionControl: true,
        });
        mapRef.current = map;
        map.on("error", (ev) => {
          const msg = ev.error?.message || "";
          if (msg.includes("siret3") && map.getLayer("siret3")) {
            map.setPaintProperty("siret3", "raster-opacity", 0);
          }
          if (msg.includes("Worker") || msg.includes("actors") || msg.includes("siret3") || msg.includes("Failed to fetch")) return;
        });
        map.on("zoom", () => setMapZoom(map.getZoom()));

        map.on("load", () => {
          if (!map || cancelled) return;
          map.resize();
          map.addSource("sample", { type: "geojson", data: sampleData as GeoJSON.GeoJSON });
          map.addSource("inspector", { type: "geojson", data: inspector as GeoJSON.GeoJSON });
          map.addSource("farmer", { type: "geojson", data: farmer as GeoJSON.GeoJSON });
          map.addSource("start", {
            type: "geojson",
            data: {
              type: "FeatureCollection",
              features: [
                {
                  type: "Feature",
                  properties: { kind: "start" },
                  geometry: { type: "Point", coordinates: OFFICIAL_START },
                },
              ],
            },
          });

          map.addLayer({
            id: "vineyard-fill",
            type: "fill",
            source: "sample",
            filter: [
              "all",
              ["==", ["get", "kind"], "vineyard"],
              ["in", ["geometry-type"], ["literal", ["Polygon", "MultiPolygon"]]],
            ],
            paint: { "fill-color": "#166534", "fill-opacity": 0.32 },
          });
          map.addLayer({
            id: "vineyard-pt",
            type: "circle",
            source: "sample",
            filter: [
              "all",
              ["==", ["get", "kind"], "vineyard"],
              ["==", ["geometry-type"], "Point"],
            ],
            paint: { "circle-color": "#166534", "circle-radius": 3.2, "circle-opacity": 0.75 },
          });
          map.addLayer({
            id: "interrow-fill",
            type: "fill",
            source: "sample",
            filter: ["==", ["get", "kind"], "interrow_area"],
            paint: { "fill-color": "#a3e635", "fill-opacity": 0.22 },
          });
          map.addLayer({
            id: "passage-fill",
            type: "fill",
            source: "sample",
            filter: ["==", ["get", "kind"], "passage"],
            paint: { "fill-color": "#94a3b8", "fill-opacity": 0.28 },
          });
          map.addLayer({
            id: "forbidden-fill",
            type: "fill",
            source: "sample",
            filter: ["==", ["get", "kind"], "forbidden"],
            paint: { "fill-color": "#b91c1c", "fill-opacity": 0.4 },
          });
          map.addLayer({
            id: "waste-fill",
            type: "fill",
            source: "sample",
            filter: ["==", ["get", "kind"], "waste"],
            paint: { "fill-color": "#ffa443", "fill-opacity": 0.75 },
          });
          map.addLayer({
            id: "row-line",
            type: "line",
            source: "sample",
            filter: ["==", ["get", "kind"], "row"],
            paint: { "line-color": "#d1fb55", "line-width": 2.2 },
          });
          map.addLayer({
            id: "inspector-line",
            type: "line",
            source: "inspector",
            filter: ["==", ["get", "kind"], "route"],
            paint: { "line-color": "#438bff", "line-width": 3.2, "line-dasharray": [1.6, 1] },
          });
          map.addLayer({
            id: "farmer-line",
            type: "line",
            source: "farmer",
            filter: ["==", ["get", "kind"], "route"],
            paint: { "line-color": "#f05d55", "line-width": 2.8, "line-dasharray": [0.7, 1.3] },
          });
          map.addLayer({
            id: "inspection-pt",
            type: "circle",
            source: "sample",
            filter: ["==", ["get", "kind"], "inspection"],
            paint: { "circle-color": "#38bdf8", "circle-radius": 4.5, "circle-stroke-width": 1, "circle-stroke-color": "#fff" },
          });
          map.addLayer({
            id: "start-pt",
            type: "circle",
            source: "start",
            paint: { "circle-color": "#438bff", "circle-radius": 7, "circle-stroke-width": 2, "circle-stroke-color": "#fff" },
          });

          for (const id of [
            "vineyard-fill",
            "vineyard-pt",
            "interrow-fill",
            "waste-fill",
            "row-line",
            "inspector-line",
            "farmer-line",
            "forbidden-fill",
            "passage-fill",
            "inspection-pt",
            "start-pt",
          ]) {
            map.on("mouseenter", id, () => {
              map.getCanvas().style.cursor = "pointer";
            });
            map.on("mouseleave", id, () => {
              map.getCanvas().style.cursor = "";
            });
            map.on("click", id, (e) => {
              const f = e.features?.[0];
              if (!f) return;
              setSelected(selectedFromClick(id, (f.properties || {}) as Record<string, unknown>));
            });
          }

          applyLayerVisibility(map, layers);
        });
        ro = new ResizeObserver(() => map?.resize());
        if (mapEl.current) ro.observe(mapEl.current);
      } catch (err) {
        if (cancelled) return;
        setError(err instanceof Error ? err.message : "Unknown map error");
        setStatus("error");
      }
    }

    boot();
    return () => {
      cancelled = true;
      ro?.disconnect();
      mapRef.current = undefined;
      map?.remove();
    };
    // layers snapshot is applied on load; later toggles use the second effect
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [reload]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map || !map.isStyleLoaded()) return;
    applyLayerVisibility(map, layers);
  }, [layers]);

  function toggleLayer(key: LayerKey) {
    setLayers((prev) => ({ ...prev, [key]: !prev[key] }));
  }

  function recenter() {
    mapRef.current?.flyTo({ center: OFFICIAL_START, zoom: 16.6 });
  }

  async function toggleFullscreen() {
    try {
      if (document.fullscreenElement) await document.exitFullscreen();
      else await workspace.current?.requestFullscreen();
    } catch {
      setMessage("Full screen is unavailable in this browser.");
    }
  }

  function showWalk() {
    if (walkMode === "inspector") {
      setLayers((prev) => ({ ...prev, inspector: true, farmer: false }));
      setMessage(`Inspector walk ${fmtM(totals.inspectorM)} · gaps + waste`);
    } else if (walkMode === "farmer") {
      setLayers((prev) => ({ ...prev, inspector: false, farmer: true }));
      setMessage(`Farmer walk ${fmtM(totals.farmerM)} · waste only`);
    } else {
      setLayers((prev) => ({ ...prev, inspector: true, farmer: true }));
      setMessage(`Both walks · inspector ${fmtM(totals.inspectorM)} · farmer ${fmtM(totals.farmerM)}`);
    }
    recenter();
  }

  const blocks = totals.nBlocks ?? String(totals.vineyard || "—");
  const rows = totals.nRows ?? String(totals.row || "—");
  const routeKm =
    walkMode === "farmer"
      ? fmtKmFromM(totals.farmerM)
      : walkMode === "inspector"
        ? fmtKmFromM(totals.inspectorM)
        : fmtKmFromM(totals.inspectorM);
  const selectedRows = selected?.kind === "row";
  const scaleM = Math.round(200 / Math.max(0.4, mapZoom / 16.6));

  return (
    <main className="workspace" ref={workspace}>
      <div ref={mapEl} className="map-surface" />

      {status === "loading" && (
        <div className="absolute inset-0 grid place-items-center bg-black/35 text-sm" style={{ zIndex: 10 }}>
          Loading Sireț3 layers…
        </div>
      )}

      <header className="topbar absolute inset-x-0 top-0 z-30 flex items-center justify-between">
        <div className="brand flex items-center gap-3">
          <span className="brand-mark">
            <Leaf size={22} strokeWidth={2.4} />
          </span>
          <span>VINEYARD INSPECTOR</span>
        </div>
        <div className="top-actions flex items-center gap-3">
          <IconAction
            label={panelsVisible ? "Hide panels" : "Show panels"}
            onClick={() => setPanelsVisible((value) => !value)}
            pressed={!panelsVisible}
          >
            {panelsVisible ? <PanelLeftClose size={23} strokeWidth={1.8} /> : <PanelLeftOpen size={23} strokeWidth={1.8} />}
          </IconAction>
          <IconAction
            label={fullscreen ? "Exit full screen" : "Enter full screen"}
            onClick={toggleFullscreen}
            pressed={fullscreen}
          >
            {fullscreen ? <Minimize2 size={22} strokeWidth={1.9} /> : <Expand size={22} strokeWidth={1.9} />}
          </IconAction>
          <IconAction label="Reload layers" onClick={() => setReload((n) => n + 1)}>
            <RefreshCw size={20} strokeWidth={1.9} />
          </IconAction>
        </div>
      </header>

      {panelsVisible && (
        <>
          <section className="identity-block" aria-label="Vineyard status">
            <div className={`status-pill flex items-center gap-2 ${status === "loading" ? "is-processing" : ""}`}>
              <span className="status-dot" />
              {status === "loading" ? "Processing…" : status === "error" ? "Map error" : status === "empty" ? "No features" : "Analysis Complete"}
            </div>
            <h1>Sireț3</h1>
            <div className="identity-meta flex items-center gap-2">
              <p>
                Aerial inspection <span>·</span> EPSG:32635
              </p>
              <div className={sampleMode ? "demo-tag" : "demo-tag is-live"}>{sampleMode ? "SAMPLE" : "MARCAJ"}</div>
            </div>
          </section>

          <section className="panel layers-panel" aria-labelledby="layers-heading">
            <div className="panel-title flex items-center gap-3">
              <Layers3 size={22} fill="white" strokeWidth={1.6} />
              <h2 id="layers-heading">Layers</h2>
            </div>
            <div className="layer-list">
              {LAYER_DEFS.map(({ key, label, swatch }) => (
                <label key={key} className={`layer-row flex items-center ${layers[key] ? "" : "layer-disabled"}`}>
                  <input
                    type="checkbox"
                    checked={layers[key]}
                    onChange={() => toggleLayer(key)}
                    className="layer-native-check"
                  />
                  <span className={`layer-check layer-check-${key}`} aria-hidden="true">
                    {layers[key] && <Check size={14} strokeWidth={2.7} />}
                  </span>
                  <span className="layer-label">{label}</span>
                  <span className={`swatch swatch-${swatch}`} aria-hidden="true" />
                </label>
              ))}
            </div>
          </section>

          <div className="right-panel-stack">
            <section className="panel summary-panel" aria-labelledby="summary-heading">
              <div className="panel-title flex items-center gap-3">
                <BarChart3 size={23} fill="white" strokeWidth={1.5} />
                <h2 id="summary-heading">Vineyard Summary</h2>
              </div>
              <div className="summary-grid grid grid-cols-2 gap-2">
                <SummaryMetric icon={<Layers3 />} label="Blocks" value={blocks} />
                <SummaryMetric icon={<Rows3 />} label="Rows" value={rows} />
                <SummaryMetric icon={<Leaf />} label="Canopy Area" value={fmtHa(totals.canopyHa)} />
                <SummaryMetric icon={<ScanLine />} label="Inter-row Area" value={fmtHa(totals.interrowHa)} />
                <SummaryMetric icon={<Route />} label="Total Row Length" value={fmtM(totals.rowLengthM)} compact />
                <SummaryMetric icon={<Route />} label="Route" value={routeKm} />
              </div>
            </section>

            {!plannerOpen && (
              <section className="panel selected-panel" aria-labelledby="selected-heading">
                <div className="panel-title flex items-center gap-3">
                  <Leaf size={23} fill="white" strokeWidth={1.3} />
                  <h2 id="selected-heading">{selected?.title || "Selected Feature"}</h2>
                </div>
                {selected ? (
                  <div className="detail-list">
                    {selected.vineyardId && <Detail label="Vineyard ID" value={selected.vineyardId} />}
                    {selected.rowId && <Detail label="Row ID" value={selected.rowId} />}
                    {selected.lengthM != null && !Number.isNaN(selected.lengthM) && (
                      <Detail label="Length" value={`${selected.lengthM.toFixed(1)} m`} />
                    )}
                    {selected.structure && (
                      <Detail
                        label="Structure"
                        value={selected.structure === "disrupted" ? "Disrupted" : selected.structure}
                        alert={selected.structure === "disrupted"}
                      />
                    )}
                    {!selectedRows && <Detail label="Details" value={selected.note || "No attributes available"} />}
                  </div>
                ) : (
                  <p className="empty-selection">Click an annotation to inspect it.</p>
                )}
              </section>
            )}
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
                <p className="field-label">Which walk</p>
                <div className="segmented three flex gap-1">
                  <Choice active={walkMode === "inspector"} onClick={() => setWalkMode("inspector")} label="Inspector" />
                  <Choice active={walkMode === "farmer"} onClick={() => setWalkMode("farmer")} label="Farmer" />
                  <Choice active={walkMode === "both"} onClick={() => setWalkMode("both")} label="Both" />
                </div>
                <button type="button" className="build-button flex items-center justify-center gap-3" onClick={showWalk}>
                  <Route size={24} strokeWidth={1.8} />
                  Show walk
                </button>
                <p className="route-caption">
                  Inspector {fmtM(totals.inspectorM)} <span>·</span> Farmer {fmtM(totals.farmerM)}
                </p>
              </div>
            </section>
          )}

          <div className="map-controls flex flex-col gap-1" aria-label="Map controls">
            <IconAction label="Zoom in" onClick={() => mapRef.current?.zoomIn()}>
              <Plus size={25} />
            </IconAction>
            <IconAction label="Zoom out" onClick={() => mapRef.current?.zoomOut()}>
              <Minus size={25} />
            </IconAction>
            <IconAction label="Go to start point" title="Go to start point" onClick={recenter}>
              <Navigation size={22} fill="white" />
            </IconAction>
          </div>

          <section className="legend panel flex items-center gap-4" aria-label="Map legend">
            {LAYER_DEFS.map((layer) => (
              <div key={layer.key} className="legend-item flex items-center gap-2">
                <span className={`swatch swatch-${layer.swatch}`} aria-hidden="true" />
                <span>{layer.legend}</span>
              </div>
            ))}
          </section>
          <button
            type="button"
            className="plan-button flex items-center justify-center gap-3"
            aria-expanded={plannerOpen}
            aria-controls="route-planner"
            onClick={() => setPlannerOpen((value) => !value)}
          >
            <Route size={24} strokeWidth={1.8} />
            Plan Route
          </button>
          <div className="scale" aria-label={`Map scale approximately ${scaleM} metres`}>
            <div className="scale-labels">
              <span>0</span>
              <span>{Math.round(scaleM / 4)}</span>
              <span>{Math.round(scaleM / 2)}</span>
              <span>{scaleM} m</span>
            </div>
            <div className="scale-rule">
              <i />
              <i />
              <i />
              <i />
            </div>
          </div>
        </>
      )}

      {(message || error) && (
        <div className="toast" role="status" aria-live="polite">
          <span>{error || message}</span>
          <button
            type="button"
            onClick={() => {
              setMessage("");
              setError("");
            }}
            aria-label="Dismiss message"
          >
            <X size={16} />
          </button>
        </div>
      )}

      {!panelsVisible && <div className="hidden-panels-hint">Panels hidden · use the top control to restore</div>}
    </main>
  );
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

function Choice({ active, onClick, label }: { active: boolean; onClick: () => void; label: string }) {
  return (
    <button
      type="button"
      className={`choice flex items-center justify-center gap-2 ${active ? "is-active" : ""}`}
      onClick={onClick}
      aria-pressed={active}
    >
      <span className="choice-radio" />
      <span>{label}</span>
    </button>
  );
}

function SummaryMetric({ icon, label, value, compact = false }: { icon: ReactNode; label: string; value: string; compact?: boolean }) {
  return (
    <div className={`metric flex items-center gap-3 ${compact ? "metric-compact" : ""}`}>
      <span className="metric-icon">{icon}</span>
      <div>
        <span className="metric-label">{label}</span>
        <strong>{value}</strong>
      </div>
    </div>
  );
}

function Detail({ label, value, alert }: { label: string; value: string; alert?: boolean }) {
  return (
    <div className="detail-row flex items-center justify-between gap-2">
      <span>{label}</span>
      <strong className={alert ? "alert-value" : ""}>
        {value}
        {alert && <span className="alert-symbol">▲</span>}
      </strong>
    </div>
  );
}
