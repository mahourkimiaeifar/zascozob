/* ═══ انیمیشن‌های صفحه درباره ما ═══ */
(function () {
  "use strict";

  /* ── ۱) شمارنده‌های متحرک آمار ── */
  function anim(el) {
    var target = parseInt(el.dataset.target, 10);
    if (!target) return;
    var dur = 1800, start = performance.now();
    function step(now) {
      var p = Math.min((now - start) / dur, 1);
      var e = 1 - Math.pow(1 - p, 3);
      el.textContent = Math.floor(e * target).toLocaleString("fa-IR");
      if (p < 1) requestAnimationFrame(step);
      else el.textContent = target.toLocaleString("fa-IR");
    }
    requestAnimationFrame(step);
  }
  var counters = document.querySelectorAll("[data-target]");
  if (counters.length && "IntersectionObserver" in window) {
    var cio = new IntersectionObserver(function (es) {
      es.forEach(function (en) {
        if (en.isIntersecting) { anim(en.target); cio.unobserve(en.target); }
      });
    }, { threshold: 0.5 });
    counters.forEach(function (c) { cio.observe(c); });
  }

  /* ── ۲) ورود پلکانی هنگام اسکرول ── */
  var REVEAL = ".cl-lead, .cl-body p, .cl-stat, .cl-section h2, .cl-intro, .cl-card, .cl-check, .cl-steps li, .cl-quote, .cl-image-band";
  if ("IntersectionObserver" in window) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (en.isIntersecting) {
          en.target.style.opacity = "";
          en.target.classList.add("revealed");
          io.unobserve(en.target);
        }
      });
    }, { threshold: 0.15, rootMargin: "0px 0px -30px 0px" });

    document.querySelectorAll(".cl-body .container, .cl-section, .cl-stats").forEach(function (scope) {
      scope.querySelectorAll(REVEAL).forEach(function (el, i) {
        el.style.setProperty("--d", (Math.min(i, 6) * 0.08).toFixed(2) + "s");
        el.style.opacity = "0";
        io.observe(el);
      });
    });
  }

  /* ── ۳) پارالاکس نرم روی نوار تصویر ── */
  var band = document.querySelector(".cl-image-band img");
  if (band) {
    var ticking = false;
    function par() {
      var r = band.parentElement.getBoundingClientRect();
      var vh = window.innerHeight;
      if (r.bottom > 0 && r.top < vh) {
        var c = (r.top + r.height / 2 - vh / 2) / vh;
        band.style.transform = "scale(1.1) translateY(" + (c * -24).toFixed(1) + "px)";
      }
      ticking = false;
    }
    window.addEventListener("scroll", function () {
      if (!ticking) { ticking = true; requestAnimationFrame(par); }
    }, { passive: true });
    par();
  }
})();