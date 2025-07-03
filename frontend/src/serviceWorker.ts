// Service Worker for AI Assistant PWA
// Provides offline functionality and caching

const CACHE_NAME = 'ai-assistant-v8.0.0';
const STATIC_CACHE = 'ai-assistant-static-v8.0.0';
const DYNAMIC_CACHE = 'ai-assistant-dynamic-v8.0.0';

// Files to cache for offline use
const STATIC_FILES = [
  '/',
  '/static/js/bundle.js',
  '/static/css/main.css',
  '/manifest.json',
  '/icons/icon-192x192.png',
  '/icons/icon-512x512.png',
  '/offline.html'
];

// API endpoints to cache
const API_CACHE_PATTERNS = [
  /\/api\/v1\/health/,
  /\/api\/v1\/data-sources\/sources/,
  /\/api\/v1\/user\/profile/
];

// Install event - cache static files
self.addEventListener('install', (event: ExtendableEvent) => {
  console.log('Service Worker: Installing...');
  
  event.waitUntil(
    caches.open(STATIC_CACHE)
      .then(cache => {
        console.log('Service Worker: Caching static files');
        return cache.addAll(STATIC_FILES);
      })
      .then(() => {
        console.log('Service Worker: Installation complete');
        return self.skipWaiting();
      })
      .catch(error => {
        console.error('Service Worker: Installation failed', error);
      })
  );
});

// Activate event - clean up old caches
self.addEventListener('activate', (event: ExtendableEvent) => {
  console.log('Service Worker: Activating...');
  
  event.waitUntil(
    caches.keys()
      .then(cacheNames => {
        return Promise.all(
          cacheNames.map(cacheName => {
            if (cacheName !== STATIC_CACHE && cacheName !== DYNAMIC_CACHE) {
              console.log('Service Worker: Deleting old cache', cacheName);
              return caches.delete(cacheName);
            }
          })
        );
      })
      .then(() => {
        console.log('Service Worker: Activation complete');
        return self.clients.claim();
      })
  );
});

// Fetch event - implement caching strategies
self.addEventListener('fetch', (event: FetchEvent) => {
  const { request } = event;
  
  // Handle different types of requests
  if (request.url.includes('/api/')) {
    // API requests - network first, then cache
    event.respondWith(networkFirstStrategy(request));
  } else if (request.destination === 'image') {
    // Images - cache first, then network
    event.respondWith(cacheFirstStrategy(request));
  } else {
    // Other requests - stale while revalidate
    event.respondWith(staleWhileRevalidateStrategy(request));
  }
});

// Push notification handling
self.addEventListener('push', (event: PushEvent) => {
  console.log('Service Worker: Push notification received');
  
  const options = {
    body: event.data?.text() || 'New update available',
    icon: '/icons/icon-192x192.png',
    badge: '/icons/badge-72x72.png',
    vibrate: [200, 100, 200],
    data: {
      url: '/'
    },
    actions: [
      {
        action: 'open',
        title: 'Open App'
      },
      {
        action: 'close',
        title: 'Close'
      }
    ]
  };
  
  event.waitUntil(
    self.registration.showNotification('AI Assistant', options)
  );
});

// Notification click handling
self.addEventListener('notificationclick', (event: NotificationEvent) => {
  event.notification.close();
  
  if (event.action === 'open' || !event.action) {
    event.waitUntil(
      self.clients.openWindow('/')
    );
  }
});

// Background sync for offline actions
self.addEventListener('sync', (event: SyncEvent) => {
  if (event.tag === 'chat-sync') {
    event.waitUntil(syncChatMessages());
  } else if (event.tag === 'search-sync') {
    event.waitUntil(syncSearchQueries());
  }
});

// Caching strategies
async function networkFirstStrategy(request: Request): Promise<Response> {
  try {
    const networkResponse = await fetch(request);
    
    if (networkResponse.ok && shouldCacheAPI(request.url)) {
      const cache = await caches.open(DYNAMIC_CACHE);
      cache.put(request, networkResponse.clone());
    }
    
    return networkResponse;
  } catch (error) {
    console.log('Service Worker: Network failed, trying cache', error);
    const cachedResponse = await caches.match(request);
    
    if (cachedResponse) {
      return cachedResponse;
    }
    
    // Return offline page for navigation requests
    if (request.mode === 'navigate') {
      return caches.match('/offline.html') || new Response('Offline');
    }
    
    throw error;
  }
}

async function cacheFirstStrategy(request: Request): Promise<Response> {
  const cachedResponse = await caches.match(request);
  
  if (cachedResponse) {
    return cachedResponse;
  }
  
  try {
    const networkResponse = await fetch(request);
    
    if (networkResponse.ok) {
      const cache = await caches.open(DYNAMIC_CACHE);
      cache.put(request, networkResponse.clone());
    }
    
    return networkResponse;
  } catch (error) {
    console.log('Service Worker: Failed to fetch', request.url);
    throw error;
  }
}

async function staleWhileRevalidateStrategy(request: Request): Promise<Response> {
  const cachedResponse = await caches.match(request);
  
  const fetchPromise = fetch(request).then(response => {
    if (response.ok) {
      const cache = caches.open(STATIC_CACHE);
      cache.then(c => c.put(request, response.clone()));
    }
    return response;
  });
  
  return cachedResponse || fetchPromise;
}

// Helper functions
function shouldCacheAPI(url: string): boolean {
  return API_CACHE_PATTERNS.some(pattern => pattern.test(url));
}

async function syncChatMessages(): Promise<void> {
  try {
    console.log('Service Worker: Syncing chat messages');
    // Implement chat message sync logic
    const pendingMessages = await getPendingChatMessages();
    
    for (const message of pendingMessages) {
      await fetch('/api/v1/chat/sync', {
        method: 'POST',
        body: JSON.stringify(message),
        headers: { 'Content-Type': 'application/json' }
      });
    }
    
    await clearPendingChatMessages();
  } catch (error) {
    console.error('Service Worker: Chat sync failed', error);
  }
}

async function syncSearchQueries(): Promise<void> {
  try {
    console.log('Service Worker: Syncing search queries');
    // Implement search query sync logic
    const pendingQueries = await getPendingSearchQueries();
    
    for (const query of pendingQueries) {
      await fetch('/api/v1/search/sync', {
        method: 'POST',
        body: JSON.stringify(query),
        headers: { 'Content-Type': 'application/json' }
      });
    }
    
    await clearPendingSearchQueries();
  } catch (error) {
    console.error('Service Worker: Search sync failed', error);
  }
}

// IndexedDB helpers for offline storage
async function getPendingChatMessages(): Promise<any[]> {
  // Implement IndexedDB retrieval
  return [];
}

async function clearPendingChatMessages(): Promise<void> {
  // Implement IndexedDB cleanup
}

async function getPendingSearchQueries(): Promise<any[]> {
  // Implement IndexedDB retrieval
  return [];
}

async function clearPendingSearchQueries(): Promise<void> {
  // Implement IndexedDB cleanup
}

// Export for TypeScript
export {}; 