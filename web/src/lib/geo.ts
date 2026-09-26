type Position = [number, number];

function firstXY(coords: unknown): Position | null {
  if (!Array.isArray(coords) || coords.length === 0) return null;
  if (typeof coords[0] === "number") return [Number(coords[0]), Number(coords[1])];
  return firstXY(coords[0]);
}

export function looksLike32635(fc: { features?: Array<{ geometry?: { coordinates?: unknown } }> }): boolean {
  const feat = fc.features?.find((f) => f.geometry?.coordinates != null);
  const xy = feat ? firstXY(feat.geometry?.coordinates) : null;
  if (!xy) return false;
  return Math.abs(xy[0]) > 180 || Math.abs(xy[1]) > 90;
}

/** Inverse UTM (WGS84), zone 35N — Sireț3 work CRS. */
export function utm35nToLonLat(easting: number, northing: number): Position {
  const a = 6378137.0;
  const e2 = 0.00669437999014;
  const e1 = (1 - Math.sqrt(1 - e2)) / (1 + Math.sqrt(1 - e2));
  const k0 = 0.9996;
  const x = easting - 500000.0;
  const y = northing;
  const lon0 = (((35 - 1) * 6 - 180 + 3) * Math.PI) / 180;
  const m = y / k0;
  const mu = m / (a * (1 - e2 / 4 - (3 * e2 ** 2) / 64 - (5 * e2 ** 3) / 256));
  const phi1 =
    mu +
    ((3 * e1) / 2 - (27 * e1 ** 3) / 32) * Math.sin(2 * mu) +
    ((21 * e1 ** 2) / 16 - (55 * e1 ** 4) / 32) * Math.sin(4 * mu) +
    ((151 * e1 ** 3) / 96) * Math.sin(6 * mu);
  const n1 = a / Math.sqrt(1 - e2 * Math.sin(phi1) ** 2);
  const t1 = Math.tan(phi1) ** 2;
  const c1 = (e2 / (1 - e2)) * Math.cos(phi1) ** 2;
  const r1 = (a * (1 - e2)) / Math.pow(1 - e2 * Math.sin(phi1) ** 2, 1.5);
  const d = x / (n1 * k0);
  const lat =
    phi1 -
    ((n1 * Math.tan(phi1)) / r1) *
      (d ** 2 / 2 -
        ((5 + 3 * t1 + 10 * c1 - 4 * c1 ** 2 - 9 * (e2 / (1 - e2))) * d ** 4) / 24 +
        ((61 + 90 * t1 + 298 * c1 + 45 * t1 ** 2 - 252 * (e2 / (1 - e2)) - 3 * c1 ** 2) * d ** 6) / 720);
  const lon =
    lon0 +
    (d -
      ((1 + 2 * t1 + c1) * d ** 3) / 6 +
      ((5 - 2 * c1 + 28 * t1 - 3 * c1 ** 2 + 8 * (e2 / (1 - e2)) + 24 * t1 ** 2) * d ** 5) / 120) /
      Math.cos(phi1);
  return [(lon * 180) / Math.PI, (lat * 180) / Math.PI];
}

function mapCoords(coords: unknown, fn: (x: number, y: number) => Position): unknown {
  if (!Array.isArray(coords) || coords.length === 0) return coords;
  if (typeof coords[0] === "number") return fn(Number(coords[0]), Number(coords[1]));
  return coords.map((c) => mapCoords(c, fn));
}

export function toLonLatCollection<T extends { features?: Array<{ geometry?: { coordinates?: unknown }; properties?: Record<string, unknown> }> }>(
  fc: T,
): T {
  if (!looksLike32635(fc)) return fc;
  return {
    ...fc,
    features: (fc.features || []).map((feat) => ({
      ...feat,
      properties: {
        ...feat.properties,
        kind: feat.properties?.kind || feat.properties?.type || feat.properties?.label,
      },
      geometry: feat.geometry
        ? { ...feat.geometry, coordinates: mapCoords(feat.geometry.coordinates, utm35nToLonLat) }
        : feat.geometry,
    })),
  };
}
