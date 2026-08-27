(function () {
    /* ═══ ۱) ظاهرشدن تدریجی کارت‌ها و بخش‌ها ═══ */
    var revealEls = document.querySelectorAll('.pf-card, .pfd-spec, .pfd-image, .pfd-cta, .pfd-header, .pfd-related');
    if ('IntersectionObserver' in window && revealEls.length) {
        revealEls.forEach(function (el, i) {
            el.style.opacity = '0';
            el.style.transform = 'translateY(30px)';
            el.style.transition = 'opacity .7s cubic-bezier(.22,1,.36,1) ' + ((i % 9) * 0.07) + 's, transform .7s cubic-bezier(.22,1,.36,1) ' + ((i % 9) * 0.07) + 's';
        });
        var io = new IntersectionObserver(function (entries) {
            entries.forEach(function (en) {
                if (en.isIntersecting) {
                    var el = en.target;
                    el.style.opacity = '1';
                    el.style.transform = 'translateY(0)';
                    /* بعد از انیمیشن، استایل inline پاک می‌شه تا hover کار کنه */
                    el.addEventListener('transitionend', function clear() {
                        el.style.opacity = '';
                        el.style.transform = '';
                        el.style.transition = '';
                        el.removeEventListener('transitionend', clear);
                    });
                    io.unobserve(el);
                }
            });
        }, { threshold: 0.08, rootMargin: '0px 0px -30px 0px' });
        revealEls.forEach(function (el) { io.observe(el); });
    }

    /* ═══ ۲) لایت‌باکس تصویر (صفحه جزئیات) ═══ */
    var img = document.querySelector('.pfd-image img');
    if (img) {
        img.style.cursor = 'zoom-in';
        img.title = 'برای بزرگ‌نمایی کلیک کنید';
        var lb = document.createElement('div');
        lb.style.cssText = 'position:fixed;inset:0;background:rgba(0,0,0,.92);backdrop-filter:blur(10px);z-index:9999;display:none;align-items:center;justify-content:center;cursor:zoom-out;padding:30px';
        var big = document.createElement('img');
        big.style.cssText = 'max-width:95%;max-height:95%;border-radius:14px;box-shadow:0 40px 100px rgba(0,0,0,.8);animation:lbIn .3s cubic-bezier(.22,1,.36,1)';
        lb.appendChild(big);
        document.body.appendChild(lb);

        var st = document.createElement('style');
        st.textContent = '@keyframes lbIn{from{opacity:0;transform:scale(.92)}to{opacity:1;transform:scale(1)}}';
        document.head.appendChild(st);

        img.addEventListener('click', function () {
            big.src = img.src;
            lb.style.display = 'flex';
            document.body.style.overflow = 'hidden';
        });
        lb.addEventListener('click', function () {
            lb.style.display = 'none';
            document.body.style.overflow = '';
        });
        document.addEventListener('keydown', function (e) {
            if (e.key === 'Escape' && lb.style.display === 'flex') lb.click();
        });
    }

    /* ═══ ) شمارنده بازدید با انیمیشن (صفحه جزئیات) ═══ */
    var viewEl = document.querySelector('.pfd-spec strong:last-of-type');
    var specs = document.querySelectorAll('.pfd-spec');
    specs.forEach(function (sp) {
        var small = sp.querySelector('small');
        var strong = sp.querySelector('strong');
        if (small && strong && small.textContent.indexOf('بازدید') > -1 && !isNaN(parseInt(strong.textContent))) {
            var target = parseInt(strong.textContent), cur = 0;
            var step = Math.max(1, Math.round(target / 40));
            var t = setInterval(function () {
                cur += step;
                if (cur >= target) { cur = target; clearInterval(t); }
                strong.textContent = cur;
            }, 30);
        }
    });
})();

/* ═══ FAB ══ */
var fabToggle = document.getElementById('fabToggle');
var adminFab = document.getElementById('adminFab');
if (fabToggle && adminFab) {
    fabToggle.addEventListener('click', function (e) {
        e.stopPropagation();
        adminFab.classList.toggle('open');
    });
    document.addEventListener('click', function (e) {
        if (!adminFab.contains(e.target)) adminFab.classList.remove('open');
    });
}

