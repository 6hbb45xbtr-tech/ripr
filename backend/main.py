
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, HttpUrl
from typing import List, Optional
import os, subprocess, glob, time, re, json, pathlib

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
    import shutil
    return {"ok": True, "ffmpeg": shutil.which("ffmpeg") is not None}

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
    # output template by yt-dlp (we reclean later)
    outtmpl = str(STORE / "%(uploader)s-%(title)s.%(ext)s")
    cmd = ["yt-dlp", "-x", "--audio-format", "mp3", "-o", outtmpl, str(inp.url)]
    try:
        subprocess.check_call(cmd)
    except subprocess.CalledProcessError as e:
        raise HTTPException(500, f"yt-dlp failed: {e}")

    # pick newest mp3
    mp3s = sorted(STORE.glob("*.mp3"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not mp3s:
        raise HTTPException(500, "No mp3 produced")
    latest = mp3s[0]
    if inp.title:
        target = STORE / (safe_name(inp.title) + ".mp3")
        if latest != target:
            target.write_bytes(latest.read_bytes())
            latest = target
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
def batch_from_playlists(volumes: Optional[List[str]] = None):
    # volumes like ["vol1","vol2",...]; default = all vol1..vol10 present
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
    return batch(BatchIn(urls=ok_urls, title_prefix="cj"))
