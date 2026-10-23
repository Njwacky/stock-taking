// Service Worker for Stock Tracker PWA
const CACHE_NAME = 'stock-tracker-v1.4';
const OFFLINE_URL = '/offline/';

// Application shell. Keep this list in sync with the assets the templates
// actually load: every entry must exist, or install fails and the PWA stops
// updating (that is exactly what the removed legacy stylesheets caused).
const urlsToCache = [
  '/offline/',
  '/static/css/ui.css',
  '/static/css/base.css',
  '/static/css/navbar.css',
  '/static/css/footer.css',
  '/static/css/floating-comment.css',
  '/static/css/add-items.css',
  '/static/css/advanced-calculator.css',
  '/static/css/analytics.css',
  '/static/css/login-lockout.css',
  '/static/js/base.js',
  '/static/js/floating-comment.js',
  '/static/js/dashboard.js',
  '/static/js/add_items.js',
  '/static/js/advanced-calculator.js',
  '/static/js/analytics.js',
  '/static/js/manage_users.js',
  '/static/images/light_blue.png',
  '/static/images/red.png',
  '/static/images/green.png',
  '/static/images/yellow.png'
];

// Install event - cache the application shell
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => {
        console.log('[Service Worker] Caching app shell');
        // Cache each asset independently: a single missing file must not
        // abort the whole install and leave users on a stale service worker.
        return Promise.allSettled(urlsToCache.map(url => cache.add(url)));
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

  // Dynamic pages contain user-specific data and CSRF tokens; never serve them
  // from or write them to the offline cache.
  if (event.request.mode === 'navigate') {
    event.respondWith(
      fetch(event.request)
        .catch(() => caches.match(OFFLINE_URL))
    );
    return;
  }
  
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
      .catch(() => caches.match(event.request))
  );
});

// Listen for messages from the page
self.addEventListener('message', event => {
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
});
