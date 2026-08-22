/* ═══ صفحه مدیریت پیام‌ها ═══ */
(function () {
    "use strict";

    // ── Search & Filter ──
    var searchInput = document.getElementById('searchInput');
    var filterSelect = document.getElementById('filterStatus');
    var rows = Array.from(document.querySelectorAll('.msg-row'));

    function filterRows() {
        var q = (searchInput ? searchInput.value : '').toLowerCase();
        var status = filterSelect ? filterSelect.value : '';
        rows.forEach(function (row) {
            var text = row.textContent.toLowerCase();
            var rowStatus = row.dataset.status || '';
            var matchText = !q || text.indexOf(q) > -1;
            var matchStatus = !status || rowStatus === status;
            row.style.display = matchText && matchStatus ? '' : 'none';
        });
    }
    if (searchInput) searchInput.addEventListener('input', filterRows);
    if (filterSelect) filterSelect.addEventListener('change', filterRows);

    // ── Refresh ──
    var refreshBtn = document.getElementById('refreshBtn');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', function () {
            location.reload();
        });
    }

    // ── View Modal ──
    var viewModal = document.getElementById('viewModal');
    var currentMsgId = null;

    document.querySelectorAll('.view-btn').forEach(function (btn) {
        btn.addEventListener('click', function () {
            var row = btn.closest('.msg-row');
            document.getElementById('viewName').textContent = row.querySelector('.name-cell strong').textContent;
            document.getElementById('viewEmail').textContent = row.querySelector('.cell-email a').textContent;
            document.getElementById('viewPhone').textContent = row.querySelector('.cell-phone').textContent;
            document.getElementById('viewDate').textContent = row.querySelector('.date-cell').textContent.trim();
            document.getElementById('viewMessage').textContent = row.querySelector('.message-preview').textContent;

            var fileBadge = row.querySelector('.file-badge');
            var wrap = document.getElementById('viewAttachmentWrap');
            if (fileBadge) {
                document.getElementById('viewAttachment').href = fileBadge.href;
                document.getElementById('viewAttachmentName').textContent = 'دانلود فایل پیوست';
                wrap.style.display = '';
            } else {
                wrap.style.display = 'none';
            }

            currentMsgId = btn.dataset.id;
            viewModal.classList.add('active');

            // Mark as read
            fetch('/panel/api/mark-read/' + currentMsgId + '/', {
                method: 'POST',
                headers: { 'X-CSRFToken': getCookie('csrftoken') }
            }).then(function () {
                row.dataset.status = 'read';
                var badge = row.querySelector('.status-badge');
                if (badge) {
                    badge.textContent = 'خوانده شده';
                    badge.className = 'status-badge status-read';
                }
            });
        });
    });

    // ── Reply Modal + CKEditor ──
    var replyModal = document.getElementById('replyModal');
    var ckeditorInstance = null;

    function initCKEditor() {
        if (ckeditorInstance) return;
        if (typeof ClassicEditor === 'undefined') return;

        ClassicEditor
            .create(document.getElementById('replyBody'), {
                language: 'fa',
                toolbar: [
                    'heading', '|',
                    'bold', 'italic', 'underline', 'strikethrough', '|',
                    'bulletedList', 'numberedList', '|',
                    'link', 'blockQuote', 'insertTable', 'imageUpload', '|',
                    'alignment', 'outdent', 'indent', '|',
                    'undo', 'redo'
                ],
                placeholder: 'متن پاسخ را اینجا بنویسید...'
            })
            .then(function (editor) {
                ckeditorInstance = editor;
            })
            .catch(function (err) { console.error(err); });
    }

    document.querySelectorAll('.reply-btn').forEach(function (btn) {
        btn.addEventListener('click', function () {
            var row = btn.closest('.msg-row');
            document.getElementById('replyName').textContent = row.querySelector('.name-cell strong').textContent;
            document.getElementById('replyEmail').value = row.querySelector('.cell-email a').textContent;
            document.getElementById('replyMessageId').value = btn.dataset.id;
            document.getElementById('replySubject').value = 'پاسخ به پیام شما';

            replyModal.classList.add('active');
            setTimeout(initCKEditor, 200);
        });
    });

    document.getElementById('viewReplyBtn').addEventListener('click', function () {
        document.querySelector('[data-id="' + currentMsgId + '"] .reply-btn').click();
        viewModal.classList.remove('active');
    });

    // ── Delete ──
    document.querySelectorAll('.delete-btn').forEach(function (btn) {
        btn.addEventListener('click', function () {
            if (!confirm('آیا از حذف این پیام مطمئن هستید؟')) return;
            var row = btn.closest('.msg-row');
            fetch('/panel/api/delete/' + btn.dataset.id + '/', {
                method: 'POST',
                headers: { 'X-CSRFToken': getCookie('csrftoken') }
            }).then(function (r) {
                if (r.ok) {
                    row.style.opacity = '0';
                    setTimeout(function () { row.remove(); }, 300);
                    showToast('پیام با موفقیت حذف شد', 'success');
                }
            });
        });
    });

    // ── Reply Form ──
    var replyForm = document.getElementById('replyForm');
    if (replyForm) {
        replyForm.addEventListener('submit', function (e) {
            e.preventDefault();
            var body = ckeditorInstance ? ckeditorInstance.getData() : document.getElementById('replyBody').value;
            if (!body) {
                showToast('متن پاسخ نمی‌تواند خالی باشد', 'error');
                return;
            }

            var formData = new FormData(replyForm);
            formData.set('body', body);

            fetch(replyForm.action, {
                method: 'POST',
                body: formData,
                headers: { 'X-CSRFToken': getCookie('csrftoken') }
            })
            .then(function (r) { return r.json(); })
            .then(function (data) {
                if (data.success) {
                    showToast('پاسخ با موفقیت ارسال شد', 'success');
                    replyModal.classList.remove('active');
                    if (ckeditorInstance) ckeditorInstance.setData('');
                } else {
                    showToast('خطا: ' + data.error, 'error');
                }
            })
            .catch(function () { showToast('خطا در ارسال', 'error'); });
        });
    }

    // ── CSRF Helper ──
    function getCookie(name) {
        var value = '; ' + document.cookie;
        var parts = value.split('; ' + name + '=');
        if (parts.length === 2) return parts.pop().split(';').shift();
        return '';
    }

    console.log('✅ Contact page initialized');
})();