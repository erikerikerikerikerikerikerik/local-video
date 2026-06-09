let favoriteViewActive = false;
let activeTagFilters = new Set();

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
        const itemTags = getItemTags(item);
        const shouldDimFavorite = favoriteViewActive && !favorites[videoPath];
        const shouldDimTag = !matchesActiveTagFilters(itemTags);

        if (shouldDimFavorite || shouldDimTag) {
            item.classList.add('dimmed');
        } else {
            item.classList.remove('dimmed');
        }
    });
}

function getItemTags(item) {
    return (item.dataset.tags || '')
        .split(',')
        .map(tag => tag.trim())
        .filter(Boolean);
}

function matchesActiveTagFilters(itemTags) {
    if (!activeTagFilters.size) return true;
    return Array.from(activeTagFilters).every(tag => itemTags.includes(tag));
}

function applyTagFilter() {
    document.querySelectorAll('.gallery-item').forEach(item => {
        const itemTags = getItemTags(item);

        if (!matchesActiveTagFilters(itemTags)) {
            item.classList.add('dimmed');
        } else if (!favoriteViewActive) {
            item.classList.remove('dimmed');
        }
    });

    document.querySelectorAll('.tag-filter-button').forEach(button => {
        button.classList.toggle('active', activeTagFilters.has(button.dataset.tag));
    });
}

async function refreshTags() {
    const res = await fetch('/api/tags');
    const data = await res.json();

    document.querySelectorAll('.gallery-item').forEach(item => {
        const videoPath = item.dataset.video;
        const itemTags = data.videos[videoPath] || [];
        item.dataset.tags = itemTags.join(',');

        item.querySelectorAll('.video-tag-option').forEach(button => {
            button.classList.toggle('selected', itemTags.includes(button.dataset.tag));
        });
    });

    applyTagFilter();
}

async function setVideoTag(video, tag, enabled = true) {
    tag = (tag || '').trim();
    if (!video || !tag) return;

    await fetch('/api/video-tags', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ filename: video, tag, enabled })
    });

    await refreshTags();
}

function setupTagFilters() {
    document.querySelectorAll('.tag-filter-button').forEach(button => {
        button.addEventListener('click', () => {
            const tag = button.dataset.tag;

            if (activeTagFilters.has(tag)) {
                activeTagFilters.delete(tag);
            } else {
                activeTagFilters.add(tag);
            }

            applyTagFilter();
        });
    });
}

function setupNewTagBox() {
    const input = document.querySelector('#new-tag-input');
    const button = document.querySelector('#new-tag-button');

    if (!input || !button) return;

    const addNewTagToMenus = () => {
        const tag = (input.value || '').trim().toLowerCase();
        if (!tag) return;

        document.querySelectorAll('.video-tag-options').forEach(options => {
            const exists = Array.from(options.querySelectorAll('.video-tag-option'))
                .some(button => button.dataset.tag === tag);

            if (!exists) {
                const button = document.createElement('button');
                button.className = 'video-tag-option';
                button.dataset.tag = tag;
                button.type = 'button';
                button.textContent = `#${tag}`;
                options.appendChild(button);
            }
        });

        const filterExists = Array.from(document.querySelectorAll('.tag-filter-button'))
            .some(button => button.dataset.tag === tag);
        const filterContainer = document.querySelector('.tag-filter-buttons');

        if (filterContainer && !filterExists) {
            const filterButton = document.createElement('button');
            filterButton.className = 'tag-filter-button';
            filterButton.dataset.tag = tag;
            filterButton.type = 'button';
            filterButton.textContent = `#${tag}`;
            filterButton.addEventListener('click', () => {
                if (activeTagFilters.has(tag)) {
                    activeTagFilters.delete(tag);
                } else {
                    activeTagFilters.add(tag);
                }

                applyTagFilter();
            });
            filterContainer.appendChild(filterButton);
        }

        input.value = '';
    };

    button.addEventListener('click', addNewTagToMenus);

    input.addEventListener('keydown', event => {
        if (event.key === 'Enter') {
            event.preventDefault();
            addNewTagToMenus();
        }
    });
}

function setupTagMenus() {
    document.querySelectorAll('.gallery-item').forEach(item => {
        const menu = item.querySelector('.tag-menu');
        if (!menu) return;

        const menuButton = menu.querySelector('.tag-menu-button');

        menuButton.addEventListener('click', event => {
            event.preventDefault();
            event.stopPropagation();
            menu.classList.toggle('open');
        });

        menu.addEventListener('click', event => {
            const tagButton = event.target.closest('.video-tag-option');
            if (!tagButton) return;

            event.preventDefault();
            event.stopPropagation();

            const enabled = !tagButton.classList.contains('selected');
            setVideoTag(item.dataset.video, tagButton.dataset.tag, enabled);
        });
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
    refreshTags();
    setupFavoriteButtons();
    setupPreviewHover();
    setupTagFilters();
    setupNewTagBox();
    setupTagMenus();
});