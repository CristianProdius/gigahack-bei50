export type LayerKey =
  | "canopies"
  | "rows"
  | "interrows"
  | "waste"
  | "inspection"
  | "route"
  | "forbidden"
  | "passages";

export type TargetMode = "inspection" | "waste" | "both";
export type Point = { x: number; y: number };

export type SelectedFeature = {
  type: "row" | "canopy" | "waste" | "inspection" | "interrow";
  title: string;
  vineyardId: string;
  rowId?: string;
  lengthM?: number;
  structure?: "regular" | "disrupted" | "unassessable";
  note?: string;
};

export type VineyardData = {
  name: string;
  crs: string;
  source: "demo" | "api";
  summary: {
    blocks: number | null;
    rows: number | null;
    canopyHa: number | null;
    interrowHa: number | null;
    totalRowKm: number | null;
    routeKm: number | null;
  };
  targets: { inspection: number; waste: number };
  organizerStart: Point;
};

export const demoVineyard: VineyardData = {
  name: "Siret Vineyard",
  crs: "EPSG:32635",
  source: "demo",
  summary: {
    blocks: 12,
    rows: 248,
    canopyHa: 19.8,
    interrowHa: 14.2,
    totalRowKm: 18.4,
    routeKm: 4.2,
  },
  targets: { inspection: 24, waste: 15 },
  organizerStart: { x: 490, y: 504 },
};

export const layerDefinitions: {
  key: LayerKey;
  label: string;
  swatch: string;
}[] = [
  { key: "canopies", label: "Canopies", swatch: "canopy" },
  { key: "rows", label: "Rows", swatch: "row" },
  { key: "interrows", label: "Inter-row Areas", swatch: "interrow" },
  { key: "waste", label: "Waste", swatch: "waste" },
  { key: "inspection", label: "Inspection Points", swatch: "inspection" },
  { key: "route", label: "Walking Route", swatch: "route" },
  { key: "forbidden", label: "Forbidden Zones", swatch: "forbidden" },
  { key: "passages", label: "Authorized Passages", swatch: "passage" },
];

export const initialLayerVisibility: Record<LayerKey, boolean> = {
  canopies: true,
  rows: true,
  interrows: true,
  waste: true,
  inspection: true,
  route: true,
  forbidden: true,
  passages: true,
};

export function targetCount(data: VineyardData, mode: TargetMode) {
  if (mode === "inspection") return data.targets.inspection;
  if (mode === "waste") return data.targets.waste;
  return data.targets.inspection + data.targets.waste;
}
