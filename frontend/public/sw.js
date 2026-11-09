/* Service worker de BarazArte: recibe las notificaciones push de consultas nuevas y abre el panel al tocarlas. */

self.addEventListener("install", () => self.skipWaiting());
self.addEventListener("activate", (event) => event.waitUntil(self.clients.claim()));

self.addEventListener("push", (event) => {
  let data = {};
  try {
    data = event.data ? event.data.json() : {};
  } catch {
    data = { body: event.data ? event.data.text() : "" };
  }

  event.waitUntil(
    (async () => {
      await self.registration.showNotification(data.title || "BarazArte", {
        body: data.body || "Tienes una consulta nueva",
        icon: "/icons/icon-192.png",
        badge: "/icons/badge-96.png",
        tag: "consulta",
        renotify: true,
        data: { url: data.url || "/panel/consultas" },
      });
      // Número en el icono de la app instalada, si el sistema lo admite.
      if (typeof data.unread === "number" && self.navigator.setAppBadge) {
        try {
          await self.navigator.setAppBadge(data.unread);
        } catch {
          /* no soportado */
        }
      }
      // Avisa a las pestañas abiertas para que refresquen el contador.
      const windows = await self.clients.matchAll({ type: "window", includeUncontrolled: true });
      windows.forEach((c) => c.postMessage({ type: "push" }));
    })(),
  );
});

self.addEventListener("notificationclick", (event) => {
  event.notification.close();
  const url = (event.notification.data && event.notification.data.url) || "/panel/consultas";
  event.waitUntil(
    (async () => {
      const windows = await self.clients.matchAll({ type: "window", includeUncontrolled: true });
      for (const c of windows) {
        if ("focus" in c) {
          if ("navigate" in c) await c.navigate(url).catch(() => undefined);
          return c.focus();
        }
      }
      return self.clients.openWindow(url);
    })(),
  );
});
