let favoriteViewActive = false;

async function loadFavorites() {
    const res = await fetch('/api/favorites');
    const favorites = await res.json();

    document.querySelectorAll('.gallery-item').forEach(item => {
        const star = item.querySelector('.favorite-star');
        const videoPath = item.dataset.video;

        if (favorites[videoPath]) {
            star.classList.add('favorited');
        }
    });
}

async function toggleFavorite(event, video) {
    event.preventDefault();
    event.stopPropagation();

    const star = event.target;
    const isFavorited = star.classList.toggle('favorited');

    await fetch('/api/favorite', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ filename: video, favorite: !!isFavorited })
    });
}

async function toggleFavoriteView() {
    favoriteViewActive = !favoriteViewActive;
    const res = await fetch('/api/favorites');
    const favorites = await res.json();

    document.querySelectorAll('.gallery-item').forEach(item => {
        const videoPath = item.dataset.video;

        if (favoriteViewActive && !favorites[videoPath]) {
            item.classList.add('dimmed');
        } else {
            item.classList.remove('dimmed');
        }
    });
}

function setGridColumns(columns) {
    document.querySelectorAll('.gallery').forEach(gallery => {
        gallery.style.gridTemplateColumns = `repeat(${columns}, 1fr)`;
        gallery.classList.remove('gallery-3', 'gallery-5', 'gallery-10', 'gallery-20');
        gallery.classList.add(`gallery-${columns}`);
    });
}

async function loadPreviewThumbnails(thumbnail) {
    const videoPath = thumbnail.dataset.video;
    const previewBase = videoPath.replace(/\.[^/.]+$/, '');
    const availablePreviews = [];

    for (let index = 0; index < 20; index += 1) {
        const preview = `${previewBase}/thumb_${String(index).padStart(2, '0')}.jpg`;
        const url = `/_thumbnails/${preview}`;

        try {
            const res = await fetch(url, { method: 'HEAD' });
            if (res.ok) {
                availablePreviews.push(preview);
            }
        } catch (_) {}
    }

    return availablePreviews;
}

function setupPreviewHover() {
    document.querySelectorAll('.thumbnail').forEach(thumbnail => {
        let currentIndex = 0;
        let interval;
        let cachedPreviews = null;

        thumbnail.addEventListener('mouseover', async () => {
            if (!cachedPreviews) {
                cachedPreviews = await loadPreviewThumbnails(thumbnail);
            }

            if (!cachedPreviews.length) return;

            interval = setInterval(() => {
                currentIndex = (currentIndex + 1) % cachedPreviews.length;
                thumbnail.src = `/_thumbnails/${cachedPreviews[currentIndex]}`;
            }, 500);
        });

        thumbnail.addEventListener('mouseout', () => {
            clearInterval(interval);
            currentIndex = 0;
            thumbnail.src = `/_thumbnails/${thumbnail.dataset.poster}`;
        });
    });
}

function setupFavoriteButtons() {
    document.querySelectorAll('.gallery-item').forEach(item => {
        const star = item.querySelector('.favorite-star');
        if (!star) return;

        star.addEventListener('click', event => {
            toggleFavorite(event, item.dataset.video);
        });
    });
}

document.addEventListener('DOMContentLoaded', () => {
    loadFavorites();
    setupFavoriteButtons();
    setupPreviewHover();
});