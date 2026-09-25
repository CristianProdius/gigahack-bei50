"use client";

import { useEffect, useRef, useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";

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

export function VineyardMap() {
  const ref = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<import("maplibre-gl").Map | undefined>(undefined);
  const [status, setStatus] = useState<Status>("loading");
  const [error, setError] = useState<string>("");
  const [picked, setPicked] = useState<Pick | null>(null);
  const [reload, setReload] = useState(0);
  const [showInspector, setShowInspector] = useState(true);
  const [showFarmer, setShowFarmer] = useState(true);
  const [totals, setTotals] = useState<Totals>({ vineyard: 0, row: 0, waste: 0 });

  useEffect(() => {
    let cancelled = false;
    let map: import("maplibre-gl").Map | undefined;

    async function boot() {
      setStatus("loading");
      setError("");
      try {
        const maplibre = await import("maplibre-gl");
        await import("maplibre-gl/dist/maplibre-gl.css");
        if (!ref.current || cancelled) return;
        // Cursor/Electron and some Next workers reject the default blob worker URL.
        maplibre.setWorkerCount(0);

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
        const c: Totals = {
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
        };
        setTotals(c);
        if (!feats.length) setStatus("empty");

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
          const msg = ev.error?.message || "Map failed to load";
          if (msg.includes("siret3")) return;
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
            paint: { "fill-color": "#166534", "fill-opacity": 0.28 },
          });
          map.addLayer({
            id: "interrow-fill",
            type: "fill",
            source: "sample",
            filter: ["==", ["get", "kind"], "interrow_area"],
            paint: { "fill-color": "#a3e635", "fill-opacity": 0.25 },
          });
          map.addLayer({
            id: "forbidden-fill",
            type: "fill",
            source: "sample",
            filter: ["==", ["get", "kind"], "forbidden"],
            paint: { "fill-color": "#b91c1c", "fill-opacity": 0.35 },
          });
          map.addLayer({
            id: "waste-fill",
            type: "fill",
            source: "sample",
            filter: ["==", ["get", "kind"], "waste"],
            paint: { "fill-color": "#ea580c", "fill-opacity": 0.7 },
          });
          map.addLayer({
            id: "row-line",
            type: "line",
            source: "sample",
            filter: ["==", ["get", "kind"], "row"],
            paint: { "line-color": "#14532d", "line-width": 2.4 },
          });
          map.addLayer({
            id: "inspector-line",
            type: "line",
            source: "inspector",
            filter: ["==", ["get", "kind"], "route"],
            paint: { "line-color": "#1d4ed8", "line-width": 3.2, "line-dasharray": [1.4, 1] },
            layout: { visibility: showInspector ? "visible" : "none" },
          });
          map.addLayer({
            id: "farmer-line",
            type: "line",
            source: "farmer",
            filter: ["==", ["get", "kind"], "route"],
            paint: { "line-color": "#dc2626", "line-width": 3, "line-dasharray": [0.8, 1.2] },
            layout: { visibility: showFarmer ? "visible" : "none" },
          });
          map.addLayer({
            id: "start-pt",
            type: "circle",
            source: "start",
            paint: { "circle-color": "#1d4ed8", "circle-radius": 6, "circle-stroke-width": 2, "circle-stroke-color": "#fff" },
          });

          for (const id of ["vineyard-fill", "interrow-fill", "waste-fill", "row-line", "inspector-line", "farmer-line"]) {
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
                      : undefined;
              setPicked({ kind: String(props.kind || id), id: props.id ? String(props.id) : props.role ? String(props.role) : undefined, extra });
            });
          }

          setStatus(feats.length ? "ready" : "empty");
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
  }, [reload]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map?.getLayer("inspector-line")) return;
    map.setLayoutProperty("inspector-line", "visibility", showInspector ? "visible" : "none");
    map.setLayoutProperty("farmer-line", "visibility", showFarmer ? "visible" : "none");
  }, [showInspector, showFarmer]);

  return (
    <div className="flex min-h-0 flex-1 flex-col gap-3 lg:flex-row">
      <Card className="order-2 flex w-full shrink-0 flex-col gap-3 p-4 lg:order-1 lg:w-80">
        <div className="flex flex-wrap items-center gap-2">
          <Badge tone="amber">SAMPLE layers</Badge>
          <Badge tone="green">EPSG:32635 metres</Badge>
        </div>
        <p className="text-sm text-stone-600">
          Official start 47.1230335 N, 28.7073776 E. Inspector walk (blue) visits gaps and waste. Farmer walk (red) collects waste only. Replace layers after the Marcaj export.
        </p>
        <div className="flex flex-col gap-1 text-sm">
          <label className="flex items-center gap-2">
            <input type="checkbox" checked={showInspector} onChange={(e) => setShowInspector(e.target.checked)} />
            Inspector (blue){totals.inspectorM ? ` · ${totals.inspectorM} m` : ""}
          </label>
          <label className="flex items-center gap-2">
            <input type="checkbox" checked={showFarmer} onChange={(e) => setShowFarmer(e.target.checked)} />
            Farmer (red){totals.farmerM ? ` · ${totals.farmerM} m` : ""}
          </label>
        </div>
        {status === "loading" && <p className="text-sm text-stone-500">Loading map and layers…</p>}
        {status === "empty" && (
          <p className="text-sm text-stone-500">No features in the GeoJSON. Drop a Marcaj export into <code>web/public/layers/</code>.</p>
        )}
        {status === "error" && (
          <p className="text-sm text-red-700">
            {error}. Check network access to OpenAerialMap and refresh.
          </p>
        )}
        {status === "ready" && (
          <ul className="text-sm text-stone-700">
            <li>{totals.nBlocks ?? totals.vineyard} block(s) / {totals.vineyard} canopy polygon(s)</li>
            <li>{totals.nRows ?? totals.row} row(s)</li>
            <li>{totals.waste} waste box(es)</li>
            {totals.canopyHa && <li>Canopy {totals.canopyHa} ha</li>}
            {totals.interrowHa && <li>Inter-row {totals.interrowHa} ha</li>}
            {totals.rowLengthM && <li>Row length {totals.rowLengthM} m</li>}
          </ul>
        )}
        {picked && (
          <div className="rounded-md bg-stone-50 p-3 text-sm">
            <div className="font-medium">{picked.kind}</div>
            {picked.id && <div>ID {picked.id}</div>}
            {picked.extra && <div>{picked.extra}</div>}
          </div>
        )}
        <div className="mt-auto flex flex-wrap gap-2">
          <Button variant="outline" onClick={() => setReload((n) => n + 1)}>
            Reload layers
          </Button>
          <a
            className="inline-flex items-center text-sm text-emerald-800 underline"
            href="https://api.imagery.hotosm.org/stac/collections/openaerialmap/items/683060c4025981aa411253c8"
            target="_blank"
            rel="noreferrer"
          >
            Sireț3 STAC
          </a>
        </div>
      </Card>
      <div className="relative order-1 min-h-[320px] flex-1 overflow-hidden rounded-xl border border-stone-200 lg:order-2 lg:min-h-[640px]">
        <div ref={ref} className="absolute inset-0" />
        {status === "loading" && (
          <div className="absolute inset-0 grid place-items-center bg-stone-100/70 text-sm text-stone-600">
            Loading Sireț3…
          </div>
        )}
      </div>
    </div>
  );
}
