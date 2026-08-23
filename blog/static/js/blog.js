(function(){
  "use strict";
  
  function getCookie(n){var v='; '+document.cookie;var p=v.split('; '+n+'=');if(p.length===2)return p.pop().split(';').shift();return '';}
  
  // لایک پست
  document.querySelectorAll('.like-btn').forEach(function(btn){
    btn.addEventListener('click',function(){
      var id=btn.dataset.id;
      fetch('/blog/api/posts/'+id+'/like/',{method:'POST',headers:{'X-CSRFToken':getCookie('csrftoken')}})
        .then(function(r){return r.json()})
        .then(function(d){
          if(d.success){
            btn.querySelector('.count').textContent=d.likes;
            btn.style.transform='scale(1.1)';
            setTimeout(function(){btn.style.transform=''},300);
          }
        });
    });
  });
  
  // لایک/دیسلایک کامنت
  document.querySelectorAll('.like-comment-btn').forEach(function(btn){
    btn.addEventListener('click',function(){
      var id=btn.dataset.id;
      fetch('/blog/api/comments/'+id+'/like/',{method:'POST',headers:{'X-CSRFToken':getCookie('csrftoken')}})
        .then(function(r){return r.json()})
        .then(function(d){if(d.success)btn.querySelector('span').textContent=d.likes});
    });
  });
  
  document.querySelectorAll('.dislike-comment-btn').forEach(function(btn){
    btn.addEventListener('click',function(){
      var id=btn.dataset.id;
      fetch('/blog/api/comments/'+id+'/dislike/',{method:'POST',headers:{'X-CSRFToken':getCookie('csrftoken')}})
        .then(function(r){return r.json()})
        .then(function(d){if(d.success)btn.querySelector('span').textContent=d.dislikes});
    });
  });
  
  // ارسال کامنت
  var form=document.getElementById('commentForm');
  if(form){
    form.addEventListener('submit',function(e){
      e.preventDefault();
      var fd=new FormData(form);
      fetch('/blog/api/comments/'+POST_ID+'/submit/',{method:'POST',body:fd,headers:{'X-CSRFToken':getCookie('csrftoken')}})
        .then(function(r){return r.json()})
        .then(function(d){
          if(d.success){
            alert(d.message);
            form.reset();
          }else{
            alert('خطا: '+d.error);
          }
        });
    });
  }
  
  // لود کامنت بیشتر
  var loadBtn=document.getElementById('loadMoreBtn');
  if(loadBtn){
    loadBtn.addEventListener('click',function(){
      var offset=parseInt(loadBtn.dataset.offset);
      var fd=new FormData();
      fd.append('offset',offset);
      fetch('/blog/api/comments/'+POST_ID+'/load/',{method:'POST',body:fd,headers:{'X-CSRFToken':getCookie('csrftoken')}})
        .then(function(r){return r.json()})
        .then(function(d){
          var list=document.getElementById('commentsList');
          d.comments.forEach(function(c){
            var div=document.createElement('div');
            div.className='comment-card';
            div.dataset.id=c.id;
            div.innerHTML='<div class="comment-header"><div class="comment-avatar">'+c.name[0]+'</div><div class="comment-info"><strong>'+c.name+'</strong><small>'+c.created+'</small></div></div><div class="comment-body">'+c.text+'</div><div class="comment-actions"><button class="comment-action like-comment-btn" data-id="'+c.id+'">👍 <span>'+c.likes+'</span></button><button class="comment-action dislike-comment-btn" data-id="'+c.id+'">👎 <span>'+c.dislikes+'</span></button></div>';
            list.appendChild(div);
          });
          loadBtn.dataset.offset=offset+d.comments.length;
          if(!d.has_more)loadBtn.style.display='none';
        });
    });
  }
  
  console.log('✅ Blog initialized');
})();