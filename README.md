
# DO ALL FOR YOU — Batch Ripper (CJ)

**One button, ten volumes.** Paste URLs into `playlists/vol1.txt … vol10.txt`, deploy backend on Render and frontend on Netlify, then hit **Rip EVERYTHING**.

## Deploy
1) Push this folder as a GitHub repo (any name).
2) Render → New Web Service → connect repo.
   - Build: `pip install -r backend/requirements.txt`
   - Start: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
   - Ensure `apt.txt` at repo root installs `ffmpeg`.
3) Netlify → new site → drag the `frontend/` folder.
4) Open Netlify site → when prompted, paste your Render URL.

## Use
- Add URLs to `playlists/volX.txt` (one per line). Save & redeploy (or mount the same repo).
- Press **Rip EVERYTHING (vol1..10)** — server reads all playlist files and rips them in order.
- You can also paste your own list in the textbox and press **Rip Custom List**.

## Endpoints
- `POST /rip` → `{ "url": "https://..." }`
- `POST /batch` → `{ "urls": ["https://...","https://..."], "title_prefix": "cj" }`
- `POST /batch_from_playlists` → `{ "volumes": ["vol1","vol2"] }` or leave empty for all 1..10
- `GET /recent` → last 50 MP3s with sizes & links
- `GET /dl/{file}` → download a file

PLUR. CJ 2025.
