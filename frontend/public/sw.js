/*
 * RationSaathi static shell cache.
 *
 * Privacy rule: never cache /api responses, never cache authenticated content,
 * and never cache anything that could contain member data. Only hashed static
 * assets are cached, and the cache is cleared when a new version activates.
 */
const SHELL_CACHE = "rationsaathi-static-v1";

self.addEventListener("install", (event) => {
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    (async () => {
      const names = await caches.keys();
      await Promise.all(names.filter((name) => name.startsWith("rationsaathi-") && name !== SHELL_CACHE).map((name) => caches.delete(name)));
      await self.clients.claim();
      // Any old runtime caches that might predate this policy are removed.
      const remaining = await caches.keys();
      await Promise.all(remaining.filter((name) => name !== SHELL_CACHE).map((name) => caches.delete(name)));
    })(),
  );
});

self.addEventListener("fetch", (event) => {
  const request = event.request;
  const url = new URL(request.url);

  // Never intercept API traffic or non-GET requests.
  if (request.method !== "GET" || url.pathname.startsWith("/api/")) return;
  if (url.origin !== self.location.origin) return;

  // Only cache static build assets. HTML and navigation requests stay network-only
  // so a shared device cannot reopen a private screen from a stale shell cache.
  if (url.pathname.startsWith("/assets/") || url.pathname === "/logo.svg" || url.pathname === "/manifest.webmanifest") {
    event.respondWith(
      (async () => {
        const cached = await caches.match(request);
        if (cached) return cached;
        const response = await fetch(request);
        if (response.ok) {
          const cache = await caches.open(SHELL_CACHE);
          await cache.put(request, response.clone());
        }
        return response;
      })(),
    );
  }
});
