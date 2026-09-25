# STOP — this is not the scored app

`frontend` is a **one-commit orphan** with **unrelated git history**.

- Repo-root Next.js on **:3000**
- White **SVG** canvas
- **DEMO DATA** only
- No `web/`, no MapLibre, no official tiles, no `siret3` pipeline

## Do not

- Open a pull request from `frontend` → `main` (GitHub Action fails it; a merge would overwrite the real repo)
- Draw Sireț3 labels here (Marcaj only)
- Treat these numbers or routes as submission files

## Do

- Checkout **`main`**
- Run the admission UI: `cd web && npm install && npm run dev` → http://127.0.0.1:43173
- Copy look-and-feel (Manrope, lime, layer toggles) onto `web/` if needed
- Keep this branch as a **visual mock** only
