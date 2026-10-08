(function () {
  'use strict';

  // ---- Config ----
  var EMAIL = 'contacto@marfil.com.mx';
  var WHATSAPP = '524777150000'; // supuesto: mismo número que el teléfono; confirmar con Marfil

  var I = window.MarfilI18n;
  var t = I.t;
  var root = document.documentElement;
  root.classList.add('js');

  // ---- Mobile menu ----
  var toggle = document.querySelector('.nav__toggle');
  var menu = document.getElementById('menu');
  function setMenu(open) {
    toggle.setAttribute('aria-expanded', String(open));
    toggle.setAttribute('aria-label', t(open ? 'menu.close' : 'menu.open'));
    menu.classList.toggle('is-open', open);
    paintNav();
  }
  toggle.addEventListener('click', function () {
    setMenu(toggle.getAttribute('aria-expanded') !== 'true');
  });
  menu.addEventListener('click', function (e) { if (e.target.closest('a')) setMenu(false); });
  document.addEventListener('keydown', function (e) { if (e.key === 'Escape') setMenu(false); });

  // ---- Nav: transparent over the hero video, solid after it ----
  var nav = document.querySelector('.nav');
  var heroEl = document.querySelector('.hero');
  var ticking = false;
  function paintNav() {
    // Inner pages have no video hero: the bar stays solid
    var past = !heroEl || window.scrollY > heroEl.offsetHeight - nav.offsetHeight - 40;
    nav.classList.toggle('is-solid', past || menu.classList.contains('is-open'));
  }
  window.addEventListener('scroll', function () {
    if (!ticking) { ticking = true; requestAnimationFrame(function () { paintNav(); ticking = false; }); }
  }, { passive: true });
  window.addEventListener('resize', paintNav);
  paintNav();

  // ---- Hero video (YouTube, muted loop). Poster stays when motion is reduced or data is saved ----
  var videoBox = document.getElementById('hero-video');
  var videoToggle = document.getElementById('video-toggle');
  var reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var saveData = navigator.connection && navigator.connection.saveData;
  var player = null;
  if (videoBox && !reduce && !saveData) {
    var vid = videoBox.getAttribute('data-youtube');
    window.onYouTubeIframeAPIReady = function () {
      player = new YT.Player(videoBox.appendChild(document.createElement('div')), {
        videoId: vid,
        host: 'https://www.youtube-nocookie.com',
        playerVars: {
          autoplay: 1, mute: 1, controls: 0, loop: 1, playlist: vid, playsinline: 1,
          modestbranding: 1, rel: 0, disablekb: 1, fs: 0, iv_load_policy: 3, origin: location.origin
        },
        events: {
          onReady: function (e) {
            e.target.mute(); e.target.playVideo();
            var f = e.target.getIframe();
            f.setAttribute('title', 'Video de la tenería Marfil');
            f.setAttribute('tabindex', '-1');
          },
          onStateChange: function (e) {
            if (e.data === YT.PlayerState.PLAYING) { videoBox.classList.add('is-playing'); videoToggle.hidden = false; }
            if (e.data === YT.PlayerState.ENDED) { e.target.seekTo(0); e.target.playVideo(); }
          }
        }
      });
    };
    var tag = document.createElement('script');
    tag.src = 'https://www.youtube.com/iframe_api';
    tag.async = true;
    document.head.appendChild(tag);

    videoToggle.addEventListener('click', function () {
      if (!player) return;
      var paused = videoToggle.getAttribute('aria-pressed') === 'true';
      if (paused) { player.playVideo(); } else { player.pauseVideo(); }
      videoToggle.setAttribute('aria-pressed', String(!paused));
      videoToggle.querySelector('.hero__pause-label').textContent = t(paused ? 'video.pause' : 'video.play');
    });
  }

  // ---- Reveal on scroll ----
  // Elements entering in the same frame cascade 60ms apart (capped), then the
  // reveal class is dropped so each element gets its own transitions back.
  var items = document.querySelectorAll('.reveal');
  function settle(el, delay) {
    setTimeout(function () { el.classList.remove('reveal', 'is-in'); el.style.removeProperty('--stagger'); }, 950 + delay);
  }
  if ('IntersectionObserver' in window) {
    var io = new IntersectionObserver(function (entries) {
      var batch = entries.filter(function (en) { return en.isIntersecting; })
        .sort(function (a, b) { return a.boundingClientRect.top - b.boundingClientRect.top || a.boundingClientRect.left - b.boundingClientRect.left; });
      batch.forEach(function (en, i) {
        var delay = Math.min(i, 5) * 60;
        en.target.style.setProperty('--stagger', delay + 'ms');
        en.target.classList.add('is-in');
        io.unobserve(en.target);
        settle(en.target, delay);
      });
    }, { rootMargin: '0px 0px -10% 0px', threshold: 0.12 });
    items.forEach(function (el) { io.observe(el); });
  } else {
    items.forEach(function (el) { el.classList.remove('reveal'); });
  }

  // ---- Sticky CTA (mobile): visible after hero, hidden over the form ----
  var sticky = document.getElementById('sticky');
  var hero = document.querySelector('.hero');
  var contact = document.getElementById('contacto');
  var pastHero = false, onForm = false;
  function paintSticky() { if (sticky) sticky.classList.toggle('is-on', pastHero && !onForm); }
  if (sticky && 'IntersectionObserver' in window) {
    var top = hero || document.querySelector('.page-hero');
    if (top) new IntersectionObserver(function (e) { pastHero = !e[0].isIntersecting; paintSticky(); }).observe(top);
    if (contact) new IntersectionObserver(function (e) { onForm = e[0].isIntersecting; paintSticky(); }, { threshold: 0.15 }).observe(contact);
  }

  // ---- Links that preselect the industry and, on catalogue pages, name the piece in the message ----
  var industria = document.getElementById('industria');
  var mensaje = document.getElementById('mensaje');
  document.querySelectorAll('[data-industria]').forEach(function (a) {
    a.addEventListener('click', function () {
      if (industria) industria.value = a.getAttribute('data-industria');
      var piece = a.getAttribute('data-pieza');
      if (piece && mensaje) {
        var line = t('msg.piece') + ': ' + piece;
        if (mensaje.value.indexOf(line) === -1) mensaje.value = (line + '\n' + mensaje.value).trim() + '\n';
      }
    });
  });

  // ---- Lead form ----
  var form = document.getElementById('lead');
  if (!form) { finish(); return; }
  var status = document.getElementById('status');
  var required = ['nombre', 'empresa', 'email', 'telefono', 'industria'];
  var via = 'mail';
  form.querySelectorAll('button[type=submit]').forEach(function (b) {
    b.addEventListener('click', function () { via = b.getAttribute('data-via'); });
  });

  function validate() {
    var firstBad = null;
    required.forEach(function (name) {
      var el = form.elements[name];
      var val = el.value.trim();
      var ok = val !== '' && (name !== 'email' || /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(val)) &&
               (name !== 'telefono' || val.replace(/\D/g, '').length >= 8);
      var field = el.closest('.field');
      field.classList.toggle('is-invalid', !ok);
      el.setAttribute('aria-invalid', String(!ok));
      var msg = form.querySelector('.err[data-for=' + name + ']');
      msg.textContent = ok ? '' : t('err.' + name);
      if (!ok && !firstBad) firstBad = el;
    });
    return firstBad;
  }

  form.addEventListener('input', function (e) {
    var f = e.target.closest('.field');
    if (f && f.classList.contains('is-invalid')) { validate(); }
  });

  form.addEventListener('submit', function (e) {
    e.preventDefault();
    status.classList.remove('is-ok');
    var bad = validate();
    if (bad) {
      status.textContent = t('err.check');
      bad.focus();
      return;
    }
    var d = function (n) { return form.elements[n].value.trim(); };
    var industryLabel = industria.options[industria.selectedIndex].text;
    var lines = [
      t('msg.hello'),
      '',
      t('msg.name') + ': ' + d('nombre'),
      t('msg.company') + ': ' + d('empresa'),
      t('msg.email') + ': ' + d('email'),
      t('msg.phone') + ': ' + d('telefono'),
      t('msg.country') + ': ' + (d('pais') || t('msg.defcountry')),
      t('msg.industry') + ': ' + industryLabel,
      '',
      d('mensaje') || t('msg.none')
    ].join('\n');

    var url = via === 'wa'
      ? 'https://wa.me/' + WHATSAPP + '?text=' + encodeURIComponent(lines)
      : 'mailto:' + EMAIL + '?subject=' + encodeURIComponent(t('msg.subject') + d('empresa')) + '&body=' + encodeURIComponent(lines);

    status.textContent = t(via === 'wa' ? 'ok.wa' : 'ok.mail');
    status.classList.add('is-ok');
    if (via === 'wa') { window.open(url, '_blank', 'noopener'); } else { window.location.href = url; }
  });

  // ---- Language change: refresh JS-owned strings and visible errors ----
  I.onChange(function () {
    toggle.setAttribute('aria-label', t(toggle.getAttribute('aria-expanded') === 'true' ? 'menu.close' : 'menu.open'));
    var vl = document.querySelector('.hero__pause-label');
    if (vl && videoToggle) vl.textContent = t(videoToggle.getAttribute('aria-pressed') === 'true' ? 'video.play' : 'video.pause');
    if (form.querySelector('.is-invalid')) validate();
    status.classList.remove('is-ok');
  });
  finish();

  function finish() {
    toggle.setAttribute('aria-label', t('menu.open'));
    var y = document.getElementById('year');
    if (y) y.textContent = new Date().getFullYear();
  }
})();
