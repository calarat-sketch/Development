/**
 * Service Worker - PWA Gestor de Rutas
 * Permite funcionamiento offline y caching
 */

const CACHE_NAME = 'rutas-v1.0.1';
const STATIC_ASSETS = [
    '/',
    '/index.html',
    '/styles.css',
    '/app.js',
    '/manifest.json'
];

// ============================================================================
// INSTALACIÓN
// ============================================================================

self.addEventListener('install', (event) => {
    console.log('📦 Service Worker instalando...');
    
    event.waitUntil(
        caches.open(CACHE_NAME).then((cache) => {
            console.log('✓ Cache abierto');
            return cache.addAll(STATIC_ASSETS).catch(err => {
                console.warn('⚠ Algunos assets no pudieron cachearse:', err);
            });
        })
    );
    
    self.skipWaiting();
});

// ============================================================================
// ACTIVACIÓN
// ============================================================================

self.addEventListener('activate', (event) => {
    console.log('🚀 Service Worker activado');
    
    event.waitUntil(
        caches.keys().then((cacheNames) => {
            return Promise.all(
                cacheNames.map((cacheName) => {
                    if (cacheName !== CACHE_NAME) {
                        console.log('🗑 Eliminando cache antiguo:', cacheName);
                        return caches.delete(cacheName);
                    }
                })
            );
        })
    );
    
    self.clients.claim();
});

// ============================================================================
// FETCH - Network First Strategy
// ============================================================================

self.addEventListener('fetch', (event) => {
    const { request } = event;
    const url = new URL(request.url);
    
    // API calls: Network first, fallback to cache
    if (url.pathname.startsWith('/api/')) {
        event.respondWith(networkFirst(request));
        return;
    }
    
    // Static assets: Cache first, fallback to network
    if (isStaticAsset(url.pathname)) {
        event.respondWith(cacheFirst(request));
        return;
    }
    
    // Otros: Network first
    event.respondWith(networkFirst(request));
});

// ============================================================================
// ESTRATEGIAS DE CACHE
// ============================================================================

async function networkFirst(request) {
    try {
        // Intentar obtener de la red
        const response = await fetch(request);
        
        // Si es exitoso, guardar en cache
        if (response.ok) {
            const cache = await caches.open(CACHE_NAME);
            cache.put(request, response.clone());
        }
        
        return response;
    } catch (error) {
        // Si falla, intentar cache
        const cached = await caches.match(request);
        if (cached) {
            return cached;
        }
        
        // Si no hay cache, retornar respuesta offline
        return new Response(
            JSON.stringify({
                error: 'Offline - No se pudo cargar el recurso',
                offline: true
            }),
            {
                status: 503,
                statusText: 'Service Unavailable',
                headers: new Headers({
                    'Content-Type': 'application/json'
                })
            }
        );
    }
}

async function cacheFirst(request) {
    // Intentar obtener del cache primero
    const cached = await caches.match(request);
    if (cached) {
        return cached;
    }
    
    try {
        // Si no está en cache, obtener de la red
        const response = await fetch(request);
        
        // Guardar en cache si es exitoso
        if (response.ok) {
            const cache = await caches.open(CACHE_NAME);
            cache.put(request, response.clone());
        }
        
        return response;
    } catch (error) {
        // Fallback offline
        return new Response(
            'Offline - Recurso no disponible',
            {
                status: 503,
                statusText: 'Service Unavailable'
            }
        );
    }
}

// ============================================================================
// UTILIDADES
// ============================================================================

function isStaticAsset(pathname) {
    return /\.(js|css|png|jpg|jpeg|gif|svg|woff|woff2|ttf)$/i.test(pathname);
}

// ============================================================================
// SYNC - Sincronización en background
// ============================================================================

self.addEventListener('sync', (event) => {
    if (event.tag === 'sync-rutas') {
        event.waitUntil(sincronizarRutas());
    }
});

async function sincronizarRutas() {
    try {
        // Aquí iría la lógica para sincronizar datos pendientes
        console.log('🔄 Sincronizando rutas...');
    } catch (error) {
        console.error('Error sincronizando:', error);
    }
}

// ============================================================================
// PUSH - Notificaciones push (opcional)
// ============================================================================

self.addEventListener('push', (event) => {
    if (event.data) {
        const options = {
            body: event.data.text(),
            icon: 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 192 192"><rect fill="%230079bf" width="192" height="192"/><text x="50%" y="50%" font-size="100" font-weight="bold" text-anchor="middle" dominant-baseline="middle" fill="white">🚌</text></svg>',
            badge: 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 192 192"><rect fill="%230079bf" width="192" height="192"/><text x="50%" y="50%" font-size="100" font-weight="bold" text-anchor="middle" dominant-baseline="middle" fill="white">🚌</text></svg>'
        };
        
        event.waitUntil(
            self.registration.showNotification('Gestor de Rutas', options)
        );
    }
});

self.addEventListener('notificationclick', (event) => {
    event.notification.close();
    event.waitUntil(
        clients.matchAll({ type: 'window' }).then((clientList) => {
            for (let i = 0; i < clientList.length; i++) {
                if (clientList[i].url === '/' && 'focus' in clientList[i]) {
                    return clientList[i].focus();
                }
            }
            if (clients.openWindow) {
                return clients.openWindow('/');
            }
        })
    );
});
