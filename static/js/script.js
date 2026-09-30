/**
 * ComicCraft – Main JavaScript
 * Handles: form validation, loading overlay, art-style selection,
 * loading step animation, and PDF download button.
 */

/* ══════════════════════════════════════════════════════════════════
   DOM READY
══════════════════════════════════════════════════════════════════ */
document.addEventListener('DOMContentLoaded', () => {
  initArtStyleSelector();
  initComicForm();
  initPanelAnimations();
  initDownloadButton();
});

/* ══════════════════════════════════════════════════════════════════
   ART STYLE SELECTOR
   Makes the radio-card grid interactive with visual feedback.
══════════════════════════════════════════════════════════════════ */
function initArtStyleSelector() {
  const grid     = document.getElementById('artStyleGrid');
  const hidden   = document.getElementById('art_style_hidden');
  if (!grid) return;

  const cards = grid.querySelectorAll('.style-card');
  const radios = grid.querySelectorAll('.style-radio');

  // Sync visual state with checked radio on load
  radios.forEach(radio => {
    if (radio.checked) activateCard(radio.closest('.style-card'));
  });

  // Update on click
  cards.forEach(card => {
    card.addEventListener('click', () => {
      const radio = card.querySelector('.style-radio');
      if (!radio) return;

      // Deactivate all
      cards.forEach(c => c.classList.remove('style-card--active'));

      // Activate selected
      radio.checked = true;
      card.classList.add('style-card--active');

      // Update hidden input for form submission
      if (hidden) hidden.value = radio.value;

      // Ripple effect
      ripple(card);
    });

    // Keyboard: allow Enter/Space
    card.addEventListener('keydown', e => {
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        card.click();
      }
    });
    card.setAttribute('tabindex', '0');
    card.setAttribute('role', 'button');
  });

  function activateCard(card) {
    if (!card) return;
    cards.forEach(c => c.classList.remove('style-card--active'));
    card.classList.add('style-card--active');
  }
}

/* Quick ripple animation on style card click */
function ripple(element) {
  const el = document.createElement('span');
  el.style.cssText = `
    position:absolute;width:6px;height:6px;border-radius:50%;
    background:rgba(232,24,95,.5);transform:scale(0);
    animation:ripple-anim .5s ease-out forwards;pointer-events:none;
    left:50%;top:50%;translate:-50% -50%;
  `;
  if (!document.getElementById('ripple-style')) {
    const s = document.createElement('style');
    s.id = 'ripple-style';
    s.textContent = `@keyframes ripple-anim{to{transform:scale(20);opacity:0}}`;
    document.head.appendChild(s);
  }
  element.style.position = 'relative';
  element.style.overflow = 'hidden';
  element.appendChild(el);
  setTimeout(() => el.remove(), 600);
}

/* ══════════════════════════════════════════════════════════════════
   COMIC FORM – Validation + Loading Overlay
══════════════════════════════════════════════════════════════════ */
function initComicForm() {
  const form      = document.getElementById('comicForm');
  const btn       = document.getElementById('generateBtn');
  const overlay   = document.getElementById('loadingOverlay');
  if (!form) return;

  form.addEventListener('submit', (e) => {
    const errors = validateForm();
    if (errors.length > 0) {
      e.preventDefault();
      showInlineErrors(errors);
      return;
    }

    // Prevent double-submit
    if (btn) {
      btn.disabled = true;
      btn.querySelector('.btn__text').textContent = 'Creating Comic…';
    }

    // Show the loading overlay
    if (overlay) {
      overlay.classList.add('active');
      overlay.setAttribute('aria-hidden', 'false');
      runLoadingSteps();
    }
  });
}

/* Form validation: returns array of error strings */
function validateForm() {
  const errors = [];
  const prompt    = document.getElementById('story_prompt');
  const character = document.getElementById('character_name');

  if (!prompt || prompt.value.trim().length < 10) {
    errors.push('Story Prompt must be at least 10 characters.');
    if (prompt) highlightField(prompt, true);
  } else {
    if (prompt) highlightField(prompt, false);
  }

  if (!character || character.value.trim().length < 1) {
    errors.push('Character Name is required.');
    if (character) highlightField(character, true);
  } else {
    if (character) highlightField(character, false);
  }

  return errors;
}

/* Add/remove error highlight styling on a field */
function highlightField(el, isError) {
  if (isError) {
    el.style.borderColor = '#e8185f';
    el.style.boxShadow  = '0 0 0 3px rgba(232,24,95,.2)';
  } else {
    el.style.borderColor = '';
    el.style.boxShadow  = '';
  }
}

/* Inject error messages near the form top */
function showInlineErrors(errors) {
  // Remove existing inline error block
  const existing = document.getElementById('js-inline-errors');
  if (existing) existing.remove();

  const box = document.createElement('div');
  box.id = 'js-inline-errors';
  box.className = 'error-box';
  box.setAttribute('role', 'alert');
  box.innerHTML = `
    <div class="error-box__icon">⚠️</div>
    <div class="error-box__content">
      <h3>Please fix the following:</h3>
      <ul>${errors.map(e => `<li>${e}</li>`).join('')}</ul>
    </div>`;

  const form = document.getElementById('comicForm');
  form.parentNode.insertBefore(box, form);
  box.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

/* ── Loading step sequencer ─────────────────────────────────────── */
function runLoadingSteps() {
  const steps    = ['lstep1', 'lstep2', 'lstep3', 'lstep4'];
  const messages = [
    '📖 Writing your story outline with Gemini...',
    '💬 Generating dialogue and narration...',
    '🖼️ Creating comic panel images...',
    '📄 Building layout and exporting PDF...',
  ];
  const msgEl = document.getElementById('loadingMessage');
  let current = 0;

  function advance() {
    if (current > 0) {
      const prev = document.getElementById(steps[current - 1]);
      if (prev) prev.classList.replace('active', 'done');
    }
    if (current < steps.length) {
      const el = document.getElementById(steps[current]);
      if (el) el.classList.add('active');
      if (msgEl) msgEl.textContent = messages[current];
      current++;
      // Randomise timing to feel organic (15-35 sec per step)
      const delay = 14000 + Math.random() * 8000;
      setTimeout(advance, delay);
    }
  }

  // Kick off after 500ms
  setTimeout(advance, 500);
}

/* ══════════════════════════════════════════════════════════════════
   PANEL ANIMATIONS – stagger panel cards on preview page
══════════════════════════════════════════════════════════════════ */
function initPanelAnimations() {
  // Uses IntersectionObserver for subtle entrance per card
  if (!('IntersectionObserver' in window)) return;

  const panels = document.querySelectorAll('.panel-card');
  if (!panels.length) return;

  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.style.animationPlayState = 'running';
        observer.unobserve(entry.target);
      }
    });
  }, { threshold: 0.08 });

  panels.forEach((p, i) => {
    // Pause until in view (CSS sets opacity:0 with delay already)
    p.style.animationPlayState = 'paused';
    observer.observe(p);
  });
}

/* ══════════════════════════════════════════════════════════════════
   DOWNLOAD BUTTON – visual feedback
══════════════════════════════════════════════════════════════════ */
function initDownloadButton() {
  const btn = document.getElementById('downloadPdfBtn');
  if (!btn) return;

  btn.addEventListener('click', () => {
    const original = btn.innerHTML;
    btn.innerHTML = '<span>⏳</span> Downloading…';
    btn.style.opacity = '0.8';
    setTimeout(() => {
      btn.innerHTML = '<span>✅</span> Downloaded!';
      btn.style.opacity = '1';
      setTimeout(() => {
        btn.innerHTML = original;
      }, 2500);
    }, 1200);
  });
}
