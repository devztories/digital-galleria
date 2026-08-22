/*
 * Live "where will my photo actually sit" preview for customizable
 * products. Wires up every element with [data-preview-widget] on the
 * page.
 *
 * A colour can now have MULTIPLE preview-enabled images — e.g. a front
 * view with 3 photo slots and a separate back view with 1 slot — each
 * shipped from the server as one "page" (see products.PreviewArea and
 * ProductVariant.preview_images). The widget renders these pages as a
 * swipeable, one-at-a-time gallery — arrows, counter, touch swipe —
 * matching the product detail page's image gallery, instead of showing
 * only a single base image.
 *
 * Shapes across ALL pages are matched to the customer's uploaded photos
 * IN ORDER, flattened page-by-page: the 1st uploaded image goes into the
 * 1st shape of the 1st page, and so on, continuing into the 2nd page's
 * shapes once the 1st page's are used up. Any uploaded images beyond the
 * total number of shapes are still stored normally, just without a live
 * preview position. Which page is currently visible doesn't affect this
 * — every shape on every page gets its input the moment files are
 * chosen, so switching pages never loses a placement.
 *
 * Each base image is always shown uncropped (object-fit: contain) so the
 * customer can see exactly where every shape sits on that whole picture.
 * Inside each shape, the customer can drag to pan and scroll/pinch to
 * zoom their photo with no fixed cap.
 *
 * Each shape's final offset/zoom is written into four hidden inputs per
 * uploaded-image-index (placement_area_N, placement_x_N, placement_y_N,
 * placement_scale_N) that get submitted with the rest of the
 * customization form, where N is that image's position in the file
 * input's file list.
 *
 * No-ops entirely if a page has no [data-preview-widget] element, or if
 * the widget has no pages/shapes configured (data-pages is empty) — in
 * that case the surrounding markup falls back to the plain thumbnail
 * list, which the calling template is responsible for rendering.
 */
document.addEventListener('DOMContentLoaded', () => {
  const MIN_SCALE = 0.1;
  const MAX_SCALE = 20; // effectively unlimited for any real use case

  document.querySelectorAll('[data-preview-widget]').forEach((root) => {
    let pages = [];
    try {
      pages = JSON.parse(root.dataset.pages || '[]');
    } catch (e) { pages = []; }
    pages = (pages || [])
      .map((p) => ({
        image_url: p.image_url,
        areas: (p.areas || []).filter((a) => Array.isArray(a.points) && a.points.length >= 3),
      }))
      .filter((p) => p.image_url && p.areas.length);
    if (!pages.length) return; // no preview-enabled images for this colour

    const track = root.querySelector('[data-preview-track]');
    const viewport = root.querySelector('[data-preview-viewport]');
    const counter = root.querySelector('[data-preview-counter]');
    const prevBtn = root.querySelector('[data-preview-prev]');
    const nextBtn = root.querySelector('[data-preview-next]');
    const labelsHost = root.querySelector('[data-preview-shape-labels]');
    const fileInput = document.getElementById(root.dataset.fileInput || '');
    const inputsHost = root.querySelector('[data-preview-inputs]');
    if (!track || !fileInput || !inputsHost) return;

    let pageIndex = 0;

    // One "shape" object per PreviewArea, flattened across every page in
    // order: its own photo layer, drag/zoom state, and hidden inputs —
    // fully independent of the others, but tagged with which page it
    // lives on so it renders in the right stage.
    const shapes = [];

    pages.forEach((page, pIdx) => {
      const stage = document.createElement('div');
      stage.className = 'preview-page';
      stage.style.cssText = 'position:relative;flex:0 0 100%;width:100%;height:100%;';

      const img = document.createElement('img');
      img.src = page.image_url;
      img.alt = '';
      img.draggable = false;
      img.style.cssText = 'display:block;width:100%;height:100%;object-fit:contain;user-select:none;background:var(--surface-2);';

      const layersHost = document.createElement('div');
      layersHost.style.cssText = 'position:absolute;inset:0;';

      stage.appendChild(img);
      stage.appendChild(layersHost);
      track.appendChild(stage);

      page.areas.forEach((area) => {
        const clip = `polygon(${area.points.map(([x, y]) => `${x}% ${y}%`).join(',')})`;
        const layer = document.createElement('div');
        layer.className = 'preview-photo-layer';
        layer.style.cssText = 'position:absolute;inset:0;overflow:hidden;touch-action:none;';
        layer.style.clipPath = clip;
        layer.style.webkitClipPath = clip;
        layersHost.appendChild(layer);

        const inputArea = document.createElement('input');
        inputArea.type = 'hidden';
        const inputX = document.createElement('input');
        inputX.type = 'hidden';
        const inputY = document.createElement('input');
        inputY.type = 'hidden';
        const inputScale = document.createElement('input');
        inputScale.type = 'hidden';
        inputsHost.append(inputArea, inputX, inputY, inputScale);

        shapes.push({
          area, layer, inputArea, inputX, inputY, inputScale, pageIndex: pIdx,
          img: null,
          offsetX: 50, offsetY: 50, scale: 1,
          dragging: false, lastX: 0, lastY: 0,
          pinchStartDist: null, pinchStartScale: 1,
        });
      });
    });

    // Labels shown below the gallery: which uploaded image number fills
    // which shape, and (when there's more than one page) which preview
    // image that shape belongs to.
    if (labelsHost && shapes.length > 1) {
      labelsHost.innerHTML = shapes.map((s, i) => {
        const pageNote = pages.length > 1 ? ` — preview image ${s.pageIndex + 1}` : '';
        return `<span>Spot ${i + 1}${s.area.name ? ` (${s.area.name})` : ''} — your image ${i + 1}${pageNote}</span>`;
      }).join('');
    }

    const showPage = (n) => {
      pageIndex = (n + pages.length) % pages.length;
      track.style.transform = `translateX(-${pageIndex * 100}%)`;
      if (counter) counter.textContent = pages.length > 1 ? `${pageIndex + 1} / ${pages.length}` : '';
    };

    if (pages.length > 1) {
      prevBtn?.addEventListener('click', () => showPage(pageIndex - 1));
      nextBtn?.addEventListener('click', () => showPage(pageIndex + 1));
      let touchStartX = 0;
      (viewport || root).addEventListener('touchstart', (e) => { touchStartX = e.changedTouches[0].clientX; }, { passive: true });
      (viewport || root).addEventListener('touchend', (e) => {
        const dx = e.changedTouches[0].clientX - touchStartX;
        if (Math.abs(dx) > 45) showPage(pageIndex + (dx < 0 ? 1 : -1));
      }, { passive: true });
    } else {
      // Only one preview image — no navigation needed.
      if (prevBtn) prevBtn.hidden = true;
      if (nextBtn) nextBtn.hidden = true;
    }
    showPage(0);

    const applyTransform = (s) => {
      if (!s.img) return;
      s.img.style.transform = `translate(-50%,-50%) translate(${(s.offsetX - 50) * 2}%, ${(s.offsetY - 50) * 2}%) scale(${s.scale})`;
    };

    const setInputs = (s, fileIdx) => {
      s.inputArea.name = `placement_area_${fileIdx}`;
      s.inputX.name = `placement_x_${fileIdx}`;
      s.inputY.name = `placement_y_${fileIdx}`;
      s.inputScale.name = `placement_scale_${fileIdx}`;
      s.inputArea.value = s.area.id;
      s.inputX.value = s.offsetX.toFixed(1);
      s.inputY.value = s.offsetY.toFixed(1);
      s.inputScale.value = s.scale.toFixed(3);
    };

    const showPhoto = (s, file, fileIdx) => {
      s.layer.innerHTML = '';
      s.offsetX = 50; s.offsetY = 50; s.scale = 1;
      s.img = document.createElement('img');
      s.img.src = URL.createObjectURL(file);
      s.img.alt = s.area.name || 'Your photo';
      s.img.draggable = false;
      s.img.style.cssText = 'position:absolute;top:50%;left:50%;min-width:100%;min-height:100%;max-width:none;user-select:none;touch-action:none;';
      s.layer.appendChild(s.img);
      setInputs(s, fileIdx);
      applyTransform(s);
    };

    const clearPhoto = (s) => {
      s.layer.innerHTML = '';
      s.img = null;
      // Detach the hidden inputs from the form by clearing their name —
      // an unmatched shape shouldn't submit a placement for a file that
      // no longer exists at that index.
      s.inputArea.removeAttribute('name');
      s.inputX.removeAttribute('name');
      s.inputY.removeAttribute('name');
      s.inputScale.removeAttribute('name');
    };

    fileInput.addEventListener('change', () => {
      const files = Array.from(fileInput.files || []);
      shapes.forEach((s, i) => {
        if (files[i]) showPhoto(s, files[i], i);
        else clearPhoto(s);
      });
      root.hidden = !files.length;
    });

    // Drag-to-pan and scroll/pinch-to-zoom, scoped per shape via its own
    // clipped layer element — pointer events only land inside the visible
    // (unclipped) region of each layer, so overlapping shapes never
    // interfere with each other, even across different pages.
    shapes.forEach((s) => {
      s.layer.style.cursor = 'grab';
      s.layer.addEventListener('pointerdown', (e) => {
        if (!s.img) return;
        s.dragging = true;
        s.lastX = e.clientX; s.lastY = e.clientY;
        s.layer.setPointerCapture(e.pointerId);
      });
      s.layer.addEventListener('pointermove', (e) => {
        if (!s.dragging || !s.img) return;
        const rect = s.layer.getBoundingClientRect();
        s.offsetX = Math.max(0, Math.min(100, s.offsetX + ((e.clientX - s.lastX) / rect.width) * -100));
        s.offsetY = Math.max(0, Math.min(100, s.offsetY + ((e.clientY - s.lastY) / rect.height) * -100));
        s.lastX = e.clientX; s.lastY = e.clientY;
        applyTransform(s);
        if (s.inputX.name) { s.inputX.value = s.offsetX.toFixed(1); s.inputY.value = s.offsetY.toFixed(1); }
      });
      const endDrag = () => { s.dragging = false; };
      s.layer.addEventListener('pointerup', endDrag);
      s.layer.addEventListener('pointercancel', endDrag);

      s.layer.addEventListener('touchstart', (e) => {
        if (e.touches.length === 2) {
          const [a, b] = e.touches;
          s.pinchStartDist = Math.hypot(a.clientX - b.clientX, a.clientY - b.clientY);
          s.pinchStartScale = s.scale;
        }
      }, { passive: true });
      s.layer.addEventListener('touchmove', (e) => {
        if (e.touches.length === 2 && s.pinchStartDist) {
          const [a, b] = e.touches;
          const dist = Math.hypot(a.clientX - b.clientX, a.clientY - b.clientY);
          s.scale = Math.max(MIN_SCALE, Math.min(MAX_SCALE, s.pinchStartScale * (dist / s.pinchStartDist)));
          applyTransform(s);
          if (s.inputScale.name) s.inputScale.value = s.scale.toFixed(3);
        }
      }, { passive: true });
      s.layer.addEventListener('touchend', () => { s.pinchStartDist = null; });

      s.layer.addEventListener('wheel', (e) => {
        if (!s.img) return;
        e.preventDefault();
        const factor = 1 + (e.deltaY < 0 ? 0.08 : -0.08);
        s.scale = Math.max(MIN_SCALE, Math.min(MAX_SCALE, s.scale * factor));
        applyTransform(s);
        if (s.inputScale.name) s.inputScale.value = s.scale.toFixed(3);
      }, { passive: false });
    });

    // Optional per-shape zoom buttons: any element with
    // data-preview-zoom-in / data-preview-zoom-out and a matching
    // data-shape-index will drive that shape only.
    root.querySelectorAll('[data-preview-zoom-in],[data-preview-zoom-out]').forEach((btn) => {
      const s = shapes[Number(btn.dataset.shapeIndex || 0)];
      if (!s) return;
      const zoomOut = btn.hasAttribute('data-preview-zoom-out');
      btn.addEventListener('click', () => {
        s.scale = Math.max(MIN_SCALE, Math.min(MAX_SCALE, s.scale * (zoomOut ? 0.85 : 1.18)));
        applyTransform(s);
        if (s.inputScale.name) s.inputScale.value = s.scale.toFixed(3);
      });
    });
  });
});