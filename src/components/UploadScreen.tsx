"use client";

import { useEffect, useRef, useState, type DragEvent } from "react";
import { ImageUp, LoaderCircle, Upload, X } from "lucide-react";
import Brand from "./Brand";

export type VineyardIdentity = { name: string; id: string };

export default function UploadScreen({ active, motion, busy, progress, filename, error, demo, identity, onUpload, onClose }: {
  active: boolean;
  motion: "initial" | "enter" | "exit";
  busy: boolean;
  progress: number;
  filename: string;
  error: string;
  demo: boolean;
  identity: VineyardIdentity;
  onUpload: (file: File, identity: VineyardIdentity) => Promise<void>;
  onClose: () => void;
}) {
  const [name, setName] = useState(identity.name);
  const [id, setId] = useState(identity.id);
  const [dragging, setDragging] = useState(false);
  const [localError, setLocalError] = useState("");
  const form = useRef<HTMLFormElement>(null);
  const input = useRef<HTMLInputElement>(null);
  const heading = useRef<HTMLHeadingElement>(null);
  const dragDepth = useRef(0);
  const showingProgress = busy || (progress === 100 && motion === "exit");

  useEffect(() => {
    if (!active) return;
    heading.current?.focus({ preventScroll: true });
    const onKey = (event: KeyboardEvent) => {
      if (event.key === "Escape" && !busy) onClose();
    };
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [active, busy, onClose]);

  function validIdentity() {
    if (!name.trim() || !id.trim()) {
      setLocalError("Enter the vineyard name and ID before choosing a map.");
      form.current?.reportValidity();
      return false;
    }
    setLocalError("");
    return form.current?.reportValidity() ?? false;
  }

  function selectFile() {
    if (!busy && validIdentity()) input.current?.click();
  }

  function acceptFile(file?: File) {
    if (!file || busy || !validIdentity()) return;
    void onUpload(file, { name: name.trim(), id: id.trim() });
  }

  function handleDrop(event: DragEvent<HTMLDivElement>) {
    event.preventDefault();
    dragDepth.current = 0;
    setDragging(false);
    if (event.dataTransfer.files.length > 1) {
      setLocalError("Choose one GeoTIFF map at a time.");
      return;
    }
    acceptFile(event.dataTransfer.files[0]);
  }

  return (
    <section className="upload-screen" data-motion={motion} aria-labelledby="upload-heading" aria-hidden={!active} inert={!active}>
      <div className="upload-vineyard-pattern" aria-hidden="true" />
      <header className="upload-screen-header">
        <Brand />
        <button type="button" className="round-action upload-close grid place-items-center" aria-label="Return to map" title="Return to map" onClick={onClose} disabled={busy}><X size={22} /></button>
      </header>
      <div className="upload-screen-content">
        <div className="upload-heading-block">
          <h1 id="upload-heading" ref={heading} tabIndex={-1}>Upload your vineyard map</h1>
          <p>Choose an aerial image to get started</p>
        </div>
        <form ref={form} className="vineyard-identity-form" onSubmit={(event) => { event.preventDefault(); selectFile(); }}>
          <label className="upload-field" htmlFor="vineyard-name"><span>Vineyard name</span><input id="vineyard-name" name="vineyardName" value={name} onChange={(event) => { setName(event.target.value); setLocalError(""); }} placeholder="e.g. Siret Vineyard" required pattern=".*\S.*" maxLength={100} disabled={busy} autoComplete="off" /></label>
          <label className="upload-field" htmlFor="vineyard-id"><span>Vineyard ID</span><input id="vineyard-id" name="vineyardId" value={id} onChange={(event) => { setId(event.target.value); setLocalError(""); }} placeholder="e.g. VIN-001" required pattern=".*\S.*" maxLength={64} disabled={busy} autoComplete="off" /></label>
          <button type="submit" className="sr-only" tabIndex={-1}>Choose file</button>
        </form>
        <div className="upload-dropzone" data-dragging={dragging} aria-busy={busy}
          onDragEnter={(event) => { event.preventDefault(); if (!busy) { dragDepth.current += 1; setDragging(true); } }}
          onDragOver={(event) => { event.preventDefault(); event.dataTransfer.dropEffect = busy ? "none" : "copy"; }}
          onDragLeave={(event) => { event.preventDefault(); dragDepth.current = Math.max(0, dragDepth.current - 1); if (dragDepth.current === 0) setDragging(false); }} onDrop={handleDrop}>
          <div className="upload-dropzone-main">
            {showingProgress ? <LoaderCircle className="upload-main-icon upload-spinner" size={76} strokeWidth={1.2} /> : <ImageUp className="upload-main-icon" size={76} strokeWidth={1.2} />}
            <h2>{showingProgress ? (progress === 100 ? "Opening your map…" : "Preparing your map…") : dragging ? "Release to upload your map" : "Drop your map here"}</h2>
            {showingProgress ? <div className="upload-processing" role="status" aria-live="polite"><p className="upload-filename" title={filename}>{filename}</p><div className="upload-progress" role="progressbar" aria-label="Map processing" aria-valuenow={progress} aria-valuemin={0} aria-valuemax={100}><span style={{ width: `${progress}%` }} /></div><strong>{progress}%</strong></div> : <><span className="upload-or">or</span><button type="button" className="choose-file-button" onClick={selectFile}><Upload size={23} strokeWidth={2} />Choose file</button><p className="upload-formats">GeoTIFF · TIF · TIFF</p></>}
            {(localError || error) && <p className="upload-error" role="alert">{localError || error}</p>}
          </div>
          <p className="upload-footnote">{showingProgress && demo ? "Preview mode · the map remains a demo placeholder" : "Processing starts automatically after upload"}</p>
          <input ref={input} type="file" accept=".tif,.tiff,image/tiff" className="hidden" disabled={busy} tabIndex={-1} aria-hidden="true" onChange={(event) => { const file = event.target.files?.[0]; event.target.value = ""; acceptFile(file); }} />
        </div>
      </div>
    </section>
  );
}
