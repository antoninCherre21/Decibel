const CACHE_NAME = 'decibel-pwa-cache-v1';
const urlsToCache = [
  '/Decibel/',
  '/Decibel/index.html',
  '/Decibel/manifest.json',
  '/Decibel/img/icon-512x512.png',
  'https://cdnjs.cloudflare.com/ajax/libs/PapaParse/5.4.1/papaparse.min.js',
  'https://unpkg.com/html5-qrcode'
];

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => {
        return cache.addAll(urlsToCache);
      })
  );
});

self.addEventListener('fetch', event => {
  // Pour les requêtes locales (hors audio volumineux si possible), on peut répondre avec le cache
  // Ici on garde une stratégie network-first ou fallback cache simple.
  event.respondWith(
    caches.match(event.request)
      .then(response => {
        if (response) {
          return response;
        }
        return fetch(event.request);
      })
  );
});
