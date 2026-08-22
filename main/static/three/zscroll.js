/* ═══ زاسکو ذوب — کریدور مهندسی (اسکرول Z) ═══ */
(function () {
  'use strict';
  if (!window.THREE) { console.error('Three.js بارگذاری نشده'); return; }

  const isMobile = window.innerWidth < 768;
  const canvas = document.getElementById('three-canvas');
  if (!canvas) { return; }

  const renderer = new THREE.WebGLRenderer({ canvas: canvas, antialias: true, alpha: true });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, isMobile ? 1.5 : 2));
  renderer.setSize(window.innerWidth, window.innerHeight);

  const scene = new THREE.Scene();
  scene.fog = new THREE.Fog(0x0b0d10, 18, 95);

  const camera = new THREE.PerspectiveCamera(60, window.innerWidth / window.innerHeight, 0.1, 300);
  scene.add(camera);

  const START_Z = 14;
  const END_Z = -94;
  const STEEL = 0x2a3140;
  const ACCENT = 0xff6b00;

  /* ── فریم‌های کریدور (با روشن‌شدن هنگام عبور دوربین) ── */
  const frames = [];
  for (let z = -6; z > -128; z -= 8) {
    const w = 11 + Math.sin(z * 0.15) * 1.5;
    const edges = new THREE.EdgesGeometry(new THREE.BoxGeometry(w, 6.2, 0.02));
    const accent = (Math.abs(z) % 32) < 8;
    const base = accent ? 0.32 : 0.55;
    const frame = new THREE.LineSegments(edges, new THREE.LineBasicMaterial({
      color: accent ? ACCENT : STEEL,
      transparent: true,
      opacity: base
    }));
    frame.position.set(0, 0, z);
    frame.userData.base = base;
    scene.add(frame);
    frames.push(frame);
  }

  /* ── خطوط راهنما ── */
  [-6.5, 6.5].forEach(function (x) {
    const g = new THREE.BufferGeometry().setFromPoints([
      new THREE.Vector3(x, -3.1, 15),
      new THREE.Vector3(x, -3.1, -140)
    ]);
    scene.add(new THREE.Line(g, new THREE.LineBasicMaterial({ color: STEEL, transparent: true, opacity: 0.4 })));
  });

  /* ── گرید فنی ── */
  const grid = new THREE.GridHelper(300, 140, 0x1c2129, 0x12161c);
  grid.position.set(0, -3.1, -60);
  grid.material.transparent = true;
  grid.material.opacity = 0.35;
  scene.add(grid);

  /* ── کره فنی ── */
  const techSphere = new THREE.Mesh(
    new THREE.IcosahedronGeometry(3.1, 1),
    new THREE.MeshBasicMaterial({ color: STEEL, wireframe: true, transparent: true, opacity: 0.22 })
  );
  techSphere.position.set(0, 0, -3);
  scene.add(techSphere);

  /* ── غبار ── */
  const dustGeo = new THREE.BufferGeometry();
  const N = isMobile ? 350 : 800;
  const pos = new Float32Array(N * 3);
  for (let i = 0; i < N * 3; i += 3) {
    pos[i] = (Math.random() - 0.5) * 26;
    pos[i + 1] = (Math.random() - 0.5) * 12;
    pos[i + 2] = 20 - Math.random() * 165;
  }
  dustGeo.setAttribute('position', new THREE.BufferAttribute(pos, 3));
  const dust = new THREE.Points(dustGeo, new THREE.PointsMaterial({
    color: 0x9aa3b2, size: 0.05, transparent: true, opacity: 0.35, depthWrite: false
  }));
  scene.add(dust);

  /* ── رابط و اسکرول ── */
  const scrollSpace = document.getElementById('scroll-space');
  const sections = Array.from(document.querySelectorAll('.z-section'));
  const progressFill = document.getElementById('scroll-progress-fill');
  const scrollHint = document.getElementById('scroll-hint');

  let targetProgress = 0;
  let progress = 0;
  let mx = 0;
  let my = 0;

  function readScroll() {
    const max = scrollSpace.offsetHeight - window.innerHeight;
    targetProgress = Math.min(Math.max(window.scrollY / max, 0), 1);
    document.body.classList.toggle('past-journey', window.scrollY > max + 60);
    if (window.scrollY > 60 && scrollHint) { scrollHint.classList.add('hidden'); }
  }
  window.addEventListener('scroll', readScroll, { passive: true });
  readScroll();

  window.addEventListener('mousemove', function (e) {
    mx = (e.clientX / window.innerWidth - 0.5) * 2;
    my = (e.clientY / window.innerHeight - 0.5) * 2;
  });

  function updateOverlays(camZ) {
    sections.forEach(function (sec) {
      const z = parseFloat(sec.dataset.z);
      const dist = camZ - z;
      let o = THREE.MathUtils.clamp(1 - (Math.abs(dist) - 4) / 14, 0, 1);
      o = o * o * (3 - 2 * o);
      sec.style.opacity = o.toFixed(3);
      sec.style.visibility = o <= 0.01 ? 'hidden' : 'visible';
      sec.style.pointerEvents = o > 0.5 ? 'auto' : 'none';
      const inner = sec.querySelector('.z-inner');
      if (inner) { inner.style.transform = 'translateY(' + (dist * -1.2).toFixed(1) + 'px)'; }
    });
  }

  const clock = new THREE.Clock();

  function animate() {
    requestAnimationFrame(animate);
    const t = clock.getElapsedTime();
    progress += (targetProgress - progress) * 0.06;

    const camZ = START_Z + (END_Z - START_Z) * progress;
    camera.position.z = camZ;
    camera.position.x += (mx * 0.5 - camera.position.x) * 0.04;
    camera.position.y += (-my * 0.35 - camera.position.y) * 0.04;
    camera.lookAt(0, 0, camZ - 20);

    /* روشن‌شدن فریم‌ها هنگام عبور دوربین */
    for (let i = 0; i < frames.length; i++) {
      const f = frames[i];
      const glow = Math.exp(-Math.abs(f.position.z - camZ) / 10) * 0.5;
      f.material.opacity = Math.min(f.userData.base + glow, 0.95);
    }

    techSphere.rotation.y = t * 0.08;
    techSphere.rotation.x = t * 0.03;

    updateOverlays(camZ);
    if (progressFill) { progressFill.style.height = (progress * 100).toFixed(2) + '%'; }
    renderer.render(scene, camera);
  }
  animate();

  window.addEventListener('resize', function () {
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
    readScroll();
  });

  console.log('✅ کریدور مهندسی فعال شد');
})();