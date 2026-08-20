document.addEventListener('DOMContentLoaded', function () {
  /* منوی موبایل */
  const menuBtn = document.querySelector('.mobile-menu-btn');
  const navLinks = document.querySelector('.nav-links');
  if (menuBtn && navLinks) {
    menuBtn.addEventListener('click', function () {
      navLinks.classList.toggle('active');
      menuBtn.classList.toggle('open');
    });
    navLinks.querySelectorAll('a').forEach(function (a) {
      a.addEventListener('click', function () {
        navLinks.classList.remove('active');
        menuBtn.classList.remove('open');
      });
    });
  }

  /* حالت اسکرول نوبار */
  const onScroll = function () {
    document.body.classList.toggle('scrolled', window.scrollY > 40);
  };
  window.addEventListener('scroll', onScroll, { passive: true });
  onScroll();

  /* خبرنامه (موقت تا ساخت پنل) */
  const form = document.getElementById('newsletter-form');
  if (form) {
    form.addEventListener('submit', function (e) {
      e.preventDefault();
      const btn = form.querySelector('button');
      btn.textContent = 'عضویت شما ثبت شد ✔';
      btn.disabled = true;
      form.querySelector('input').value = '';
    });
  }
});