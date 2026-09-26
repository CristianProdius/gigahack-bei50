import type { Point } from "./vineyard-data";

export type MapView = { zoom: number; center: Point };
export type MapProjection = { scale: number; left: number; top: number };

export function mapProjection(rect: { width: number; height: number; left: number; top: number }): MapProjection {
  const scale = Math.max(rect.width / 1440, rect.height / 810, 0.001);
  return { scale, left: rect.left + (rect.width - 1440 * scale) / 2, top: rect.top + (rect.height - 810 * scale) / 2 };
}

export function mapScreenPoint(x: number, y: number, projection: MapProjection): Point {
  return { x: (x - projection.left) / projection.scale, y: (y - projection.top) / projection.scale };
}

export function zoomAround(view: MapView, zoom: number, anchor: Point): MapView {
  const nextZoom = Math.max(0.5, Math.min(4, zoom));
  return {
    zoom: nextZoom,
    center: {
      x: view.center.x + (anchor.x - 720) * (1 / view.zoom - 1 / nextZoom),
      y: view.center.y + (anchor.y - 405) * (1 / view.zoom - 1 / nextZoom),
    },
  };
}

type Scheduler = {
  requestFrame: (callback: (timestamp: number) => void) => number;
  cancelFrame: (id: number) => void;
  reducedMotion: () => boolean;
};

/** Keep camera motion outside React. Input bursts accumulate into one paint per frame. */
export class MapViewport {
  private view: MapView = { zoom: 1, center: { x: 720, y: 405 } };
  private target: MapView = this.view;
  private frame: number | null = null;
  private previousTime: number | null = null;
  private flying = false;
  private velocity = { zoom: 0, x: 0, y: 0 };

  constructor(private scheduler: Scheduler, private paint: (view: MapView) => void, private onRest: (view: MapView) => void) {}

  getView() { return this.view; }
  getTarget() { return this.target; }

  private schedule() {
    if (this.frame === null) this.frame = this.scheduler.requestFrame(this.step);
  }

  private interruptFlight() {
    if (!this.flying) return;
    this.flying = false;
    this.velocity = { zoom: 0, x: 0, y: 0 };
    this.target = this.view;
  }

  pan(x: number, y: number, projectionScale: number) {
    if (x === 0 && y === 0) return;
    this.interruptFlight();
    const scale = projectionScale * this.target.zoom;
    this.target = { zoom: this.target.zoom, center: { x: this.target.center.x + x / scale, y: this.target.center.y + y / scale } };
    this.schedule();
  }

  pinch(factor: number, anchor: Point) {
    if (factor === 1) return;
    this.interruptFlight();
    const target = zoomAround(this.target, this.target.zoom * factor, anchor);
    if (target.zoom === this.target.zoom) return;
    this.target = target;
    this.schedule();
  }

  dragTo(view: MapView) {
    this.flying = false;
    this.target = view;
    this.schedule();
  }

  flyTo(view: MapView) {
    const target = { zoom: Math.max(0.5, Math.min(4, view.zoom)), center: { ...view.center } };
    if (target.zoom === this.view.zoom && target.center.x === this.view.center.x && target.center.y === this.view.center.y) {
      this.stop();
      this.onRest(this.view);
      return;
    }
    this.target = target;
    // Retarget the same spring. Repeated zoom clicks retain their velocity.
    this.flying = true;
    this.schedule();
  }

  stop() {
    if (this.frame !== null) this.scheduler.cancelFrame(this.frame);
    this.frame = null;
    this.flying = false;
    this.velocity = { zoom: 0, x: 0, y: 0 };
    this.previousTime = null;
    this.target = this.view;
  }

  private step = (timestamp: number) => {
    this.frame = null;
    const elapsed = Math.min(64, Math.max(1, this.previousTime === null ? 16 : timestamp - this.previousTime));
    this.previousTime = timestamp;
    if (this.scheduler.reducedMotion()) {
      this.view = this.target;
      this.velocity = { zoom: 0, x: 0, y: 0 };
    } else {
      // Solve a critically damped spring in camera-matrix space. Position and
      // velocity stay continuous when wheel events or button presses retarget it.
      // Native trackpad momentum already arrives as wheel events; do not add it twice.
      const frequency = this.flying ? 13 : 38;
      const dt = elapsed / 1000;
      const zoom = this.spring(this.view.zoom, this.target.zoom, this.velocity.zoom, frequency, dt);
      const x = this.spring(720 - this.view.center.x * this.view.zoom, 720 - this.target.center.x * this.target.zoom, this.velocity.x, frequency, dt);
      const y = this.spring(405 - this.view.center.y * this.view.zoom, 405 - this.target.center.y * this.target.zoom, this.velocity.y, frequency, dt);
      const scale = Math.max(0.5, Math.min(4, zoom.position));
      this.velocity = { zoom: scale === zoom.position ? zoom.velocity : 0, x: x.velocity, y: y.velocity };
      this.view = { zoom: scale, center: { x: (720 - x.position) / scale, y: (405 - y.position) / scale } };
    }
    const settled = Math.abs(this.view.zoom - this.target.zoom) < 0.00005 && Math.hypot(this.view.center.x - this.target.center.x, this.view.center.y - this.target.center.y) * this.view.zoom < 0.02 && Math.abs(this.velocity.zoom) < 0.001 && Math.hypot(this.velocity.x, this.velocity.y) < 0.5;
    if (settled) { this.view = this.target; this.velocity = { zoom: 0, x: 0, y: 0 }; this.flying = false; }
    this.paint(this.view);
    if (settled) {
      this.previousTime = null;
      this.onRest(this.view);
    } else this.schedule();
  };

  private spring(position: number, target: number, velocity: number, frequency: number, dt: number) {
    const distance = position - target;
    const coefficient = velocity + frequency * distance;
    const decay = Math.exp(-frequency * dt);
    return { position: target + (distance + coefficient * dt) * decay, velocity: (velocity - frequency * coefficient * dt) * decay };
  }
}
