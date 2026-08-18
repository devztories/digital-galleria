document.addEventListener("DOMContentLoaded", function () {
  const launcher = document.getElementById("hopy-launcher");
  const win = document.getElementById("hopy-window");
  if (!launcher || !win) return;

  function clamp() {
    const margin = 10;
    const maxX = Math.max(margin, window.innerWidth - launcher.offsetWidth - margin);
    const maxY = Math.max(margin, window.innerHeight - launcher.offsetHeight - margin);
    let x = parseFloat(launcher.style.left || (window.innerWidth - 80));
    let y = parseFloat(launcher.style.top || (window.innerHeight - 90));
    x = Math.min(Math.max(margin, x), maxX);
    y = Math.min(Math.max(margin, y), maxY);
    launcher.style.left = x + "px";
    launcher.style.top = y + "px";
    launcher.style.right = "auto";
    launcher.style.bottom = "auto";
    win.style.left = Math.min(x, window.innerWidth - win.offsetWidth - margin) + "px";
    win.style.bottom = Math.max(76, window.innerHeight - y + 14) + "px";
  }

  window.addEventListener("resize", clamp);
  window.addEventListener("orientationchange", clamp);
  clamp();

  let dragging = false, dragged = false, offX = 0, offY = 0;
  launcher.addEventListener("pointerdown", function (e) {
    dragging = true; dragged = false;
    offX = e.clientX - launcher.offsetLeft;
    offY = e.clientY - launcher.offsetTop;
    launcher.setPointerCapture(e.pointerId);
  });
  launcher.addEventListener("pointermove", function (e) {
    if (!dragging) return;
    dragged = true;
    launcher.style.left = (e.clientX - offX) + "px";
    launcher.style.top = (e.clientY - offY) + "px";
    clamp();
  });
  launcher.addEventListener("pointerup", function () {
    dragging = false;
    if (!dragged) toggleChat();
  });

  function toggleChat() {
    win.classList.toggle("open");
    if (win.classList.contains("open")) {
      clamp();
      win.querySelector('input[name="text"]')?.focus();
    }
  }

  win.querySelector(".hopy-close")?.addEventListener("click", toggleChat);

  const form = win.querySelector(".hopy-input-row");
  const messagesBox = win.querySelector(".hopy-messages");
  const textInput = form?.querySelector('input[name="text"]');
  const fileInput = form?.querySelector('input[name="attachment"]');

  function addMessage(message, sender) {
    const div = document.createElement("div");
    div.className = "hopy-msg " + sender;
    if (message.text) {
      const text = document.createElement("div");
      text.textContent = message.text;
      div.appendChild(text);
    }
    if (message.attachment_url) {
      if (message.attachment_type === "image") {
        const img = document.createElement("img");
        img.src = message.attachment_url; img.alt = message.attachment_name || "Attachment";
        img.className = "hopy-attachment-image"; div.appendChild(img);
      } else if (message.attachment_type === "video") {
        const video = document.createElement("video");
        video.src = message.attachment_url; video.controls = true; video.preload = "metadata";
        video.className = "hopy-attachment-video"; div.appendChild(video);
      } else {
        const a = document.createElement("a");
        a.href = message.attachment_url; a.target = "_blank"; a.rel = "noopener";
        a.textContent = message.attachment_name || "Open attachment";
        a.className = "hopy-file"; div.appendChild(a);
      }
    }
    const time = document.createElement("time");
    time.className = "hopy-time";
    time.textContent = new Date().toLocaleTimeString([], {hour:"2-digit", minute:"2-digit"});
    div.appendChild(time);
    messagesBox.appendChild(div);
    messagesBox.scrollTop = messagesBox.scrollHeight;
  }

  fileInput?.addEventListener("change", function () {
    if (!fileInput.files.length) return;
    const file = fileInput.files[0];
    addMessage({text: "Attachment selected: " + file.name}, "user pending");
  });

  form?.addEventListener("submit", function (e) {
    e.preventDefault();
    const text = textInput.value.trim();
    const file = fileInput.files[0];
    if (!text && !file) return;

    const fd = new FormData(form);
    addMessage({text: text, attachment_url: file ? URL.createObjectURL(file) : "", attachment_type: file ? (file.type.startsWith("image/") ? "image" : file.type.startsWith("video/") ? "video" : "file") : "", attachment_name: file?.name || ""}, "user");
    textInput.value = "";
    fileInput.value = "";

    fetch("/chat/send/", {method:"POST", body:fd})
      .then(r => r.json().then(data => ({ok:r.ok,data})))
      .then(({ok,data}) => {
        if (!ok) { addMessage({text:data.error || "Unable to send that attachment."}, "bot"); return; }
        addMessage({text:data.reply}, "bot");
        (data.products || []).forEach(p => addMessage({text:p.name + " — ₹" + p.price}, "bot"));
      })
      .catch(() => addMessage({text:"Something went wrong. Please try again."}, "bot"));
  });
});
