import React from "react";
import ReactDOM from "react-dom/client";
import { App } from "./app/App";
import { SessionProvider } from "./app/session";
import { I18nProvider } from "./lib/i18n";
import "./index.css";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <I18nProvider>
      <SessionProvider>
        <App />
      </SessionProvider>
    </I18nProvider>
  </React.StrictMode>,
);

// Static-only service worker: it never caches API responses or private data.
if ("serviceWorker" in navigator && import.meta.env.PROD) {
  window.addEventListener("load", () => {
    navigator.serviceWorker.register("/sw.js").catch(() => {
      // Offline shell support is optional; the application remains usable online.
    });
  });
}
