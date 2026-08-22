/* ═══ انیمیشن‌های صفحه تماس ═══ */
(function () {
  "use strict";

  /* ── ۱) ورود پلکانی هنگام اسکرول ── */
  var REVEAL = ".co-lead, .co-body p, .co-section-head, .co-intro, .co-contact-card, .co-address-card, .co-reason, .co-step, .co-form-wrap, .co-field, .co-submit, .co-final-inner";
  if ("IntersectionObserver" in window) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (en.isIntersecting) {
          en.target.style.opacity = "";
          en.target.classList.add("co-visible");
          io.unobserve(en.target);
        }
      });
    }, { threshold: 0.12, rootMargin: "0px 0px -30px 0px" });

    document.querySelectorAll(REVEAL).forEach(function (el, i) {
      el.style.setProperty("--d", (Math.min(i, 8) * 0.08).toFixed(2) + "s");
      el.style.opacity = "0";
      io.observe(el);
    });
  }

  /* ── ۲) انیمیشن Hero بعد از لودینگ ── */
  function animateHero() {
    document.querySelector(".co-hero").classList.add("co-hero-ready");
  }
  if (document.readyState === "complete") {
    setTimeout(animateHero, 400);
  } else {
    window.addEventListener("load", function () { setTimeout(animateHero, 400); });
  }

  /* ── ۳) افکت فیلدهای فرم ── */
  document.querySelectorAll(".co-field input, .co-field textarea").forEach(function (input) {
    input.addEventListener("focus", function () {
      input.parentElement.classList.add("co-focused");
    });
    input.addEventListener("blur", function () {
      if (!input.value) input.parentElement.classList.remove("co-focused");
    });
    if (input.value) input.parentElement.classList.add("co-focused");
  });

  /* ── ۴) Loader دکمه ارسال ── */
  var form = document.getElementById("co-form");
  if (form) {
    form.addEventListener("submit", function () {
      var btn = form.querySelector(".co-submit");
      btn.classList.add("co-loading");
    });
  }

  /* ── ۵) پارالاکس روی orb های هیرو ── */
  var orbs = document.querySelectorAll(".co-hero-orb");
  if (orbs.length) {
    window.addEventListener("mousemove", function (e) {
      var mx = (e.clientX / window.innerWidth - 0.5) * 2;
      var my = (e.clientY / window.innerHeight - 0.5) * 2;
      orbs.forEach(function (orb, i) {
        var factor = (i + 1) * 20;
        orb.style.transform = "translate(" + (mx * factor) + "px, " + (my * factor) + "px)";
      });
    });
  }

  /* ── ۶) Tilt ملایم روی کارت‌ها ── */
  document.querySelectorAll(".co-contact-card").forEach(function (card) {
    card.addEventListener("mousemove", function (e) {
      var r = card.getBoundingClientRect();
      var cx = r.left + r.width / 2;
      var cy = r.top + r.height / 2;
      var rx = ((e.clientY - cy) / (r.height / 2)) * -2;
      var ry = ((e.clientX - cx) / (r.width / 2)) * 2;
      card.style.transform = "perspective(1000px) rotateX(" + rx + "deg) rotateY(" + ry + "deg) translateY(-6px)";
    });
    card.addEventListener("mouseleave", function () {
      card.style.transform = "";
    });
  });

  console.log("✨ انیمیشن‌های تماس فعال شد");
  /* ── ۷) مدیریت آپلود فایل ── */
  var dropZone = document.getElementById('co-file-drop');
  var fileInput = document.getElementById('attachment');
  var emptyState = document.getElementById('co-file-empty');
  var previewState = document.getElementById('co-file-preview');
  var fileIcon = document.getElementById('co-file-icon');
  var fileImage = document.getElementById('co-file-image');
  var fileName = document.getElementById('co-file-name');
  var fileSize = document.getElementById('co-file-size');
  var removeBtn = document.getElementById('co-file-remove');
  var fileError = document.getElementById('co-file-error');

  if (dropZone) {
    // کلیک روی drop zone
    dropZone.addEventListener('click', function (e) {
      if (e.target !== removeBtn && !removeBtn.contains(e.target)) {
        fileInput.click();
      }
    });

    // Drag and drop
    ['dragenter', 'dragover'].forEach(function (evt) {
      dropZone.addEventListener(evt, function (e) {
        e.preventDefault();
        dropZone.classList.add('co-dragging');
      });
    });
    ['dragleave', 'drop'].forEach(function (evt) {
      dropZone.addEventListener(evt, function (e) {
        e.preventDefault();
        dropZone.classList.remove('co-dragging');
      });
    });
    dropZone.addEventListener('drop', function (e) {
      var files = e.dataTransfer.files;
      if (files.length) handleFile(files[0]);
    });

    // انتخاب فایل
    fileInput.addEventListener('change', function () {
      if (fileInput.files.length) handleFile(fileInput.files[0]);
    });

    // حذف فایل
    removeBtn.addEventListener('click', function (e) {
      e.stopPropagation();
      fileInput.value = '';
      emptyState.style.display = '';
      previewState.style.display = 'none';
      fileError.style.display = 'none';
      dropZone.classList.remove('co-has-file');
    });

    function handleFile(file) {
      fileError.style.display = 'none';

      // اعتبارسنجی سایز
      if (file.size > 5 * 1024 * 1024) {
        showError('حجم فایل نباید بیشتر از ۵ مگابایت باشد.');
        return;
      }

      // اعتبارسنجی نوع
      var allowedTypes = ['image/jpeg', 'image/png', 'image/jpg', 'image/gif', 'image/webp',
        'application/pdf', 'application/msword',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document'];
      var allowedExts = ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.pdf', '.doc', '.docx', '.dwg'];
      var ext = '.' + file.name.split('.').pop().toLowerCase();

      if (allowedTypes.indexOf(file.type) === -1 && allowedExts.indexOf(ext) === -1) {
        showError('نوع فایل مجاز نیست. لطفاً تصویر، PDF، Word یا DWG ارسال کنید.');
        return;
      }

      // نمایش اطلاعات
      fileName.textContent = file.name;
      fileSize.textContent = formatSize(file.size);
      emptyState.style.display = 'none';
      previewState.style.display = 'flex';
      dropZone.classList.add('co-has-file');

      // پیش‌نمایش تصویر
      if (file.type.startsWith('image/')) {
        var reader = new FileReader();
        reader.onload = function (e) {
          fileImage.src = e.target.result;
          fileImage.style.display = 'block';
          fileIcon.style.display = 'none';
        };
        reader.readAsDataURL(file);
      } else {
        fileImage.style.display = 'none';
        fileIcon.style.display = 'flex';
        // آیکون مخصوص هر نوع فایل
        if (ext === '.pdf') fileIcon.textContent = '📕';
        else if (ext === '.doc' || ext === '.docx') fileIcon.textContent = '📘';
        else if (ext === '.dwg') fileIcon.textContent = '📐';
        else fileIcon.textContent = '📎';
      }
    }

    function showError(msg) {
      fileError.textContent = msg;
      fileError.style.display = 'block';
      fileInput.value = '';
    }

    function formatSize(bytes) {
      if (bytes < 1024) return bytes + ' B';
      if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
      return (bytes / (1024 * 1024)).toFixed(2) + ' MB';
    }
  }
  /* ── ۸) اسکرول خودکار به پیام موفقیت/خطا ── */
  var alertBox = document.querySelector('.co-success, .co-error');
  if (alertBox) {
    setTimeout(function () {
      alertBox.scrollIntoView({ behavior: 'smooth', block: 'center' });
      alertBox.classList.add('co-flash');
    }, 700);
  }
    /* ── ۹) فیلتر زنده شماره تماس (فقط اعداد و +) ── */
  var phoneInput = document.getElementById('phone');
  if (phoneInput) {
    phoneInput.addEventListener('input', function () {
      this.value = this.value.replace(/[^0-9+]/g, '');
    });
  }
})();