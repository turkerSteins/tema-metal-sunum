'use strict';

/* ─── STATE & DOM (DYNAMIC SLIDES) ─────────────────── */
const slides = Array.from(document.querySelectorAll('.slide:not(.slide-hidden)'));
const dots = Array.from(document.querySelectorAll('.ndot:not(.slide-hidden)'));
const TOTAL = slides.length;
let cur = 0, busy = false;

const prevBtn = document.getElementById('prevBtn');
const nextBtn = document.getElementById('nextBtn');
const counter = document.getElementById('counter');
const coverCta = document.getElementById('coverCta');
const restartBtn = document.getElementById('restartBtn');

/* ─── NAVIGATE ──────────────────────────────────────── */
function go(to, dir = 'next') {
  if (busy || to === cur || to < 0 || to >= TOTAL) return;
  busy = true;

  const old = slides[cur];
  const nxt = slides[to];

  old.classList.remove('active');
  old.classList.add('exit-l');

  nxt.style.transform = dir === 'next' ? 'translateX(80px) scale(0.98)' : 'translateX(-80px) scale(0.98)';
  nxt.style.opacity = '0';
  void nxt.offsetWidth; // force reflow

  nxt.style.transition = 'opacity .55s cubic-bezier(0.16, 1, 0.3, 1), transform .55s cubic-bezier(0.16, 1, 0.3, 1)';
  nxt.style.transform = 'none';
  nxt.style.opacity = '1';
  nxt.classList.add('active');

  setTimeout(() => {
    old.classList.remove('exit-l');
    old.style.transform = old.style.opacity = '';
    nxt.style.transition = nxt.style.transform = nxt.style.opacity = '';
    busy = false;
    onEnter(to);
  }, 580);

  cur = to;
  updateUI();
  if (history.replaceState && slides[cur]) {
    history.replaceState(null, '', '#' + slides[cur].id);
  }
}

const next = () => go(cur + 1, 'next');
const prev = () => go(cur - 1, 'prev');

function updateUI() {
  dots.forEach((d, i) => d.classList.toggle('active', i === cur));
  counter.textContent = `${cur + 1} / ${TOTAL}`;
  prevBtn.disabled = cur === 0;
  nextBtn.disabled = cur === TOTAL - 1;
}

/* ─── SLIDE ENTER HOOKS (MAPPED BY SLIDE ID) ────────── */
function onEnter(idx) {
  const slide = slides[idx];
  if (!slide) return;
  const id = slide.id;

  if (id === 's0') {
    initCanvas('coverCanvas');
    animateCounters('#s0');
  } else if (id === 's1') {
    animateMetricCards();
  } else if (id === 's2') {
    animateFlowDiagramV2();
  } else if (id === 's3') {
    animateQualitySlide();
  } else if (id === 's4') {
    animateEMS();
  } else if (id === 's5') {
    animateHeroLayout();
  } else if (id === 's6') {
    animateCockpitSlide();
  } else if (id === 's7') {
    initCanvas('closingCanvas');
    animateClosingSlide();
  }

  if (window.lucide && typeof window.lucide.createIcons === 'function') {
    window.lucide.createIcons();
  }
}

// Dynamically re-index stag numbers for active slides
function updateSlideStags() {
  slides.forEach((slide, i) => {
    const stag = slide.querySelector('.stag');
    if (stag && i > 0) {
      const parts = stag.textContent.split('·');
      if (parts.length > 1) {
        const numStr = String(i + 1).padStart(2, '0');
        stag.textContent = `${numStr} ·${parts.slice(1).join('·')}`;
      }
    }
  });
}
updateSlideStags();

/* ─── COUNT-UP ──────────────────────────────────────── */
function countUp(el, target, dur = 1400) {
  const t0 = performance.now();
  const rawTarget = el.dataset.target || target.toString();
  const isFloat = rawTarget.includes('.') || target % 1 !== 0;
  const decimals = isFloat ? (rawTarget.split('.')[1] || '0').length : 0;

  const snap = () => {
    const p = Math.min((performance.now() - t0) / dur, 1);
    const e = 1 - Math.pow(1 - p, 4);
    if (isFloat) {
      el.textContent = (e * target).toFixed(decimals);
    } else {
      el.textContent = Math.round(e * target);
    }
    if (p < 1) requestAnimationFrame(snap);
  };
  requestAnimationFrame(snap);
}

function animateCounters(scope) {
  document.querySelectorAll(`${scope} .countup`).forEach(el => {
    el.textContent = '0';
    countUp(el, parseFloat(el.dataset.target), 1800);
  });
}

/* ─── METRIC CARDS (S1) ─────────────────────────────── */
function animateMetricCards() {
  const cards = document.querySelectorAll('#s1 .mc');
  cards.forEach(c => {
    c.classList.remove('animated');
    c.querySelectorAll('.countup').forEach(el => (el.textContent = '0'));
    void c.offsetWidth;
  });
  cards.forEach((c, i) => {
    setTimeout(() => {
      c.classList.add('animated');
      c.querySelectorAll('.countup').forEach(el => countUp(el, +el.dataset.target, 1400));
    }, i * 110);
  });
}

/* ─── ISOMETRIC FACTORY FLOW LOOP (S2) ──────────────── */
let isoS2Running = false;
let isoS2StartTime = 0;
const ISO_S2_DURATION = 18.5;

function initIsoGridS2() {
  const gridGroup = document.getElementById('isoGridLinesS2');
  if (gridGroup && gridGroup.children.length === 0) {
    const ns = 'http://www.w3.org/2000/svg';
    for (let i = -14; i <= 26; i++) {
      let l1 = document.createElementNS(ns, 'line');
      l1.setAttribute('x1', -350 + i * 72);
      l1.setAttribute('y1', 220);
      l1.setAttribute('x2', 400 + i * 72);
      l1.setAttribute('y2', 880);
      l1.setAttribute('class', 'grids');
      gridGroup.appendChild(l1);

      let l2 = document.createElementNS(ns, 'line');
      l2.setAttribute('x1', -350 + i * 80);
      l2.setAttribute('y1', 680);
      l2.setAttribute('x2', 400 + i * 80);
      l2.setAttribute('y2', 30);
      l2.setAttribute('class', 'grids');
      gridGroup.appendChild(l2);
    }
  }
}

function animateFlowDiagramV2() {
  const iframe = document.getElementById('isoEmbedIframe');
  if (iframe && iframe.contentWindow) {
    try {
      // Focus or reset if supported
      iframe.contentWindow.postMessage({ type: 'SLIDE_ACTIVE' }, '*');
    } catch (e) {}
  }
}


/* ─── QUALITY & MAINTENANCE (S3) ────────────────────── */
function animateQualitySlide() {
  const gates = document.querySelectorAll('#s3 .qm-gate');
  const maints = document.querySelectorAll('#s3 .maint-item, #s3 .maint-innovation');

  gates.forEach(g => {
    g.classList.remove('animated');
    void g.offsetWidth;
  });
  maints.forEach(m => {
    m.classList.remove('animated');
    void m.offsetWidth;
  });

  gates.forEach((g, i) => {
    setTimeout(() => g.classList.add('animated'), 60 + i * 75);
  });
  maints.forEach((m, i) => {
    setTimeout(() => m.classList.add('animated'), 100 + i * 85);
  });
}

/* ─── EMS ANIMATION (S4) ─────────────────────────────── */
function animateEMS() {
  const cards = document.querySelectorAll('#s4 .ems-card');
  cards.forEach(c => {
    c.classList.remove('animated');
    c.querySelectorAll('.countup').forEach(el => (el.textContent = '0'));
    void c.offsetWidth;
  });
  cards.forEach((c, i) => {
    setTimeout(() => {
      c.classList.add('animated');
      c.querySelectorAll('.countup').forEach(el => countUp(el, parseFloat(el.dataset.target), 1400));
    }, i * 130);
  });
}

/* ─── HERO LAYOUT ANIMATION (S5) ─────────────────────── */
function animateHeroLayout() {
  const frame = document.getElementById('heroLayoutFrame');
  if (frame) {
    frame.classList.remove('hero-entered');
    void frame.offsetWidth;
    setTimeout(() => frame.classList.add('hero-entered'), 60);
  }
}

/* ─── COCKPIT SLIDE ANIMATION (S6) ───────────────────── */
function animateCockpitSlide() {
  const frame = document.getElementById('heroCockpitFrame');
  if (frame) {
    frame.classList.remove('hero-entered');
    void frame.offsetWidth;
    setTimeout(() => frame.classList.add('hero-entered'), 60);
  }

  const cards = document.querySelectorAll('#cockpitCardsCol .glass-info-card');
  cards.forEach(c => c.classList.remove('card-visible'));
  cards.forEach((c, i) => {
    setTimeout(() => c.classList.add('card-visible'), 160 + i * 120);
  });
}

/* ─── CLOSING SLIDE ANIMATION (S7) ───────────────────── */
function animateClosingSlide() {
  const cards = document.querySelectorAll('#s7 .croi-card');
  cards.forEach(c => {
    c.classList.remove('animated');
    c.querySelectorAll('.countup').forEach(el => (el.textContent = '0'));
    void c.offsetWidth;
  });
  cards.forEach((c, i) => {
    setTimeout(() => {
      c.classList.add('animated');
      c.querySelectorAll('.countup').forEach(el => countUp(el, +el.dataset.target, 1500));
    }, 140 + i * 110);
  });
}

/* ─── CANVAS PARTICLES (S0 & S7) ────────────────────── */
function initCanvas(id) {
  const canvas = document.getElementById(id);
  if (!canvas || canvas._done) return;
  canvas._done = true;

  const ctx = canvas.getContext('2d');
  let W, H, particles;

  function resize() {
    W = canvas.width = canvas.offsetWidth;
    H = canvas.height = canvas.offsetHeight;
  }
  resize();
  new ResizeObserver(resize).observe(canvas.parentElement);

  const N = 55;
  particles = Array.from({ length: N }, () => mkP());

  function mkP() {
    return {
      x: Math.random() * (W || 1920),
      y: Math.random() * (H || 1080),
      vx: (Math.random() - 0.5) * 0.4,
      vy: -0.2 - Math.random() * 0.6,
      r: Math.random() * 2 + 0.5,
      a: 0,
      life: Math.random(),
      maxLife: 0.5 + Math.random() * 0.5,
      color: Math.random() > 0.5 ? '#0284c7' : '#00f2fe',
    };
  }

  function tick() {
    ctx.clearRect(0, 0, W, H);

    // Grid dots
    ctx.fillStyle = 'rgba(56,189,248,0.05)';
    const step = 60;
    for (let gx = 0; gx < W; gx += step) {
      for (let gy = 0; gy < H; gy += step) {
        ctx.beginPath();
        ctx.arc(gx, gy, 1.5, 0, Math.PI * 2);
        ctx.fill();
      }
    }

    // Particles
    particles.forEach((p, i) => {
      p.life += 0.004;
      if (p.life >= p.maxLife) {
        particles[i] = mkP();
        particles[i].y = H + 10;
        return;
      }
      const frac = p.life / p.maxLife;
      const alpha = frac < 0.2 ? frac / 0.2 : frac > 0.8 ? (1 - frac) / 0.2 : 1;
      p.x += p.vx;
      p.y += p.vy;
      ctx.beginPath();
      ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
      ctx.fillStyle = p.color + Math.round(alpha * 160).toString(16).padStart(2, '0');
      ctx.fill();

      // Glow
      const g = ctx.createRadialGradient(p.x, p.y, 0, p.x, p.y, p.r * 6);
      g.addColorStop(0, p.color + '22');
      g.addColorStop(1, 'transparent');
      ctx.fillStyle = g;
      ctx.beginPath();
      ctx.arc(p.x, p.y, p.r * 6, 0, Math.PI * 2);
      ctx.fill();
    });

    // Diagonal scan lines
    ctx.strokeStyle = 'rgba(56,189,248,0.03)';
    ctx.lineWidth = 1;
    const t = Date.now() / 6000;
    for (let k = -5; k < 15; k++) {
      const off = ((k + t) % 10) * 120;
      ctx.beginPath();
      ctx.moveTo(off - H, 0);
      ctx.lineTo(off, H);
      ctx.stroke();
    }

    requestAnimationFrame(tick);
  }
  tick();
}

/* ─── EVENTS ────────────────────────────────────────── */
prevBtn.addEventListener('click', prev);
nextBtn.addEventListener('click', next);
coverCta?.addEventListener('click', next);
restartBtn?.addEventListener('click', () => go(0, 'prev'));
dots.forEach((d, i) => d.addEventListener('click', () => go(i, i > cur ? 'next' : 'prev')));

// Quick Isometric Flow Direct Navigators
const btnJumpToIsoFlow = document.getElementById('btnJumpToIsoFlow');

const goToIsoSlide = () => {
  const s2Idx = slides.findIndex(s => s.id === 's2');
  if (s2Idx !== -1) {
    go(s2Idx, s2Idx > cur ? 'next' : 'prev');
  }
};

btnJumpToIsoFlow?.addEventListener('click', goToIsoSlide);

// Keyboard Navigation
document.addEventListener('keydown', e => {
  if (['ArrowRight', 'ArrowDown', ' '].includes(e.key)) {
    e.preventDefault();
    next();
  }
  if (['ArrowLeft', 'ArrowUp'].includes(e.key)) {
    e.preventDefault();
    prev();
  }
  if (e.key === 'Home') {
    e.preventDefault();
    go(0, 'prev');
  }
  if (e.key === 'End') {
    e.preventDefault();
    go(TOTAL - 1, 'next');
  }
  if (e.key === 'f' || e.key === 'F' || e.key === 'F10' || e.key === 'F11') {
    e.preventDefault();
    togglePresentationFullscreen();
  }
});

function togglePresentationFullscreen() {
  if (!document.fullscreenElement) {
    document.documentElement.requestFullscreen().catch(() => { });
  } else {
    document.exitFullscreen().catch(() => { });
  }
}

const fsToggleBtn = document.getElementById('fullscreenToggleBtn');
if (fsToggleBtn) {
  fsToggleBtn.addEventListener('click', togglePresentationFullscreen);
}

// Touch / Swipe Navigation
let tx = 0;
document.addEventListener('touchstart', e => {
  tx = e.touches[0].clientX;
}, { passive: true });

document.addEventListener('touchend', e => {
  const dx = e.changedTouches[0].clientX - tx;
  if (Math.abs(dx) > 60) {
    dx < 0 ? next() : prev();
  }
}, { passive: true });

// Wheel Navigation
let wt = null;
document.addEventListener('wheel', e => {
  if (wt) return;
  if (Math.abs(e.deltaY) < 15) return;
  e.preventDefault();
  e.deltaY > 0 ? next() : prev();
  wt = setTimeout(() => (wt = null), 900);
}, { passive: false });

/* ─── INIT ──────────────────────────────────────────── */
// Export modu (?export=1): LinkedIn carousel için ekran görüntüsü alınırken
// navigasyon arayüzünü gizler. Normal sunum kullanımını etkilemez.
const exportParams = new URLSearchParams(window.location.search);
if (exportParams.has('export')) {
  document.body.classList.add('export-mode');
  // İzometrik akışı istenen saniyede dondur (?export=1&freeze=11[&overview=1])
  const isoFrame = document.getElementById('isoEmbedIframe');
  if (isoFrame && exportParams.has('freeze')) {
    const ov = exportParams.has('overview') ? '&overview=1' : '';
    isoFrame.src = `izometrik_akis.html?embed=1&freeze=${exportParams.get('freeze')}${ov}`;
  }
}

const initialHash = window.location.hash.replace('#', '');
if (initialHash) {
  const hashIdx = slides.findIndex(s => s.id === initialHash);
  if (hashIdx >= 0) {
    slides[0].classList.remove('active');
    slides[hashIdx].classList.add('active');
    cur = hashIdx;
  }
}

updateUI();
onEnter(cur);

if (window.lucide && typeof window.lucide.createIcons === 'function') {
  window.lucide.createIcons();
}

// Mobil dikey ekranda açıldığında yatay çevirme ipucu göster
if (!exportParams.has('export')) {
  const hint = document.createElement('div');
  hint.className = 'rotate-hint';
  hint.innerHTML = '<span>📱 En iyi deneyim için telefonunuzu <strong>yatay çevirin</strong> veya masaüstünde açın.</span><button type="button">Tamam</button>';
  hint.querySelector('button').onclick = () => document.body.classList.add('rotate-dismissed');
  document.body.appendChild(hint);
}
