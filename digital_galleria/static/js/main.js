/* ---------- Inline expanding search ---------- */
(function () {
  const toggleBtn = document.getElementById('searchToggle');
  const searchForm = document.getElementById('searchForm');
  const searchInput = document.getElementById('searchInput');
  const suggestionsBox = document.getElementById('searchSuggestions');
  if (!toggleBtn || !searchForm) return;

  toggleBtn.addEventListener('click', () => {
    searchForm.classList.toggle('open');
    if (searchForm.classList.contains('open')) {
      setTimeout(() => searchInput.focus(), 150);
    } else {
      suggestionsBox.classList.remove('show');
    }
  });

  let debounceTimer;
  searchInput.addEventListener('input', () => {
    clearTimeout(debounceTimer);
    const q = searchInput.value.trim();
    if (q.length < 2) {
      suggestionsBox.classList.remove('show');
      return;
    }
    debounceTimer = setTimeout(() => fetchSuggestions(q), 250);
  });

  function fetchSuggestions(q) {
    fetch(`/products/search-suggestions/?q=${encodeURIComponent(q)}`)
      .then(r => r.json())
      .then(data => {
        suggestionsBox.innerHTML = '';
        if (!data.results || data.results.length === 0) {
          suggestionsBox.innerHTML = '<div class="suggestion-empty">No memories found.<br>Try another search.</div>';
        } else {
          data.results.forEach(item => {
            const a = document.createElement('a');
            a.href = item.url;
            a.className = 'suggestion-item';
            a.innerHTML = `
              ${item.image ? `<img src="${item.image}" alt="">` : ''}
              <div>
                <div class="suggestion-name">${item.name}</div>
                <div class="suggestion-cat">${item.category} · ₹${item.price}</div>
              </div>`;
            suggestionsBox.appendChild(a);
          });
        }
        suggestionsBox.classList.add('show');
      });
  }

  document.addEventListener('click', (e) => {
    if (!searchForm.contains(e.target) && e.target !== toggleBtn) {
      suggestionsBox.classList.remove('show');
    }
  });

  // Mobile menu
  const hamburger = document.getElementById('hamburgerBtn');
  const mobileMenu = document.getElementById('mobileMenu');
  const mobileClose = document.getElementById('mobileMenuClose');
  if (hamburger && mobileMenu) {
    hamburger.addEventListener('click', () => mobileMenu.classList.add('open'));
    mobileClose && mobileClose.addEventListener('click', () => mobileMenu.classList.remove('open'));
  }

  // Scroll reveal
  const revealEls = document.querySelectorAll('.reveal');
  if (revealEls.length && 'IntersectionObserver' in window) {
    const obs = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add('in');
          obs.unobserve(entry.target);
        }
      });
    }, { threshold: 0.15 });
    revealEls.forEach(el => obs.observe(el));
  } else {
    revealEls.forEach(el => el.classList.add('in'));
  }
})();
