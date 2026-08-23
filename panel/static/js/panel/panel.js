/* ═══ کدهای مشترک پنل ═══ */
(function () {
    "use strict";

    // ── Sidebar toggle ──
    var sidebar = document.getElementById('panelSidebar');
    var overlay = document.getElementById('sidebarOverlay');
    var menuToggle = document.getElementById('menuToggle');
    var sidebarClose = document.getElementById('sidebarClose');

    function openSidebar() {
        if (!sidebar) return;
        sidebar.classList.add('active');
        if (overlay) overlay.classList.add('active');
        document.body.style.overflow = 'hidden';
    }
    function closeSidebar() {
        if (!sidebar) return;
        sidebar.classList.remove('active');
        if (overlay) overlay.classList.remove('active');
        document.body.style.overflow = '';
    }

    if (menuToggle) menuToggle.addEventListener('click', openSidebar);
    if (sidebarClose) sidebarClose.addEventListener('click', closeSidebar);
    if (overlay) overlay.addEventListener('click', closeSidebar);

    // ── User menu dropdown ──
    var userMenu = document.getElementById('userMenu');
    if (userMenu) {
        var userBtn = userMenu.querySelector('.user-btn');
        if (userBtn) {
            userBtn.addEventListener('click', function (e) {
                e.stopPropagation();
                userMenu.classList.toggle('open');
            });
        }
        document.addEventListener('click', function () {
            userMenu.classList.remove('open');
        });
    }

    // ── 📅 تاریخ جلالی + ساعت زنده ──
    function updateClock() {
        var now = new Date();
        var dateEl = document.getElementById('jalaliDate');
        var timeEl = document.getElementById('liveTime');
        if (dateEl) {
            dateEl.textContent = new Intl.DateTimeFormat('fa-IR', {
                weekday: 'long', year: 'numeric', month: 'long', day: 'numeric'
            }).format(now);
        }
        if (timeEl) {
            timeEl.textContent = new Intl.DateTimeFormat('fa-IR', {
                hour: '2-digit', minute: '2-digit'
            }).format(now);
        }
    }
    updateClock();
    setInterval(updateClock, 1000);

    // ── Modals ──
    document.querySelectorAll('[data-close]').forEach(function (btn) {
        btn.addEventListener('click', function () {
            var m = btn.closest('.modal');
            if (m) m.classList.remove('active');
        });
    });
    document.querySelectorAll('.modal-backdrop').forEach(function (backdrop) {
        backdrop.addEventListener('click', function () {
            var m = backdrop.closest('.modal');
            if (m) m.classList.remove('active');
        });
    });
    document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape') {
            document.querySelectorAll('.modal.active').forEach(function (m) {
                m.classList.remove('active');
            });
        }
    });

    // ── Toast ─
    window.showToast = function (message, type) {
        type = type || 'info';
        var container = document.getElementById('toastContainer');
        if (!container) return;
        var toast = document.createElement('div');
        toast.className = 'toast ' + type;
        toast.textContent = message;
        container.appendChild(toast);
        setTimeout(function () {
            toast.style.opacity = '0';
            setTimeout(function () { toast.remove(); }, 400);
        }, 4000);
    };

    console.log('✅ Panel initialized');
})();