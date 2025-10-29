
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

PLUR — CJ 2025
