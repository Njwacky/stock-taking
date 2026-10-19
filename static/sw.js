// Service Worker for Stock Tracker PWA
const CACHE_NAME = 'stock-tracker-v1.2';
const OFFLINE_URL = '/offline/';
const urlsToCache = [
  '/',
  '/offline/',
  '/static/css/style.css',
  '/static/css/navbar.css',
  '/static/css/footer.css',
  '/static/css/calculator.css',
  '/static/css/advanced-calculator.css',
  '/static/css/table_data.css',
  '/static/css/dashboard-controls.css',
  '/static/css/most-received-kits.css',
  '/static/css/base.css',
  '/static/js/base.js',
  '/static/js/calculator.js',
  '/static/js/advanced-calculator.js',
  '/static/js/floating-comment.js',
  '/static/images/light_blue.png',
  '/static/images/red.png',
  '/static/images/green.png'
];

// Install event - cache the application shell
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => {
        console.log('[Service Worker] Caching app shell');
        return cache.addAll(urlsToCache);
      })
  );
  // Activate the new service worker immediately
  self.skipWaiting();
});

// Activate event - clean up old caches
self.addEventListener('activate', event => {
  const cacheWhitelist = [CACHE_NAME];
  
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames.map(cacheName => {
          if (!cacheWhitelist.includes(cacheName)) {
            console.log('[Service Worker] Removing old cache:', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    })
  );
  
  // Take control of all clients
  event.waitUntil(clients.claim());
});

// Fetch event - Network first, then cache
self.addEventListener('fetch', event => {
  // Skip non-GET requests
  if (event.request.method !== 'GET') return;
  
  // Handle API requests differently
  if (event.request.url.includes('/api/')) {
    event.respondWith(
      fetch(event.request)
        .then(response => {
          // Don't cache API responses, but clone for the page to use
          return response;
        })
        .catch(() => {
          // If offline and API call fails, return a generic response
          return new Response(JSON.stringify({ error: 'You are offline' }), {
            headers: { 'Content-Type': 'application/json' }
          });
        })
    );
    return;
  }
  
  // For all other requests, try network first, then cache, then offline page
  event.respondWith(
    fetch(event.request)
      .then(response => {
        // Check if we received a valid response
        if (!response || response.status !== 200 || response.type !== 'basic') {
          return response;
        }
        
        // Clone the response
        const responseToCache = response.clone();
        
        caches.open(CACHE_NAME)
          .then(cache => {
            cache.put(event.request, responseToCache);
          });
          
        return response;
      })
      .catch(() => {
        // If both network and cache fail, show offline page
        if (event.request.mode === 'navigate') {
          return caches.match(OFFLINE_URL);
        }
        return caches.match(event.request);
      })
  );
});

// Listen for messages from the page
self.addEventListener('message', event => {
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
});
