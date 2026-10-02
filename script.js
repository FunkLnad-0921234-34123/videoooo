// =========================================================
//  ⚠️ این فایل خودکار تولید شده — دستی ویرایش نکن
//  منبع: scripts/generate.py
//  Release: video  |  Repo: FunkLnad-0921234-34123/videoooo
// =========================================================

const videos = [
    {
        "id": "mohammadafk1",
        "title": "Mohammad Afk 1",
        "channel": "Purple",
        "views": "0 بازدید",
        "parts": [
            {
                "name": "کامل",
                "src": "https://cdn.jsdelivr.net/gh/FunkLnad-0921234-34123/videoooo@video/mohammad-afk-1.mp4"
            }
        ]
    }
];

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

// =========================================================
//  منو
// =========================================================
menuBtn.addEventListener('click', () => {
    if (window.innerWidth < 900) {
        sidebar.classList.toggle('open');
    } else {
        sidebar.classList.toggle('collapsed');
    }
});

// =========================================================
//  جستجو
// =========================================================
searchInput.addEventListener('input', (e) => {
    const q = e.target.value.trim().toLowerCase();
    const filtered = videos.filter(v =>
        v.title.toLowerCase().includes(q) ||
        v.channel.toLowerCase().includes(q)
    );
    renderGrid(filtered);
});

// =========================================================
//  شروع
// =========================================================
renderGrid();
