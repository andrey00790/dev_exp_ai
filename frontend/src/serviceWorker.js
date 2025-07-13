/**
 * Enhanced Service Worker for AI Assistant MVP PWA
 * Version: 8.0 Enterprise Mobile Optimized
 * 
 * Features:
 * - Offline functionality for critical features
 * - Background sync for chat messages
 * - Push notifications
 * - Intelligent caching strategies
 * - Performance optimization
 */

const CACHE_NAME = 'ai-assistant-v8.0.0';
const API_CACHE_NAME = 'ai-assistant-api-v8.0.0';
const STATIC_CACHE_NAME = 'ai-assistant-static-v8.0.0';

// Resources to cache for offline usage
const STATIC_RESOURCES = [
  '/',
  '/static/js/bundle.js',
  '/static/css/main.css',
  '/manifest.json',
  '/static/media/logo.svg',
  '/offline.html'
];

// API endpoints to cache
const API_ROUTES_TO_CACHE = [
  '/api/v1/health',
  '/api/v1/auth/me',
  '/api/v1/search',
  '/api/v1/ai/chat'
];

// Background sync tags
const SYNC_TAGS = {
  CHAT_MESSAGE: 'chat-message-sync',
  ANALYTICS: 'analytics-sync',
  SEARCH_CACHE: 'search-cache-sync'
};

// Install event - cache static resources
self.addEventListener('install', (event) => {
  console.log('🔧 Service Worker installing...');
  
  event.waitUntil(
    Promise.all([
      // Cache static resources
      caches.open(STATIC_CACHE_NAME).then((cache) => {
        console.log('📦 Caching static resources');
        return cache.addAll(STATIC_RESOURCES);
      }),
      
      // Cache API responses
      caches.open(API_CACHE_NAME).then((cache) => {
        console.log('🌐 Preparing API cache');
        return Promise.resolve();
      })
    ]).then(() => {
      console.log('✅ Service Worker installed successfully');
      // Force activation
      return self.skipWaiting();
    })
  );
});

// Activate event - cleanup old caches
self.addEventListener('activate', (event) => {
  console.log('🚀 Service Worker activating...');
  
  event.waitUntil(
    Promise.all([
      // Clean up old caches
      caches.keys().then((cacheNames) => {
        return Promise.all(
          cacheNames.map((cacheName) => {
            if (
              cacheName !== CACHE_NAME &&
              cacheName !== API_CACHE_NAME &&
              cacheName !== STATIC_CACHE_NAME
            ) {
              console.log(`🗑️ Deleting old cache: ${cacheName}`);
              return caches.delete(cacheName);
            }
          })
        );
      }),
      
      // Take control of all clients
      self.clients.claim()
    ]).then(() => {
      console.log('✅ Service Worker activated successfully');
    })
  );
});

// Fetch event - implement caching strategies
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);
  
  // Handle different types of requests with appropriate strategies
  if (isStaticResource(request)) {
    event.respondWith(handleStaticResource(request));
  } else if (isAPIRequest(request)) {
    event.respondWith(handleAPIRequest(request));
  } else if (isImageRequest(request)) {
    event.respondWith(handleImageRequest(request));
  } else {
    event.respondWith(handleGenericRequest(request));
  }
});

// Background sync for offline actions
self.addEventListener('sync', (event) => {
  console.log(`🔄 Background sync triggered: ${event.tag}`);
  
  switch (event.tag) {
    case SYNC_TAGS.CHAT_MESSAGE:
      event.waitUntil(syncChatMessages());
      break;
    case SYNC_TAGS.ANALYTICS:
      event.waitUntil(syncAnalytics());
      break;
    case SYNC_TAGS.SEARCH_CACHE:
      event.waitUntil(syncSearchCache());
      break;
    default:
      console.log(`Unknown sync tag: ${event.tag}`);
  }
});

// Push notifications
self.addEventListener('push', (event) => {
  console.log('📱 Push notification received');
  
  const options = {
    body: 'You have new updates in AI Assistant',
    icon: '/static/media/logo-192.png',
    badge: '/static/media/badge-72.png',
    vibrate: [100, 50, 100],
    data: {
      dateOfArrival: Date.now(),
      primaryKey: 1
    },
    actions: [
      {
        action: 'explore',
        title: 'Open App',
        icon: '/static/media/checkmark.png'
      },
      {
        action: 'close',
        title: 'Close',
        icon: '/static/media/xmark.png'
      }
    ]
  };
  
  if (event.data) {
    const payload = event.data.json();
    options.body = payload.body || options.body;
    options.data = { ...options.data, ...payload.data };
  }
  
  event.waitUntil(
    self.registration.showNotification('AI Assistant', options)
  );
});

// Notification click handling
self.addEventListener('notificationclick', (event) => {
  console.log('🔔 Notification clicked');
  
  event.notification.close();
  
  if (event.action === 'explore') {
    event.waitUntil(
      clients.openWindow('/')
    );
  }
});

// Message handling for communication with main thread
self.addEventListener('message', (event) => {
  console.log('💬 Message received:', event.data);
  
  if (event.data && event.data.type) {
    switch (event.data.type) {
      case 'SKIP_WAITING':
        self.skipWaiting();
        break;
      case 'CACHE_CHAT_MESSAGE':
        cacheChatMessage(event.data.payload);
        break;
      case 'CACHE_SEARCH_RESULT':
        cacheSearchResult(event.data.payload);
        break;
      case 'CLEAR_CACHE':
        clearAllCaches();
        break;
      default:
        console.log(`Unknown message type: ${event.data.type}`);
    }
  }
});

// ============================================================================
// Caching Strategy Functions
// ============================================================================

/**
 * Handle static resources (Cache First strategy)
 */
async function handleStaticResource(request) {
  try {
    const cache = await caches.open(STATIC_CACHE_NAME);
    const cachedResponse = await cache.match(request);
    
    if (cachedResponse) {
      console.log(`📦 Serving from cache: ${request.url}`);
      return cachedResponse;
    }
    
    console.log(`🌐 Fetching static resource: ${request.url}`);
    const networkResponse = await fetch(request);
    
    if (networkResponse.ok) {
      cache.put(request, networkResponse.clone());
    }
    
    return networkResponse;
  } catch (error) {
    console.error('❌ Error handling static resource:', error);
    return new Response('Resource unavailable offline', { status: 503 });
  }
}

/**
 * Handle API requests (Network First with fallback strategy)
 */
async function handleAPIRequest(request) {
  const cache = await caches.open(API_CACHE_NAME);
  const url = new URL(request.url);
  
  try {
    // Always try network first for API requests
    console.log(`🌐 Fetching API: ${url.pathname}`);
    
    const networkResponse = await fetch(request.clone());
    
    if (networkResponse.ok) {
      // Cache successful responses for offline access
      if (shouldCacheAPIResponse(url.pathname)) {
        cache.put(request, networkResponse.clone());
      }
    }
    
    return networkResponse;
  } catch (error) {
    console.log(`📦 Network failed, trying cache for: ${url.pathname}`);
    
    // Try to serve from cache
    const cachedResponse = await cache.match(request);
    if (cachedResponse) {
      // Add offline indicator header
      const response = cachedResponse.clone();
      response.headers.set('X-Served-From', 'cache');
      return response;
    }
    
    // Return offline fallback for critical endpoints
    return getOfflineFallback(url.pathname);
  }
}

/**
 * Handle image requests (Cache First with network fallback)
 */
async function handleImageRequest(request) {
  try {
    const cache = await caches.open(CACHE_NAME);
    const cachedResponse = await cache.match(request);
    
    if (cachedResponse) {
      return cachedResponse;
    }
    
    const networkResponse = await fetch(request);
    if (networkResponse.ok) {
      cache.put(request, networkResponse.clone());
    }
    
    return networkResponse;
  } catch (error) {
    // Return placeholder image for offline
    return new Response(
      '<svg width="200" height="200" xmlns="http://www.w3.org/2000/svg"><rect width="200" height="200" fill="#f0f0f0"/><text x="100" y="100" text-anchor="middle" dy=".3em">Image unavailable</text></svg>',
      { headers: { 'Content-Type': 'image/svg+xml' } }
    );
  }
}

/**
 * Handle generic requests
 */
async function handleGenericRequest(request) {
  try {
    return await fetch(request);
  } catch (error) {
    // Return offline page for navigation requests
    if (request.mode === 'navigate') {
      const cache = await caches.open(STATIC_CACHE_NAME);
      return cache.match('/offline.html');
    }
    
    return new Response('Service unavailable', { status: 503 });
  }
}

// ============================================================================
// Background Sync Functions
// ============================================================================

/**
 * Sync cached chat messages when back online
 */
async function syncChatMessages() {
  try {
    console.log('🔄 Syncing chat messages...');
    
    const db = await openIndexedDB();
    const transaction = db.transaction(['chatMessages'], 'readonly');
    const store = transaction.objectStore('chatMessages');
    const messages = await getAllFromStore(store);
    
    for (const message of messages) {
      if (!message.synced) {
        try {
          const response = await fetch('/api/v1/ai/chat', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${message.token}`
            },
            body: JSON.stringify(message.data)
          });
          
          if (response.ok) {
            // Mark as synced
            await markMessageAsSynced(db, message.id);
            console.log(`✅ Synced message: ${message.id}`);
          }
        } catch (error) {
          console.error(`❌ Failed to sync message ${message.id}:`, error);
        }
      }
    }
    
    console.log('✅ Chat message sync completed');
  } catch (error) {
    console.error('❌ Error syncing chat messages:', error);
  }
}

/**
 * Sync analytics data
 */
async function syncAnalytics() {
  try {
    console.log('🔄 Syncing analytics...');
    
    const db = await openIndexedDB();
    const transaction = db.transaction(['analytics'], 'readonly');
    const store = transaction.objectStore('analytics');
    const events = await getAllFromStore(store);
    
    if (events.length > 0) {
      const response = await fetch('/api/v1/analytics/events', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ events })
      });
      
      if (response.ok) {
        // Clear synced analytics
        await clearAnalyticsStore(db);
        console.log(`✅ Synced ${events.length} analytics events`);
      }
    }
  } catch (error) {
    console.error('❌ Error syncing analytics:', error);
  }
}

/**
 * Sync search cache
 */
async function syncSearchCache() {
  try {
    console.log('🔄 Updating search cache...');
    
    // Fetch popular searches to cache
    const response = await fetch('/api/v1/search/popular');
    if (response.ok) {
      const popularSearches = await response.json();
      
      const cache = await caches.open(API_CACHE_NAME);
      for (const search of popularSearches) {
        const searchRequest = new Request(`/api/v1/search?q=${encodeURIComponent(search.query)}`);
        const searchResponse = await fetch(searchRequest);
        if (searchResponse.ok) {
          cache.put(searchRequest, searchResponse);
        }
      }
      
      console.log(`✅ Cached ${popularSearches.length} popular searches`);
    }
  } catch (error) {
    console.error('❌ Error syncing search cache:', error);
  }
}

// ============================================================================
// Utility Functions
// ============================================================================

function isStaticResource(request) {
  const url = new URL(request.url);
  return (
    url.pathname.startsWith('/static/') ||
    url.pathname === '/' ||
    url.pathname === '/manifest.json' ||
    url.pathname.endsWith('.html') ||
    url.pathname.endsWith('.css') ||
    url.pathname.endsWith('.js')
  );
}

function isAPIRequest(request) {
  const url = new URL(request.url);
  return url.pathname.startsWith('/api/');
}

function isImageRequest(request) {
  const url = new URL(request.url);
  return /\.(jpg|jpeg|png|gif|webp|svg)$/i.test(url.pathname);
}

function shouldCacheAPIResponse(pathname) {
  const cacheableRoutes = [
    '/api/v1/health',
    '/api/v1/auth/me',
    '/api/v1/search',
    '/api/v1/documents/templates'
  ];
  
  return cacheableRoutes.some(route => pathname.startsWith(route));
}

function getOfflineFallback(pathname) {
  const offlineResponses = {
    '/api/v1/health': new Response(
      JSON.stringify({ status: 'offline', timestamp: new Date().toISOString() }),
      { headers: { 'Content-Type': 'application/json' } }
    ),
    '/api/v1/auth/me': new Response(
      JSON.stringify({ error: 'Authentication unavailable offline' }),
      { status: 503, headers: { 'Content-Type': 'application/json' } }
    )
  };
  
  return offlineResponses[pathname] || new Response(
    JSON.stringify({ error: 'Service unavailable offline' }),
    { status: 503, headers: { 'Content-Type': 'application/json' } }
  );
}

/**
 * Cache chat message for background sync
 */
async function cacheChatMessage(messageData) {
  try {
    const db = await openIndexedDB();
    const transaction = db.transaction(['chatMessages'], 'readwrite');
    const store = transaction.objectStore('chatMessages');
    
    const message = {
      id: Date.now() + Math.random(),
      data: messageData,
      timestamp: Date.now(),
      synced: false
    };
    
    await store.add(message);
    console.log('💾 Chat message cached for sync');
    
    // Register background sync
    if ('serviceWorker' in navigator && 'sync' in window.ServiceWorkerRegistration.prototype) {
      const registration = await navigator.serviceWorker.ready;
      await registration.sync.register(SYNC_TAGS.CHAT_MESSAGE);
    }
  } catch (error) {
    console.error('❌ Error caching chat message:', error);
  }
}

/**
 * Cache search result
 */
async function cacheSearchResult(searchData) {
  try {
    const cache = await caches.open(API_CACHE_NAME);
    const request = new Request(`/api/v1/search?q=${encodeURIComponent(searchData.query)}`);
    const response = new Response(JSON.stringify(searchData.result), {
      headers: { 'Content-Type': 'application/json' }
    });
    
    await cache.put(request, response);
    console.log('💾 Search result cached');
  } catch (error) {
    console.error('❌ Error caching search result:', error);
  }
}

/**
 * Clear all caches
 */
async function clearAllCaches() {
  try {
    const cacheNames = await caches.keys();
    await Promise.all(
      cacheNames.map(cacheName => caches.delete(cacheName))
    );
    console.log('🗑️ All caches cleared');
  } catch (error) {
    console.error('❌ Error clearing caches:', error);
  }
}

// ============================================================================
// IndexedDB Helper Functions
// ============================================================================

function openIndexedDB() {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open('ai-assistant-db', 1);
    
    request.onerror = () => reject(request.error);
    request.onsuccess = () => resolve(request.result);
    
    request.onupgradeneeded = (event) => {
      const db = event.target.result;
      
      if (!db.objectStoreNames.contains('chatMessages')) {
        db.createObjectStore('chatMessages', { keyPath: 'id' });
      }
      
      if (!db.objectStoreNames.contains('analytics')) {
        db.createObjectStore('analytics', { keyPath: 'id', autoIncrement: true });
      }
      
      if (!db.objectStoreNames.contains('searchCache')) {
        db.createObjectStore('searchCache', { keyPath: 'query' });
      }
    };
  });
}

function getAllFromStore(store) {
  return new Promise((resolve, reject) => {
    const request = store.getAll();
    request.onerror = () => reject(request.error);
    request.onsuccess = () => resolve(request.result);
  });
}

async function markMessageAsSynced(db, messageId) {
  const transaction = db.transaction(['chatMessages'], 'readwrite');
  const store = transaction.objectStore('chatMessages');
  const message = await store.get(messageId);
  
  if (message) {
    message.synced = true;
    await store.put(message);
  }
}

async function clearAnalyticsStore(db) {
  const transaction = db.transaction(['analytics'], 'readwrite');
  const store = transaction.objectStore('analytics');
  await store.clear();
}

console.log('🚀 AI Assistant Service Worker v8.0.0 loaded'); 