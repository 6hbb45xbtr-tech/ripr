
# CrateJuice — One‑Shot (Random repo + site)

This is the **works-first** seed: paste a URL, get an MP3 (yt-dlp + ffmpeg), download/play.

## One‑shot deploy (GitHub → Render + Netlify)

1. **Create a random GitHub repo** (e.g. `cj-one-shot-<random>`). Upload everything in this folder.  
   *Keep the structure (backend/, frontend/, apt.txt, render.yaml).*

2. **Render (backend API)** → New → Web Service → Connect the repo
   - Runtime: **Python**
   - **Build**: `pip install -r backend/requirements.txt`
   - **Start**: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
   - Add file **apt.txt** in the repo root with one line: `ffmpeg` (already included) so Render installs it.
   - After deploy, you get: `https://cj-ripper-one-shot.onrender.com` (example).

3. **Netlify (frontend)** → New site → Drag the **frontend/** folder
   - When it opens, it will read `?api=<your-render-url>` if you append it, or you can paste once and it’ll be saved.

   Example: `https://random-cj-site.netlify.app/?api=https://cj-ripper-one-shot.onrender.com`

## Use
- Paste a YouTube/SoundCloud URL → **Rip** → wait → the MP3 appears under **Recent** with a download link + inline player.
- **Refresh** lists recent files.

## Notes
- ffmpeg is installed by Render via `apt.txt`. If health says `(no ffmpeg)`, check your build logs and ensure `apt.txt` is picked up.
- Keep it simple for now — no DB. Files are stored under `backend/store/` on the Render instance.
- Free plans may sleep; first request can take a moment.
 - Free plans may sleep; first request can take a moment.

API notes
- The `POST /batch_from_playlists` endpoint accepts a JSON object with an optional `volumes` field. Example body:

```json
{"volumes": ["vol1", "vol7"]}
```

If `volumes` is omitted, the server will try `vol1`..`vol10`. If no valid URLs are found in the requested playlists the endpoint returns a 400 with a helpful message.

PLUR — CJ 2025

yt-dlp fallback
- The server prefers the `yt-dlp` console script. If that binary is not available it will fall back to running `yt-dlp` as a Python module via `python -m yt_dlp` (this is useful on platforms where the console script isn't installed).
- You can ensure the module is available by adding `yt-dlp` to `backend/requirements.txt` (already present) or running `pip install yt-dlp` in your environment.
- The `/health` endpoint reports two flags: `yt_dlp_binary` (console script present) and `yt_dlp_module` (python module importable). If either is true, ripping should be possible (assuming `ffmpeg` is also present for audio conversion).

