/* ═══ کد امنیتی ضد کپی‌برداری ═══ */
(function () {
  "use strict";

  // ── ۱) جلوگیری از راست‌کلیک ──
  document.addEventListener('contextmenu', function (e) {
    e.preventDefault();
    showToast('راست‌کلیک غیرفعال است', 'warning');
  });

  // ── ۲) جلوگیری از سلکت کردن متن ──
  document.addEventListener('selectstart', function (e) {
    if (!e.target.closest('input, textarea, [contenteditable]')) {
      e.preventDefault();
    }
  });

  // ── ۳) جلوگیری از کپی (Ctrl+C, Ctrl+X, Ctrl+V) ──
  document.addEventListener('keydown', function (e) {
    // Ctrl+C (کپی)
    if (e.ctrlKey && e.key === 'c') {
      e.preventDefault();
      showToast('کپی غیرفعال است', 'error');
      return false;
    }
    // Ctrl+X (کات)
    if (e.ctrlKey && e.key === 'x') {
      e.preventDefault();
      showToast('کات غیرفعال است', 'error');
      return false;
    }
    // Ctrl+U (نمایش سورس)
    if (e.ctrlKey && e.key === 'u') {
      e.preventDefault();
      showToast('مشاهده سورس غیرفعال است', 'error');
      return false;
    }
    // Ctrl+S (ذخیره صفحه)
    if (e.ctrlKey && e.key === 's') {
      e.preventDefault();
      showToast('ذخیره صفحه غیرفعال است', 'error');
      return false;
    }
    // Ctrl+P (پرینت)
    if (e.ctrlKey && e.key === 'p') {
      e.preventDefault();
      showToast('پرینت غیرفعال است', 'error');
      return false;
    }
    // F12 (DevTools)
    if (e.key === 'F12') {
      e.preventDefault();
      showToast('DevTools غیرفعال است', 'error');
      return false;
    }
    // Ctrl+Shift+I (DevTools)
    if (e.ctrlKey && e.shiftKey && e.key === 'I') {
      e.preventDefault();
      showToast('DevTools غیرفعال است', 'error');
      return false;
    }
    // Ctrl+Shift+J (Console)
    if (e.ctrlKey && e.shiftKey && e.key === 'J') {
      e.preventDefault();
      showToast('Console غیرفعال است', 'error');
      return false;
    }
    // Ctrl+Shift+C (Inspect Element)
    if (e.ctrlKey && e.shiftKey && e.key === 'C') {
      e.preventDefault();
      showToast('Inspect غیرفعال است', 'error');
      return false;
    }
  });

  // ── ۴) جلوگیری از کشیدن و رها کردن ──
  document.addEventListener('dragstart', function (e) {
    if (!e.target.closest('input, textarea, [contenteditable]')) {
      e.preventDefault();
    }
  });

  // ── ۵) تشخیص DevTools باز ──
  let devtoolsOpen = false;
  const threshold = 160;
  
  function checkDevTools() {
    const widthThreshold = window.outerWidth - window.innerWidth > threshold;
    const heightThreshold = window.outerHeight - window.innerHeight > threshold;
    
    if (widthThreshold || heightThreshold) {
      if (!devtoolsOpen) {
        devtoolsOpen = true;
        showToast('DevTools شناسایی شد! لطفاً ببندید.', 'error');
      }
    } else {
      devtoolsOpen = false;
    }
  }
  
  setInterval(checkDevTools, 1000);

  // ── ۶) جلوگیری از Print Screen ──
  document.addEventListener('keyup', function (e) {
    if (e.key === 'PrintScreen') {
      navigator.clipboard.writeText('');
      showToast('اسکرین‌شات غیرفعال است', 'warning');
    }
  });

  // ── ۷) Toast Notification ──
  function showToast(message, type) {
    type = type || 'info';
    let container = document.getElementById('secureToastContainer');
    if (!container) {
      container = document.createElement('div');
      container.id = 'secureToastContainer';
      container.style.cssText = 'position:fixed;top:90px;left:30px;z-index:99999;display:flex;flex-direction:column;gap:10px;max-width:320px;pointer-events:none;';
      document.body.appendChild(container);
    }
    
    const toast = document.createElement('div');
    toast.style.cssText = `
      background:linear-gradient(135deg,#141419,#0b0d10);
      border:1px solid rgba(255,107,0,.3);
      border-radius:12px;
      padding:14px 18px;
      box-shadow:0 20px 50px rgba(0,0,0,.5);
      font-size:.88rem;
      font-weight:600;
      color:#eef1f6;
      animation:secureToastIn .4s;
      border-right:3px solid ${type === 'error' ? '#f44336' : type === 'warning' ? '#ff9800' : '#2196f3'};
      pointer-events:auto;
    `;
    toast.textContent = message;
    container.appendChild(toast);
    
    setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transform = 'translateX(-20px)';
      setTimeout(() => toast.remove(), 400);
    }, 3000);
  }

  // ── ۸) CSS برای user-select: none ──
  const style = document.createElement('style');
  style.textContent = `
    * {
      -webkit-user-select: none;
      -moz-user-select: none;
      -ms-user-select: none;
      user-select: none;
    }
    input, textarea, [contenteditable] {
      -webkit-user-select: text;
      -moz-user-select: text;
      -ms-user-select: text;
      user-select: text;
    }
    @keyframes secureToastIn {
      from { opacity: 0; transform: translateX(-20px); }
      to { opacity: 1; transform: translateX(0); }
    }
  `;
  document.head.appendChild(style);

  console.log('🔒 Security mode activated');
})();