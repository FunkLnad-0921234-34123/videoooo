#!/usr/bin/env python3
"""
تولید script.js از assets.json (خوانده‌شده از GitHub Release)
لینک‌ها از jsDelivr ساخته می‌شن تا در مرورگر پخش بشن.

ساختار jsDelivr برای Release:
    https://cdn.jsdelivr.net/gh/USER/REPO@TAG/filename

پشتیبانی از سه ساختار assets.json:
  1) {"assets": [{"name": ..., "url": ...}, ...]}
  2) [{"name": ..., "url": ...}, ...]
  3) ["filename.mp4", "filename2.mp4", ...]
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

REPO = os.environ.get("REPO", "user/repo")   # مثل: ali/videoooo
TAG = os.environ.get("TAG", "latest")

VIDEO_EXTS = {".mp4", ".webm", ".ogg", ".mov", ".m4v"}


# =========================================================
#  HELPERS
# =========================================================
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
        try:
            return json.loads(META_FILE.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"⚠️  خطا در videos-meta.json: {e}")
    return {}


def jsdelivr_url(filename: str) -> str:
    """
    https://cdn.jsdelivr.net/gh/USER/REPO@TAG/filename
    """
    return f"https://cdn.jsdelivr.net/gh/{REPO}@{TAG}/{quote(filename)}"


# =========================================================
#  CORE
# =========================================================
def load_assets():
    """assets.json رو می‌خونه و لیست اسم فایل‌ها رو برمی‌گردونه."""
    if not ASSETS_FILE.exists():
        print("❌ assets.json پیدا نشد")
        return []

    try:
        raw = json.loads(ASSETS_FILE.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"❌ خطا در خواندن assets.json: {e}")
        return []

    # نرمال‌سازی
    if isinstance(raw, dict):
        assets = raw.get("assets", [])
    elif isinstance(raw, list):
        assets = raw
    else:
        print("❌ ساختار assets.json ناشناخته")
        return []

    names = []
    for a in assets:
        if isinstance(a, str):
            names.append(a)
        elif isinstance(a, dict):
            n = a.get("name") or a.get("filename") or ""
            if n:
                names.append(n)

    return names


def build_video_data():
    names = load_assets()
    if not names:
        print("⚠️  هیچ فایلی توی assets پیدا نشد")
        return []

    meta = load_meta()
    groups = {}

    for name in names:
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


# =========================================================
#  TEMPLATE
# =========================================================
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

// =========================================================
//  رندر کارت‌ها
// =========================================================
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

// =========================================================
//  باز کردن ویدیو
// =========================================================
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

function switchPart(index) {
    playPart(index);
}

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
    if (window.innerWidth < 900) {
        sidebar.classList.toggle('open');
    } else {
        sidebar.classList.toggle('collapsed');
    }
});

searchInput.addEventListener('input', (e) => {
    const q = e.target.value.trim().toLowerCase();
    const filtered = videos.filter(v =>
        v.title.toLowerCase().includes(q) ||
        v.channel.toLowerCase().includes(q)
    );
    renderGrid(filtered);
});

renderGrid();
"""


# =========================================================
#  MAIN
# =========================================================
def main():
    print(f"🔧 REPO = {REPO}")
    print(f"🔧 TAG  = {TAG}")

    data = build_video_data()
    js = (TEMPLATE
          .replace("__DATA__", json.dumps(data, ensure_ascii=False, indent=4))
          .replace("__TAG__", TAG)
          .replace("__REPO__", REPO))
    OUTPUT.write_text(js, encoding="utf-8")
    print(f"✅ script.js ساخته شد — {len(data)} گروه ویدیو")
    for g in data:
        print(f"   • {g['title']}  ({len(g['parts'])} پارت)")
        for p in g["parts"]:
            print(f"      → {p['src']}")


if __name__ == "__main__":
    main()
