/**
 * Service Worker - PDV Móvel
 * Cache básico para funcionamento offline.
 */

var CACHE_NAME = 'pdv-movel-v1';
var CACHE_URLS = [
    '/pdv-movel/',
    '/pdv-movel/login/',
    '/pdv-movel/pedido/novo/',
    '/pdv-movel/pedidos/',
    '/static/pdv_movel/css/base.css',
    '/static/pdv_movel/css/components.css',
    '/static/pdv_movel/css/tablet.css',
    '/static/pdv_movel/js/utils.js',
    '/static/pdv_movel/js/api.js',
    '/static/pdv_movel/js/pedido.js',
    '/static/pdv_movel/js/produtos.js',
    '/static/pdv_movel/manifest.json'
];

self.addEventListener('install', function(e) {
    e.waitUntil(
        caches.open(CACHE_NAME).then(function(cache) {
            return cache.addAll(CACHE_URLS).catch(function(err) {
                console.error('[SW] Erro ao cachear:', err);
            });
        })
    );
    self.skipWaiting();
});

self.addEventListener('activate', function(e) {
    e.waitUntil(
        caches.keys().then(function(names) {
            return Promise.all(names.map(function(n) {
                if (n !== CACHE_NAME) return caches.delete(n);
            }));
        })
    );
    self.clients.claim();
});

self.addEventListener('fetch', function(e) {
    var req = e.request;
    var url = new URL(req.url);
    if (url.origin !== location.origin) return;

    if (url.pathname.indexOf('/pdv-movel/api/') === 0) {
        e.respondWith(fetch(req));
        return;
    }

    e.respondWith(
        fetch(req).then(function(res) {
            if (res.ok) {
                var clone = res.clone();
                caches.open(CACHE_NAME).then(function(cache) { cache.put(req, clone); });
            }
            return res;
        }).catch(function() {
            return caches.match(req).then(function(cached) {
                if (cached) return cached;
                if (req.mode === 'navigate') return caches.match('/pdv-movel/');
                return new Response('Recurso não disponível offline', { status: 503, statusText: 'Service Unavailable' });
            });
        })
    );
});

self.addEventListener('message', function(e) {
    if (e.data && e.data.action === 'skipWaiting') self.skipWaiting();
});
