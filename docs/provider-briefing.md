# Provider briefing — verbal context

Notes from the GigaHack challenge-provider session, plus a conflict table against the **scored** documents. Official PDFs win if this file and a PDF disagree.

Scored spec: [`challenge.md`](challenge.md), [`scoring.md`](scoring.md), [`annotation-rules.md`](annotation-rules.md). Pack: `data/challenge/03_docs/`. What to train: [`sota-research.md`](sota-research.md).

**Do not** invent a Marcaj “tree” class, withhold the official start, or treat this briefing as the score card.

---

## What they told teams

Challenge providers briefed teams on a GigaHack computer-vision task: build an AI model to detect vineyard trees, missed trees and waste from drone imagery, plus a web app and a route-planning tool for government inspectors.

### Challenge context (spoken)

- Moldovan government inspectors verify vineyard **area** and **tree counts** to validate subsidy eligibility.
- Dataset is drone imagery of Sireț / “Syret” vineyards in GeoTIFF, about **3 cm/px**.
- Data is **not** pre-labelled. Teams may label via the annotation platform, but the speakers said that is “not optimal.”

### Required deliverables (spoken)

- AI/ML model (they said e.g. a semantic-segmentation net) for tree detection.
- Annotations exported in the platform format (one config file with pixel-level markers).
- Conversion of pixel annotations into geospatial coordinates (GeoTIFF).
- Business measurements: row count, row length, area, per-tree IDs.
- Web application recommended, plus a GitHub link with clear instructions.

### Route planning (spoken)

- App must accept a georeferenced start point (entered via UI) and compute an optimal inspection route.
- Route visits missed / dead trees and waste, then returns to start. About **1 m** precision was called acceptable.
- Dead trees are accessible from **both sides** of a row; waste is randomly placed and accessible **one way**.
- Start-point coordinates were described as withheld until the challenge end, as an integration test.

### Scoring and constraints (spoken)

- Six sub-solutions weighted together; detailed weights to be shared as a PDF (they were — see [`scoring.md`](scoring.md)).
- Hardware and model hosting unconstrained: local weights or API-served LLMs / vision models allowed.
- Cost efficiency judged relative to comparable solutions.
- Code quality and pipeline instructions checked via static and dynamic analysis.

### Coaching and logistics

- Speaker 3 is the team coach; will connect via a Telegram group with team leaders.
- Nail the **core use case** before extras (real-time drone updates, ground robots).
- Team leaders stay after the session for one-to-one intros and Telegram setup.
- Slack challenge channel: Marcaj team **09:00–23:00**. Pinned clarifications apply to all teams.

### Spoken next steps (organisers)

- Share presentation, dataset link, and relevant Moldovan subsidy legislation.
- Provide access to the annotation platform.
- One-to-one meetings with each team leader.
- Share the detailed scoring-weights PDF.
- Survey who has NVIDIA GPUs.
- Create a general Telegram group and keep contact across the three days.

### Spoken decisions

- Dataset delivered unlabeled; teams handle labeling themselves.
- Drone imagery only (GeoTIFF). No video, no ground-robot data.
- On-device weights are not required; API-served models are permitted.
- Live model demo required during the final presentation.
- Inspection route targets “middle trees of rows” plus waste, minimizing walking.

---

## Conflict table — briefing vs official PDF

The verbal session used “Markaz” / “Syret” / “trees.” The scored project is **Marcaj**, **Sireț3**, and **grapevine canopies**. Use the right-hand column.

| Briefing claim | Official rule | What we do |
| --- | --- | --- |
| “Markaz” | **Marcaj** | Use Marcaj |
| “Labeling on the platform is not optimal” | Sireț3 drawing is **only** in Marcaj. Organizers score the published project | Pre-annotate with the model, correct in Marcaj, **submit every job** |
| Semantic segmentation of “trees” | **Instance** `vineyard` polygons, **one plant** | Instance seg. A row blob kills canopy F1 |
| Start withheld until the end | Start is in [`data/challenge/02_route/start.geojson`](../data/challenge/02_route/start.geojson) (629504.70, 5220250.75) | Use that point. UI may still let a juror type another start |
| ~1 m route precision | A target is visited if the route is within **2 m**. Start snap **5 m** | Design for 2 m / 5 m |
| Targets = “middle trees of rows” + waste | Hidden inspection locations **and** waste. Our inspect points = gaps / missing planting | Visit waste + gap midpoints. Do **not** add a Marcaj “tree” or “inspect” label |
| Dead trees reachable from both sides; waste one-way | Not in the PDF | Useful **routing** hint: approach gaps from either adjacent inter-row; waste only from the passable side |
| Live model demo | Engineering 15% + 5+5 min pitch | Keep a 3-tile infer path that runs on the laptop |
| API-served models allowed | Yes if listed in the README | Default stays **local** weights (reproducible, cheaper) |
| Nail the core use case | Coach advice | No live drone, no robots, no real-time updates |
| Six sub-solutions | 25 + 10 + 15 + 10 + 25 + 15 = 100 | See [`scoring.md`](scoring.md) |
| ~3 cm/px | Challenge tiles are **2.5 cm/px** (0.025 m); source ortho ~3.52 cm/px | Inventory reads the GeoTIFF; do not assume 3 cm |
| “Per-tree IDs” | `vineyard_id` on every object; `row_id` on rows. Canopy count is instance F1, not a tree-ID attribute | Do not invent `tree_id` in Marcaj |
| Platform export is the submission | Annotations are **exported by organizers** from Marcaj at 15:00. Repo must contain `route.geojson`, `measurements.csv`, README, code | We still export for measurements and the map |

---

## Logistics that still matter

- **Deadline:** Sunday 27 Sep 2026, 15:00 Europe/Chisinau. Repo **and** Marcaj freeze together.
- **Prize:** MDL 30,000, one team. Subsidy story in the PDF: MDL 52,000–80,000 / ha maintenance; 20 ha → MDL 1.04–1.60 million / year. Route example: 6 km → 4.2 km = 27 min at 4 km/h.
- **Compute:** none provided. Own laptop or cloud. No model-size limit. Weights may be a link.
- **Support:** GigaHack Slack challenge channel, Marcaj 09:00–23:00. Coach on Telegram for team leaders.
- **Pitch:** 5 min + 5 min questions. Show the working web interface (map, objects, IDs, measurements, route). Laptop demo accepted; deployed URL goes in the README.
- **Admission:** working UI, published Marcaj with submitted jobs, correct formats and georeferencing.

## How this file is used

Read it so the subsidy / inspector story and the both-sides gap hint are not lost. When implementing labels, CRS, start, or scores, open [`challenge.md`](challenge.md) and [`scoring.md`](scoring.md) instead.
