document.addEventListener("DOMContentLoaded", function () {
  const root = document.documentElement;

  /* Premium inline search */
  const header = document.querySelector(".site-header");
  const search = document.getElementById("header-search");
  const searchInput = search && search.querySelector(".js-search-input");
  const suggestions = search && search.querySelector(".search-suggestions");
  const endpoint = header && header.dataset.searchEndpoint;
  const triggers = document.querySelectorAll("[data-search-trigger]");
  const close = document.querySelector("[data-search-close]");
  let searchTimer = null;

  function openSearch() {
    if (!search) return;
    search.classList.add("is-open");
    triggers.forEach(btn => btn.setAttribute("aria-expanded", "true"));
    window.requestAnimationFrame(() => searchInput && searchInput.focus());
  }
  function closeSearch() {
    if (!search) return;
    search.classList.remove("is-open");
    suggestions && (suggestions.hidden = true);
    triggers.forEach(btn => btn.setAttribute("aria-expanded", "false"));
  }
  triggers.forEach(btn => btn.addEventListener("click", function (e) {
    e.preventDefault();
    if (search && search.classList.contains("is-open")) closeSearch(); else openSearch();
  }));
  close && close.addEventListener("click", closeSearch);

  if (searchInput && suggestions) {
    searchInput.addEventListener("input", function () {
      clearTimeout(searchTimer);
      const q = searchInput.value.trim();
      if (!q) { suggestions.innerHTML = ""; suggestions.hidden = true; return; }
      searchTimer = setTimeout(() => {
        fetch(endpoint + "?q=" + encodeURIComponent(q), { headers: { "X-Requested-With": "XMLHttpRequest" } })
          .then(r => r.ok ? r.json() : { results: [] })
          .then(data => {
            suggestions.innerHTML = "";
            (data.results || []).slice(0, 6).forEach(item => {
              const a = document.createElement("a");
              a.href = "/products/" + encodeURIComponent(item.slug) + "/";
              a.setAttribute("role", "option");
              a.textContent = item.name;
              suggestions.appendChild(a);
            });
            suggestions.hidden = !suggestions.children.length;
          }).catch(() => { suggestions.hidden = true; });
      }, 180);
    });
  }
  document.addEventListener("click", e => {
    if (search && !search.contains(e.target) && !e.target.closest("[data-search-trigger]")) closeSearch();
  });
  document.addEventListener("keydown", e => { if (e.key === "Escape") closeSearch(); });

  /* Hero rotation */
  const heroTrack = document.querySelector(".hero-track");
  if (heroTrack) {
    const slides = heroTrack.querySelectorAll(".hero-slide");
    const dots = document.querySelectorAll(".hero-dots span");
    let idx = 0;
    const duration = parseInt(heroTrack.dataset.duration || "5000", 10);
    const show = i => { idx = (i + slides.length) % slides.length; heroTrack.style.transform = `translateX(-${idx * 100}%)`; dots.forEach((d, di) => d.classList.toggle("active", di === idx)); };
    let timer = window.matchMedia("(prefers-reduced-motion: reduce)").matches ? null : setInterval(() => show(idx + 1), duration);
    show(0);
    heroTrack.addEventListener("click", () => { if (timer) { clearInterval(timer); timer = setInterval(() => show(idx + 1), duration); } });
  }

  /* Stories */
  const storyItems = document.querySelectorAll(".story-item");
  const modal = document.getElementById("story-modal");
  if (storyItems.length && modal) {
    const modalImg = modal.querySelector("img"), progressBar = modal.querySelector(".story-progress-bar");
    let storyIdx = 0, storyTimer = null, storyHistoryPushed = false;
    const images = Array.from(storyItems).map(el => ({ src: el.dataset.image, duration: parseInt(el.dataset.duration || "4000", 10) }));
    function playStory(i) {
      if (!images.length) return closeModal();
      storyIdx = (i + images.length) % images.length; modalImg.src = images[i].src; progressBar.style.transition = "none"; progressBar.style.width = "0%";
      if (!window.matchMedia("(prefers-reduced-motion: reduce)").matches) requestAnimationFrame(() => { progressBar.style.transition = `width ${images[i].duration}ms linear`; progressBar.style.width = "100%"; });
      clearTimeout(storyTimer); storyTimer = setTimeout(() => playStory(storyIdx + 1), images[i].duration);
    }
    function openModal(i) {
      modal.classList.add("open");
      document.body.classList.add("modal-open");
      if (!storyHistoryPushed) { history.pushState({ storyModal: true }, "", location.href); storyHistoryPushed = true; }
      playStory(i);
    }
    function closeModal(fromPopstate) {
      modal.classList.remove("open");
      document.body.classList.remove("modal-open");
      clearTimeout(storyTimer);
      if (storyHistoryPushed) {
        storyHistoryPushed = false;
        if (!fromPopstate) { history.back(); return; }
      }
    }
    window.addEventListener("popstate", () => { if (modal.classList.contains("open")) closeModal(true); });
    storyItems.forEach((el, i) => el.addEventListener("click", () => openModal(i)));
    let storyStartX = 0;
    modal.addEventListener("touchstart", e => { storyStartX = e.changedTouches[0].clientX; }, {passive:true});
    modal.addEventListener("touchend", e => {
      if (e.target.closest(".story-close")) return;
      const dx = e.changedTouches[0].clientX - storyStartX;
      if (Math.abs(dx) > 45) playStory(storyIdx + (dx < 0 ? 1 : -1));
      else if (e.target === modal || e.target === modalImg) playStory(storyIdx + 1);
    }, {passive:true});
    modal.addEventListener("click", e => {
      if (e.target.closest(".story-close")) { closeModal(false); return; }
      // Backdrop / image taps advance to the next story rather than
      // closing — closing is only via the explicit close button or
      // the device/browser back action.
      if (e.target === modal || e.target === modalImg) playStory(storyIdx + 1);
    });
  }

  /* Product sections: max 10 products per horizontal row/segment.
     Carousels start hidden (see CSS) so this DOM restructuring
     happens invisibly instead of causing a visible layout "jerk"
     right after the page paints. */
  document.querySelectorAll('[data-product-carousel]').forEach(carousel => {
    const cards = Array.from(carousel.children);
    if (cards.length > 10) {
      const fragment = document.createDocumentFragment();
      for (let start = 0; start < cards.length; start += 10) {
        const row = document.createElement('div');
        row.className = 'product-carousel-row';
        cards.slice(start, start + 10).forEach(card => row.appendChild(card));
        fragment.appendChild(row);
      }
      carousel.replaceChildren(fragment);
      carousel.classList.add('product-carousel-grouped');
    }
    carousel.classList.add('carousel-ready');
  });

  /* Theme preference, retained for existing account/theme functionality */
  document.querySelectorAll("[data-theme-toggle]").forEach(btn => btn.addEventListener("click", () => {
    const current = root.getAttribute("data-theme") || "system";
    const next = current === "light" ? "dark" : current === "dark" ? "system" : "light";
    root.setAttribute("data-theme", next); localStorage.setItem("dg-theme", next);
  }));
  const savedTheme = localStorage.getItem("dg-theme");
  if (savedTheme === "light" || savedTheme === "dark" || savedTheme === "system") root.setAttribute("data-theme", savedTheme);

  /* Global button feedback */
  document.addEventListener("click", e => {
    const btn = e.target.closest("button, .btn");
    if (btn && !btn.disabled) { btn.classList.remove("tap-feedback"); void btn.offsetWidth; btn.classList.add("tap-feedback"); }
  });
});

/* Admin theme live preview: local form preview only, never mutates saved settings. */
document.addEventListener("input", function (event) {
  if (!document.body.classList.contains("admin-theme-editor")) return;
  const field = event.target;
  if (!field.name || !field.value) return;
  const token = field.name;
  const map = {background:"--bg", surface:"--surface", text:"--text", muted_text:"--text-dim", heading:"--heading", accent:"--ivory", button:"--button", button_text:"--button-text", border:"--border"};
  if (map[token]) document.documentElement.style.setProperty(map[token], field.value);
});
