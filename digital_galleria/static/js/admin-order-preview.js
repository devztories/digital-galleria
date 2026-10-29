/*
 * Read-only "how did the customer position this photo" reference for the
 * admin Order Detail page. Wires up every [.admin-placement-preview] box:
 * clips a copy of the customer's reference photo to the same shape the
 * customer placed it in (see products.PreviewArea), and applies the exact
 * offset/zoom the customer set on the storefront (CustomizationImage.
 * preview_offset_x/y/preview_scale) — a static mirror of the live preview
 * widget, purely for admin/production reference. No interaction here; the
 * original file is always available separately via the
 * "Download original (full quality)" link next to each box.
 */
document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('.admin-placement-preview').forEach((box) => {
    let points = [];
    try {
      points = JSON.parse(box.dataset.points || '[]');
    } catch (e) { points = []; }
    if (!Array.isArray(points) || points.length < 3) return;

    const layer = box.querySelector('.admin-placement-layer');
    const photo = box.querySelector('.admin-placement-photo');
    if (!layer || !photo) return;

    const clip = `polygon(${points.map(([x, y]) => `${x}% ${y}%`).join(',')})`;
    layer.style.clipPath = clip;
    layer.style.webkitClipPath = clip;

    const offsetX = parseFloat(box.dataset.offsetX || '50');
    const offsetY = parseFloat(box.dataset.offsetY || '50');
    const scale = parseFloat(box.dataset.scale || '1');
    photo.style.transform = `translate(-50%,-50%) translate(${(offsetX - 50) * 2}%, ${(offsetY - 50) * 2}%) scale(${scale})`;
  });
});
