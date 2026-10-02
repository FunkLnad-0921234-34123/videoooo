#!/usr/bin/env python3
"""
تولید script.js از assets.json (که از Release خوانده شده)
لینک‌ها از jsDelivr ساخته می‌شوند تا در مرورگر پخش شوند.
"""
import os
import re
import json
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parent.parent
ASSETS_FILE = ROOT / "assets.json"
META_FILE = ROOT / "videos-meta.json"
OUTPUT = ROOT / "script.js"

REPO = os.environ.get("REPO", "user/repo")   # مثل: ali/tube-pages
TAG = os.environ.get("TAG", "latest")

VIDEO_EXTS = {".mp4", ".webm", ".ogg", ".mov", ".m4v"}


def pretty_title(slug: str) -> str:
    s = slug.replace("_", " ").replace("-", " ")
    return " ".join(w.capitalize() for w in s.split())


def parse_filename(name: str):
    """
    python-j1__1.mp4  → ('python-j1', '1')
    flask__full.mp4   → ('flask', 'full')
    intro.mp4         → ('intro', None)
    """
    stem = Path(name).stem
    if "__" in stem:
        group, part = stem.rsplit("__", 1)
        return group, part
    return stem, None


def load_meta():
    if META_FILE.exists():
        return json.loads(META_FILE.read_text(encoding="utf-8"))
    return {}


def jsdelivr_url(filename: str) -> str:
    """
    https://cdn.jsdelivr.net/gh/USER/REPO@TAG/filename
    """
    return f"https://cdn.jsdelivr.net/gh/{REPO}@{TAG}/{quote(filename)}"


def build_video_data():
    if not ASSETS_FILE.exists():
        print("❌ assets.json پیدا نشد")
        return []

    assets = json.loads(ASSETS_FILE.read_text(encoding="utf-8"))
    meta = load_meta()

    groups = {}

    for a in assets:
        name = a["name"]
        if Path(name).suffix.lower() not in VIDEO_EXTS:
            continue

        group, part = parse_filename(name)
        key = group.lower()

        if key not in groups:
            m = meta.get(key, {})
            groups[key] = {
                "id": re.sub(r"[^a-z0-9]", "", key)[:20] or f"v{len(groups)+1}",
                "title": m.get("title") or pretty_title(group),
                "channel": m.get("channel", "Purple"),
                "views": m.get("views", "0 بازدید"),
                "parts": [],
            }

        part_name = f"پارت {part}" if part else "کامل"
        groups[key]["parts"].append({
            "name": part_name,
            "src": jsdelivr_url(name),
            "_sort": part if (part and part.isdigit()) else "999",
        })

    result = []
    for g in groups.values():
        g["parts"].sort(key=lambda p: (len(p["_sort"]), p["_sort"]))
        for p in g["parts"]:
            p.pop("_sort", None)
        result.append(g)

    result.sort(key=lambda g: g["title"].lower())
    return result


TEMPLATE = r"""// =========================================================
//  ⚠️ این فایل خودکار تولید شده — دستی ویرایش نکن
//  منبع: scripts/generate.py
//  Release: __TAG__  |  Repo: __REPO__
// =========================================================

const videos = __DATA__;

// =========================================================
//  DOM
// =========================================================
const grid = document.getElementById('grid');
const watch = document.getElementById('watch');
const player = document.getElementById('player');
const watchTitle = document.getElementById('watchTitle');
const watchViews = document.getElementById('watchViews');
const watchParts = document.getElementById('watchParts');
const partsBar = document.getElementById('partsBar');
const backBtn = document.getElementById('backBtn');
const menuBtn = document.getElementById('menuBtn');
const sidebar = document.getElementById('sidebar');
const searchInput = document.getElementById('searchInput');

let currentVideo = null;
let currentPart = 0;

function renderGrid(list = videos) {
    grid.innerHTML = '';
    if (list.length === 0) {
        grid.innerHTML = '<div style="grid-column:1/-1;text-align:center;padding:60px;color:#888;">چیزی پیدا نشد</div>';
        return;
    }
    list.forEach(v => {
        const partsCount = v.parts.length;
        const card = document.createElement('div');
        card.className = 'video-card';
        card.innerHTML = `
            <div class="video-thumb">
                <div class="play-icon">
                    <svg viewBox="0 0 24 24" width="22" height="22"><path fill="currentColor" d="M8 5v14l11-7z"/></svg>
                </div>
                ${partsCount > 1 ? `<span class="parts-badge">${partsCount} پارت</span>` : ''}
            </div>
            <div class="video-info-row">
                <div class="channel-avatar">${v.channel.charAt(0)}</div>
                <div class="video-meta">
                    <div class="video-title">${v.title}</div>
                    <div class="video-sub">${v.channel}</div>
                    <div class="video-sub">${v.views}</div>
                </div>
            </div>
        `;
        card.addEventListener('click', () => openWatch(v));
        grid.appendChild(card);
    });
}

function openWatch(video) {
    currentVideo = video;
    currentPart = 0;

    grid.style.display = 'none';
    watch.style.display = 'block';
    window.scrollTo({ top: 0, behavior: 'smooth' });

    watchTitle.textContent = video.title;
    watchViews.textContent = video.views;
    watchParts.textContent = video.parts.length > 1 ? `${video.parts.length} پارت` : '';

    partsBar.innerHTML = '';
    if (video.parts.length > 1) {
        video.parts.forEach((p, i) => {
            const btn = document.createElement('button');
            btn.className = 'part-btn' + (i === 0 ? ' active' : '');
            btn.textContent = p.name;
            btn.addEventListener('click', () => switchPart(i));
            partsBar.appendChild(btn);
        });
    }

    playPart(0);
}

function playPart(index) {
    if (!currentVideo) return;
    currentPart = index;
    player.src = currentVideo.parts[index].src;
    player.play().catch(() => {});
    document.querySelectorAll('.part-btn').forEach((b, i) => {
        b.classList.toggle('active', i === index);
    });
}

function switchPart(index) { playPart(index); }

player.addEventListener('ended', () => {
    if (currentVideo && currentPart < currentVideo.parts.length - 1) {
        playPart(currentPart + 1);
    }
});

backBtn.addEventListener('click', () => {
    player.pause();
    player.src = '';
    watch.style.display = 'none';
    grid.style.display = 'grid';
});

menuBtn.addEventListener('click', () => {
    if (window.innerWidth < 900) sidebar.classList.toggle('open');
    else sidebar.classList.toggle('collapsed');
});

searchInput.addEventListener('input', (e) => {
    const q = e.target.value.trim().toLowerCase();
    const filtered = videos.filter(v =>
        v.title.toLowerCase().includes(q) || v.channel.toLowerCase().includes(q)
    );
    renderGrid(filtered);
});

renderGrid();
"""


def main():
    data = build_video_data()
    js = (TEMPLATE
          .replace("__DATA__", json.dumps(data, ensure_ascii=False, indent=4))
          .replace("__TAG__", TAG)
          .replace("__REPO__", REPO))
    OUTPUT.write_text(js, encoding="utf-8")
    print(f"✅ script.js ساخته شد — {len(data)} گروه ویدیو")


if __name__ == "__main__":
    main()
