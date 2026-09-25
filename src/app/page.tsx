import VineyardWorkspace from "@/components/VineyardWorkspace";

export default function Home() {
  return (
    <>
      <aside
        role="status"
        style={{
          position: "sticky",
          top: 0,
          zIndex: 80,
          padding: "10px 16px",
          background: "#d1fb55",
          color: "#152e11",
          fontFamily: "Manrope, Arial, sans-serif",
          fontSize: 14,
          fontWeight: 700,
          lineHeight: 1.35,
        }}
      >
        DEMO / ORPHAN BRANCH — not the scored app. Do not merge into main. Real map:{" "}
        <code>web/</code> on <code>main</code> (http://127.0.0.1:43173). See STOP.md.
      </aside>
      <VineyardWorkspace />
    </>
  );
}
