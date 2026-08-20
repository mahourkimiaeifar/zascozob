console.log("✅ فایل foundry.js با موفقیت بارگذاری شد.");

const container = document.getElementById("three-canvas-container");
if (!container) {
  console.error("❌ خطا: کانتینر three-canvas-container در صفحه پیدا نشد!");
} else {
  console.log("✅ کانتینر پیدا شد. در حال راه‌اندازی موتور Three.js...");
}

// ۱. تنظیمات اولیه صحنه
const scene = new THREE.Scene();
scene.fog = new THREE.FogExp2(0x0a0a0c, 0.02); // مه غلیظ‌تر برای عمق بیشتر

const camera = new THREE.PerspectiveCamera(
  75,
  window.innerWidth / window.innerHeight,
  0.1,
  1000,
);
camera.position.z = 5;

const renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true });
renderer.setSize(window.innerWidth, window.innerHeight);
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
container.appendChild(renderer.domElement);

// ۲. ساخت شیء اصلی (کره صنعتی درخشان)
const geometry = new THREE.IcosahedronGeometry(2.2, 2);

const materialWire = new THREE.MeshBasicMaterial({
  color: 0xff6b00,
  wireframe: true,
  transparent: true,
  opacity: 0.4,
});

const materialCore = new THREE.MeshPhongMaterial({
  color: 0x141419,
  emissive: 0xff4500,
  emissiveIntensity: 0.4, // درخشش بیشتر
  shininess: 100,
  flatShading: true,
});

const meshWire = new THREE.Mesh(geometry, materialWire);
const meshCore = new THREE.Mesh(geometry, materialCore);

const group = new THREE.Group();
group.add(meshWire);
group.add(meshCore);
scene.add(group);

// ۳. ذرات معلق (Spark/Ember effect)
const particlesGeometry = new THREE.BufferGeometry();
const particlesCount = 1000; // تعداد بیشتر برای جلوه بهتر
const posArray = new Float32Array(particlesCount * 3);

for (let i = 0; i < particlesCount * 3; i++) {
  posArray[i] = (Math.random() - 0.5) * 15;
}

particlesGeometry.setAttribute(
  "position",
  new THREE.BufferAttribute(posArray, 3),
);
const particlesMaterial = new THREE.PointsMaterial({
  size: 0.03,
  color: 0xffaa00,
  transparent: true,
  opacity: 0.8,
  blending: THREE.AdditiveBlending,
});

const particlesMesh = new THREE.Points(particlesGeometry, particlesMaterial);
scene.add(particlesMesh);

// ۴. نورپردازی قوی
const ambientLight = new THREE.AmbientLight(0xffffff, 0.3);
scene.add(ambientLight);

const pointLight = new THREE.PointLight(0xff6b00, 3, 50);
pointLight.position.set(5, 5, 5);
scene.add(pointLight);

const pointLight2 = new THREE.PointLight(0x0088ff, 1.5, 50);
pointLight2.position.set(-5, -5, 5);
scene.add(pointLight2);

// ۵. تعامل با موس
let mouseX = 0,
  mouseY = 0;
const windowHalfX = window.innerWidth / 2;
const windowHalfY = window.innerHeight / 2;

document.addEventListener("mousemove", (event) => {
  mouseX = (event.clientX - windowHalfX) * 0.001;
  mouseY = (event.clientY - windowHalfY) * 0.001;
});

// ۶. حلقه انیمیشن
const clock = new THREE.Clock();

function animate() {
  requestAnimationFrame(animate);
  const elapsedTime = clock.getElapsedTime();

  group.rotation.y += 0.005;
  group.rotation.x += 0.002;

  // افکت ضربان (تپش مذاب)
  const scale = 1 + Math.sin(elapsedTime * 1.5) * 0.04;
  group.scale.set(scale, scale, scale);

  particlesMesh.rotation.y = -elapsedTime * 0.05;

  // حرکت نرم با موس
  group.rotation.y += 0.05 * (mouseX - group.rotation.y);
  group.rotation.x += 0.05 * (mouseY - group.rotation.x);

  renderer.render(scene, camera);
}

animate();
console.log("✅ انیمیشن Three.js شروع شد.");

// ۷. واکنش‌گرایی
window.addEventListener("resize", () => {
  camera.aspect = window.innerWidth / window.innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(window.innerWidth, window.innerHeight);
});
