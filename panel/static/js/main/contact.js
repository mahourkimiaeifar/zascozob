/* ═══ مدیریت پیام‌های تماس ═══ */
(function () {
  "use strict";

  function getCookie(n) { var v = '; ' + document.cookie; var p = v.split('; ' + n + '='); if (p.length === 2) return p.pop().split(';').shift(); return ''; }
  function formatSize(b) { if (b < 1024) return b + ' B'; if (b < 1024 * 1024) return (b / 1024).toFixed(1) + ' KB'; return (b / (1024 * 1024)).toFixed(2) + ' MB'; }
  function escapeHtml(s) { var d = document.createElement('div'); d.textContent = s; return d.innerHTML; }

  /* جستجو و فیلتر */
  var searchInput = document.getElementById('searchInput');
  var filterSelect = document.getElementById('filterStatus');
  var cards = Array.prototype.slice.call(document.querySelectorAll('.msg-card'));
  function filterCards() {
    var q = searchInput ? searchInput.value.toLowerCase() : '';
    var st = filterSelect ? filterSelect.value : '';
    cards.forEach(function (c) {
      var okText = !q || c.textContent.toLowerCase().indexOf(q) > -1;
      var okStatus = !st || c.dataset.status === st;
      c.style.display = (okText && okStatus) ? '' : 'none';
    });
  }
  if (searchInput) searchInput.addEventListener('input', filterCards);
  if (filterSelect) filterSelect.addEventListener('change', filterCards);

  var refreshBtn = document.getElementById('refreshBtn');
  if (refreshBtn) refreshBtn.addEventListener('click', function () { location.reload(); });

  /* مودال مشاهده پیام */
  var viewModal = document.getElementById('viewModal');
  var currentId = null;
  document.querySelectorAll('.view-btn').forEach(function (btn) {
    btn.addEventListener('click', function () {
      var card = btn.closest('.msg-card');
      document.getElementById('viewName').textContent = card.dataset.name;
      document.getElementById('viewEmail').textContent = card.dataset.email || '—';
      document.getElementById('viewPhone').textContent = card.dataset.phone || '—';
      document.getElementById('viewDate').textContent = card.dataset.date;
      document.getElementById('viewMessage').textContent = card.querySelector('.msg-full').textContent;
      var fb = card.querySelector('.msg-tags .file-badge');
      var wrap = document.getElementById('viewAttachmentWrap');
      if (fb) { document.getElementById('viewAttachment').href = fb.href; wrap.style.display = ''; }
      else wrap.style.display = 'none';
      currentId = btn.dataset.id;
      viewModal.classList.add('active');
      fetch('/zasco-admin-x9k2p/api/mark-read/' + currentId + '/', { method: 'POST', headers: { 'X-CSRFToken': getCookie('csrftoken') } })
        .then(function () {
          if (card.dataset.status === 'unread') card.dataset.status = 'read';
          card.classList.remove('is-unread');
          var dot = card.querySelector('.unread-dot'); if (dot) dot.remove();
          var b = card.querySelector('.status-badge');
          if (b && b.className.indexOf('answered') === -1) { b.textContent = 'خوانده شده'; b.className = 'status-badge status-read'; }
        });
    });
  });

  /* مودال مشاهده پاسخ ادمین */
  document.querySelectorAll('.view-reply-btn').forEach(function (btn) {
    btn.addEventListener('click', function () {
      var card = btn.closest('.msg-card');
      document.getElementById('vrSubject').textContent = card.dataset.replySubject || '—';
      document.getElementById('vrDate').textContent = card.dataset.repliedDate || '—';
      document.getElementById('vrBody').innerHTML = card.querySelector('.reply-full').innerHTML;
      var atts = card.querySelector('.reply-atts');
      var wrap = document.getElementById('vrAttsWrap');
      if (atts && atts.innerHTML.trim()) { document.getElementById('vrAtts').innerHTML = atts.innerHTML; wrap.style.display = ''; }
      else wrap.style.display = 'none';
      document.getElementById('viewReplyModal').classList.add('active');
    });
  });

  /* ── پیوست‌های چندتایی پاسخ ── */
  var selectedFiles = [];
  var filesInput = document.getElementById('replyFiles');
  var drop = document.getElementById('replyFilesDrop');
  var list = document.getElementById('replyFilesList');

  function renderFiles() {
    list.innerHTML = '';
    drop.classList.toggle('has-files', selectedFiles.length > 0);
    selectedFiles.forEach(function (f, i) {
      var li = document.createElement('li');
      li.innerHTML = '<span class="rf-name">📎 ' + escapeHtml(f.name) + '</span><span class="rf-size">' + formatSize(f.size) + '</span><button type="button" class="rf-remove" data-i="' + i + '">×</button>';
      list.appendChild(li);
    });
  }
  function addFiles(fl) {
    Array.prototype.forEach.call(fl, function (f) {
      if (f.size > 10 * 1024 * 1024) { showToast('فایل ' + f.name + ' بزرگ‌تر از ۱۰MB است', 'error'); return; }
      selectedFiles.push(f);
    });
    renderFiles();
  }
  if (drop) {
    drop.addEventListener('click', function (e) { if (!e.target.closest('.rf-remove')) filesInput.click(); });
    ['dragenter', 'dragover'].forEach(function (ev) { drop.addEventListener(ev, function (e) { e.preventDefault(); drop.classList.add('dragging'); }); });
    ['dragleave', 'drop'].forEach(function (ev) { drop.addEventListener(ev, function (e) { e.preventDefault(); drop.classList.remove('dragging'); }); });
    drop.addEventListener('drop', function (e) { addFiles(e.dataTransfer.files); });
    filesInput.addEventListener('change', function () { addFiles(filesInput.files); filesInput.value = ''; });
    list.addEventListener('click', function (e) {
      var b = e.target.closest('.rf-remove');
      if (b) { selectedFiles.splice(+b.dataset.i, 1); renderFiles(); }
    });
  }

  /* مودال پاسخ + CKEditor */
  var replyModal = document.getElementById('replyModal');
  var editor = null;
  function initEditor() {
    if (editor || typeof ClassicEditor === 'undefined') return;
    ClassicEditor.create(document.getElementById('replyBody'), {
      language: 'fa',
      toolbar: ['heading', '|', 'bold', 'italic', 'underline', '|', 'bulletedList', 'numberedList', '|', 'link', 'insertTable', 'imageUpload', '|', 'alignment', 'undo', 'redo']
    }).then(function (e) { editor = e; }).catch(function (err) { console.error(err); });
  }
  function openReply(card) {
    document.getElementById('replyName').textContent = card.dataset.name;
    document.getElementById('replyEmail').value = card.dataset.email || '';
    document.getElementById('replyMessageId').value = card.dataset.id;
    document.getElementById('replySubject').value = 'پاسخ به پیام شما - زاسکو ذوب';
    selectedFiles = []; renderFiles();
    replyModal.classList.add('active');
    setTimeout(initEditor, 200);
  }
  document.querySelectorAll('.reply-btn').forEach(function (btn) {
    btn.addEventListener('click', function () { openReply(btn.closest('.msg-card')); });
  });
  var viewReplyBtn = document.getElementById('viewReplyBtn');
  if (viewReplyBtn) viewReplyBtn.addEventListener('click', function () {
    viewModal.classList.remove('active');
    var card = document.querySelector('.msg-card[data-id="' + currentId + '"]');
    if (card) openReply(card);
  });

  /* حذف */
  document.querySelectorAll('.delete-btn').forEach(function (btn) {
    btn.addEventListener('click', function () {
      if (!confirm('آیا از حذف این پیام مطمئن هستید؟')) return;
      var card = btn.closest('.msg-card');
      fetch('/zasco-admin-x9k2p/api/delete/' + btn.dataset.id + '/', { method: 'POST', headers: { 'X-CSRFToken': getCookie('csrftoken') } })
        .then(function (r) { if (r.ok) { card.style.opacity = '0'; card.style.transform = 'scale(.97)'; setTimeout(function () { card.remove(); }, 300); showToast('پیام حذف شد', 'success'); } });
    });
  });

  /* ارسال پاسخ — با قفل دکمه ضد کلیک تکراری */
  var replyForm = document.getElementById('replyForm');
  var sendBtn = replyForm ? replyForm.querySelector('[type="submit"]') : null;
  if (replyForm) replyForm.addEventListener('submit', function (e) {
    e.preventDefault();
    if (sendBtn && sendBtn.disabled) return;
    var body = editor ? editor.getData() : document.getElementById('replyBody').value;
    if (!body || body === '<p>&nbsp;</p>') { showToast('متن پاسخ خالی است', 'error'); return; }
    if (sendBtn) { sendBtn.disabled = true; sendBtn.innerHTML = '⏳ در حال ارسال...'; }
    var fd = new FormData(replyForm);
    fd.set('body', body);
    selectedFiles.forEach(function (f) { fd.append('attachments', f); });
    fetch(replyForm.action, { method: 'POST', body: fd, headers: { 'X-CSRFToken': getCookie('csrftoken') } })
      .then(function (r) { return r.json(); })
      .then(function (d) {
        if (d.success) { showToast('پاسخ با موفقیت ارسال شد', 'success'); replyModal.classList.remove('active'); if (editor) editor.setData(''); setTimeout(function () { location.reload(); }, 800); }
        else showToast('خطا: ' + d.error, 'error');
      })
      .catch(function () { showToast('خطا در ارسال', 'error'); })
      .finally(function () { if (sendBtn) { sendBtn.disabled = false; sendBtn.innerHTML = 'ارسال ایمیل'; } });
  });

  console.log('✅ Contact page initialized');
})();