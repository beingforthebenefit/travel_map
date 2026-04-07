# travel_map — Product & Technical Specification

## Overview

A self-hosted web application that generates high-resolution, print-ready stylized maps for multi-city trips. The user inputs an ordered list of stops (city, dates, optional photo), configures style and print settings, and the app renders a composited map image with a route path, photo bubbles, city labels, and a title banner. Output targets physical print (posters, framed art).

---

## Architecture

```
┌─────────────────────────────────────┐
│         Docker Compose              │
│                                     │
│  ┌──────────────┐  ┌─────────────┐  │
│  │  frontend     │  │  backend    │  │
│  │  React/Vite   │  │  FastAPI    │  │
│  │  Nginx (prod) │──│  Python 3.12│  │
│  │  :3000        │  │  :8000      │  │
│  └──────────────┘  └──────┬──────┘  │
│                           │         │
│                    ┌──────┴──────┐  │
│                    │  /data      │  │
│                    │  (volume)   │  │
│                    │  trips/     │  │
│                    │  tile_cache/│  │
│                    │  output/    │  │
│                    └─────────────┘  │
└─────────────────────────────────────┘
```

### Stack

| Layer | Technology | Rationale |
|-------|-----------|-----------|
| Frontend | React 18 + TypeScript + Vite | Fast iteration, strong typing, widely supported |
| Styling | Tailwind CSS 4 | Utility-first, no custom CSS sprawl |
| State | Zustand | Minimal boilerplate, good DevTools |
| Drag & drop | dnd-kit | Accessible, performant reordering of stops |
| Backend | FastAPI + Python 3.12 | Same language as rendering pipeline, async, auto-generated OpenAPI docs |
| Rendering | Pillow + PyCairo | Proven from POC; Pillow for compositing, Cairo for anti-aliased vector paths |
| Geocoding | Nominatim (OpenStreetMap) | Free, no API key, sufficient for city-level lookup |
| Map tiles | Stadia Maps (primary), CartoDB/OSM (fallback) | Stamen Watercolor is the best aesthetic; CartoDB free fallback |
| Storage | Filesystem + SQLite | No need for a full RDBMS; SQLite for trip metadata, filesystem for images |
| Containerization | Docker Compose | Two services (frontend, backend), one data volume |
| Testing | Vitest (frontend), pytest (backend) | Standard, fast, good DX |

### Why not Node.js for the backend

The rendering pipeline is inherently Python (Pillow, PyCairo, numpy). Wrapping it in Express would mean either shelling out to Python or maintaining two runtimes. FastAPI is performant, generates OpenAPI docs automatically, and keeps the stack to one backend language.

---

## Data Model

### Trip (SQLite: `trips` table)

```sql
CREATE TABLE trips (
    id            TEXT PRIMARY KEY,   -- UUID
    title         TEXT NOT NULL,
    subtitle      TEXT DEFAULT '',
    created_at    TEXT NOT NULL,      -- ISO 8601
    updated_at    TEXT NOT NULL,
    style         TEXT DEFAULT 'watercolor',
    print_width   REAL DEFAULT 24.0,  -- inches
    print_height  REAL DEFAULT 18.0,
    dpi           INTEGER DEFAULT 300,
    show_title    INTEGER DEFAULT 1,
    api_key_ref   TEXT DEFAULT NULL    -- 'env' = use STADIA_API_KEY env var
);
```

### Stop (SQLite: `stops` table)

```sql
CREATE TABLE stops (
    id            TEXT PRIMARY KEY,
    trip_id       TEXT NOT NULL REFERENCES trips(id) ON DELETE CASCADE,
    sort_order    INTEGER NOT NULL,
    city          TEXT NOT NULL,
    label         TEXT DEFAULT NULL,   -- display override (e.g. "Madrid (return)")
    lat           REAL NOT NULL,
    lon           REAL NOT NULL,
    dates         TEXT NOT NULL,       -- freeform, e.g. "Mar 27–29"
    nights        INTEGER DEFAULT 0,
    highlight     INTEGER DEFAULT 0,
    photo_path    TEXT DEFAULT NULL,   -- relative to /data/trips/{trip_id}/photos/
    created_at    TEXT NOT NULL
);
```

### Filesystem layout

```
/data/
├── db.sqlite3
├── tile_cache/
│   └── {provider}/{z}/{x}/{y}.png
├── trips/
│   └── {trip_id}/
│       ├── photos/
│       │   ├── {stop_id}_original.jpg
│       │   └── {stop_id}_thumb.jpg     (256×256, for UI preview)
│       └── output/
│           ├── travel_map_watercolor.png
│           └── travel_map_dark.png
└── fonts/
    ├── PlayfairDisplay-Bold.ttf
    └── SourceSans3-Regular.ttf
```

---

## API Endpoints

Base: `/api/v1`

### Trips

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/trips` | List all trips (summary: id, title, updated_at, stop count, has_output) |
| `POST` | `/trips` | Create trip. Body: `{ title, subtitle? }`. Returns full trip object. |
| `GET` | `/trips/{id}` | Get trip with all stops (ordered) |
| `PUT` | `/trips/{id}` | Update trip metadata (title, subtitle, style, print settings) |
| `DELETE` | `/trips/{id}` | Delete trip, all stops, photos, and outputs |
| `POST` | `/trips/{id}/duplicate` | Deep-copy a trip |
| `POST` | `/trips/import` | Import from YAML (same schema as POC) |
| `GET` | `/trips/{id}/export` | Export trip as YAML |

### Stops

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/trips/{id}/stops` | Add stop. Body: `{ city, dates, lat?, lon?, nights?, highlight? }`. If lat/lon omitted, geocode via Nominatim. |
| `PUT` | `/trips/{id}/stops/{stop_id}` | Update stop fields |
| `DELETE` | `/trips/{id}/stops/{stop_id}` | Delete stop and its photo |
| `PUT` | `/trips/{id}/stops/reorder` | Body: `{ stop_ids: string[] }` — set new sort order |
| `POST` | `/trips/{id}/stops/{stop_id}/photo` | Upload photo (multipart). Server generates thumbnail. Max 20 MB. |
| `DELETE` | `/trips/{id}/stops/{stop_id}/photo` | Remove photo |

### Rendering

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/trips/{id}/render` | Queue render job. Body: `{ style?, all_styles? }`. Returns `{ job_id }`. |
| `GET` | `/trips/{id}/render/status` | Poll status: `{ status: "pending" | "rendering" | "done" | "error", progress?: number, styles_complete?: string[] }` |
| `GET` | `/trips/{id}/render/{style}.png` | Download rendered map image |
| `GET` | `/trips/{id}/render/preview` | Low-res preview (zoom reduced, 1200px wide) for in-app display |

### Settings

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/settings` | Get global settings (tile API key status, default style, default print size) |
| `PUT` | `/settings` | Update global settings |

### Geocoding

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/geocode?q={city}` | Search Nominatim. Returns `[{ display_name, lat, lon }]`. Rate-limited to 1 req/sec per Nominatim policy. |

---

## Frontend

### Pages / Views

**1. Trip List** (`/`)
- Card grid of saved trips. Each card shows: title, subtitle, stop count, last updated, thumbnail of most recent render (or placeholder).
- "New Trip" button. Import from YAML button.

**2. Trip Editor** (`/trips/{id}`)
- Two-panel layout:
  - **Left panel**: interactive Leaflet.js map showing current stops as markers with route polyline. Click map to add a stop. Markers are draggable to adjust coordinates.
  - **Right panel**: ordered stop list (drag to reorder via dnd-kit). Each stop row shows:
    - City name (editable inline)
    - Dates (editable inline)
    - Lat/Lon (shown small, editable on click)
    - Photo thumbnail (click to upload/replace, × to remove)
    - Highlight toggle (star icon)
    - Delete button
  - "Add Stop" row at bottom with city search (Nominatim typeahead, debounced 500ms).
- Top bar: trip title (editable), subtitle (editable), "Settings" gear icon, "Generate Map" primary button.

**3. Settings Panel** (slide-over drawer from Trip Editor)
- **Map Style**: visual selector showing thumbnail previews of each style. Styles:
  - `watercolor` — Stamen Watercolor (requires Stadia API key)
  - `toner` — Stamen Toner Lite (requires Stadia API key)
  - `terrain` — Stamen Terrain (requires Stadia API key)
  - `positron` — CartoDB Positron (free)
  - `dark` — CartoDB Dark Matter (free)
  - `osm` — OpenStreetMap Standard (free)
- **Print Size**: dropdown presets (18×12, 24×18, 36×24, custom) + custom W×H inputs.
- **DPI**: 150 (draft), 300 (print), custom.
- **Title**: show/hide toggle, custom title/subtitle override.
- **Route Style**: solid, dashed, dotted. Line weight slider (thin/medium/thick).
- **Photo Bubbles**: diameter slider, border color picker, show/hide for cities without photos.
- **Label Style**: font size slider, background opacity slider.
- **API Key**: Stadia Maps API key input. Stored server-side in env or SQLite settings table. Status indicator (valid/missing/invalid). "Stamen styles require a free Stadia API key" helper text with signup link.
- **Generate All Styles**: toggle. When enabled, "Generate Map" produces one image per available style.

**4. Render Output** (modal or dedicated view)
- Shows rendered map(s) at screen resolution with zoom/pan.
- Download button per style (full resolution PNG).
- "Regenerate" button.
- Progress bar during rendering with tile-fetch and compositing stages.

### UI/UX Requirements

- Responsive down to 1024px width (this is a desktop-first tool, not mobile).
- Dark mode support (system preference, toggle in header).
- All destructive actions require confirmation.
- Optimistic UI for stop reordering and inline edits.
- Toast notifications for async results (render complete, errors).
- Drag and drop file upload for photos (on the stop row and on a dedicated drop zone).
- Keyboard shortcuts: `Ctrl+S` save, `Ctrl+Enter` generate, `Ctrl+Z` undo last stop edit.

---

## Rendering Pipeline (Backend Detail)

This is the core of the application. The rendering pipeline runs as a background task (FastAPI `BackgroundTasks` or a simple in-process thread pool, no need for Celery).

### Pipeline stages

1. **Bounds calculation**: compute lat/lon bounding box from stops with configurable padding.
2. **Zoom selection**: pick optimal tile zoom level for the output resolution.
3. **Tile fetching**: fetch tiles from provider with disk cache, retry logic (3 attempts, exponential backoff), 50ms delay between requests. Report progress as `tiles_fetched / tiles_total`.
4. **Tile stitching**: composite tiles into a single RGBA canvas at output resolution. Center the map extent in the canvas.
5. **Route drawing** (PyCairo): draw the route path as a smooth polyline with configurable style (solid/dashed/dotted), directional arrows, and a subtle drop shadow.
6. **Photo compositing** (Pillow): for each stop with a photo, create a circular crop with border ring, position above the stop coordinate. For stops without photos, draw a styled dot marker.
7. **Label drawing** (Pillow): city name (bold) + dates (accent color) on a semi-transparent background pill, positioned below each stop marker. Collision avoidance: if labels overlap, nudge them apart vertically.
8. **Title banner** (Pillow): semi-transparent banner at top of canvas with title and subtitle.
9. **Flatten and export**: convert to RGB, save as PNG at target DPI.

### Label collision avoidance

After placing all labels at their default positions (directly below the marker), run a simple iterative nudge pass:
- For each pair of labels, if bounding boxes overlap, push the lower one down by the overlap amount + 8px padding.
- Run 3 iterations max. This handles the common case (vertically stacked nearby stops) without overengineering.

### Coordinate projection

Use Web Mercator (EPSG:3857) throughout, matching the tile coordinate system. The `lat_lon_to_tile` / `tile_to_lat_lon` functions from the POC are correct and should be preserved.

---

## Configuration

### Environment Variables

```env
# Required for Stamen tile styles
STADIA_API_KEY=your_key_here

# Optional
DATA_DIR=/data                    # persistent volume mount
HOST=0.0.0.0
PORT=8000
LOG_LEVEL=info
MAX_UPLOAD_MB=20
NOMINATIM_USER_AGENT=travel_map/1.0 (your@email.com)
```

### Docker Compose

```yaml
services:
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    volumes:
      - app_data:/data
    environment:
      - STADIA_API_KEY=${STADIA_API_KEY:-}
      - DATA_DIR=/data
    restart: unless-stopped

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
      args:
        VITE_API_URL: /api/v1
    ports:
      - "3000:80"
    depends_on:
      - backend
    restart: unless-stopped

volumes:
  app_data:
```

The frontend Dockerfile builds the Vite app and serves it via Nginx, which also reverse-proxies `/api` to the backend container.

---

## Repository Structure

```
travel_map/
├── README.md
├── docker-compose.yml
├── .env.example
├── backend/
│   ├── Dockerfile
│   ├── pyproject.toml              (deps: fastapi, uvicorn, pillow, pycairo, numpy, httpx, aiosqlite)
│   ├── alembic.ini                 (if using migrations, otherwise init_db on startup)
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                 (FastAPI app, lifespan, CORS, static mounts)
│   │   ├── config.py               (pydantic-settings: env vars, defaults)
│   │   ├── database.py             (aiosqlite connection, schema init)
│   │   ├── models.py               (Pydantic request/response schemas)
│   │   ├── routers/
│   │   │   ├── trips.py
│   │   │   ├── stops.py
│   │   │   ├── render.py
│   │   │   ├── settings.py
│   │   │   └── geocode.py
│   │   ├── services/
│   │   │   ├── trip_service.py     (CRUD logic)
│   │   │   ├── photo_service.py    (upload, thumbnail generation, cleanup)
│   │   │   ├── geocode_service.py  (Nominatim client with rate limiting)
│   │   │   └── render_service.py   (orchestrates the rendering pipeline)
│   │   ├── renderer/
│   │   │   ├── __init__.py
│   │   │   ├── pipeline.py         (top-level generate_map, progress callback)
│   │   │   ├── tiles.py            (fetch, cache, stitch)
│   │   │   ├── route.py            (path drawing with PyCairo)
│   │   │   ├── labels.py           (text rendering, collision avoidance)
│   │   │   ├── photos.py           (circular crop, bubble compositing)
│   │   │   ├── styles.py           (tile provider configs, color palettes)
│   │   │   └── fonts.py            (font loading, bundled font paths)
│   │   └── fonts/
│   │       ├── PlayfairDisplay-Bold.ttf
│   │       └── SourceSans3-Regular.ttf
│   └── tests/
│       ├── conftest.py             (test client fixture, temp DB, temp data dir)
│       ├── test_trips.py           (CRUD endpoints)
│       ├── test_stops.py           (CRUD, reorder, photo upload)
│       ├── test_render.py          (render pipeline with mocked tile fetcher)
│       ├── test_geocode.py         (mock Nominatim responses)
│       ├── test_renderer/
│       │   ├── test_tiles.py       (tile math, cache hits/misses)
│       │   ├── test_labels.py      (collision avoidance logic)
│       │   ├── test_route.py       (path drawing produces valid image)
│       │   └── test_photos.py      (circular crop, missing photo fallback)
│       └── fixtures/
│           ├── sample_trip.yaml
│           └── test_photo.jpg      (small test image)
├── frontend/
│   ├── Dockerfile
│   ├── nginx.conf
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   ├── index.html
│   ├── src/
│   │   ├── main.tsx
│   │   ├── App.tsx
│   │   ├── api/
│   │   │   └── client.ts           (typed fetch wrapper, error handling)
│   │   ├── stores/
│   │   │   ├── tripStore.ts        (Zustand: current trip, stops, UI state)
│   │   │   └── settingsStore.ts    (Zustand: global settings, theme)
│   │   ├── pages/
│   │   │   ├── TripList.tsx
│   │   │   └── TripEditor.tsx
│   │   ├── components/
│   │   │   ├── MapPanel.tsx         (Leaflet map with markers + route)
│   │   │   ├── StopList.tsx         (dnd-kit sortable stop rows)
│   │   │   ├── StopRow.tsx          (inline-editable city, dates, photo)
│   │   │   ├── AddStop.tsx          (city search with typeahead)
│   │   │   ├── SettingsDrawer.tsx   (all settings in a slide-over)
│   │   │   ├── StylePicker.tsx      (visual grid of style thumbnails)
│   │   │   ├── RenderModal.tsx      (progress bar, preview, download)
│   │   │   ├── PhotoUpload.tsx      (drag-and-drop zone)
│   │   │   ├── TripCard.tsx         (card for trip list)
│   │   │   └── ui/                  (Button, Input, Drawer, Modal, Toast, etc.)
│   │   ├── hooks/
│   │   │   ├── useTrip.ts           (fetch/mutate trip data)
│   │   │   ├── useRender.ts         (polling render status)
│   │   │   └── useGeocode.ts        (debounced city search)
│   │   └── lib/
│   │       ├── types.ts             (Trip, Stop, RenderStatus, Settings)
│   │       └── constants.ts         (style configs for UI previews, print presets)
│   └── tests/
│       ├── setup.ts
│       ├── TripEditor.test.tsx      (render, add stop, reorder, delete)
│       ├── StopRow.test.tsx         (inline edit, photo upload)
│       ├── SettingsDrawer.test.tsx  (style selection, print size, API key)
│       ├── RenderModal.test.tsx     (progress, download)
│       └── api/
│           └── client.test.ts       (request/response handling, error cases)
└── scripts/
    ├── seed.py                      (seed DB with sample Spain/Portugal trip)
    └── dev.sh                       (docker-compose up with hot reload)
```

---

## Test Plan

### Backend (pytest)

**Unit tests** (`tests/test_renderer/`):
- `test_tiles.py`: lat/lon ↔ tile coordinate conversion (known values), zoom selection for various bounds/resolutions, cache write on fetch and cache hit on second fetch (mock HTTP), graceful fallback on tile fetch failure.
- `test_labels.py`: no overlap after collision avoidance for known overlapping label positions, labels unchanged when already non-overlapping, edge case with all stops at same coordinates.
- `test_route.py`: path drawn between 2+ points produces a non-empty RGBA image, arrow direction is correct (spot-check pixel sampling).
- `test_photos.py`: circular crop output has transparent corners, missing photo produces a dot of the correct color, oversized upload is rejected.

**Integration tests** (`tests/test_trips.py`, etc.):
- Full CRUD cycle: create trip → add stops → reorder → update → delete.
- Photo upload: upload JPEG, verify thumbnail created, verify original stored, delete and verify cleanup.
- Render: create trip with 3 stops, render with mocked tile fetcher (return solid-color tiles), verify output PNG exists at correct dimensions and DPI.
- Import/export: round-trip a YAML file through import and export, verify data integrity.
- Geocode: mock Nominatim, verify rate limiting (second request within 1s is queued).

### Frontend (Vitest + React Testing Library)

- `TripEditor.test.tsx`: renders stop list, add a stop updates list, drag reorder updates sort order, delete stop with confirmation.
- `StopRow.test.tsx`: inline edit city name, click photo area triggers file input, uploaded photo shows thumbnail.
- `SettingsDrawer.test.tsx`: style picker highlights active style, print size presets populate fields, API key input masks value.
- `RenderModal.test.tsx`: shows progress bar while rendering, shows download buttons when done, shows error state.
- `client.test.ts`: successful requests return typed data, 4xx/5xx responses throw with message, network errors are caught.

### E2E smoke test (optional, Playwright)

One happy-path test: load app → create trip → add 3 stops by searching → upload a photo → set style → generate → verify download link works. This is stretch goal, not blocking.

---

## Seed Data

The `scripts/seed.py` script populates the database with the Spain & Portugal 2026 trip as sample data, using the exact itinerary from the POC (11 stops, all coordinates, dates, highlight flags). This ensures the app has working data on first launch for development and demo purposes.

---

## Development Workflow

```bash
# First run
cp .env.example .env
# Edit .env to add STADIA_API_KEY (optional, free tier)

# Development (hot reload)
./scripts/dev.sh
# → frontend at http://localhost:3000
# → backend at http://localhost:8000
# → API docs at http://localhost:8000/docs

# Run tests
docker compose exec backend pytest
docker compose exec frontend npx vitest run

# Production build
docker compose up --build -d
```

`dev.sh` runs docker-compose with volume mounts for source code and Vite dev server (not Nginx) for hot reload. Backend uses `uvicorn --reload`.

---

## Non-Goals (v1)

Things explicitly out of scope for the initial build:

- User authentication / multi-user. This is a single-user self-hosted tool.
- PDF export. PNG at 300 DPI is sufficient for print shops.
- Curved / bezier route paths. Straight-line segments with arrows are clean enough. Can revisit.
- Mobile-responsive UI below 1024px.
- Real-time collaborative editing.
- AI-powered itinerary suggestions.
- Elevation profiles or distance calculations.