/* ═══ کدهای مشترک پنل ═══ */
(function () {
    "use strict";

    /* ── Sidebar: موبایل = اورلی، دسکتاپ = جمع‌شدنی ── */
    var sidebar = document.getElementById('panelSidebar');
    var overlay = document.getElementById('sidebarOverlay');
    var menuToggle = document.getElementById('menuToggle');
    var sidebarClose = document.getElementById('sidebarClose');

    function isMobile() { return window.innerWidth <= 1024; }
    function openSidebar() { if (!sidebar) return; sidebar.classList.add('active'); if (overlay) overlay.classList.add('active'); document.body.style.overflow = 'hidden'; }
    function closeSidebar() { if (!sidebar) return; sidebar.classList.remove('active'); if (overlay) overlay.classList.remove('active'); document.body.style.overflow = ''; }

    if (menuToggle) menuToggle.addEventListener('click', function () {
        if (isMobile()) { openSidebar(); }
        else {
            document.body.classList.toggle('sidebar-closed');
            try { localStorage.setItem('panel_sidebar_closed', document.body.classList.contains('sidebar-closed') ? '1' : '0'); } catch (e) { }
        }
    });
    if (sidebarClose) sidebarClose.addEventListener('click', closeSidebar);
    if (overlay) overlay.addEventListener('click', closeSidebar);
    window.addEventListener('resize', function () { if (!isMobile()) closeSidebar(); });

    /* یادآوری حالت سایدبار در دسکتاپ */
    try {
        if (!isMobile() && localStorage.getItem('panel_sidebar_closed') === '1') document.body.classList.add('sidebar-closed');
    } catch (e) { }

    /* ── User menu ── */
    var userMenu = document.getElementById('userMenu');
    if (userMenu) {
        var userBtn = userMenu.querySelector('.user-btn');
        if (userBtn) userBtn.addEventListener('click', function (e) { e.stopPropagation(); userMenu.classList.toggle('open'); });
        document.addEventListener('click', function () { userMenu.classList.remove('open'); });
    }

    /* ── 📅 تاریخ جلالی + ساعت ── */
    function updateClock() {
        var now = new Date();
        var d = document.getElementById('jalaliDate');
        var t = document.getElementById('liveTime');
        if (d) d.textContent = new Intl.DateTimeFormat('fa-IR', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' }).format(now);
        if (t) t.textContent = new Intl.DateTimeFormat('fa-IR', { hour: '2-digit', minute: '2-digit' }).format(now);
    }
    updateClock();
    setInterval(updateClock, 1000);

    /* ── Modals ── */
    document.querySelectorAll('[data-close]').forEach(function (b) {
        b.addEventListener('click', function () { var m = b.closest('.modal'); if (m) m.classList.remove('active'); });
    });
    document.querySelectorAll('.modal-backdrop').forEach(function (bd) {
        bd.addEventListener('click', function () { var m = bd.closest('.modal'); if (m) m.classList.remove('active'); });
    });
    document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape') document.querySelectorAll('.modal.active').forEach(function (m) { m.classList.remove('active'); });
    });

    /* ── Toast ── */
    window.showToast = function (msg, type) {
        type = type || 'info';
        var c = document.getElementById('toastContainer');
        if (!c) return;
        var t = document.createElement('div');
        t.className = 'toast ' + type;
        t.textContent = msg;
        c.appendChild(t);
        setTimeout(function () { t.style.opacity = '0'; setTimeout(function () { t.remove(); }, 400); }, 4000);
    };

    console.log('✅ Panel initialized');
})();
/* ═══ زیرمنوی کشویی سایدبار ═══ */
document.querySelectorAll('.nav-group-toggle').forEach(function (btn) {
    btn.addEventListener('click', function () {
        btn.closest('.nav-group').classList.toggle('open');
    });
});

/* باز شدن خودکار اگه زیرمنوی فعال باز باشه */
document.querySelectorAll('.nav-sub-item.active').forEach(function (item) {
    var g = item.closest('.nav-group');
    if (g) g.classList.add('open');
});