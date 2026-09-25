import { VineyardMap } from "@/components/vineyard-map";

export default function Home() {
  return (
    <div className="flex min-h-screen flex-col bg-stone-50">
      <header className="border-b border-stone-200 bg-white">
        <div className="mx-auto flex w-full max-w-6xl flex-col gap-1 px-4 py-4 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <p className="text-xs uppercase tracking-wide text-emerald-800">GigaHack · Marcaj</p>
            <h1 className="text-xl font-semibold text-stone-900 sm:text-2xl">Sireț3 vineyard map</h1>
          </div>
          <p className="max-w-xl text-sm text-stone-600">
            Canopy, rows, inter-rows, waste, and a closed inspection walk. Measurements are planar EPSG:32635. Deadline Sunday 27 Sep 2026, 15:00 Chișinău.
          </p>
        </div>
      </header>
      <main className="mx-auto flex min-h-0 w-full max-w-6xl flex-1 flex-col px-4 py-4">
        <VineyardMap />
      </main>
    </div>
  );
}
