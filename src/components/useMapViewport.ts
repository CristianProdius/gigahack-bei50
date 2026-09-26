"use client";

import { useEffect, useImperativeHandle, useRef, type MouseEvent, type PointerEvent, type Ref } from "react";
import { MapViewport, mapProjection, mapScreenPoint, zoomAround, type MapView, type MapProjection } from "@/lib/map-viewport";
import type { Point } from "@/lib/vineyard-data";

export type MapHandle = { zoomBy: (amount: number) => void; flyTo: (center: Point, zoom: number) => void; reset: () => void };

export function useMapViewport(ref: Ref<MapHandle>, placingPoint: "start" | "end" | null, onPlacePoint: (point: Point) => void, onRest: (zoom: number) => void) {
  const canvas = useRef<HTMLDivElement>(null);
  const camera = useRef<HTMLDivElement>(null);
  const controller = useRef<MapViewport | null>(null);
  const projection = useRef<MapProjection>({ scale: 1, left: 0, top: 0 });
  const callbacks = useRef({ placingPoint, onPlacePoint, onRest });
  callbacks.current = { placingPoint, onPlacePoint, onRest };
  const drag = useRef<{ pointerId: number; x: number; y: number; view: MapView; scale: number } | null>(null);
  const dragged = useRef(false);
  const markActive = useRef<() => void>(() => {});

  useImperativeHandle(ref, () => ({
    zoomBy: (amount) => {
      const map = controller.current;
      if (!map) return;
      markActive.current();
      const view = map.getTarget();
      map.flyTo({ center: view.center, zoom: view.zoom + amount });
    },
    flyTo: (center, zoom) => { markActive.current(); controller.current?.flyTo({ center, zoom }); },
    reset: () => controller.current?.flyTo({ center: { x: 720, y: 405 }, zoom: 1 }),
  }), []);

  useEffect(() => {
    const viewport = canvas.current;
    const layer = camera.current;
    if (!viewport || !layer) return;
    const motion = window.matchMedia("(prefers-reduced-motion: reduce)");
    let quietTimer = 0;
    let active = false;
    const keepActive = () => {
      active = true;
      viewport.classList.add("is-interacting");
      window.clearTimeout(quietTimer);
      quietTimer = window.setTimeout(() => { active = false; viewport.classList.remove("is-interacting"); }, 180);
    };
    let localProjection: MapProjection = { scale: 1, left: 0, top: 0 };
    const paint = (view: MapView) => {
      const { scale, left, top } = localProjection;
      const x = left + scale * (720 - view.center.x * view.zoom);
      const y = top + scale * (405 - view.center.y * view.zoom);
      // Move one HTML compositor layer, rather than repainting each SVG shape.
      layer.style.transform = `translate3d(${x}px, ${y}px, 0) scale(${scale * view.zoom})`;
    };
    const updateProjection = () => {
      const rect = viewport.getBoundingClientRect();
      projection.current = mapProjection(rect);
      localProjection = mapProjection({ width: rect.width, height: rect.height, left: 0, top: 0 });
      if (controller.current) paint(controller.current.getView());
    };
    const map = new MapViewport({ requestFrame: (callback) => window.requestAnimationFrame(callback), cancelFrame: (id) => window.cancelAnimationFrame(id), reducedMotion: () => motion.matches }, (view) => {
      keepActive();
      paint(view);
    }, (view) => callbacks.current.onRest(view.zoom));
    controller.current = map;
    updateProjection();
    const observer = new ResizeObserver(updateProjection);
    observer.observe(viewport);
    window.addEventListener("scroll", updateProjection, { passive: true, capture: true });
    markActive.current = () => {
      if (!active) updateProjection();
      keepActive();
    };
    let gestureStart: { view: MapView; anchor: Point } | null = null;
    let gestureEndedAt = -Infinity;
    const wheel = (event: WheelEvent) => {
      event.preventDefault();
      // Safari can emit both native gesture and ctrl-wheel events for one pinch.
      if ((event.ctrlKey || event.metaKey) && (gestureStart || event.timeStamp - gestureEndedAt < 80)) return;
      markActive.current();
      const unit = event.deltaMode === 1 ? 16 : event.deltaMode === 2 ? viewport.clientHeight : 1;
      if (event.ctrlKey || event.metaKey) {
        const anchor = mapScreenPoint(event.clientX, event.clientY, projection.current);
        map.pinch(Math.exp(-event.deltaY * unit * 0.006), anchor);
      } else map.pan(event.deltaX * unit, event.deltaY * unit, projection.current.scale);
    };
    viewport.addEventListener("wheel", wheel, { passive: false });
    const gesture = (event: Event) => {
      const pinch = event as Event & { scale: number; clientX: number; clientY: number };
      event.preventDefault();
      markActive.current();
      if (event.type === "gestureend") { gestureStart = null; gestureEndedAt = event.timeStamp; return; }
      if (event.type === "gesturestart") {
        map.stop();
        const rect = viewport.getBoundingClientRect();
        gestureStart = { view: map.getView(), anchor: mapScreenPoint(Number.isFinite(pinch.clientX) ? pinch.clientX : rect.left + rect.width / 2, Number.isFinite(pinch.clientY) ? pinch.clientY : rect.top + rect.height / 2, projection.current) };
      } else if (gestureStart && Number.isFinite(pinch.scale)) {
        // Safari reports an absolute scale from gesturestart; never multiply it twice.
        const next = zoomAround(gestureStart.view, gestureStart.view.zoom * pinch.scale, gestureStart.anchor);
        const current = map.getTarget();
        map.pinch(next.zoom / current.zoom, gestureStart.anchor);
      }
    };
    for (const type of ["gesturestart", "gesturechange", "gestureend"]) viewport.addEventListener(type, gesture, { passive: false });
    return () => {
      map.stop();
      controller.current = null;
      markActive.current = () => {};
      window.clearTimeout(quietTimer);
      observer.disconnect();
      viewport.classList.remove("is-interacting", "is-panning");
      window.removeEventListener("scroll", updateProjection, true);
      viewport.removeEventListener("wheel", wheel);
      for (const type of ["gesturestart", "gesturechange", "gestureend"]) viewport.removeEventListener(type, gesture);
    };
  }, []);

  function beginPan(event: PointerEvent<HTMLDivElement>) {
    const map = controller.current;
    if (event.button !== 0 || !map) return;
    map.stop();
    projection.current = mapProjection(event.currentTarget.getBoundingClientRect());
    dragged.current = false;
    drag.current = { pointerId: event.pointerId, x: event.clientX, y: event.clientY, view: map.getView(), scale: projection.current.scale };
  }

  function movePan(event: PointerEvent<HTMLDivElement>) {
    const initial = drag.current;
    if (!initial || initial.pointerId !== event.pointerId) return;
    if (!dragged.current && Math.hypot(event.clientX - initial.x, event.clientY - initial.y) < 5) return;
    if (!dragged.current) { dragged.current = true; event.currentTarget.classList.add("is-panning"); event.currentTarget.setPointerCapture(event.pointerId); }
    markActive.current();
    const scale = initial.scale * initial.view.zoom;
    controller.current?.dragTo({ zoom: initial.view.zoom, center: { x: initial.view.center.x + (initial.x - event.clientX) / scale, y: initial.view.center.y + (initial.y - event.clientY) / scale } });
  }

  function endPan(event: PointerEvent<HTMLDivElement>) {
    if (drag.current?.pointerId !== event.pointerId) return;
    drag.current = null;
    event.currentTarget.classList.remove("is-panning");
    if (event.currentTarget.hasPointerCapture(event.pointerId)) event.currentTarget.releasePointerCapture(event.pointerId);
  }

  function handleMapClick(event: MouseEvent<HTMLDivElement>) {
    if (!callbacks.current.placingPoint) return;
    const view = controller.current?.getView();
    if (!view) return;
    projection.current = mapProjection(event.currentTarget.getBoundingClientRect());
    const screen = mapScreenPoint(event.clientX, event.clientY, projection.current);
    const point = { x: view.center.x + (screen.x - 720) / view.zoom, y: view.center.y + (screen.y - 405) / view.zoom };
    callbacks.current.onPlacePoint({ x: Math.round(point.x), y: Math.round(point.y) });
  }

  return { canvas, camera, handlers: {
    onPointerDown: beginPan, onPointerMove: movePan, onPointerUp: endPan, onPointerCancel: endPan,
    onLostPointerCapture: () => { drag.current = null; canvas.current?.classList.remove("is-panning"); },
    onClickCapture: (event: MouseEvent<HTMLDivElement>) => { if (dragged.current) { event.stopPropagation(); dragged.current = false; } },
    onClick: handleMapClick,
  } };
}
