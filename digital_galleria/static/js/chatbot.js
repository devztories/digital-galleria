(function () {
  const launcher = document.getElementById('gvBotLauncher');
  const win = document.getElementById('gvBotWindow');
  if (!launcher || !win) return;

  const messagesBox = document.getElementById('gvBotMessages');
  const input = document.getElementById('gvBotInput');
  const sendBtn = document.getElementById('gvBotSend');

  // ---- Position ----
  function setPosition(x, y) {
    launcher.style.left = x + 'px';
    launcher.style.top = y + 'px';
    launcher.style.right = 'auto';
    launcher.style.bottom = 'auto';
    positionWindowNear(x, y);
  }

  function positionWindowNear(x, y) {
    const vw = window.innerWidth;
    const vh = window.innerHeight;

    let winLeft = x;
    let winTop = y - 470;

    if (winTop < 20) winTop = y + 76;
    if (winLeft + 340 > vw - 16) winLeft = vw - 356;
    if (winLeft < 16) winLeft = 16;

    win.style.left = winLeft + 'px';
    win.style.top = Math.max(16, winTop) + 'px';
    win.style.right = 'auto';
    win.style.bottom = 'auto';
  }

  const stored = sessionStorage.getItem('gvBotPos');

  if (stored) {
    try {
      const { x, y } = JSON.parse(stored);
      setPosition(x, y);
    } catch (e) {
      launcher.style.right = '28px';
      launcher.style.bottom = '28px';
    }
  } else {
    launcher.style.right = '28px';
    launcher.style.bottom = '28px';
  }

  // ---- Drag ----
  let dragging = false;
  let moved = false;
  let startX;
  let startY;
  let originX;
  let originY;

  launcher.addEventListener('pointerdown', (e) => {
    dragging = true;
    moved = false;

    launcher.classList.add('dragging');

    startX = e.clientX;
    startY = e.clientY;

    const rect = launcher.getBoundingClientRect();

    originX = rect.left;
    originY = rect.top;

    launcher.setPointerCapture(e.pointerId);
  });

  launcher.addEventListener('pointermove', (e) => {
    if (!dragging) return;

    const dx = e.clientX - startX;
    const dy = e.clientY - startY;

    if (Math.abs(dx) > 4 || Math.abs(dy) > 4) {
      moved = true;
    }

    if (moved) {
      const nx = Math.min(
        Math.max(0, originX + dx),
        window.innerWidth - launcher.offsetWidth
      );

      const ny = Math.min(
        Math.max(0, originY + dy),
        window.innerHeight - launcher.offsetHeight
      );

      setPosition(nx, ny);
    }
  });

  launcher.addEventListener('pointerup', (e) => {
    dragging = false;

    launcher.classList.remove('dragging');

    const rect = launcher.getBoundingClientRect();

    sessionStorage.setItem(
      'gvBotPos',
      JSON.stringify({
        x: rect.left,
        y: rect.top
      })
    );

    if (!moved) {
      toggleWindow();
    }
  });

  launcher.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      toggleWindow();
    }
  });

  // ---- Outside click closes Hopy ----
  document.addEventListener('pointerdown', (e) => {
    if (!win.classList.contains('open')) return;

    if (!win.contains(e.target) && !launcher.contains(e.target)) {
      win.classList.remove('open');
      launcher.classList.remove('open');

      win.setAttribute('aria-hidden', 'true');
    }
  });

  function toggleWindow() {
    const isOpen = win.classList.toggle('open');

    launcher.classList.toggle('open', isOpen);

    win.setAttribute('aria-hidden', String(!isOpen));

    if (isOpen) {
      const rect = launcher.getBoundingClientRect();

      positionWindowNear(
        rect.left,
        rect.top
      );

      input.focus();
    }
  }

  // ============================================================
  // CHAT MESSAGE
  // ============================================================

  function addMessage(text, from, links, suggestions) {
    const div = document.createElement('div');

    div.className =
      'gv-msg ' +
      (from === 'user'
        ? 'gv-msg-user'
        : 'gv-msg-bot');

    div.textContent = text;

    messagesBox.appendChild(div);

    // ==========================================================
    // PRODUCT SUGGESTIONS
    // ==========================================================

    if (
      from === 'bot' &&
      Array.isArray(suggestions) &&
      suggestions.length
    ) {
      const suggestionWrap =
        document.createElement('div');

      suggestionWrap.className =
        'hopy-suggestions';

      const title =
        document.createElement('div');

      title.className =
        'hopy-suggestion-title';

      title.textContent =
        'Did you mean? 😊';

      suggestionWrap.appendChild(title);

      suggestions
        .slice(0, 5)
        .forEach((item) => {

          if (!item || !item.name) return;

          const button =
            document.createElement('button');

          button.type = 'button';

          button.className =
            'hopy-suggestion-btn';

          button.textContent =
            item.name;

          /*
           * When user taps the product name:
           *
           * 1. Put product name into input
           * 2. Automatically send it
           *
           * So chat becomes:
           *
           * User: Photo Frame
           * Hopy: Photo Frame is ₹699...
           */

          button.addEventListener('click', () => {

            input.value = item.name;

            sendMessage();

          });

          suggestionWrap.appendChild(button);
        });

      messagesBox.appendChild(
        suggestionWrap
      );
    }

    // ==========================================================
    // EXISTING PRODUCT LINKS
    // ==========================================================

    if (
      from === 'bot' &&
      Array.isArray(links) &&
      links.length
    ) {
      const wrap =
        document.createElement('div');

      wrap.className =
        'hopy-links';

      links
        .slice(0, 6)
        .forEach((item) => {

          if (
            !item ||
            !item.url ||
            !item.label
          ) {
            return;
          }

          const a =
            document.createElement('a');

          a.href = item.url;

          a.className =
            'hopy-link-card';

          a.textContent =
            item.label +
            (
              item.price
                ? ' · ₹' + item.price
                : ''
            );

          wrap.appendChild(a);
        });

      messagesBox.appendChild(wrap);
    }

    messagesBox.scrollTop =
      messagesBox.scrollHeight;
  }

  // ============================================================
  // CSRF
  // ============================================================

  function getCookie(name) {
    const match =
      document.cookie.match(
        '(^|;)\\s*' +
        name +
        '\\s*=\\s*([^;]+)'
      );

    return match ? match.pop() : '';
  }

  // ============================================================
  // SEND MESSAGE
  // ============================================================

  function sendMessage() {

    const text =
      input.value.trim();

    if (!text) return;

    // Show user message immediately
    addMessage(
      text,
      'user'
    );

    input.value = '';

    // Disable temporarily
    sendBtn.disabled = true;

    fetch('/chatbot/reply/', {
      method: 'POST',

      headers: {
        'Content-Type':
          'application/x-www-form-urlencoded',

        'X-CSRFToken':
          getCookie('csrftoken'),
      },

      body:
        'message=' +
        encodeURIComponent(text),

    })

      .then((response) => {

        if (!response.ok) {
          throw new Error(
            'Chatbot request failed'
          );
        }

        return response.json();

      })

      .then((data) => {

        addMessage(
          data.reply ||
            'I’m here to help 😊',

          'bot',

          data.links || [],

          data.suggestions || []
        );

      })

      .catch(() => {

        addMessage(
          "Sorry, I couldn't reach the concierge right now.",
          'bot'
        );

      })

      .finally(() => {

        sendBtn.disabled = false;

        input.focus();

      });
  }

  // ============================================================
  // BUTTON
  // ============================================================

  sendBtn.addEventListener(
    'click',
    sendMessage
  );

  // ============================================================
  // ENTER
  // ============================================================

  input.addEventListener(
    'keydown',
    (e) => {

      if (e.key === 'Enter') {

        e.preventDefault();

        sendMessage();

      }

    }
  );

})();