# travel_map

A self-hosted web application that generates high-resolution, print-ready stylized maps for multi-city trips. Input an ordered list of stops, configure style and print settings, and render a composited map image with route paths, photo bubbles, city labels, and a title banner.

## Quick Start

```bash
# Clone and configure
git clone https://github.com/beingforthebenefit/travel_map.git
cd travel_map
cp .env.example .env
# Optionally add your Stadia Maps API key to .env for watercolor/toner/terrain styles

# Run
docker compose up --build

# Access
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

## Seed Data

Load the sample Spain & Portugal trip:

```bash
docker compose exec backend python /app/scripts/seed.py
```

## Architecture

```
Frontend (React 18 + TypeScript + Vite)    Backend (FastAPI + Python 3.12)
  :3000 / Nginx                              :8000
  |                                          |
  +-- Trip List                              +-- REST API (/api/v1)
  +-- Trip Editor                            +-- SQLite database
  |   +-- Leaflet Map                        +-- Rendering pipeline
  |   +-- Stop List (dnd-kit)                |   +-- Tile fetching & caching
  |   +-- Settings Drawer                    |   +-- Route drawing (PyCairo)
  +-- Render Modal                           |   +-- Photo bubbles (Pillow)
                                             |   +-- Label collision avoidance
                                             +-- Geocoding (Nominatim)
```

## Map Styles

| Style | Provider | API Key Required |
|-------|----------|:---:|
| Watercolor | Stadia (Stamen) | Yes |
| Toner Lite | Stadia (Stamen) | Yes |
| Terrain | Stadia (Stamen) | Yes |
| Positron | CartoDB | No |
| Dark Matter | CartoDB | No |
| OpenStreetMap | OSM | No |

Get a free Stadia Maps API key at https://stadiamaps.com/

## Development

```bash
# Run tests
docker compose run --rm backend pytest tests/ -v
cd frontend && npm test

# API documentation
open http://localhost:8000/docs
```

## Stack

- **Frontend**: React 18, TypeScript, Vite, Tailwind CSS 4, Zustand, dnd-kit, Leaflet
- **Backend**: FastAPI, Python 3.12, Pillow, PyCairo, aiosqlite, httpx
- **Infrastructure**: Docker Compose, Nginx, SQLite

## License

GPL-3.0
