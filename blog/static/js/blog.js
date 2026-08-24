(function () {
  "use strict";

  function getCookie(n) {
    var v = '; ' + document.cookie;
    var p = v.split('; ' + n + '=');
    if (p.length === 2) return p.pop().split(';').shift();
    return '';
  }

  /* ═══ Toast ══ */
  function showToast(msg, type) {
    type = type || 'info';
    var colors = { success: '#4caf50', error: '#f44336', warning: '#ff9800', info: '#2196f3' };
    var t = document.createElement('div');
    t.style.cssText = 'position:fixed;bottom:100px;left:30px;padding:14px 22px;background:rgba(20,20,25,.95);border:1px solid ' + colors[type] + ';border-radius:12px;color:#fff;font-family:Vazirmatn;font-size:.9rem;font-weight:600;z-index:9999;backdrop-filter:blur(16px);box-shadow:0 10px 30px rgba(0,0,0,.5);border-right:3px solid ' + colors[type] + ';animation:blogToast .4s';
    t.textContent = msg;
    document.body.appendChild(t);
    setTimeout(function () { t.style.opacity = '0'; t.style.transform = 'translateY(10px)'; setTimeout(function () { t.remove(); }, 400); }, 2500);
  }

  /* ═══ منوی موبایل ═══ */
  var menuBtn = document.querySelector('.mobile-menu-btn');
  var navLinks = document.querySelector('.nav-links');
  if (menuBtn && navLinks) {
    menuBtn.addEventListener('click', function (e) {
      e.stopPropagation();
      navLinks.classList.toggle('active');
    });
    document.addEventListener('click', function (e) {
      if (!e.target.closest('.navbar')) navLinks.classList.remove('active');
    });
  }

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

  /* ═══ آپدیت هر دو عدد بدون رفرش ═══ */
  function updateCommentVotes(commentId, likes, dislikes, votedType) {
    var likeBtn = document.querySelector('.like-comment-btn[data-id="' + commentId + '"]');
    var disBtn = document.querySelector('.dislike-comment-btn[data-id="' + commentId + '"]');
    if (likeBtn) {
      likeBtn.querySelector('span').textContent = likes;
      likeBtn.classList.remove('voted', 'liked');
      if (votedType === 'like') likeBtn.classList.add('voted', 'liked');
    }
    if (disBtn) {
      disBtn.querySelector('span').textContent = dislikes;
      disBtn.classList.remove('voted', 'disliked');
      if (votedType === 'dislike') disBtn.classList.add('voted', 'disliked');
    }
  }

  /* ═══ رأی‌دهی با Event Delegation (کامنت‌های load-more هم کار می‌کنن) ═══ */
  document.addEventListener('click', function (e) {
    var likeBtn = e.target.closest('.like-comment-btn');
    var disBtn = e.target.closest('.dislike-comment-btn');
    var postLikeBtn = e.target.closest('.like-btn');

    /* ── لایک کامنت ── */
    if (likeBtn) {
      e.preventDefault();
      if (likeBtn.classList.contains('liked')) {
        showToast('قبلاً این کامنت را لایک کرده‌اید', 'warning');
        return;
      }
      fetch('/blog/api/comments/' + likeBtn.dataset.id + '/like/', { method: 'POST', headers: { 'X-CSRFToken': getCookie('csrftoken') } })
        .then(function (r) { return r.json(); })
        .then(function (d) {
          if (d.success) {
            updateCommentVotes(likeBtn.dataset.id, d.likes, d.dislikes, 'like');
            showToast('لایک ثبت شد ✓', 'success');
          } else if (d.error) {
            showToast(d.error, 'error');
          }
        });
      return;
    }

    /* ── دیسلایک کامنت ── */
    if (disBtn) {
      e.preventDefault();
      if (disBtn.classList.contains('disliked')) {
        showToast('قبلاً این کامنت را دیسلایک کرده‌اید', 'warning');
        return;
      }
      fetch('/blog/api/comments/' + disBtn.dataset.id + '/dislike/', { method: 'POST', headers: { 'X-CSRFToken': getCookie('csrftoken') } })
        .then(function (r) { return r.json(); })
        .then(function (d) {
          if (d.success) {
            updateCommentVotes(disBtn.dataset.id, d.likes, d.dislikes, 'dislike');
            showToast('دیسلایک ثبت شد', 'info');
          } else if (d.error) {
            showToast(d.error, 'error');
          }
        });
      return;
    }

    /* ── لایک پست ── */
    if (postLikeBtn) {
      e.preventDefault();
      if (postLikeBtn.classList.contains('liked')) {
        showToast('شما قبلاً این مقاله را لایک کرده‌اید', 'warning');
        return;
      }
      fetch('/blog/api/posts/' + postLikeBtn.dataset.id + '/like/', { method: 'POST', headers: { 'X-CSRFToken': getCookie('csrftoken') } })
        .then(function (r) { return r.json(); })
        .then(function (d) {
          if (d.success) {
            postLikeBtn.querySelector('.count').textContent = d.likes;
            postLikeBtn.classList.add('voted', 'liked');
            showToast('لایک ثبت شد ✓', 'success');
          } else if (d.error) {
            showToast(d.error, 'error');
          }
        });
    }
  });

  /* ═══ ارسال کامنت ═══ */
  var form = document.getElementById('commentForm');
  if (form) {
    form.addEventListener('submit', function (e) {
      e.preventDefault();
      var fd = new FormData(form);
      fetch('/blog/api/comments/' + POST_ID + '/submit/', { method: 'POST', body: fd, headers: { 'X-CSRFToken': getCookie('csrftoken') } })
        .then(function (r) { return r.json(); })
        .then(function (d) {
          if (d.success) { showToast(d.message, 'success'); form.reset(); }
          else showToast('خطا: ' + d.error, 'error');
        });
    });
  }

  /* ═══ لود کامنت بیشتر ═══ */
  var loadBtn = document.getElementById('loadMoreBtn');
  if (loadBtn) {
    loadBtn.addEventListener('click', function () {
      var offset = parseInt(loadBtn.dataset.offset);
      var fd = new FormData();
      fd.append('offset', offset);
      fetch('/blog/api/comments/' + POST_ID + '/load/', { method: 'POST', body: fd, headers: { 'X-CSRFToken': getCookie('csrftoken') } })
        .then(function (r) { return r.json(); })
        .then(function (d) {
          var list = document.getElementById('commentsList');
          d.comments.forEach(function (c) {
            var div = document.createElement('div');
            div.className = 'comment-card';
            div.dataset.id = c.id;
            div.innerHTML = '<div class="comment-header"><div class="comment-avatar">' + c.name[0] + '</div><div class="comment-info"><strong>' + c.name + '</strong><small>' + c.created + '</small></div></div><div class="comment-body">' + c.text + '</div><div class="comment-actions"><button class="comment-action like-comment-btn" data-id="' + c.id + '">👍 <span>' + c.likes + '</span></button><button class="comment-action dislike-comment-btn" data-id="' + c.id + '">👎 <span>' + c.dislikes + '</span></button></div>';
            list.appendChild(div);
          });
          loadBtn.dataset.offset = offset + d.comments.length;
          if (!d.has_more) loadBtn.style.display = 'none';
        });
    });
  }
  /* ═══ جلوه‌های مقاله: نوار پیشرفت + Reveal ═══ */
  var articleBody = document.querySelector('.article-body');
  if (articleBody) {

    /* ── نوار پیشرفت خواندن ── */
    var bar = document.createElement('div');
    bar.className = 'reading-progress';
    bar.innerHTML = '<div class="reading-progress-fill"></div>';
    document.body.appendChild(bar);
    var fill = bar.querySelector('.reading-progress-fill');

    function updateProgress() {
      var rect = articleBody.getBoundingClientRect();
      var total = rect.height - window.innerHeight * 0.6;
      var scrolled = -rect.top + window.innerHeight * 0.3;
      var p = Math.min(Math.max(scrolled / total, 0), 1);
      fill.style.width = (p * 100).toFixed(2) + '%';
    }
    window.addEventListener('scroll', updateProgress, { passive: true });
    window.addEventListener('resize', updateProgress);
    updateProgress();

    /* ── ظاهرشدن تدریجی عناصر ── */
    var items = articleBody.querySelectorAll('p, h2, h3, h4, ul, ol, blockquote, pre, table, figure, img, hr');
    if ('IntersectionObserver' in window) {
      items.forEach(function (el) { el.classList.add('reveal-item'); });
      var io = new IntersectionObserver(function (entries) {
        entries.forEach(function (en) {
          if (en.isIntersecting) {
            en.target.classList.add('revealed');
            io.unobserve(en.target);
          }
        });
      }, { threshold: 0.08, rootMargin: '0px 0px -40px 0px' });
      items.forEach(function (el) { io.observe(el); });
    }
  }
  /* ── فهرست مطالب + Scrollspy ── */
  var tocList = document.getElementById('tocList');
  var tocBox = document.getElementById('tocBox');
  if (tocList) {
    var heads = articleBody.querySelectorAll('h2, h3');
    if (!heads.length && tocBox) {
      tocBox.style.display = 'none';
    } else {
      heads.forEach(function (h, i) {
        if (!h.id) h.id = 'sec-' + i;
        var li = document.createElement('li');
        li.className = 'toc-' + h.tagName.toLowerCase();
        var a = document.createElement('a');
        a.href = '#' + h.id;
        a.textContent = h.textContent;
        a.addEventListener('click', function (e) {
          e.preventDefault();
          var target = document.getElementById(h.id);
          var y = target.getBoundingClientRect().top + window.pageYOffset - 100;
          window.scrollTo({ top: y, behavior: 'smooth' });
        });
        li.appendChild(a);
        tocList.appendChild(li);
      });

      /* Scrollspy */
      var tocLinks = tocList.querySelectorAll('a');
      function spy() {
        var current = null;
        heads.forEach(function (h) {
          if (h.getBoundingClientRect().top < 140) current = h.id;
        });
        tocLinks.forEach(function (a) {
          a.classList.toggle('active', a.getAttribute('href') === '#' + current);
        });
      }
      window.addEventListener('scroll', spy, { passive: true });
      spy();
    }
  }
  console.log('✅ Blog initialized');
})();