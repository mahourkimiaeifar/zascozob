// بررسی وجود کانتینر برای جلوگیری از خطا در صفحات دیگر
const container = document.getElementById('three-canvas-container');
if (!container) return;

// ۱. تنظیمات اولیه صحنه
const scene = new THREE.Scene();
// اضافه کردن مه ملایم برای عمق دادن به صحنه
scene.fog = new THREE.FogExp2(0x0a0a0c, 0.002);

const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
camera.position.z = 5;

const renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true });
renderer.setSize(window.innerWidth, window.innerHeight);
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2)); // بهینه‌سازی برای موبایل
container.appendChild(renderer.domElement);

// ۲. ساخت شیء اصلی (یک چندوجهی با ظاهر صنعتی/مذاب)
const geometry = new THREE.IcosahedronGeometry(2, 2); // شعاع ۲، جزئیات ۲

// متریال وایرفریم (شبکه‌ای) به رنگ نارنجی مذاب
const materialWire = new THREE.MeshBasicMaterial({ 
    color: 0xff6b00, 
    wireframe: true, 
    transparent: true, 
    opacity: 0.3 
});

// متریال داخلی برای درخشش
const materialCore = new THREE.MeshPhongMaterial({
    color: 0x141419,
    emissive: 0xff4500,
    emissiveIntensity: 0.2,
    shininess: 100,
    flatShading: true
});

const meshWire = new THREE.Mesh(geometry, materialWire);
const meshCore = new THREE.Mesh(geometry, materialCore);

const group = new THREE.Group();
group.add(meshWire);
group.add(meshCore);
scene.add(group);

// ۳. اضافه کردن ذرات معلق (Particles) در پس‌زمینه
const particlesGeometry = new THREE.BufferGeometry();
const particlesCount = 700;
const posArray = new Float32Array(particlesCount * 3);

for(let i = 0; i < particlesCount * 3; i++) {
    // پخش کردن ذرات در یک فضای بزرگ
    posArray[i] = (Math.random() - 0.5) * 15;
}

particlesGeometry.setAttribute('position', new THREE.BufferAttribute(posArray, 3));
const particlesMaterial = new THREE.PointsMaterial({
    size: 0.02,
    color: 0xffaa00,
    transparent: true,
    opacity: 0.8,
    blending: THREE.AdditiveBlending
});

const particlesMesh = new THREE.Points(particlesGeometry, particlesMaterial);
scene.add(particlesMesh);

// ۴. نورپردازی
const ambientLight = new THREE.AmbientLight(0xffffff, 0.5);
scene.add(ambientLight);

const pointLight = new THREE.PointLight(0xff6b00, 2, 50);
pointLight.position.set(5, 5, 5);
scene.add(pointLight);

const pointLight2 = new THREE.PointLight(0x0088ff, 1, 50); // نور آبی ملایم برای کنتراست
pointLight2.position.set(-5, -5, 5);
scene.add(pointLight2);

// ۵. تعامل با موس (Parallax Effect)
let mouseX = 0;
let mouseY = 0;
let targetX = 0;
let targetY = 0;

const windowHalfX = window.innerWidth / 2;
const windowHalfY = window.innerHeight / 2;

document.addEventListener('mousemove', (event) => {
    mouseX = (event.clientX - windowHalfX);
    mouseY = (event.clientY - windowHalfY);
});

// ۶. حلقه انیمیشن
const clock = new THREE.Clock();

function animate() {
    requestAnimationFrame(animate);
    const elapsedTime = clock.getElapsedTime();

    // چرخش آرام شیء اصلی
    group.rotation.y += 0.003;
    group.rotation.x += 0.001;

    // ضربان (Pulsing) ملایم برای القای حس "مذاب" بودن
    const scale = 1 + Math.sin(elapsedTime * 1.5) * 0.03;
    group.scale.set(scale, scale, scale);

    // چرخش ذرات پس‌زمینه
    particlesMesh.rotation.y = -elapsedTime * 0.05;
    particlesMesh.rotation.x = elapsedTime * 0.02;

    // حرکت نرم دوربین بر اساس موس (Parallax)
    targetX = mouseX * 0.001;
    targetY = mouseY * 0.001;
    
    group.rotation.y += 0.05 * (targetX - group.rotation.y);
    group.rotation.x += 0.05 * (targetY - group.rotation.x);

    renderer.render(scene, camera);
}

animate();

// ۷. واکنش‌گرایی (Responsive)
window.addEventListener('resize', () => {
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
});