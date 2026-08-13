(function () {
  const frame = document.getElementById('storyFrame');
  if (!frame) return;
  const slides = Array.from(frame.querySelectorAll('.story-slide'));
  const bars = Array.from(frame.querySelectorAll('.story-bar'));
  if (slides.length === 0) return;

  let current = 0;
  let timer = null;
  let touchStartX = 0;

  function showSlide(index) {
    slides.forEach((s, i) => s.classList.toggle('active', i === index));
    bars.forEach((b, i) => {
      b.classList.toggle('done', i < index);
      const fill = b.querySelector('.story-bar-fill');
      if (i === index) {
        fill.style.transition = 'none';
        fill.style.width = '0%';
        void fill.offsetWidth;
        const duration = parseFloat(slides[index].dataset.duration || '4');
        fill.style.transition = `width ${duration}s linear`;
        requestAnimationFrame(() => { fill.style.width = '100%'; });
      } else if (i > index) {
        fill.style.transition = 'none';
        fill.style.width = '0%';
      }
    });
  }

  function next() {
    current = (current + 1) % slides.length;
    showSlide(current);
    scheduleNext();
  }

  function scheduleNext() {
    clearTimeout(timer);
    const duration = parseFloat(slides[current].dataset.duration || '4') * 1000;
    timer = setTimeout(next, duration);
  }

  function goNext() {
    next();
  }

  // Tap/click on the story advances immediately to the next story.
  frame.addEventListener('click', function (event) {
    // Ignore clicks on explicit controls/links.
    if (event.target.closest('a, button, input')) return;
    goNext();
  });

  // Also support a left swipe on touch devices.
  frame.addEventListener('touchstart', function (event) {
    touchStartX = event.changedTouches[0].clientX;
  }, {passive: true});

  frame.addEventListener('touchend', function (event) {
    const endX = event.changedTouches[0].clientX;
    if (touchStartX - endX > 40) goNext();
  }, {passive: true});

  showSlide(current);
  scheduleNext();
})();
