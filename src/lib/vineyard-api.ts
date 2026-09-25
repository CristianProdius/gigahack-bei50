import { demoVineyard, type VineyardData } from "./vineyard-data";

// An API URL can be supplied once the real processing service is ready.
// This adapter keeps demo behavior and server integration out of the UI.
const apiBase = process.env.NEXT_PUBLIC_VINEYARD_API_URL?.replace(/\/$/, "");

export function isDemoMode() {
  return !apiBase;
}

export async function loadVineyard(): Promise<VineyardData> {
  if (!apiBase) return demoVineyard;
  const response = await fetch(`${apiBase}/vineyard`, { cache: "no-store" });
  if (!response.ok) throw new Error("The vineyard data could not be loaded.");
  return (await response.json()) as VineyardData;
}

type Job = {
  id: string;
  status: "queued" | "processing" | "complete" | "failed";
  progress: number;
  result?: VineyardData;
  error?: string;
};

const pause = (ms: number) => new Promise<void>((resolve) => setTimeout(resolve, ms));

export async function uploadAndAnalyze(
  file: File,
  onProgress: (progress: number) => void,
): Promise<VineyardData> {
  if (!apiBase) {
    // A UI preview only. No GeoTIFF parsing or AI analysis occurs here.
    for (const progress of [8, 19, 33, 49, 67, 83, 100]) {
      await pause(260);
      onProgress(progress);
    }
    return demoVineyard;
  }

  const formData = new FormData();
  formData.append("file", file);
  const upload = await fetch(`${apiBase}/analyses`, { method: "POST", body: formData });
  if (!upload.ok) throw new Error("The GeoTIFF could not be uploaded.");
  const { id } = (await upload.json()) as Pick<Job, "id">;
  if (!id) throw new Error("The server did not return an analysis job ID.");

  for (;;) {
    await pause(700);
    const response = await fetch(`${apiBase}/analyses/${encodeURIComponent(id)}`, {
      cache: "no-store",
    });
    if (!response.ok) throw new Error("The processing status could not be loaded.");
    const job = (await response.json()) as Job;
    onProgress(Math.max(0, Math.min(100, job.progress || 0)));
    if (job.status === "failed") throw new Error(job.error || "Analysis failed.");
    if (job.status === "complete") {
      if (!job.result) throw new Error("Analysis completed without data.");
      return job.result;
    }
  }
}
