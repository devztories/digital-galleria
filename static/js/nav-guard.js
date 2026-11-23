/* Back-button behaviour for the storefront  (loaded in <head>, runs before first paint)
 *
 *  A. BACK GOES HOME  — pages that set  window.DG_BACK_HOME = true  (Account, Profile, My Orders,
 *     Addresses, Settings, Change Password, Payment-success). Pressing the browser/phone Back
 *     button on them lands on the Home page directly, whatever you browsed before.
 *
 *  B. FINISHED ORDER IS SEALED  — once an order's payment is submitted, every product / customize /
 *     cart / checkout / payment page that was visited BEFORE it is "stale". If Back ever reaches
 *     one of them it is skipped instantly (no flash, no filled form, no product page) until a
 *     normal page such as Home is reached.
 *
 *  C. Duplicate entries are skipped (cart update, coupon, add-to-cart … that redirect to the page
 *     you were already on would otherwise need several Back presses).
 *
 *  D. On the Home page, Back asks for a second press before leaving the site.
 *
 * Best-effort only: if sessionStorage / history are unavailable the site behaves like a normal
 * website.
 */
(function () {
  "use strict";
  var HOME = window.DG_HOME_URL || "/";
  var path = location.pathname;
  var nav = (performance.getEntriesByType && performance.getEntriesByType("navigation")[0]) || {};
  var type = nav.type || "navigate";

  function get(k) { try { return sessionStorage.getItem(k); } catch (e) { return null; } }
  function set(k, v) { try { sessionStorage.setItem(k, v); } catch (e) {} }
  function list(k) { try { return JSON.parse(get(k) || "[]"); } catch (e) { return []; } }
  function stripHash(u) { return (u || "").split("#")[0]; }
  function state() { return history.state && typeof history.state === "object" ? history.state : {}; }
  function merge(extra) { try { history.replaceState(Object.assign({}, state(), extra), ""); } catch (e) {} }
  function epoch() { return parseInt(get("dgEpoch") || "0", 10) || 0; }
  function refPath() {
    try { var u = new URL(document.referrer); return u.origin === location.origin ? u.pathname : null; }
    catch (e) { return null; }
  }

  // Pages that belong to the buying journey (product detail -> customize -> cart -> checkout -> payment).
  var STALE = /^\/(products\/[^\/]+\/?$|customize\/|cart\/|orders\/checkout|payments\/)/;
  function isStale(st) {
    var e = st && typeof st.dgEpoch === "number" ? st.dgEpoch : 0;
    return STALE.test(path) && e < epoch();
  }
  function bounce() {
    window.__dgSkipping = true;
    document.documentElement.style.visibility = "hidden";   // nothing flashes while we skip
    history.back();
    setTimeout(function () { location.replace(HOME); }, 600); // nothing left to go back to -> Home
  }

  /* Called by the payment-success page once the order is complete. */
  window.DGNav = {
    sealFlow: function () {
      var e = epoch() + 1;
      set("dgEpoch", String(e));
      merge({ dgEpoch: e });
    }
  };

  // ---- B. never show a stale (pre-order) page again ---------------------------------------
  if (type === "back_forward" && isStale(state())) { bounce(); return; }
  window.addEventListener("pageshow", function (e) {
    // restored from the back/forward cache: scripts don't re-run, so re-check here
    if (e.persisted && isStale(state())) bounce();
  });

  // stamp this history entry with the current epoch (once)
  if (typeof state().dgEpoch !== "number") merge({ dgEpoch: epoch() });

  // ---- C. skip duplicate entries ----------------------------------------------------------
  var id = state().dgId;
  var skip = list("dgSkip");
  if (type === "back_forward" && id && skip.indexOf(id) > -1 && !state().dgMarker) { window.__dgSkipping = true; history.back(); return; }
  if (!id) {
    id = Date.now() + "-" + Math.random().toString(36).slice(2, 7);
    merge({ dgId: id });
  }
  var prev = get("dgCur");
  var selfRedirect = type === "navigate" && stripHash(document.referrer) === stripHash(location.href);
  if (selfRedirect && prev && skip.indexOf(prev) < 0) {
    skip.push(prev);
    set("dgSkip", JSON.stringify(skip.slice(-60)));
  }
  set("dgCur", id);

  // ---- A. Back goes Home ------------------------------------------------------------------
  if (window.DG_BACK_HOME) {
    var st = state();
    if (st.dgMarker && type === "back_forward") {            // the guard entry itself was reopened
      window.__dgSkipping = true;
      document.documentElement.style.visibility = "hidden";
      if (st.dgFromHome) history.back(); else location.replace(HOME);
      return;
    }
    if (!st.dgMarker && !st.dgTop) {                         // first visit of this entry
      if (selfRedirect) {
        merge({ dgTop: true });                              // form saved & redirected back here: no new guard needed
      } else {
        try {
          var fromHome = refPath() === HOME;
          history.replaceState(Object.assign({}, st, { dgMarker: true, dgFromHome: fromHome }), "");
          history.pushState(Object.assign({}, st, { dgTop: true }), "");
        } catch (e) {}
      }
    }
    window.addEventListener("popstate", function (e) {
      if (document.body && document.body.classList.contains("modal-open")) return;
      if (e.state && e.state.dgMarker) {
        window.__dgSkipping = true;
        if (e.state.dgFromHome) history.back(); else location.replace(HOME);
      }
    });
    return;
  }

  // ---- D. Home: Back stays here, a quick second Back leaves -------------------------------
  if (path === HOME) {
    try {
      var hs = state();
      if (!hs.dgHomeTop && !hs.dgHomeBase) {                 // first visit of this entry only
        history.replaceState(Object.assign({}, hs, { dgHomeBase: true }), "");
        history.pushState(Object.assign({}, hs, { dgHomeTop: true }), "");
      }
    } catch (e) { return; }
    var lastBack = 0, toast = null;
    window.addEventListener("popstate", function (e) {
      if (document.body && document.body.classList.contains("modal-open")) return;   // story viewer handles its own Back
      if (e.state && e.state.storyModal) return;
      if (e.state && e.state.dgHomeBase) {
        var now = Date.now();
        if (now - lastBack < 1800) { history.back(); return; }                       // second quick Back = leave
        lastBack = now;
        try { history.pushState({ dgHomeTop: true, dgId: id, dgEpoch: epoch() }, ""); } catch (x) {}
        if (!toast) {
          toast = document.createElement("div");
          toast.textContent = "Press back again to leave";
          toast.setAttribute("role", "status");
          toast.style.cssText = "position:fixed;left:50%;bottom:calc(24px + env(safe-area-inset-bottom,0px));transform:translateX(-50%);background:#4A0D14;color:#F7E7CE;border:1px solid #CFA0A2;padding:10px 20px;border-radius:999px;font:600 13px/1.2 Manrope,system-ui,sans-serif;letter-spacing:.02em;z-index:9999;opacity:0;transition:opacity .25s;pointer-events:none";
          document.body.appendChild(toast);
        }
        toast.style.opacity = "1";
        setTimeout(function () { toast.style.opacity = "0"; }, 1600);
      }
    });
  }
})();
