// Keeps the navbar unread-notifications badge current. Polls every 60 seconds,
// skips hidden tabs, and stops entirely if the session ends (HTTP 401).
(function () {
  "use strict";

  var INTERVAL_MS = 60000;
  var badge = document.querySelector("[data-unread-badge]");
  if (!badge) {
    return;
  }
  var timer = null;

  function refresh() {
    if (document.visibilityState === "hidden") {
      return;
    }
    fetch("/notifications/unread-count.json", { headers: { Accept: "application/json" }, cache: "no-store" })
      .then(function (response) {
        if (response.status === 401 && timer !== null) {
          clearInterval(timer);
          timer = null;
          return null;
        }
        return response.ok ? response.json() : null;
      })
      .then(function (data) {
        if (!data || typeof data.unread !== "number") {
          return;
        }
        badge.textContent = data.unread.toLocaleString("fa-IR");
        badge.hidden = data.unread === 0;
      })
      .catch(function () {
        // Keep the server-rendered count.
      });
  }

  timer = setInterval(refresh, INTERVAL_MS);
  document.addEventListener("visibilitychange", refresh);
})();
