/* Digital Galleria motion layer. Passive listeners, one rAF loop, IntersectionObserver.
   Does nothing when Admin turned animations off or the visitor prefers reduced motion
   (base.html only adds .js-motion in that case). */
(function () {
  "use strict";
  var root = document.documentElement;
  if (!root.classList.contains("js-motion")) return;

  // KEEP in sync with the selector list in static/css/motion.css
  var REVEAL = ":is(main, .site-footer) :is(.section-title, .stories-row, .category-card, .product-card, .card, .cart-line, .settings-hub-card, .order-summary-link, .checkout-section, .checkout-summary, .payment-card, .empty-state, .value-card, .track-panel, .contact-band, .account-page-header, .product-detail-grid > *, .footer-grid > *):not(.story-modal *, .customization-drawer *, .dg-marquee *, [data-no-reveal])";

  function ready(fn) { if (document.readyState !== "loading") fn(); else document.addEventListener("DOMContentLoaded", fn); }

  ready(function () {
    // main.js (loaded before us) restructures carousels on DOMContentLoaded; run after it.
    requestAnimationFrame(init);
  });

  function init() {
    root.classList.add("dg-motion-ready");

    /* ---------- 1. marquee for admin ad images ---------- */
    document.querySelectorAll("[data-marquee]").forEach(function (row) {
      var items = Array.prototype.slice.call(row.children);
      if (!items.length) return;
      var track = document.createElement("div");
      track.className = "dg-marquee-track";
      items.forEach(function (el) { track.appendChild(el); });
      row.appendChild(track);
      row.classList.add("dg-marquee");
      // repeat the set until one half of the track is wider than the viewport, then double it for a seamless loop
      var base = items.slice(), guard = 0;
      while (track.scrollWidth < row.clientWidth * 1.1 && guard++ < 8) base.forEach(function (el) { track.appendChild(clone(el)); });
      var half = Array.prototype.slice.call(track.children);
      half.forEach(function (el) { track.appendChild(clone(el)); });
      row.style.setProperty("--mq-dur", Math.max(24, half.length * 7) + "s");
    });
    function clone(el) { var c = el.cloneNode(true); c.setAttribute("aria-hidden", "true"); c.tabIndex = -1; c.querySelectorAll("a").forEach(function (a) { a.tabIndex = -1; }); return c; }

    /* ---------- 2. reveal on scroll (stagger by on-screen order) ---------- */
    var targets = document.querySelectorAll(REVEAL);
    if ("IntersectionObserver" in window) {
      var io = new IntersectionObserver(function (entries) {
        var vis = entries.filter(function (e) { return e.isIntersecting; });
        vis.sort(function (a, b) { var A = a.boundingClientRect, B = b.boundingClientRect; return (A.top - B.top) || (A.left - B.left); });
        vis.forEach(function (e, i) {
          e.target.style.setProperty("--rv-i", Math.min(i, 8));
          e.target.classList.add("is-in");
          io.unobserve(e.target);
          // drop the stagger/animation bookkeeping once finished so hovers & later layout are untouched
          e.target.addEventListener("animationend", function done(ev) { if (ev.target !== e.target) return; e.target.style.removeProperty("--rv-i"); e.target.removeEventListener("animationend", done); });
        });
      }, { rootMargin: "0px 140px -6% 140px", threshold: 0.06 });
      targets.forEach(function (el) { io.observe(el); });
    } else {
      targets.forEach(function (el) { el.classList.add("is-in"); });
    }

    /* ---------- 3. images fade in when loaded; lazy-load everything below the fold ---------- */
    document.querySelectorAll("main img, .site-footer img").forEach(function (img) {
      if (img.closest(".story-modal")) return;
      var inHero = !!img.closest(".hero");
      if (!inHero) {
        if (!img.hasAttribute("loading")) img.loading = "lazy";
        if (!img.hasAttribute("decoding")) img.decoding = "async";
      }
      if (inHero || img.complete) return;
      img.classList.add("dg-img-pending");
      var done = function () { img.classList.remove("dg-img-pending"); img.classList.add("dg-img-in"); };
      img.addEventListener("load", done, { once: true });
      img.addEventListener("error", function () { img.classList.remove("dg-img-pending"); }, { once: true });
      setTimeout(function () { img.classList.remove("dg-img-pending"); }, 5000); // never leave an image invisible
    });

    /* ---------- 4. spotlight glint following the pointer (mouse only) ---------- */
    if (window.matchMedia("(hover: hover) and (pointer: fine)").matches) {
      document.querySelectorAll(".product-card, .category-card").forEach(function (card) {
        var glint = document.createElement("span"), raf = 0, px = 0, py = 0;
        glint.className = "dg-glint"; glint.setAttribute("aria-hidden", "true");
        card.appendChild(glint);
        card.addEventListener("pointermove", function (e) {
          var r = card.getBoundingClientRect(); px = e.clientX - r.left; py = e.clientY - r.top;
          if (!raf) raf = requestAnimationFrame(function () { raf = 0; glint.style.transform = "translate3d(" + px + "px," + py + "px,0)"; });
        }, { passive: true });
      });
    }

    /* ---------- 5. one rAF scroll loop: progress bar + hero parallax ---------- */
    // Phones / touch: skip the scroll loop (parallax, progress bar, header resize all force
    // style recalculation every scroll frame = jerky scrolling). Header stays one fixed size on phones.
    if (window.matchMedia("(max-width: 767px), (hover: none)").matches) return;
    var bar = document.createElement("div");
    bar.className = "dg-progress"; bar.setAttribute("aria-hidden", "true");
    document.body.appendChild(bar);
    var siteHeader = document.querySelector(".site-header"), scrolledNow = false;
    var hero = document.querySelector(".hero"), heroImgs = hero ? hero.querySelectorAll(".hero-slide img") : [];
    var docMax = 1, heroH = 0, ticking = false;
    function measure() { docMax = Math.max(1, root.scrollHeight - window.innerHeight); heroH = hero ? hero.offsetHeight : 0; }
    function frame() {
      ticking = false;
      var y = window.pageYOffset;
      bar.style.transform = "scaleX(" + Math.min(1, y / docMax).toFixed(4) + ")";
      if (siteHeader && (y > 24) !== scrolledNow) { scrolledNow = y > 24; siteHeader.classList.toggle("is-scrolled", scrolledNow); }
      if (hero && y < heroH + 200) {
        var py = Math.round(y * 0.12 * 10) / 10; // image drifts at 12% of scroll speed (covered by the Ken Burns scale)
        for (var i = 0; i < heroImgs.length; i++) heroImgs[i].style.setProperty("--py", py + "px");
      }
    }
    function onScroll() { if (!ticking) { ticking = true; requestAnimationFrame(frame); } }
    measure(); frame();
    window.addEventListener("scroll", onScroll, { passive: true });
    window.addEventListener("resize", function () { measure(); onScroll(); }, { passive: true });
    window.addEventListener("load", function () { measure(); onScroll(); });
    if ("ResizeObserver" in window) {
      var roPending = 0;
      new ResizeObserver(function () { if (roPending) return; roPending = requestAnimationFrame(function () { roPending = 0; measure(); }); }).observe(document.body);
    }
  }
})();
