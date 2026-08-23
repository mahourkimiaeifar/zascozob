/* ═══ مدیریت پیام‌های تماس ═══ */
(function () {
    "use strict";

    function getCookie(n) { var v = '; ' + document.cookie; var p = v.split('; ' + n + '='); if (p.length === 2) return p.pop().split(';').shift(); return ''; }

    /* جستجو و فیلتر */
    var searchInput = document.getElementById('searchInput');
    var filterSelect = document.getElementById('filterStatus');
    var rows = Array.prototype.slice.call(document.querySelectorAll('.msg-row'));
    function filterRows() {
        var q = searchInput ? searchInput.value.toLowerCase() : '';
        var st = filterSelect ? filterSelect.value : '';
        rows.forEach(function (r) {
            var okText = !q || r.textContent.toLowerCase().indexOf(q) > -1;
            var okStatus = !st || r.dataset.status === st;
            r.style.display = (okText && okStatus) ? '' : 'none';
        });
    }
    if (searchInput) searchInput.addEventListener('input', filterRows);
    if (filterSelect) filterSelect.addEventListener('change', filterRows);

    var refreshBtn = document.getElementById('refreshBtn');
    if (refreshBtn) refreshBtn.addEventListener('click', function () { location.reload(); });

    /* مودال مشاهده */
    var viewModal = document.getElementById('viewModal');
    var currentId = null;
    document.querySelectorAll('.view-btn').forEach(function (btn) {
        btn.addEventListener('click', function () {
            var row = btn.closest('.msg-row');
            document.getElementById('viewName').textContent = row.querySelector('.name-cell strong').textContent;
            document.getElementById('viewEmail').textContent = row.querySelector('.cell-email a').textContent;
            document.getElementById('viewPhone').textContent = row.querySelector('.cell-phone').textContent.trim();
            document.getElementById('viewDate').textContent = row.querySelector('.date-cell').textContent.trim();
            document.getElementById('viewMessage').textContent = row.querySelector('.message-preview').textContent;
            var fb = row.querySelector('.file-badge');
            var wrap = document.getElementById('viewAttachmentWrap');
            if (fb) { document.getElementById('viewAttachment').href = fb.href; wrap.style.display = ''; }
            else wrap.style.display = 'none';
            currentId = btn.dataset.id;
            viewModal.classList.add('active');
            fetch('/zasco-admin-x9k2p/api/mark-read/' + currentId + '/', { method: 'POST', headers: { 'X-CSRFToken': getCookie('csrftoken') } })
                .then(function () { row.dataset.status = 'read'; var b = row.querySelector('.status-badge'); if (b) { b.textContent = 'خوانده شده'; b.className = 'status-badge status-read'; } });
        });
    });

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
    function openReply(row) {
        document.getElementById('replyName').textContent = row.querySelector('.name-cell strong').textContent;
        document.getElementById('replyEmail').value = row.querySelector('.cell-email a').textContent;
        document.getElementById('replyMessageId').value = row.querySelector('.reply-btn').dataset.id;
        document.getElementById('replySubject').value = 'پاسخ به پیام شما - زاسکو ذوب';
        replyModal.classList.add('active');
        setTimeout(initEditor, 200);
    }
    document.querySelectorAll('.reply-btn').forEach(function (btn) {
        btn.addEventListener('click', function () { openReply(btn.closest('.msg-row')); });
    });
    var viewReplyBtn = document.getElementById('viewReplyBtn');
    if (viewReplyBtn) viewReplyBtn.addEventListener('click', function () {
        viewModal.classList.remove('active');
        var row = document.querySelector('.msg-row[data-id="' + currentId + '"]');
        if (row) openReply(row);
    });

    /* حذف */
    document.querySelectorAll('.delete-btn').forEach(function (btn) {
        btn.addEventListener('click', function () {
            if (!confirm('آیا از حذف این پیام مطمئن هستید؟')) return;
            var row = btn.closest('.msg-row');
            fetch('/zasco-admin-x9k2p/api/delete/' + btn.dataset.id + '/', { method: 'POST', headers: { 'X-CSRFToken': getCookie('csrftoken') } })
                .then(function (r) { if (r.ok) { row.style.opacity = '0'; setTimeout(function () { row.remove(); }, 300); showToast('پیام حذف شد', 'success'); } });
        });
    });

    /* ارسال پاسخ */
    var replyForm = document.getElementById('replyForm');
    if (replyForm) replyForm.addEventListener('submit', function (e) {
        e.preventDefault();
        var body = editor ? editor.getData() : document.getElementById('replyBody').value;
        if (!body || body === '<p>&nbsp;</p>') { showToast('متن پاسخ خالی است', 'error'); return; }
        var fd = new FormData(replyForm);
        fd.set('body', body);
        fetch(replyForm.action, { method: 'POST', body: fd, headers: { 'X-CSRFToken': getCookie('csrftoken') } })
            .then(function (r) { return r.json(); })
            .then(function (d) {
                if (d.success) { showToast('پاسخ با موفقیت ارسال شد', 'success'); replyModal.classList.remove('active'); if (editor) editor.setData(''); setTimeout(function () { location.reload(); }, 800); }
                else showToast('خطا: ' + d.error, 'error');
            })
            .catch(function () { showToast('خطا در ارسال', 'error'); });
    });

    console.log('✅ Contact page initialized');
})();