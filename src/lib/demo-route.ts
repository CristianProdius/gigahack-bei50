import type { Point, TargetMode } from "./vineyard-data";

export type DemoTarget = { id: string; kind: "inspection" | "waste"; point: Point };
export type WasteBox = { id: string; x: number; y: number; w: number; h: number; r: number };
export type DemoRoute = {
  points: Point[];
  targetIds: string[];
  lengthM: number;
  returnsToStart: boolean;
};

export const inspectionPoints: DemoTarget[] = [
  [554, 204], [707, 273], [895, 363], [515, 385], [624, 414], [1003, 462],
  [382, 124], [424, 157], [466, 182], [366, 301], [410, 337], [461, 373],
  [555, 283], [608, 236], [660, 257], [757, 302], [812, 330], [681, 442],
  [746, 468], [811, 502], [882, 523], [966, 518], [542, 549], [608, 568],
].map(([x, y], index) => ({ id: `IP-${String(index + 1).padStart(3, "0")}`, kind: "inspection", point: { x, y } }));

export const wasteBoxes: WasteBox[] = [
  { id: "W-001", x: 488, y: 192, w: 31, h: 52, r: 13 },
  { id: "W-002", x: 614, y: 405, w: 25, h: 29, r: 12 },
  { id: "W-003", x: 1008, y: 451, w: 37, h: 44, r: 8 },
  { id: "W-004", x: 346, y: 207, w: 18, h: 20, r: 9 },
  { id: "W-005", x: 434, y: 456, w: 18, h: 18, r: 4 },
  { id: "W-006", x: 574, y: 321, w: 18, h: 18, r: 8 },
  { id: "W-007", x: 679, y: 371, w: 17, h: 18, r: 6 },
  { id: "W-008", x: 771, y: 414, w: 18, h: 19, r: 4 },
  { id: "W-009", x: 846, y: 470, w: 18, h: 18, r: 8 },
  { id: "W-010", x: 947, y: 499, w: 20, h: 18, r: 6 },
  { id: "W-011", x: 330, y: 420, w: 17, h: 19, r: 5 },
  { id: "W-012", x: 519, y: 518, w: 19, h: 18, r: 11 },
  { id: "W-013", x: 736, y: 564, w: 19, h: 18, r: 7 },
  { id: "W-014", x: 887, y: 565, w: 19, h: 19, r: 5 },
  { id: "W-015", x: 1034, y: 547, w: 20, h: 18, r: 7 },
];

export const demoTargets: DemoTarget[] = [
  ...inspectionPoints,
  ...wasteBoxes.map((box) => ({
    id: box.id,
    kind: "waste" as const,
    point: { x: box.x + box.w / 2, y: box.y + box.h / 2 },
  })),
];

// The approximate red polygon in the SVG. The route preview keeps clear of it.
const forbidden = { left: 878, top: 127, right: 1105, bottom: 350 };
const corners: Point[] = [
  { x: forbidden.left, y: forbidden.top },
  { x: forbidden.right, y: forbidden.top },
  { x: forbidden.right, y: forbidden.bottom },
  { x: forbidden.left, y: forbidden.bottom },
];

const distance = (a: Point, b: Point) => Math.hypot(a.x - b.x, a.y - b.y);

function insideForbidden(point: Point) {
  return point.x > forbidden.left && point.x < forbidden.right && point.y > forbidden.top && point.y < forbidden.bottom;
}

function crossesForbidden(a: Point, b: Point) {
  // Clip the segment against the open interior; touching the border is allowed.
  const inset = 0.01;
  const box = {
    left: forbidden.left + inset,
    top: forbidden.top + inset,
    right: forbidden.right - inset,
    bottom: forbidden.bottom - inset,
  };
  let low = 0;
  let high = 1;
  for (const [origin, delta, min, max] of [
    [a.x, b.x - a.x, box.left, box.right],
    [a.y, b.y - a.y, box.top, box.bottom],
  ]) {
    if (Math.abs(delta) < 1e-9) {
      if (origin <= min || origin >= max) return false;
      continue;
    }
    const first = (min - origin) / delta;
    const second = (max - origin) / delta;
    low = Math.max(low, Math.min(first, second));
    high = Math.min(high, Math.max(first, second));
    if (low >= high) return false;
  }
  return low < high && high > 0 && low < 1;
}

function shortestLeg(start: Point, end: Point): Point[] {
  if (!crossesForbidden(start, end)) return [start, end];
  const nodes = [start, end, ...corners];
  const costs = Array<number>(nodes.length).fill(Infinity);
  const previous = Array<number>(nodes.length).fill(-1);
  const visited = new Set<number>();
  costs[0] = 0;

  for (let step = 0; step < nodes.length; step++) {
    let current = -1;
    for (let i = 0; i < nodes.length; i++) {
      if (!visited.has(i) && (current < 0 || costs[i] < costs[current])) current = i;
    }
    if (current < 0 || !Number.isFinite(costs[current]) || current === 1) break;
    visited.add(current);
    for (let next = 0; next < nodes.length; next++) {
      if (next === current || crossesForbidden(nodes[current], nodes[next])) continue;
      const candidate = costs[current] + distance(nodes[current], nodes[next]);
      if (candidate < costs[next]) {
        costs[next] = candidate;
        previous[next] = current;
      }
    }
  }

  if (!Number.isFinite(costs[1])) return [start, end];
  const path: Point[] = [];
  for (let node = 1; node >= 0; node = previous[node]) {
    path.push(nodes[node]);
    if (node === 0) break;
  }
  return path.reverse();
}

export function buildDemoRoute(start: Point, end: Point, mode: TargetMode): DemoRoute | null {
  const targets = demoTargets.filter((target) => mode === "both" || target.kind === mode);
  if (insideForbidden(start) || insideForbidden(end) || targets.some((target) => insideForbidden(target.point))) return null;

  const nodes = [start, ...targets.map((target) => target.point), end];
  const endIndex = nodes.length - 1;
  const legs = new Map<string, Point[]>();
  function leg(a: number, b: number) {
    const key = `${a}:${b}`;
    let path = legs.get(key);
    if (!path) {
      path = shortestLeg(nodes[a], nodes[b]);
      legs.set(key, path);
    }
    return path;
  }
  function cost(a: number, b: number) {
    const path = leg(a, b);
    return path.slice(1).reduce((sum, point, index) => sum + distance(path[index], point), 0);
  }

  const remaining = new Set(targets.map((_, index) => index + 1));
  const visitOrder = [0];
  while (remaining.size) {
    const from = visitOrder[visitOrder.length - 1];
    let nearest = -1;
    for (const candidate of remaining) {
      if (nearest < 0 || cost(from, candidate) < cost(from, nearest)) nearest = candidate;
    }
    visitOrder.push(nearest);
    remaining.delete(nearest);
  }
  visitOrder.push(endIndex);

  // Improve the open tour while keeping the chosen start and end fixed.
  for (let pass = 0; pass < 6; pass++) {
    let improved = false;
    for (let first = 1; first < visitOrder.length - 2; first++) {
      for (let last = first + 1; last < visitOrder.length - 1; last++) {
        const before = cost(visitOrder[first - 1], visitOrder[first]) + cost(visitOrder[last], visitOrder[last + 1]);
        const after = cost(visitOrder[first - 1], visitOrder[last]) + cost(visitOrder[first], visitOrder[last + 1]);
        if (after + 0.001 < before) {
          const reversed = visitOrder.slice(first, last + 1).reverse();
          visitOrder.splice(first, reversed.length, ...reversed);
          improved = true;
        }
      }
    }
    if (!improved) break;
  }

  const points: Point[] = [start];
  for (let index = 1; index < visitOrder.length; index++) points.push(...leg(visitOrder[index - 1], visitOrder[index]).slice(1));
  const lengthM = points.slice(1).reduce((sum, point, index) => sum + distance(points[index], point), 0) * 1.35;
  return {
    points,
    targetIds: visitOrder.slice(1, -1).map((index) => targets[index - 1].id),
    lengthM,
    returnsToStart: distance(start, end) < 0.5,
  };
}
