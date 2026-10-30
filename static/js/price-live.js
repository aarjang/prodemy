// Refreshes the home page price card from /prices/latest.json every 30 seconds.
// Progressive enhancement: the server-rendered values stay when this script fails or is off.
(function () {
  "use strict";

  var INTERVAL_MS = 30000;
  var card = document.querySelector("[data-price-card]");
  if (!card) {
    return;
  }

  function setText(selector, text) {
    var el = card.querySelector(selector);
    if (el && text) {
      el.textContent = text;
    }
  }

  function setHidden(selector, hidden) {
    var el = card.querySelector(selector);
    if (el) {
      el.hidden = hidden;
    }
  }

  function refresh() {
    if (document.visibilityState === "hidden") {
      return;
    }
    fetch("/prices/latest.json", { headers: { Accept: "application/json" }, cache: "no-store" })
      .then(function (response) {
        return response.ok ? response.json() : null;
      })
      .then(function (data) {
        if (!data || data.price === null) {
          return;
        }
        setText("[data-price]", data.price_display);
        setText("[data-fetched-at]", data.fetched_at_display);
        setText("[data-traded-at]", data.traded_at_display);
        setHidden("[data-stale-badge]", !data.stale);
        setHidden("[data-stale-note]", !data.stale);
        setHidden("[data-no-recent-trades]", !data.no_recent_trades);
      })
      .catch(function () {
        // Keep the values already on the page.
      });
  }

  setInterval(refresh, INTERVAL_MS);
  document.addEventListener("visibilitychange", refresh);
})();
