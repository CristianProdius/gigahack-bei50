"use client";

import { useEffect, useRef, useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";

const SIRET3_XYZ =
  "https://api.imagery.hotosm.org/raster/collections/openaerialmap/items/683060c4025981aa411253c8/tiles/WebMercatorQuad/{z}/{x}/{y}?assets=visual";

const CENTER: [number, number] = [28.71155, 47.12205];

type Status = "loading" | "ready" | "error" | "empty";

type Pick = { kind: string; id?: string; extra?: string };

export function VineyardMap() {
  const ref = useRef<HTMLDivElement | null>(null);
  const [status, setStatus] = useState<Status>("loading");
  const [error, setError] = useState<string>("");
  const [picked, setPicked] = useState<Pick | null>(null);
  const [showSample, setShowSample] = useState(true);
  const [counts, setCounts] = useState({ vineyard: 0, row: 0, waste: 0 });

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

        const [sample, route] = await Promise.all([
          fetch("/layers/sample.geojson").then((r) => {
            if (!r.ok) throw new Error(`sample layers ${r.status}`);
            return r.json();
          }),
          fetch("/layers/route.geojson").then((r) => {
            if (!r.ok) throw new Error(`route ${r.status}`);
            return r.json();
          }),
        ]);

        const feats = (sample.features || []) as Array<{ properties?: { kind?: string } }>;
        const c = {
          vineyard: feats.filter((f) => f.properties?.kind === "vineyard").length,
          row: feats.filter((f) => f.properties?.kind === "row").length,
          waste: feats.filter((f) => f.properties?.kind === "waste").length,
        };
        setCounts(c);
        if (!feats.length) {
          setStatus("empty");
        }

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
          center: CENTER,
          zoom: 16.4,
          attributionControl: true,
        });

        map.on("error", (ev) => {
          const msg = ev.error?.message || "Map failed to load";
          if (msg.includes("siret3")) {
            // Ortho tiles can 404 at some zooms; keep OSM.
            return;
          }
        });

        map.on("load", () => {
          if (!map || cancelled) return;
          map.addSource("sample", { type: "geojson", data: sample });
          map.addSource("route", { type: "geojson", data: route });

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
            id: "route-line",
            type: "line",
            source: "route",
            filter: ["==", ["get", "kind"], "route"],
            paint: { "line-color": "#1d4ed8", "line-width": 3, "line-dasharray": [1.4, 1] },
          });
          map.addLayer({
            id: "start-pt",
            type: "circle",
            source: "route",
            filter: ["==", ["get", "kind"], "start"],
            paint: { "circle-color": "#1d4ed8", "circle-radius": 6, "circle-stroke-width": 2, "circle-stroke-color": "#fff" },
          });

          for (const id of ["vineyard-fill", "interrow-fill", "waste-fill", "row-line", "route-line"]) {
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
              setPicked({ kind: String(props.kind || id), id: props.id ? String(props.id) : undefined, extra });
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
      map?.remove();
    };
  }, [showSample]);

  return (
    <div className="flex min-h-0 flex-1 flex-col gap-3 lg:flex-row">
      <Card className="order-2 flex w-full shrink-0 flex-col gap-3 p-4 lg:order-1 lg:w-80">
        <div className="flex flex-wrap items-center gap-2">
          <Badge tone="amber">SAMPLE layers</Badge>
          <Badge tone="green">EPSG:32635 metres</Badge>
        </div>
        <p className="text-sm text-stone-600">
          Sireț3 ortho (20 May 2025, 3.52 cm/px, CC BY 4.0, 3DATA COLLECT) with a synthetic vineyard, rows, inter-row, waste box, and a closed walk. Replace after the Marcaj export.
        </p>
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
            <li>{counts.vineyard} vineyard polygon(s)</li>
            <li>{counts.row} row polyline(s)</li>
            <li>{counts.waste} waste box(es)</li>
            <li>Closed route, start snap 5 m</li>
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
          <Button variant="outline" onClick={() => setShowSample((v) => !v)}>
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
