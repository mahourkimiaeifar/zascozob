/* ═══ زاسکو ذوب — لودینگ، ذرات، بازگشت‌به‌بالا، شناوری ورود، پارالاکس ═══ */
(function () {
  "use strict";

  /* ── ۰) لودینگ (ضد گیر کردن - با timeout اضطراری) ── */
  let loaderHidden = false;
  function hideLoader() {
    if (loaderHidden) return;
    loaderHidden = true;
    document.body.classList.add("loaded");
  }
  
  // اولویت ۱: DOM آماده شد
  if (document.readyState === "complete" || document.readyState === "interactive") {
    setTimeout(hideLoader, 400);
  } else {
    document.addEventListener("DOMContentLoaded", function () {
      setTimeout(hideLoader, 400);
    });
  }
  
  // اولویت ۲: همه چیز لود شد
  window.addEventListener("load", hideLoader);
  
  // 🛡️ اضطراری: حداکثر ۳ ثانیه بعد، هر طور شده لودینگ رو ببند
  // این از گیر کردن به خاطر تصاویر 404 یا CDN کند جلوگیری می‌کنه
  setTimeout(hideLoader, 3000);

  /* ── ۱) ذرات بالارونده ── */
  const canvas = document.getElementById("ambient-canvas");
  if (canvas) {
    const ctx = canvas.getContext("2d");
    let W, H;
    const COUNT = window.innerWidth < 768 ? 32 : 70;

    function resize() {
      W = canvas.width = window.innerWidth;
      H = canvas.height = window.innerHeight;
    }
    resize();
    window.addEventListener("resize", resize);

    function make(fromBottom) {
      return {
        x: Math.random() * W,
        y: fromBottom ? H + 10 : Math.random() * H,
        r: Math.random() * 1.8 + 0.6,
        s: Math.random() * 0.35 + 0.12,
        dx: (Math.random() - 0.5) * 0.15,
        o: Math.random() * 0.35 + 0.1,
        warm: Math.random() > 0.35,
        ph: Math.random() * Math.PI * 2,
      };
    }
    const parts = Array.from({ length: COUNT }, function () {
      return make(false);
    });

    let t = 0;
    (function tick() {
      requestAnimationFrame(tick);
      t += 0.016;
      ctx.clearRect(0, 0, W, H);
      for (let i = 0; i < parts.length; i++) {
        const p = parts[i];
        p.y -= p.s;
        p.x += p.dx + Math.sin(t + p.ph) * 0.08;
        if (p.y < -10 || p.x < -10 || p.x > W + 10) {
          Object.assign(p, make(true));
        }
        const flicker = p.o * (0.75 + Math.sin(t * 2 + p.ph) * 0.25);
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
        ctx.fillStyle = p.warm
          ? "rgba(255,140,60," + flicker.toFixed(3) + ")"
          : "rgba(160,170,190," + (flicker * 0.7).toFixed(3) + ")";
        ctx.fill();
      }
    })();
  }

  /* ── ۲) دکمه بازگشت به بالا ── */
  const btn = document.getElementById("back-to-top");
  if (btn) {
    window.addEventListener(
      "scroll",
      function () {
        btn.classList.toggle("show", window.scrollY > 400);
      },
      { passive: true },
    );
    btn.addEventListener("click", function () {
      window.scrollTo({ top: 0, behavior: "smooth" });
    });
  }

  /* ── ۳) ورود شناوری پلکانی (خانه + درباره ما) ── */
  const REVEAL_SEL =
    ".y-intro-title, .y-intro p, .y-intro .rule, .y-head, .editorial h2, .editorial p, .editorial-list li, .editorial-media, .t-step, .chip, .work-card, .cta-glass, .contact-ribbon, .about-title, .breadcrumb, .section-h2, .section-intro, .intro-main p, .side-card, .about-story p, .mission-card, .infra-card, .benefit-item, .process-step, .vision-box";

  if ("IntersectionObserver" in window) {
    const io = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (en) {
          if (en.isIntersecting) {
            en.target.style.opacity = "";
            en.target.classList.add("revealed");
            io.unobserve(en.target);
          }
        });
      },
      { threshold: 0.12, rootMargin: "0px 0px -40px 0px" },
    );

    document
      .querySelectorAll(
        ".y-section, .y-intro, .cta-final, .about-section, .about-hero",
      )
      .forEach(function (scope) {
        scope.querySelectorAll(REVEAL_SEL).forEach(function (el, i) {
          el.style.setProperty("--d", (Math.min(i, 8) * 0.09).toFixed(2) + "s");
          el.style.opacity = "0";
          io.observe(el);
        });
      });
  }

  /* ── ۴) پارالاکس ملایم ── */
  const paras = Array.from(
    document.querySelectorAll(".editorial-media, .kb-overlay"),
  );
  if (paras.length) {
    let ticking = false;
    function par() {
      const vh = window.innerHeight;
      paras.forEach(function (el) {
        const r = el.getBoundingClientRect();
        if (r.bottom < -100 || r.top > vh + 100) {
          return;
        }
        const c = r.top + r.height / 2 - vh / 2;
        const speed = el.classList.contains("kb-overlay") ? 0.12 : 0.06;
        el.style.translate = "0 " + (c * -speed).toFixed(1) + "px";
      });
      ticking = false;
    }
    window.addEventListener(
      "scroll",
      function () {
        if (!ticking) {
          ticking = true;
          requestAnimationFrame(par);
        }
      },
      { passive: true },
    );
    par();
  }
})();