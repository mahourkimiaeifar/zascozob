/* ═══ کدهای مشترک پنل ═══ */
(function () {
    "use strict";

    // ── Sidebar toggle ──
    var sidebar = document.getElementById('panelSidebar');
    var overlay = document.getElementById('sidebarOverlay');
    var menuToggle = document.getElementById('menuToggle');
    var sidebarClose = document.getElementById('sidebarClose');

    function openSidebar() {
        sidebar.classList.add('active');
        overlay.classList.add('active');
        document.body.style.overflow = 'hidden';
    }
    function closeSidebar() {
        sidebar.classList.remove('active');
        overlay.classList.remove('active');
        document.body.style.overflow = '';
    }

    if (menuToggle) menuToggle.addEventListener('click', openSidebar);
    if (sidebarClose) sidebarClose.addEventListener('click', closeSidebar);
    if (overlay) overlay.addEventListener('click', closeSidebar);

    // ── User menu dropdown ──
    var userMenu = document.getElementById('userMenu');
    if (userMenu) {
        var userBtn = userMenu.querySelector('.user-btn');
        userBtn.addEventListener('click', function (e) {
            e.stopPropagation();
            userMenu.classList.toggle('open');
        });
        document.addEventListener('click', function () {
            userMenu.classList.remove('open');
        });
    }

    // ── Modals ──
    document.querySelectorAll('[data-close]').forEach(function (btn) {
        btn.addEventListener('click', function () {
            btn.closest('.modal').classList.remove('active');
        });
    });

    document.querySelectorAll('.modal-backdrop').forEach(function (backdrop) {
        backdrop.addEventListener('click', function () {
            backdrop.closest('.modal').classList.remove('active');
        });
    });

    document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape') {
            document.querySelectorAll('.modal.active').forEach(function (m) {
                m.classList.remove('active');
            });
        }
    });

    // ── Toast notifications ──
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
            toast.style.transform = 'translateX(-20px)';
            setTimeout(function () { toast.remove(); }, 400);
        }, 4000);
    };

    console.log('✅ Panel initialized');
})();