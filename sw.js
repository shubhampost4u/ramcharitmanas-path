// Offline support: app shell cached on install; data refreshed from network when online;
// images and audio cached the first time they are played or shown.
const VERSION = 'rcm-v1';
const SHELL = ['./', 'index.html', 'manifest.webmanifest', 'icon.svg', 'icon-192.png', 'icon-512.png',
  'data/sundar.json', 'data/sundar.scenes.json'];

self.addEventListener('install', e => {
  e.waitUntil(caches.open(VERSION).then(c => c.addAll(SHELL)).then(() => self.skipWaiting()));
});
self.addEventListener('activate', e => {
  e.waitUntil(caches.keys().then(keys => Promise.all(keys.filter(k => k !== VERSION).map(k => caches.delete(k))))
    .then(() => self.clients.claim()));
});
self.addEventListener('fetch', e => {
  const url = new URL(e.request.url);
  if (e.request.method !== 'GET' || url.origin !== location.origin) return;
  const isData = url.pathname.includes('/data/') || url.pathname.endsWith('/') || url.pathname.endsWith('index.html');
  if (isData) {
    // network first, fall back to cache
    e.respondWith(fetch(e.request).then(r => { const c = r.clone(); caches.open(VERSION).then(x => x.put(e.request, c)); return r; })
      .catch(() => caches.match(e.request, { ignoreSearch: true })));
  } else {
    // cache first for images, audio, fonts, icons
    e.respondWith(caches.match(e.request).then(hit => hit || fetch(e.request).then(r => {
      if (r.ok && r.status === 200) { const c = r.clone(); caches.open(VERSION).then(x => x.put(e.request, c)); }
      return r;
    })));
  }
});
