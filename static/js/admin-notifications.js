/* Admin notification bell: polling, live toasts, sound, and web-push opt-in. */
(function () {
  var wrap = document.getElementById('notif-wrap');
  if (!wrap) return;

  var bell = document.getElementById('notif-bell');
  var panel = document.getElementById('notif-panel');
  var countEl = document.getElementById('notif-count');
  var navCount = document.getElementById('nav-notif-count');
  var listEl = document.getElementById('notif-list');
  var toasts = document.getElementById('notif-toasts');
  var pushBtn = document.getElementById('push-toggle');
  var pushState = document.getElementById('push-state');
  var readAllBtn = document.getElementById('notif-read-all');

  var POLL = wrap.dataset.poll;
  var csrf = (document.cookie.match(/csrftoken=([^;]+)/) || [])[1] || '';
  var lastId = null;          // highest notification id we've already shown
  var vapidKey = '';
  var timer = null;

  function esc(s) { var d = document.createElement('div'); d.textContent = s == null ? '' : s; return d.innerHTML; }

  function post(url, body) {
    return fetch(url, {
      method: 'POST', credentials: 'same-origin', keepalive: true,
      headers: { 'X-CSRFToken': csrf, 'X-Requested-With': 'XMLHttpRequest', 'Content-Type': 'application/json' },
      body: body ? JSON.stringify(body) : '{}'
    });
  }

  function itemHtml(n) {
    return '<a class="notif-item ' + (n.unread ? 'unread' : '') + '" href="' + esc(n.url) + '" data-id="' + n.id + '">' +
      '<span class="notif-dot kind-' + esc(n.kind) + '">' + n.icon + '</span>' +
      '<span><div class="notif-title">' + esc(n.title) + '</div>' +
      (n.body ? '<div class="notif-body">' + esc(n.body) + '</div>' : '') +
      '<div class="notif-time">' + esc(n.time) + '</div></span></a>';
  }

  function renderList(items) {
    listEl.innerHTML = items.length ? items.map(itemHtml).join('') : '<div class="notif-empty">No notifications yet.<br>New orders, payments and customizations will show up here.</div>';
  }

  function setCount(n) {
    [countEl, navCount].forEach(function (el) {
      if (!el) return;
      el.textContent = n > 99 ? '99+' : n;
      el.hidden = !n;
    });
    document.title = (n ? '(' + n + ') ' : '') + document.title.replace(/^\(\d+\+?\)\s/, '');
  }

  // --- sound: a short two-tone chime generated in the browser (no audio file needed) ---
  var audioCtx = null;
  function chime() {
    try {
      audioCtx = audioCtx || new (window.AudioContext || window.webkitAudioContext)();
      var now = audioCtx.currentTime;
      [880, 1320].forEach(function (f, i) {
        var o = audioCtx.createOscillator(), g = audioCtx.createGain();
        o.type = 'sine'; o.frequency.value = f;
        g.gain.setValueAtTime(0.0001, now + i * 0.12);
        g.gain.exponentialRampToValueAtTime(0.15, now + i * 0.12 + 0.02);
        g.gain.exponentialRampToValueAtTime(0.0001, now + i * 0.12 + 0.35);
        o.connect(g); g.connect(audioCtx.destination);
        o.start(now + i * 0.12); o.stop(now + i * 0.12 + 0.4);
      });
    } catch (e) { /* autoplay blocked until the first click — ignore */ }
  }

  function toast(n) {
    var el = document.createElement('a');
    el.className = 'notif-toast'; el.href = n.url;
    el.innerHTML = '<span class="notif-dot kind-' + esc(n.kind) + '">' + n.icon + '</span><span><div class="notif-title">' + esc(n.title) + '</div>' +
      (n.body ? '<div class="notif-body">' + esc(n.body) + '</div>' : '') + '</span>';
    toasts.appendChild(el);
    setTimeout(function () { el.classList.add('leaving'); setTimeout(function () { el.remove(); }, 300); }, 7000);
  }

  function poll() {
    var url = POLL + (lastId !== null ? '?after=' + lastId : '');
    fetch(url, { credentials: 'same-origin', headers: { 'X-Requested-With': 'XMLHttpRequest' } })
      .then(function (r) { if (r.status === 403 || r.redirected) throw new Error('auth'); return r.json(); })
      .then(function (d) {
        setCount(d.unread);
        renderList(d.items);
        vapidKey = d.vapid_key || d.vapid_public_key || '';
        if (lastId !== null && d.new.length) {
          d.new.forEach(toast);
          chime();
          bell.classList.remove('ring'); void bell.offsetWidth; bell.classList.add('ring');
        }
        lastId = d.latest_id;
        updatePushUi(d);
      })
      .catch(function () { /* offline or logged out — try again next tick */ });
  }

  function schedule() {
    clearInterval(timer);
    timer = setInterval(function () { if (!document.hidden) poll(); }, 15000);
  }
  document.addEventListener('visibilitychange', function () { if (!document.hidden) poll(); });

  // --- panel open/close ---
  bell.addEventListener('click', function (e) {
    e.stopPropagation();
    var open = panel.classList.toggle('open');
    bell.setAttribute('aria-expanded', open ? 'true' : 'false');
    if (open) poll();
  });
  document.addEventListener('click', function (e) { if (!wrap.contains(e.target)) { panel.classList.remove('open'); bell.setAttribute('aria-expanded', 'false'); } });
  document.addEventListener('keydown', function (e) { if (e.key === 'Escape') panel.classList.remove('open'); });

  listEl.addEventListener('click', function (e) {
    var a = e.target.closest('.notif-item'); if (!a) return;
    // mark read in the background, then follow the link
    post(wrap.dataset.readBase + a.dataset.id + '/read/');
  });
  readAllBtn.addEventListener('click', function () { post(wrap.dataset.readAll).then(poll); });

  // --- web push ---
  function urlB64ToUint8(b64) {
    var pad = '='.repeat((4 - b64.length % 4) % 4);
    var raw = atob((b64 + pad).replace(/-/g, '+').replace(/_/g, '/'));
    var out = new Uint8Array(raw.length);
    for (var i = 0; i < raw.length; i++) out[i] = raw.charCodeAt(i);
    return out;
  }
  var pushSupported = 'serviceWorker' in navigator && 'PushManager' in window && 'Notification' in window;

  function updatePushUi(d) {
    if (!pushBtn) return;
    if (!d.push_ready) { pushBtn.hidden = true; pushState.textContent = 'Push not configured'; return; }
    if (!pushSupported) { pushBtn.hidden = true; pushState.textContent = 'Push unsupported here'; return; }
    if (Notification.permission === 'denied') { pushBtn.hidden = true; pushState.textContent = 'Push blocked in browser'; return; }
    pushBtn.hidden = false;
    pushBtn.textContent = d.subscribed ? 'Disable push' : 'Enable push';
    pushBtn.dataset.on = d.subscribed ? '1' : '';
    pushState.textContent = d.subscribed ? 'Push on ✓' : '';
  }

  function registerSw() { return navigator.serviceWorker.register(wrap.dataset.sw, { scope: '/admin/' }); }

  pushBtn && pushBtn.addEventListener('click', function () {
    if (pushBtn.dataset.on) {
      registerSw().then(function (reg) { return reg.pushManager.getSubscription(); }).then(function (sub) {
        if (!sub) return;
        return post(wrap.dataset.unsubscribe, { endpoint: sub.endpoint }).then(function () { return sub.unsubscribe(); });
      }).then(poll);
      return;
    }
    Notification.requestPermission().then(function (perm) {
      if (perm !== 'granted') { poll(); return; }
      registerSw().then(function (reg) { return navigator.serviceWorker.ready.then(function () { return reg; }); }).then(function (reg) {
        return reg.pushManager.subscribe({ userVisibleOnly: true, applicationServerKey: urlB64ToUint8(vapidKey) });
      }).then(function (sub) {
        return post(wrap.dataset.subscribe, sub.toJSON());
      }).then(poll).catch(function (err) { pushState.textContent = 'Could not enable push'; console.warn(err); });
    });
  });

  // keep an already-subscribed device's service worker fresh
  if (pushSupported && Notification.permission === 'granted') { registerSw().catch(function () {}); }

  poll(); schedule();
})();
