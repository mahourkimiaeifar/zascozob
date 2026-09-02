/* ═══════════════════════════════════════════════════════════════
   پنل مدیریت زاسکو ذوب — نسخه ۲.۰ | JavaScript یکپارچه
═══════════════════════════════════════════════════════════════ */

(function () {
    'use strict';

    /* ═══ ۱) Theme Switcher ═══ */
    const ThemeManager = {
        init() {
            this.current = localStorage.getItem('panel_theme') || 'dark';
            this.apply(this.current);

            document.addEventListener('click', (e) => {
                const btn = e.target.closest('.theme-toggle');
                if (btn) this.toggle(btn);
            });
        },

        apply(theme) {
            document.documentElement.setAttribute('data-theme', theme);
            this.current = theme;
            localStorage.setItem('panel_theme', theme);
        },

        toggle(btn) {
            const newTheme = this.current === 'dark' ? 'light' : 'dark';
            btn.classList.add('rotating');
            setTimeout(() => btn.classList.remove('rotating'), 500);
            this.apply(newTheme);

            // به‌روزرسانی نمودارها اگه وجود داشتن
            if (window.PanelCharts) window.PanelCharts.updateColors();

            this.showToast(
                newTheme === 'light' ? 'حالت روشن فعال شد' : 'حالت تیره فعال شد',
                'success',
                newTheme === 'light' ? 'fa-sun' : 'fa-moon'
            );
        },

        showToast(msg, type, icon) {
            // به Toast System وصل می‌شود
            if (window.showToast) window.showToast(msg, type, icon);
        }
    };

    /* ═══ ۲) Sidebar Manager ═══ */
    const SidebarManager = {
        sidebar: null,
        overlay: null,
        menuToggle: null,
        sidebarClose: null,

        init() {
            this.sidebar = document.getElementById('panelSidebar');
            this.overlay = document.getElementById('sidebarOverlay');
            this.menuToggle = document.getElementById('menuToggle');
            this.sidebarClose = document.getElementById('sidebarClose');

            if (!this.sidebar) return;

            this.menuToggle?.addEventListener('click', () => {
                if (this.isMobile()) this.open();
                else this.toggleDesktop();
            });

            this.sidebarClose?.addEventListener('click', () => this.close());
            this.overlay?.addEventListener('click', () => this.close());

            window.addEventListener('resize', () => {
                if (!this.isMobile()) this.close();
            });

            // یادآوری حالت بسته سایدبار
            try {
                if (!this.isMobile() && localStorage.getItem('panel_sidebar_closed') === '1') {
                    document.body.classList.add('sidebar-closed');
                }
            } catch (e) { }
        },

        isMobile() { return window.innerWidth <= 1024; },

        open() {
            this.sidebar.classList.add('active');
            this.overlay?.classList.add('active');
            document.body.style.overflow = 'hidden';
        },

        close() {
            this.sidebar.classList.remove('active');
            this.overlay?.classList.remove('active');
            document.body.style.overflow = '';
        },

        toggleDesktop() {
            document.body.classList.toggle('sidebar-closed');
            try {
                localStorage.setItem(
                    'panel_sidebar_closed',
                    document.body.classList.contains('sidebar-closed') ? '1' : '0'
                );
            } catch (e) { }
        }
    };

    /* ═══ ۳) Submenu Toggles ═══ */
    const MenuToggle = {
        init() {
            document.querySelectorAll('.nav-group-toggle').forEach(btn => {
                btn.addEventListener('click', () => {
                    btn.closest('.nav-group').classList.toggle('open');
                });
            });

            // باز کردن خودکار اگه زیرمنوی فعال باز باشه
            document.querySelectorAll('.nav-sub-item.active').forEach(item => {
                const group = item.closest('.nav-group');
                if (group) group.classList.add('open');
            });
        }
    };

    /* ═══ ۴) Clock (Date & Time) ═══ */
    const Clock = {
        init() {
            this.update();
            setInterval(() => this.update(), 1000);
        },

        update() {
            const now = new Date();
            const dateEl = document.getElementById('jalaliDate');
            const timeEl = document.getElementById('liveTime');

            if (dateEl) {
                dateEl.textContent = new Intl.DateTimeFormat('fa-IR', {
                    weekday: 'long', year: 'numeric', month: 'long', day: 'numeric'
                }).format(now);
            }

            if (timeEl) {
                timeEl.textContent = new Intl.DateTimeFormat('fa-IR', {
                    hour: '2-digit', minute: '2-digit', second: '2-digit'
                }).format(now);
            }
        }
    };

    /* ═══ ۵) User Menu ═══ */
    const UserMenu = {
        init() {
            const userMenu = document.getElementById('userMenu');
            if (!userMenu) return;

            const userBtn = userMenu.querySelector('.user-btn');
            if (userBtn) {
                userBtn.addEventListener('click', (e) => {
                    e.stopPropagation();
                    userMenu.classList.toggle('open');
                });
            }

            document.addEventListener('click', () => {
                userMenu.classList.remove('open');
            });
        }
    };

    /* ═══ ۶) Modal Manager ═══ */
    const ModalManager = {
        init() {
            document.querySelectorAll('[data-close]').forEach(btn => {
                btn.addEventListener('click', () => {
                    const modal = btn.closest('.modal');
                    if (modal) modal.classList.remove('active');
                });
            });

            document.querySelectorAll('.modal-backdrop').forEach(bd => {
                bd.addEventListener('click', () => {
                    const modal = bd.closest('.modal');
                    if (modal) modal.classList.remove('active');
                });
            });

            document.addEventListener('keydown', (e) => {
                if (e.key === 'Escape') {
                    document.querySelectorAll('.modal.active').forEach(m => {
                        m.classList.remove('active');
                    });
                }
            });
        }
    };

    /* ═══ ۷) Toast System ═══ */
    window.showToast = function (msg, type, icon) {
        type = type || 'info';
        const icons = {
            info: 'fa-circle-info',
            success: 'fa-circle-check',
            error: 'fa-circle-xmark',
            warning: 'fa-triangle-exclamation'
        };
        const selectedIcon = icon || icons[type] || icons.info;

        const container = document.getElementById('toastContainer');
        if (!container) return;

        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.innerHTML = `<i class="fa-solid ${selectedIcon}"></i><span>${msg}</span>`;
        container.appendChild(toast);

        setTimeout(() => {
            toast.style.opacity = '0';
            setTimeout(() => toast.remove(), 400);
        }, 4000);
    };

    /* ═══ ۸) Init All ═══ */
    document.addEventListener('DOMContentLoaded', () => {
        ThemeManager.init();
        SidebarManager.init();
        MenuToggle.init();
        Clock.init();
        UserMenu.init();
        ModalManager.init();

        console.log('✅ Panel 2.0 initialized');
    });

})();

/* ── Theme Toggle (ذخیره برای هر اکانت) ── */
(function () {
    var btn = document.getElementById('themeToggle');
    if (!btn) return;
    btn.addEventListener('click', function () {
        var cur = document.documentElement.getAttribute('data-theme') === 'light' ? 'dark' : 'light';
        document.documentElement.setAttribute('data-theme', cur);
        try { localStorage.setItem('panel_theme', cur); } catch (e) { }
    });
})();

/* ═══ ZPicker درختی — نمایش مادر/فرزند ═══ */
(function () {
    var dataEl = document.getElementById('categories-data');
    var hidden = document.getElementById('id_category');
    if (!dataEl || !hidden) return;

    var cats;
    try { cats = JSON.parse(dataEl.textContent); }
    catch (e) {
        try {
            cats = JSON.parse(dataEl.textContent
                .replace(/u'([^']*)'/g, '"$1"').replace(/'/g, '"')
                .replace(/\bNone\b/g, 'null').replace(/\bTrue\b/g, 'true').replace(/\bFalse\b/g, 'false'));
        } catch (e2) { console.error('ZPicker parse error', e2); return; }
    }
    if (!Array.isArray(cats)) return;

    var btn = document.getElementById('catBtn');
    var valueEl = document.getElementById('catValue');
    var clearBtn = document.getElementById('catClear');
    var panel = document.getElementById('catPanel');
    var search = document.getElementById('catSearch');
    var tree = document.getElementById('catTree');
    var pathEl = document.getElementById('catPath');
    var selectedId = hidden.value ? parseInt(hidden.value, 10) : null;

    function escapeHtml(s) { var d = document.createElement('div'); d.textContent = s || ''; return d.innerHTML; }
    function byId(id) { for (var i = 0; i < cats.length; i++) if (cats[i].id === id) return cats[i]; return null; }
    function kids(pid) { return cats.filter(function (c) { return c.parent === pid; }); }
    function roots() { return cats.filter(function (c) { return !c.parent; }); }
    function pathOf(id) {
        var parts = []; var cur = byId(id);
        while (cur) { parts.unshift(cur.title); cur = cur.parent ? byId(cur.parent) : null; }
        return parts;
    }

    function itemRow(c, isChild) {
        var row = document.createElement('div');
        row.className = 'zpicker-item' + (isChild ? ' child' : '') + (selectedId === c.id ? ' selected' : '');
        row.innerHTML =
            '<span class="zpicker-item-icon"><i class="fa-solid ' + (isChild ? 'fa-folder-open' : 'fa-folder') + '"></i></span>' +
            '<span class="zpicker-item-title">' + escapeHtml(c.title) + '</span>' +
            (selectedId === c.id ? '<span class="zpicker-check">✓</span>' : '');
        row.addEventListener('click', function () { select(c.id); });
        return row;
    }

    function renderTree(filterText) {
        tree.innerHTML = '';
        filterText = (filterText || '').trim().toLowerCase();

        /* ── حالت جستجو: لیست تخت + نمایش مسیر مادر ── */
        if (filterText) {
            var matches = cats.filter(function (c) { return (c.title || '').toLowerCase().indexOf(filterText) > -1; });
            if (!matches.length) { tree.innerHTML = '<div class="zpicker-empty">موردی یافت نشد</div>'; return; }
            matches.forEach(function (c) {
                var row = itemRow(c, !!c.parent);
                row.classList.add('search');
                if (c.parent) {
                    var p = byId(c.parent);
                    if (p) {
                        var badge = document.createElement('span');
                        badge.className = 'zpicker-path';
                        badge.textContent = 'مادر: ' + p.title;
                        row.appendChild(badge);
                    }
                }
                tree.appendChild(row);
            });
            return;
        }

        /* ── حالت عادی: درخت مادر/فرزند ── */
        var rs = roots();
        if (!rs.length) { tree.innerHTML = '<div class="zpicker-empty">دسته‌ای تعریف نشده</div>'; return; }

        rs.forEach(function (r) {
            var kidsList = kids(r.id);
            var wrap = document.createElement('div');

            var row = document.createElement('div');
            row.className = 'zpicker-item' + (selectedId === r.id ? ' selected' : '');
            row.innerHTML =
                '<span class="zpicker-item-icon"><i class="fa-solid fa-folder"></i></span>' +
                '<span class="zpicker-item-title">' + escapeHtml(r.title) + '</span>' +
                (kidsList.length ? '<span class="zpicker-badge">مادر • ' + kidsList.length + ' زیرمجموعه</span>' : '') +
                (selectedId === r.id ? '<span class="zpicker-check">✓</span>' : '');
            row.addEventListener('click', function () { select(r.id); });
            wrap.appendChild(row);

            if (kidsList.length) {
                var toggle = document.createElement('button');
                toggle.type = 'button';
                toggle.className = 'zpicker-toggle';
                toggle.title = 'نمایش زیرمجموعه‌ها';
                toggle.innerHTML = '<i class="fa-solid fa-chevron-left"></i>';
                toggle.addEventListener('click', function (e) {
                    e.stopPropagation();
                    var kidsEl = wrap.querySelector('.zpicker-kids');
                    var isOpen = kidsEl.style.display !== 'none';
                    kidsEl.style.display = isOpen ? 'none' : 'flex';
                    toggle.classList.toggle('open', !isOpen);
                });
                row.appendChild(toggle);

                var kidsEl = document.createElement('div');
                kidsEl.className = 'zpicker-kids';
                kidsEl.style.display = 'none';
                if (selectedId && kidsList.some(function (k) { return k.id === selectedId; })) {
                    kidsEl.style.display = 'flex';
                    toggle.classList.add('open');
                }
                kidsList.forEach(function (k) { kidsEl.appendChild(itemRow(k, true)); });
                wrap.appendChild(kidsEl);
            }
            tree.appendChild(wrap);
        });
    }

    function select(id) {
        selectedId = id;
        hidden.value = id;
        var parts = pathOf(id);
        valueEl.textContent = parts.join(' › ');
        valueEl.classList.remove('is-placeholder');
        clearBtn.style.display = 'inline-flex';
        pathEl.innerHTML = 'انتخاب شده: <strong>' + escapeHtml(parts.join(' › ')) + '</strong>';
        close();
        renderTree();
    }

    function open() { panel.classList.add('open'); btn.classList.add('open'); search.value = ''; renderTree(); setTimeout(function () { search.focus(); }, 100); }
    function close() { panel.classList.remove('open'); btn.classList.remove('open'); }

    btn.addEventListener('click', function (e) { e.stopPropagation(); panel.classList.contains('open') ? close() : open(); });
    panel.addEventListener('click', function (e) { e.stopPropagation(); });
    document.addEventListener('click', close);
    document.addEventListener('keydown', function (e) { if (e.key === 'Escape') close(); });
    search.addEventListener('input', function () { renderTree(search.value); });

    clearBtn.addEventListener('click', function (e) {
        e.stopPropagation();
        selectedId = null; hidden.value = '';
        valueEl.textContent = 'انتخاب دسته‌بندی...';
        valueEl.classList.add('is-placeholder');
        clearBtn.style.display = 'none';
        pathEl.textContent = 'هنوز دسته‌ای انتخاب نشده';
        renderTree();
    });

    if (selectedId) {
        var parts = pathOf(selectedId);
        if (parts.length) {
            valueEl.textContent = parts.join(' › ');
            valueEl.classList.remove('is-placeholder');
            clearBtn.style.display = 'inline-flex';
            pathEl.innerHTML = 'انتخاب شده: <strong>' + escapeHtml(parts.join(' › ')) + '</strong>';
        }
    }
    renderTree();
})();