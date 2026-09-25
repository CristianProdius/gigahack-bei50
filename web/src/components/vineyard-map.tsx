"use client";

import { useEffect, useRef, useState } from "react";

const SIRET3_XYZ =
  "https://api.imagery.hotosm.org/raster/collections/openaerialmap/items/683060c4025981aa411253c8/tiles/WebMercatorQuad/{z}/{x}/{y}?assets=visual";

/** Official start in WGS84 (data/challenge/02_route/start.geojson). */
const OFFICIAL_START: [number, number] = [28.7073776, 47.1230335];

type Status = "loading" | "ready" | "error" | "empty";
type Pick = { kind: string; id?: string; extra?: string };
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

type LayerKey = "vineyard" | "interrow" | "row" | "waste" | "forbidden" | "inspector" | "farmer";

const LAYER_MAP: Record<LayerKey, string[]> = {
  vineyard: ["vineyard-fill"],
  interrow: ["interrow-fill"],
  row: ["row-line"],
  waste: ["waste-fill"],
  forbidden: ["forbidden-fill"],
  inspector: ["inspector-line"],
  farmer: ["farmer-line"],
};

const LAYERS: Array<{ key: LayerKey; label: string; swatch: string; hint: string }> = [
  { key: "inspector", label: "Inspector walk", swatch: "#438bff", hint: "Gaps + waste" },
  { key: "farmer", label: "Farmer walk", swatch: "#f05d55", hint: "Waste only" },
  { key: "vineyard", label: "Canopies", swatch: "#166534", hint: "vineyard polygons" },
  { key: "row", label: "Rows", swatch: "#d1fb55", hint: "row axes" },
  { key: "interrow", label: "Inter-rows", swatch: "#a3e635", hint: "passable ground" },
  { key: "waste", label: "Waste", swatch: "#ffa443", hint: "boxes" },
  { key: "forbidden", label: "Forbidden", swatch: "#b91c1c", hint: "do not walk" },
];

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

function applyLayerVisibility(map: import("maplibre-gl").Map, layers: Record<LayerKey, boolean>) {
  for (const [key, ids] of Object.entries(LAYER_MAP) as Array<[LayerKey, string[]]>) {
    const vis = layers[key] ? "visible" : "none";
    for (const id of ids) {
      if (map.getLayer(id)) map.setLayoutProperty(id, "visibility", vis);
    }
  }
}

export function VineyardMap() {
  const ref = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<import("maplibre-gl").Map | undefined>(undefined);
  const [status, setStatus] = useState<Status>("loading");
  const [error, setError] = useState("");
  const [picked, setPicked] = useState<Pick | null>(null);
  const [reload, setReload] = useState(0);
  const [layers, setLayers] = useState<Record<LayerKey, boolean>>({
    vineyard: true,
    interrow: true,
    row: true,
    waste: true,
    forbidden: true,
    inspector: true,
    farmer: true,
  });
  const [totals, setTotals] = useState<Totals>({ vineyard: 0, row: 0, waste: 0 });

  useEffect(() => {
    let cancelled = false;
    let map: import("maplibre-gl").Map | undefined;

    async function boot() {
      setStatus("loading");
      setError("");
      try {
        const maplibre = await import("maplibre-gl");
        if (!ref.current || cancelled) return;
        maplibre.config.WORKER_URL = `${window.location.origin}/maplibre-gl-worker.mjs`;

        const [sample, inspector, farmer, csvText] = await Promise.all([
          fetch("/layers/sample.geojson").then((r) => {
            if (!r.ok) throw new Error(`sample layers ${r.status}`);
            return r.json();
          }),
          fetch("/layers/route.geojson").then((r) => {
            if (!r.ok) throw new Error(`inspector route ${r.status}`);
            return r.json();
          }),
          fetch("/layers/route-farmer.geojson").then((r) => {
            if (!r.ok) throw new Error(`farmer route ${r.status}`);
            return r.json();
          }),
          fetch("/layers/measurements.csv").then((r) => (r.ok ? r.text() : "")),
        ]);

        const feats = (sample.features || []) as Array<{ properties?: { kind?: string } }>;
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
          container: ref.current,
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
          if (msg.includes("Worker") || msg.includes("actors") || msg.includes("siret3") || msg.includes("Failed to fetch")) return;
        });

        map.on("load", () => {
          if (!map || cancelled) return;
          map.addSource("sample", { type: "geojson", data: sample });
          map.addSource("inspector", { type: "geojson", data: inspector });
          map.addSource("farmer", { type: "geojson", data: farmer });
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
            filter: ["==", ["get", "kind"], "vineyard"],
            paint: { "fill-color": "#166534", "fill-opacity": 0.32 },
          });
          map.addLayer({
            id: "interrow-fill",
            type: "fill",
            source: "sample",
            filter: ["==", ["get", "kind"], "interrow_area"],
            paint: { "fill-color": "#a3e635", "fill-opacity": 0.22 },
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
            id: "start-pt",
            type: "circle",
            source: "start",
            paint: { "circle-color": "#438bff", "circle-radius": 7, "circle-stroke-width": 2, "circle-stroke-color": "#fff" },
          });

          for (const id of ["vineyard-fill", "interrow-fill", "waste-fill", "row-line", "inspector-line", "farmer-line", "start-pt"]) {
            map.on("click", id, (e) => {
              const f = e.features?.[0];
              if (!f) return;
              const props = f.properties || {};
              const extra =
                props.area_m2 != null
                  ? `${props.area_m2} m²`
                  : props.length_m != null
                    ? `${props.length_m} m`
                    : props.interrow_cover
                      ? String(props.interrow_cover)
                      : props.kind === "start"
                        ? "Official start · 47.1230335 N, 28.7073776 E"
                        : undefined;
              setPicked({
                kind: String(props.kind || id),
                id: props.id ? String(props.id) : props.role ? String(props.role) : undefined,
                extra,
              });
            });
          }

          applyLayerVisibility(map, layers);

        });
      } catch (err) {
        if (cancelled) return;
        setError(err instanceof Error ? err.message : "Unknown map error");
        setStatus("error");
      }
    }

    boot();
    return () => {
      cancelled = true;
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

  function toggle(key: LayerKey) {
    setLayers((prev) => ({ ...prev, [key]: !prev[key] }));
  }

  function recenter() {
    mapRef.current?.flyTo({ center: OFFICIAL_START, zoom: 16.6 });
  }

  return (
    <div className="relative isolate h-dvh min-h-[36rem] overflow-hidden bg-[#111614] text-[#e8eee9]">
      <div ref={ref} className="absolute inset-0" style={{ zIndex: 0 }} />

      {status === "loading" && (
        <div className="absolute inset-0 grid place-items-center bg-black/35 text-sm" style={{ zIndex: 10 }}>
          Loading Sireț3 layers…
        </div>
      )}

      <header className="pointer-events-none absolute inset-x-0 top-0 flex items-start justify-between gap-3 p-3 sm:p-4" style={{ zIndex: 20 }}>
        <div className="pointer-events-auto flex items-center gap-2 rounded-2xl border border-[var(--panel-border)] bg-[var(--panel)] px-3 py-2 shadow-md">
          <span className="grid size-7 place-items-center rounded-full bg-[var(--lime)] text-xs font-bold text-[#152e11]">S3</span>
          <div>
            <h1 className="text-balance text-sm font-semibold text-white">Sireț3 vineyard map</h1>
            <p className="text-pretty text-[11px] text-white/65">Marcaj · EPSG:32635 · 27 Sep 15:00</p>
          </div>
        </div>
        <div className="pointer-events-auto flex flex-wrap items-center justify-end gap-2">
          <span className="rounded-full bg-amber-200 px-2.5 py-1 text-[11px] font-semibold text-amber-950">SAMPLE</span>
          <button
            type="button"
            onClick={recenter}
            className="rounded-full border border-[var(--panel-border)] bg-[var(--panel)] px-3 py-1.5 text-xs font-medium text-white"
          >
            Official start
          </button>
          <button
            type="button"
            onClick={() => setReload((n) => n + 1)}
            className="rounded-full bg-[var(--lime)] px-3 py-1.5 text-xs font-semibold text-[#152e11]"
          >
            Reload
          </button>
        </div>
      </header>

      <aside className="absolute bottom-3 left-3 top-20 flex w-[min(100%-1.5rem,20rem)] flex-col gap-2 overflow-y-auto sm:top-24" style={{ zIndex: 10 }}>
        <section className="rounded-2xl border border-[var(--panel-border)] bg-[var(--panel)] p-3 shadow-md">
          <p className="text-[11px] font-semibold uppercase text-white/55">Layers</p>
          <ul className="mt-2 flex flex-col">
            {LAYERS.map((item) => (
              <li key={item.key}>
                <label className="flex cursor-pointer items-center gap-2 rounded-lg px-1 py-1.5 text-sm hover:bg-white/5">
                  <input
                    type="checkbox"
                    checked={layers[item.key]}
                    onChange={() => toggle(item.key)}
                    className="size-4 accent-[var(--lime)]"
                  />
                  <span className="size-2.5 shrink-0 rounded-full" style={{ background: item.swatch }} />
                  <span className="min-w-0 flex-1 truncate text-white">{item.label}</span>
                  <span className="tabular-nums text-[11px] text-white/50">
                    {item.key === "inspector" ? fmtM(totals.inspectorM) : item.key === "farmer" ? fmtM(totals.farmerM) : item.hint}
                  </span>
                </label>
              </li>
            ))}
          </ul>
        </section>

        <section className="rounded-2xl border border-[var(--panel-border)] bg-[var(--panel)] p-3 shadow-md">
          <p className="text-[11px] font-semibold uppercase text-white/55">Measurements</p>
          {status === "error" && (
            <p className="mt-2 text-pretty text-sm text-red-300">
              {error}. Check OpenAerialMap and reload.
            </p>
          )}
          {status === "empty" && (
            <p className="mt-2 text-pretty text-sm text-white/70">
              No features. Drop a Marcaj export into <code>web/public/layers/</code>.
            </p>
          )}
          {(status === "ready" || status === "loading") && (
            <dl className="mt-2 grid grid-cols-2 gap-x-3 gap-y-2 text-sm">
              <div>
                <dt className="text-[11px] text-white/50">Blocks</dt>
                <dd className="tabular-nums font-medium">{totals.nBlocks ?? totals.vineyard}</dd>
              </div>
              <div>
                <dt className="text-[11px] text-white/50">Rows</dt>
                <dd className="tabular-nums font-medium">{totals.nRows ?? totals.row}</dd>
              </div>
              <div>
                <dt className="text-[11px] text-white/50">Canopy</dt>
                <dd className="tabular-nums font-medium">{fmtHa(totals.canopyHa)}</dd>
              </div>
              <div>
                <dt className="text-[11px] text-white/50">Inter-row</dt>
                <dd className="tabular-nums font-medium">{fmtHa(totals.interrowHa)}</dd>
              </div>
              <div className="col-span-2">
                <dt className="text-[11px] text-white/50">Row length</dt>
                <dd className="tabular-nums font-medium">{fmtM(totals.rowLengthM)}</dd>
              </div>
              <div>
                <dt className="text-[11px] text-white/50">Inspector</dt>
                <dd className="tabular-nums font-medium text-[var(--blue)]">{fmtM(totals.inspectorM)}</dd>
              </div>
              <div>
                <dt className="text-[11px] text-white/50">Farmer</dt>
                <dd className="tabular-nums font-medium text-[var(--red)]">{fmtM(totals.farmerM)}</dd>
              </div>
            </dl>
          )}
        </section>

        {picked && (
          <section className="rounded-2xl border border-[var(--panel-border)] bg-[var(--panel)] p-3 shadow-md">
            <div className="flex items-start justify-between gap-2">
              <p className="text-[11px] font-semibold uppercase text-white/55">Selected</p>
              <button type="button" onClick={() => setPicked(null)} className="text-xs text-white/60">
                Clear
              </button>
            </div>
            <p className="mt-1 font-medium text-white">{picked.kind}</p>
            {picked.id && <p className="tabular-nums text-sm text-white/80">ID {picked.id}</p>}
            {picked.extra && <p className="text-pretty text-sm text-white/70">{picked.extra}</p>}
          </section>
        )}

        <p className="px-1 text-pretty text-[11px] text-white/55">
          Official start 47.1230335 N, 28.7073776 E. Inspector (blue) visits gaps and waste. Farmer (red) collects waste only.
        </p>
      </aside>
    </div>
  );
}
