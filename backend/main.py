
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, HttpUrl
from typing import List, Optional
from fastapi import Body
import os, subprocess, glob, time, re, json, pathlib, shutil, sys, importlib.util

APP_DIR = pathlib.Path(__file__).parent.resolve()
STORE = APP_DIR / "store"
STORE.mkdir(exist_ok=True)

PLAYLISTS_DIR = APP_DIR.parent / "playlists"

app = FastAPI(title="CrateJuice — Do All For You", version="0.2")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SAFE = re.compile(r"[^a-zA-Z0-9._-]+")
def safe_name(s: str) -> str:
    s = SAFE.sub("_", s).strip("_")
    return s or f"track_{int(time.time())}"

@app.get("/health")
def health():
    yt_dlp_binary = shutil.which("yt-dlp") or shutil.which("yt_dlp")
    yt_dlp_module = importlib.util.find_spec("yt_dlp") is not None
    return {
        "ok": True,
        "ffmpeg": shutil.which("ffmpeg") is not None,
        "yt_dlp_binary": bool(yt_dlp_binary),
        "yt_dlp_module": bool(yt_dlp_module),
    }

@app.get("/recent")
def recent(limit: int = 50):
    files = sorted(STORE.glob("*.mp3"), key=lambda p: p.stat().st_mtime, reverse=True)
    out = [{"file": f.name, "size": f.stat().st_size, "url": f"/dl/{f.name}"} for f in files[:limit]]
    return {"items": out}

@app.get("/dl/{fname}")
def dl(fname: str):
    p = STORE / fname
    if not p.exists():
        raise HTTPException(404, "Not found")
    return FileResponse(str(p), media_type="audio/mpeg", filename=fname)

class RipIn(BaseModel):
    url: HttpUrl
    title: Optional[str] = None

@app.post("/rip")
def rip_one(inp: RipIn):
    # choose how to invoke yt-dlp: prefer binary, fall back to `python -m yt_dlp` if module present
    yt_dlp_bin = shutil.which("yt-dlp") or shutil.which("yt_dlp")
    yt_dlp_module = importlib.util.find_spec("yt_dlp") is not None
    if yt_dlp_bin:
        runner = [yt_dlp_bin]
    elif yt_dlp_module:
        runner = [sys.executable, "-m", "yt_dlp"]
    else:
        raise HTTPException(503, "yt-dlp not available as a binary or python module on server")

    # output template by yt-dlp (we reclean later)
    outtmpl = str(STORE / "%(uploader)s-%(title)s.%(ext)s")
    cmd = runner + ["-x", "--audio-format", "mp3", "-o", outtmpl, str(inp.url)]
    try:
        p = subprocess.run(cmd, capture_output=True, text=True)
        if p.returncode != 0:
            # include a small slice of stderr to help debugging
            err = p.stderr or p.stdout or ""
            snippet = (err[-4000:]) if len(err) > 4000 else err
            raise HTTPException(500, f"yt-dlp failed (rc={p.returncode}): {snippet}")
    except FileNotFoundError:
        raise HTTPException(503, "yt-dlp binary not executable on server")
    except subprocess.SubprocessError as e:
        raise HTTPException(500, f"yt-dlp subprocess error: {e}")

    # pick newest mp3
    mp3s = sorted(STORE.glob("*.mp3"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not mp3s:
        raise HTTPException(500, "No mp3 produced")
    latest = mp3s[0]
    if inp.title:
        target = STORE / (safe_name(inp.title) + ".mp3")
        try:
            if latest.name != target.name:
                # copy to new name to preserve original naming produced by yt-dlp
                target.write_bytes(latest.read_bytes())
                latest = target
        except Exception as e:
            raise HTTPException(500, f"failed to rename/copy produced file: {e}")
    return {"ok": True, "file": latest.name, "url": f"/dl/{latest.name}"}

class BatchIn(BaseModel):
    urls: List[HttpUrl]
    title_prefix: Optional[str] = None

@app.post("/batch")
def batch(inp: BatchIn):
    results = []
    for idx, u in enumerate(inp.urls, start=1):
        try:
            title = f"{inp.title_prefix or 'track'}_{idx:03d}"
            res = rip_one(RipIn(url=u, title=title))
            results.append({"url": str(u), "file": res["file"], "ok": True})
        except Exception as e:
            results.append({"url": str(u), "error": str(e), "ok": False})
    return {"ok": True, "count": len(results), "results": results}

@app.post("/batch_from_playlists")
def batch_from_playlists(payload: Optional[dict] = Body(None)):
    # Accept body like {"volumes": ["vol1","vol2",...]}. If omitted, use vol1..vol10
    volumes = None
    if payload and isinstance(payload, dict):
        volumes = payload.get("volumes")
    vols = volumes or [f"vol{i}" for i in range(1,11)]
    all_urls = []
    for v in vols:
        path = PLAYLISTS_DIR / f"{v}.txt"
        if not path.exists():
            continue
        for line in path.read_text().splitlines():
            s = line.strip()
            if s and not s.startswith("#"):
                all_urls.append(s)
    # Basic validation: allow http(s) strings
    ok_urls = [u for u in all_urls if u.startswith("http")]
    if not ok_urls:
        # return a helpful message rather than silently doing nothing
        return JSONResponse({"ok": False, "count": 0, "message": "no valid URLs found in requested playlists"}, status_code=400)
    return batch(BatchIn(urls=ok_urls, title_prefix="cj"))
