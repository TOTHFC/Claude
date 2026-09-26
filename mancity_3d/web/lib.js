// 공용 도구: 수학·재질·글자 텍스처·캐릭터·소품
import * as THREE from './three.module.js';
import { RoomEnvironment } from './RoomEnvironment.js';
let ENV = null;
export function setRenderer(r) { ENV = new THREE.PMREMGenerator(r).fromScene(new RoomEnvironment(), 0.04).texture; }

export const clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
export const P = (t, t0, d = 0.5) => clamp((t - t0) / d);
export const lerp = (a, b, k) => a + (b - a) * k;
export const eio = k => (k < 0.5 ? 4 * k * k * k : 1 - Math.pow(-2 * k + 2, 3) / 2);
export const eout = k => 1 - Math.pow(1 - k, 3);
export const ein = k => k * k * k;
export const back = k => { const c = 1.8; return 1 + (c + 1) * Math.pow(k - 1, 3) + c * Math.pow(k - 1, 2); };
export const elastic = k => (k <= 0 ? 0 : k >= 1 ? 1 : Math.pow(2, -9 * k) * Math.sin((k * 10 - 0.75) * (2 * Math.PI) / 3) + 1);
export function rng(seed) {
  return () => {
    seed |= 0; seed = (seed + 0x6d2b79f5) | 0;
    let t = Math.imul(seed ^ (seed >>> 15), 1 | seed);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

export function mat(c, r = 0.5, m = 0, extra = {}) {
  return new THREE.MeshStandardMaterial({ color: c, roughness: r, metalness: m, ...extra });
}
export const GOLD = () => mat(0xf2c14e, 0.28, 0.75);

export function add(parent, geo, material, o = {}) {
  const m = new THREE.Mesh(geo, material);
  m.position.set(o.x || 0, o.y || 0, o.z || 0);
  m.scale.set(o.sx ?? 1, o.sy ?? 1, o.sz ?? 1);
  if (o.rx) m.rotation.x = o.rx;
  if (o.ry) m.rotation.y = o.ry;
  if (o.rz) m.rotation.z = o.rz;
  m.castShadow = o.cast ?? true;
  m.receiveShadow = o.recv ?? true;
  parent.add(m);
  return m;
}
export function group(parent, x = 0, y = 0, z = 0) {
  const g = new THREE.Group();
  g.position.set(x, y, z);
  if (parent) parent.add(g);
  return g;
}
export const SPH = new THREE.SphereGeometry(1, 48, 32);
export const SPH_LO = new THREE.SphereGeometry(1, 20, 14);

// ---------------------------------------------------------------- 글자 텍스처
export function textCanvas(lines, o = {}) {
  const size = o.size || 120, weight = o.weight || 900, pad = o.pad ?? 40, lh = o.lh || 1.2;
  const c = document.createElement('canvas');
  const g = c.getContext('2d');
  g.font = `${weight} ${size}px Pretendard`;
  const arr = Array.isArray(lines) ? lines : [lines];
  const sizes = arr.map((_, i) => (o.sizes ? o.sizes[i] : size));
  let w = 0;
  arr.forEach((s, i) => { g.font = `${weight} ${sizes[i]}px Pretendard`; w = Math.max(w, g.measureText(s).width); });
  const hsum = sizes.reduce((a, b) => a + b * lh, 0);
  c.width = Math.ceil(o.w || w + pad * 2);
  c.height = Math.ceil(o.h || hsum + pad * 2);
  const g2 = c.getContext('2d');
  if (o.bg) {
    g2.fillStyle = o.bg;
    const r = o.radius ?? 36;
    g2.beginPath(); g2.roundRect(0, 0, c.width, c.height, r); g2.fill();
    if (o.border) { g2.lineWidth = o.borderW || 12; g2.strokeStyle = o.border; g2.beginPath(); g2.roundRect(6, 6, c.width - 12, c.height - 12, r); g2.stroke(); }
  }
  let y = (c.height - hsum) / 2;
  arr.forEach((s, i) => {
    g2.font = `${weight} ${sizes[i]}px Pretendard`;
    g2.fillStyle = (o.colors && o.colors[i]) || o.color || '#1b2233';
    g2.textAlign = 'center'; g2.textBaseline = 'middle';
    g2.fillText(s, c.width / 2, y + sizes[i] * lh / 2);
    y += sizes[i] * lh;
  });
  return c;
}
export function label(parent, lines, h, o = {}) {
  const c = textCanvas(lines, o);
  const tex = new THREE.CanvasTexture(c);
  tex.colorSpace = THREE.SRGBColorSpace;
  tex.anisotropy = 8;
  const m = new THREE.Mesh(new THREE.PlaneGeometry((h * c.width) / c.height, h),
    o.lit ? new THREE.MeshStandardMaterial({ map: tex, transparent: true, roughness: 0.8 })
      : new THREE.MeshBasicMaterial({ map: tex, transparent: true, toneMapped: false }));
  m.position.set(o.x || 0, o.y || 0, o.z || 0);
  if (o.ry) m.rotation.y = o.ry;
  if (o.rx) m.rotation.x = o.rx;
  if (o.rz) m.rotation.z = o.rz;
  m.castShadow = !!o.cast;
  if (parent) parent.add(m);
  return m;
}

// ---------------------------------------------------------------- 캐릭터 공통 얼굴
function face(par, o) {
  const surfZ = (x, y) => o.sz * Math.sqrt(Math.max(0, 1 - (x / o.sx) ** 2 - (y / o.sy) ** 2));
  const f = { eyes: [], pupils: [], brows: [], lids: [] };
  for (const s of [-1, 1]) {
    const ex = s * o.eyeX, ey = o.eyeY, r = o.eyeR;
    const eg = group(par, ex, o.cy + ey, surfZ(ex, ey) - r * 0.35);
    eg.rotation.y = s * 0.18;
    add(eg, SPH, mat(0xffffff, 0.25), { sx: r, sy: r * 1.12, sz: r * 0.75 });
    const pg = group(eg, 0, 0, r * 0.55);
    if (o.iris) add(pg, SPH, mat(o.iris, 0.3), { sx: r * 0.72, sy: r * 0.72, sz: r * 0.3, cast: false });
    add(pg, SPH, mat(0x141824, 0.2), { sx: r * 0.46, sy: r * 0.5, sz: r * 0.3, z: r * 0.06, cast: false });
    add(pg, SPH_LO, mat(0xffffff, 0.1, 0, { emissive: 0xffffff, emissiveIntensity: 0.6 }),
      { sx: r * 0.14, sy: r * 0.14, sz: r * 0.1, x: r * 0.16, y: r * 0.2, z: r * 0.22, cast: false });
    // 눈꺼풀(몸 색 반구) ─ 깜빡임과 반쯤 감은 눈
    const lid = add(eg, new THREE.SphereGeometry(1, 32, 16, 0, Math.PI * 2, 0, Math.PI / 2), mat(o.lid, 0.5),
      { sx: r * 1.06, sy: r * 1.18, sz: r * 0.8, cast: false });
    lid.rotation.x = -Math.PI / 2 - 0.1;
    lid.visible = false;
    const brow = add(par, new THREE.CapsuleGeometry(r * 0.16, r * 0.9, 4, 12), mat(o.brow ?? 0x1d2433, 0.6),
      { x: ex, y: o.cy + ey + r * 1.45, z: surfZ(ex, ey + r * 1.4) + 0.02, rz: Math.PI / 2, cast: false });
    f.eyes.push(eg); f.pupils.push(pg); f.brows.push(brow); f.lids.push(lid);
  }
  const my = o.mouthY;
  f.mouth = add(par, SPH, mat(0x3b0d1c, 0.6),
    { x: 0, y: o.cy + my, z: surfZ(0, my) - 0.035, sx: o.mouthW, sy: 0.04, sz: 0.06, cast: false });
  f.set = (s) => {
    const open = s.open || 0;
    f.mouth.scale.y = 0.035 + open * (o.mouthH || 0.16) + (s.smile ? 0.03 : 0);
    f.mouth.scale.x = o.mouthW * (1 + (s.smile || 0) * 0.35 - open * 0.15);
    const lx = s.look ? s.look[0] : 0, ly = s.look ? s.look[1] : 0;
    for (let i = 0; i < 2; i++) {
      f.pupils[i].position.x = lx * o.eyeR * 0.32;
      f.pupils[i].position.y = ly * o.eyeR * 0.3;
      const b = s.blink || 0; // 0 눈뜸 ~ 1 감음
      f.lids[i].visible = b > 0.02;
      f.lids[i].rotation.x = -Math.PI / 2 - 0.1 + (1 - b) * -1.4;
      f.eyes[i].scale.setScalar(s.eyeScale || 1);
      const sgn = i === 0 ? 1 : -1;
      f.brows[i].rotation.z = Math.PI / 2 + sgn * (s.brow || 0);
      f.brows[i].position.y = o.cy + o.eyeY + o.eyeR * (1.45 + (s.browUp || 0) * 0.6) * (s.eyeScale || 1);
    }
  };
  return f;
}

function autoBlink(t, seed) {
  const period = 3.3 + (seed % 5) * 0.37;
  const ph = (t + seed * 0.71) % period;
  return ph < 0.14 ? Math.sin((ph / 0.14) * Math.PI) : 0;
}

// 둥근 몸 캐릭터(시티·돈 가방·에버튼·감독)
export function blob(o) {
  const root = new THREE.Group();
  const body = group(root);
  const sx = o.sx || 1, sy = o.sy || 1.12, sz = o.sz || 0.95, cy = o.cy || 1.35;
  add(body, SPH, mat(o.color, o.rough ?? 0.42), { y: cy, sx, sy, sz });
  if (o.belly) add(body, SPH, mat(o.belly, 0.5), { y: cy - sy * 0.62, z: sz * 0.36, sx: sx * 0.62, sy: sy * 0.4, sz: sz * 0.5 });
  const fc = face(body, { sx, sy, sz, cy, eyeX: o.eyeX || 0.33, eyeY: o.eyeY ?? 0.3, eyeR: o.eyeR || 0.25,
    mouthY: o.mouthY ?? -0.12, mouthW: o.mouthW || 0.24, mouthH: o.mouthH || 0.2, lid: o.color, iris: o.iris, brow: o.browColor });
  const arms = [];
  for (const s of [-1, 1]) {
    const pv = group(body, s * sx * 0.9, cy - 0.1, 0);
    add(pv, new THREE.CapsuleGeometry(0.12, 0.5, 6, 12), mat(o.arm || o.color, 0.45), { y: -0.36 });
    add(pv, SPH, mat(o.hand || o.arm || o.color, 0.45), { y: -0.72, sx: 0.17, sy: 0.17, sz: 0.17 });
    pv.rotation.z = s * 0.35;
    arms.push(pv);
  }
  for (const s of [-1, 1]) add(body, SPH, mat(o.foot || 0x23324f, 0.5), { x: s * 0.42, y: 0.12, z: 0.18, sx: 0.3, sy: 0.15, sz: 0.42 });
  const ch = { root, body, face: fc, arms, cy, seed: o.seed || 1, height: cy + sy };
  ch.update = (t, s = {}) => {
    const talk = s.talk || 0;
    const breathe = Math.sin(t * 2.6 + ch.seed) * 0.012;
    body.scale.set(1 - breathe * 0.5 - (s.squash || 0) * 0.3, 1 + breathe + talk * 0.03 + (s.squash || 0) * -1, 1);
    body.position.y = (s.hop || 0);
    body.rotation.z = (s.lean || 0) + talk * Math.sin(t * 9) * 0.03;
    body.rotation.x = s.tilt || 0;
    fc.set({ open: talk, look: s.look, blink: Math.max(s.lid || 0, autoBlink(t, ch.seed)), brow: s.brow, browUp: s.browUp,
      smile: s.smile, eyeScale: s.eyeScale });
    const wave = talk * Math.sin(t * 7 + 1) * 0.25;
    arms[0].rotation.z = -(s.armL ?? 0.35) - wave * 0.5;
    arms[1].rotation.z = (s.armR ?? 0.35) + wave;
    arms[0].rotation.x = s.armLx || 0;
    arms[1].rotation.x = s.armRx || 0;
  };
  return ch;
}

export function makeCity() {
  const c = blob({ color: 0x6cabdd, belly: 0xeaf4fb, foot: 0x1c2c4c, seed: 3 });
  // 금목걸이와 £ 메달
  add(c.body, new THREE.CylinderGeometry(0.17, 0.17, 0.05, 32), GOLD(), { y: c.cy - 0.62, z: 0.83, rx: Math.PI / 2 - 0.35 });
  label(c.body, '£', 0.22, { color: '#7a5a00', size: 140, pad: 10, x: 0, y: c.cy - 0.61, z: 0.865, rx: -0.35 });
  // 이마 위 선글라스
  const sg = group(c.body, 0, c.cy + 0.83, 0.42);
  sg.rotation.x = -0.5;
  for (const s of [-1, 1]) add(sg, SPH, mat(0x0d1220, 0.15, 0.3), { x: s * 0.24, sx: 0.2, sy: 0.13, sz: 0.06 });
  add(sg, new THREE.BoxGeometry(0.25, 0.04, 0.04), mat(0x0d1220, 0.2), {});
  c.shades = sg;
  c.shadesOn = (k) => { // 0 이마 위 ~ 1 눈 위
    sg.position.set(0, c.cy + lerp(0.83, 0.26, k), lerp(0.42, 0.98, k));
    sg.rotation.x = lerp(-0.5, 0, k);
  };
  c.shadesOn(0);
  return c;
}

export function makeBag() {
  const c = blob({ color: 0xc9a46a, sx: 0.8, sy: 0.78, sz: 0.76, cy: 0.95, eyeR: 0.17, eyeX: 0.24, eyeY: 0.12,
    mouthY: -0.18, mouthW: 0.13, foot: 0x6b4e2a, rough: 0.85, seed: 7 });
  add(c.body, new THREE.CylinderGeometry(0.2, 0.32, 0.3, 24), mat(0xc9a46a, 0.85), { y: 1.78 });
  add(c.body, new THREE.TorusGeometry(0.22, 0.05, 10, 32), mat(0x7a4f1d, 0.7), { y: 1.72, rx: Math.PI / 2 });
  add(c.body, SPH, mat(0xc9a46a, 0.85), { y: 2.0, sx: 0.32, sy: 0.16, sz: 0.3 });
  label(c.body, '£', 0.42, { color: '#6b4a12', size: 160, pad: 6, y: 0.7, z: 0.77, lit: true });
  // 변장: 콧수염 + 실크햇 + 띠
  const dis = group(c.body);
  const mus = group(dis, 0, 0.9, 0.74);
  for (const s of [-1, 1]) add(mus, SPH, mat(0x2b1a10, 0.6), { x: s * 0.13, sx: 0.16, sy: 0.06, sz: 0.06, rz: s * -0.35 });
  const hat = group(dis, 0, 1.92, 0);
  add(hat, new THREE.CylinderGeometry(0.28, 0.28, 0.5, 32), mat(0x14161c, 0.4), { y: 0.25 });
  add(hat, new THREE.CylinderGeometry(0.45, 0.45, 0.04, 32), mat(0x14161c, 0.4), {});
  add(hat, new THREE.CylinderGeometry(0.285, 0.285, 0.1, 32), mat(0xd23b3b, 0.5), { y: 0.08 });
  const sash = label(dis, '스폰서', 0.2, { bg: '#ffffff', color: '#b3261e', size: 90, pad: 18, radius: 14,
    y: 0.62, z: 0.78, rz: 0.18, lit: true });
  dis.visible = false;
  c.disguise = dis; c.mustache = mus; c.hat = hat; c.sash = sash;
  return c;
}

export function makeCoach() {
  const c = blob({ color: 0x33456b, belly: 0x3f5580, foot: 0x111827, seed: 11, arm: 0x33456b, hand: 0xf1c7a1 });
  const cap = group(c.body, 0, c.cy + 0.9, 0);
  add(cap, new THREE.SphereGeometry(0.62, 32, 16, 0, Math.PI * 2, 0, Math.PI / 2), mat(0xeeeeee, 0.6), {});
  add(cap, new THREE.CylinderGeometry(0.36, 0.36, 0.04, 24, 1, false, -Math.PI / 2, Math.PI), mat(0xeeeeee, 0.6),
    { z: 0.46, y: 0.02 });
  add(c.body, SPH, mat(0xc0c7d4, 0.3, 0.6), { y: c.cy - 0.55, z: 0.9, sx: 0.08, sy: 0.08, sz: 0.08 });
  return c;
}

export function makeEverton() {
  const c = blob({ color: 0x2747a8, belly: 0xdfe6f7, foot: 0x14214d, seed: 5 });
  c.root.scale.setScalar(0.85);
  return c;
}

export function makeLion() {
  const root = new THREE.Group();
  const body = group(root);
  const suit = 0x3d195b;
  add(body, new THREE.CapsuleGeometry(0.62, 0.8, 8, 24), mat(suit, 0.55), { y: 1.35, sz: 0.8 });
  add(body, new THREE.ConeGeometry(0.28, 0.5, 3), mat(0xffffff, 0.6), { y: 1.95, z: 0.4, rx: Math.PI, sz: 0.3 });
  add(body, new THREE.BoxGeometry(0.1, 0.42, 0.05), mat(0xe03a6a, 0.5), { y: 1.72, z: 0.52 });
  for (const s of [-1, 1]) add(body, new THREE.CapsuleGeometry(0.2, 0.55, 6, 12), mat(0x241036, 0.6), { x: s * 0.28, y: 0.45 });
  for (const s of [-1, 1]) add(body, SPH, mat(0x111111, 0.4), { x: s * 0.28, y: 0.12, z: 0.1, sx: 0.24, sy: 0.12, sz: 0.34 });
  const head = group(body, 0, 2.62, 0);
  const maneMat = mat(0xb8651f, 0.8);
  for (let i = 0; i < 18; i++) {
    const a = (i / 18) * Math.PI * 2;
    add(head, SPH, maneMat, { x: Math.cos(a) * 0.72, y: Math.sin(a) * 0.72, z: -0.18, sx: 0.36, sy: 0.36, sz: 0.3 });
  }
  add(head, SPH, maneMat, { z: -0.3, sx: 0.8, sy: 0.8, sz: 0.4 });
  add(head, SPH, mat(0xe8a33d, 0.55), { sx: 0.72, sy: 0.7, sz: 0.66 });
  for (const s of [-1, 1]) add(head, SPH, mat(0xe8a33d, 0.55), { x: s * 0.52, y: 0.55, sx: 0.17, sy: 0.17, sz: 0.1 });
  add(head, SPH, mat(0xfff1d6, 0.6), { y: -0.24, z: 0.5, sx: 0.36, sy: 0.24, sz: 0.24 });
  add(head, SPH, mat(0x3b2416, 0.4), { y: -0.1, z: 0.72, sx: 0.12, sy: 0.08, sz: 0.07 });
  const fc = face(head, { sx: 0.72, sy: 0.7, sz: 0.66, cy: 0, eyeX: 0.25, eyeY: 0.14, eyeR: 0.13, mouthY: -0.42,
    mouthW: 0.13, mouthH: 0.1, lid: 0xe8a33d, brow: 0x6b3a12 });
  // 안경
  for (const s of [-1, 1]) {
    const e = fc.eyes[s < 0 ? 0 : 1].position;
    add(head, new THREE.TorusGeometry(0.17, 0.022, 8, 32), mat(0x1a1a1a, 0.3), { x: e.x, y: e.y, z: e.z + 0.1, cast: false });
  }
  add(head, new THREE.BoxGeometry(0.16, 0.025, 0.025), mat(0x1a1a1a, 0.3), { y: fc.eyes[0].position.y, z: fc.eyes[0].position.z + 0.12 });
  // 흰 수염(세월이 흐르면 자란다)
  const beard = add(head, new THREE.ConeGeometry(0.2, 0.5, 16), mat(0xf2f2f2, 0.9), { y: -0.62, z: 0.4, rx: Math.PI });
  beard.scale.set(0.01, 0.01, 0.01);
  const arms = [];
  for (const s of [-1, 1]) {
    const pv = group(body, s * 0.62, 1.85, 0);
    add(pv, new THREE.CapsuleGeometry(0.14, 0.62, 6, 12), mat(suit, 0.55), { y: -0.4 });
    add(pv, SPH, mat(0xe8a33d, 0.55), { y: -0.82, sx: 0.17, sy: 0.17, sz: 0.17 });
    pv.rotation.z = s * 0.25;
    arms.push(pv);
  }
  // 오른손 클립보드
  const clip = group(arms[1], 0.05, -0.85, 0.2);
  add(clip, new THREE.BoxGeometry(0.5, 0.66, 0.04), mat(0x8a5a2b, 0.7), {});
  add(clip, new THREE.BoxGeometry(0.42, 0.56, 0.01), mat(0xffffff, 0.8), { z: 0.025 });
  clip.rotation.x = -0.3;
  const ch = { root, body, head, face: fc, arms, seed: 9, mane: maneMat, beard, clip, height: 3.4 };
  ch.update = (t, s = {}) => {
    const talk = s.talk || 0;
    const br = Math.sin(t * 2.2 + 1) * 0.01;
    body.scale.y = 1 + br;
    body.position.y = s.hop || 0;
    head.rotation.z = talk * Math.sin(t * 8) * 0.04 + (s.headTilt || 0);
    head.rotation.x = (s.nod || 0) + talk * Math.sin(t * 6) * 0.03;
    head.rotation.y = s.headTurn || 0;
    fc.set({ open: talk, look: s.look, blink: Math.max(s.lid || 0, autoBlink(t, 9)), brow: s.brow, browUp: s.browUp,
      eyeScale: s.eyeScale });
    arms[0].rotation.z = -(s.armL ?? 0.25);
    arms[1].rotation.z = (s.armR ?? 0.25) + talk * Math.sin(t * 6) * 0.12;
    arms[0].rotation.x = s.armLx || 0;
    arms[1].rotation.x = s.armRx || 0;
  };
  return ch;
}

export function makeOwl(seed = 2) {
  const root = new THREE.Group();
  const body = group(root);
  const sx = 0.9, sy = 1.15, sz = 0.85, cy = 1.35;
  add(body, SPH, mat(0x8b5e3c, 0.7), { y: cy, sx, sy, sz });
  add(body, SPH, mat(0xdcbf94, 0.75), { y: cy + 0.28, z: 0.3, sx: 0.72, sy: 0.6, sz: 0.62 });
  const fc = face(body, { sx, sy, sz, cy, eyeX: 0.3, eyeY: 0.3, eyeR: 0.27, mouthY: -0.08, mouthW: 0.08, mouthH: 0.06,
    lid: 0x8b5e3c, iris: 0xf2b705, brow: 0x3d2614 });
  add(body, new THREE.ConeGeometry(0.1, 0.26, 16), mat(0xe58a1f, 0.4), { y: cy + 0.05, z: 0.9, rx: Math.PI / 2 + 0.5 });
  for (const s of [-1, 1]) add(body, new THREE.ConeGeometry(0.14, 0.35, 12), mat(0x6e4529, 0.7), { x: s * 0.5, y: cy + 1.08, rz: -s * 0.35 });
  // 판사 가발
  const wig = mat(0xf4f1ea, 0.9);
  for (let i = 0; i < 7; i++) add(body, SPH, wig, { x: -0.48 + i * 0.16, y: cy + 1.02, z: 0.1, sx: 0.16, sy: 0.14, sz: 0.3 });
  for (const s of [-1, 1]) for (let j = 0; j < 3; j++)
    add(body, new THREE.TorusGeometry(0.11, 0.06, 10, 20), wig, { x: s * 0.86, y: cy + 0.55 - j * 0.24, z: 0.05, ry: Math.PI / 2 });
  // 법복
  add(body, new THREE.CylinderGeometry(0.78, 1.0, 1.2, 32, 1, true), mat(0x15151c, 0.6, 0, { side: THREE.DoubleSide }), { y: 0.72 });
  add(body, new THREE.BoxGeometry(0.24, 0.3, 0.05), mat(0xffffff, 0.8), { y: 1.2, z: 0.82 });
  const arms = [];
  for (const s of [-1, 1]) {
    const pv = group(body, s * 0.85, cy, 0);
    add(pv, SPH, mat(0x6e4529, 0.7), { y: -0.35, sx: 0.16, sy: 0.45, sz: 0.2 });
    pv.rotation.z = s * 0.3;
    arms.push(pv);
  }
  const gavel = group(arms[1], 0, -0.7, 0.25);
  add(gavel, new THREE.CylinderGeometry(0.035, 0.035, 0.5, 12), mat(0x5a3718, 0.5), { z: 0.2, rx: Math.PI / 2 });
  add(gavel, new THREE.CylinderGeometry(0.1, 0.1, 0.32, 20), mat(0x6b4020, 0.45), { z: 0.45, rz: Math.PI / 2 });
  gavel.visible = false;
  const ch = { root, body, face: fc, arms, gavel, seed, height: 2.6 };
  ch.update = (t, s = {}) => {
    const talk = s.talk || 0;
    body.scale.y = 1 + Math.sin(t * 2 + seed) * 0.01;
    body.rotation.z = (s.lean || 0) + talk * Math.sin(t * 7) * 0.025;
    fc.set({ open: talk, look: s.look, blink: Math.max(s.lid || 0, autoBlink(t, seed * 3)), brow: s.brow ?? 0.25, browUp: s.browUp, eyeScale: s.eyeScale });
    arms[0].rotation.z = -(s.armL ?? 0.3);
    arms[1].rotation.z = s.armR ?? 0.3;
    arms[1].rotation.x = s.armRx || 0;
  };
  return ch;
}

// ---------------------------------------------------------------- 소품
export function paperStack(parent, n, o = {}) {
  const g = group(parent, o.x || 0, o.y || 0, o.z || 0);
  const r = rng(o.seed || 4);
  const th = (o.h || 1.6) / n;
  const pm = mat(0xfbfbf6, 0.85);
  const geo = new THREE.BoxGeometry(o.w || 1.1, th * 0.9, o.d || 0.8);
  for (let i = 0; i < n; i++)
    add(g, geo, pm, { y: th * (i + 0.5), x: (r() - 0.5) * 0.08, z: (r() - 0.5) * 0.06, ry: (r() - 0.5) * 0.12 });
  if (o.text) {
    const band = add(g, new THREE.BoxGeometry((o.w || 1.1) + 0.16, (o.h || 1.6) * 0.18, (o.d || 0.8) + 0.16), mat(0xc62828, 0.5),
      { y: (o.h || 1.6) * 0.55 });
    void band;
    label(g, o.text, (o.h || 1.6) * 0.14, { color: '#ffffff', size: 110, pad: 8, y: (o.h || 1.6) * 0.55, z: (o.d || 0.8) / 2 + 0.09 });
  }
  return g;
}

export function trophy(parent, o = {}) {
  const g = group(parent, o.x || 0, o.y || 0, o.z || 0);
  const pts = [];
  for (let i = 0; i <= 12; i++) { const k = i / 12; pts.push(new THREE.Vector2(0.05 + Math.sin(k * Math.PI * 0.5) * 0.32, 0.45 + k * 0.5)); }
  const gm = GOLD();
  add(g, new THREE.LatheGeometry(pts, 32), gm, {});
  add(g, new THREE.CylinderGeometry(0.05, 0.08, 0.3, 16), gm, { y: 0.3 });
  add(g, new THREE.CylinderGeometry(0.2, 0.22, 0.14, 24), gm, { y: 0.1 });
  for (const s of [-1, 1]) add(g, new THREE.TorusGeometry(0.13, 0.03, 8, 20), gm, { x: s * 0.36, y: 0.75 });
  g.scale.setScalar(o.s || 1);
  if (o.ry) g.rotation.y = o.ry;
  return g;
}

export function balance(parent, o = {}) {
  const g = group(parent, o.x || 0, 0, o.z || 0);
  const metal = mat(0xb9975b, 0.35, 0.7);
  add(g, new THREE.CylinderGeometry(0.8, 1.0, 0.25, 40), mat(0x5b4636, 0.6), { y: 0.12 });
  add(g, new THREE.CylinderGeometry(0.1, 0.12, o.h || 3.4, 20), metal, { y: (o.h || 3.4) / 2 });
  const piv = group(g, 0, o.h || 3.4, 0);
  const L = o.L || 2.5;
  add(piv, new THREE.BoxGeometry(L * 2 + 0.3, 0.14, 0.18), metal, {});
  add(g, SPH, metal, { y: (o.h || 3.4) + 0.05, sx: 0.2, sy: 0.2, sz: 0.2 });
  const pans = [];
  for (const s of [-1, 1]) {
    const pan = group(g);
    const drop = o.drop || 1.4;
    for (let k = 0; k < 3; k++) {
      const a = (k / 3) * Math.PI * 2;
      const sx = Math.cos(a) * 0.8, sz = Math.sin(a) * 0.8;
      const len = Math.hypot(drop, 0.8);
      const m = add(pan, new THREE.CylinderGeometry(0.015, 0.015, len, 6), mat(0x333333, 0.5), { cast: false });
      m.position.set(sx / 2, drop / 2, sz / 2);
      m.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), new THREE.Vector3(-sx, drop, -sz).normalize());
    }
    add(pan, new THREE.CylinderGeometry(0.95, 0.7, 0.16, 40), metal, {});
    pans.push({ g: pan, side: s, drop });
  }
  const lab = [];
  for (const [i, txt, col] of [[0, o.left || '수입', '#1f6fd1'], [1, o.right || '지출', '#c0392b']])
    lab.push(label(pans[i].g, txt, 0.42, { bg: col, color: '#ffffff', size: 100, pad: 22, radius: 24, y: -0.45, z: 0.75 }));
  const bal = { g, piv, pans, L, labels: lab };
  bal.set = (ang) => {
    piv.rotation.z = ang;
    for (const p of pans) {
      const x = p.side * L * Math.cos(ang), y = (o.h || 3.4) + p.side * L * Math.sin(ang);
      p.g.position.set(x, y - p.drop, 0);
    }
  };
  bal.set(0);
  return bal;
}

export function envelope(parent, o = {}) {
  const g = group(parent, o.x || 0, o.y || 0, o.z || 0);
  const w = o.w || 0.6, h = o.h || 0.4;
  add(g, new THREE.BoxGeometry(w, h, 0.04), mat(o.color || 0xf7f2e6, 0.8), {});
  const flap = add(g, new THREE.ConeGeometry(w * 0.72, h * 0.5, 3), mat(o.flap || 0xe9dfc8, 0.8), { y: h * 0.25, z: 0.025, rz: Math.PI, sz: 0.05 });
  flap.rotation.y = Math.PI / 6 * 0;
  add(g, new THREE.CylinderGeometry(w * 0.09, w * 0.09, 0.03, 20), mat(0xb3261e, 0.4), { y: h * 0.02, z: 0.04, rx: Math.PI / 2 });
  if (o.text) label(g, o.text, h * 0.26, { color: '#3a2a10', size: 90, pad: 6, y: -h * 0.3, z: 0.03 });
  return g;
}

export function smokePuffs(parent, n = 9, seed = 3) {
  const g = group(parent);
  const r = rng(seed);
  const m = mat(0xffffff, 0.9, 0, { transparent: true, opacity: 1 });
  const ps = [];
  for (let i = 0; i < n; i++) {
    const p = add(g, SPH_LO, m, { cast: false });
    ps.push({ p, dir: new THREE.Vector3(r() - 0.5, r() * 0.8 + 0.1, r() - 0.5).normalize(), s: 0.25 + r() * 0.3 });
  }
  g.visible = false;
  return {
    g, set(k) { // 0~1
      g.visible = k > 0 && k < 1;
      m.opacity = 1 - k;
      for (const q of ps) {
        q.p.position.copy(q.dir).multiplyScalar(eout(k) * 1.1);
        q.p.scale.setScalar(q.s * (0.4 + eout(k) * 1.4));
      }
    },
  };
}

export function confetti(parent, n, seed, box) {
  const r = rng(seed);
  const cols = [0x3987e5, 0xd95926, 0x199e70, 0xc98500, 0xd55181, 0x6cabdd];
  const geo = new THREE.BoxGeometry(0.12, 0.2, 0.01);
  const ms = cols.map(c => mat(c, 0.6, 0, { side: THREE.DoubleSide }));
  const ps = [];
  for (let i = 0; i < n; i++) {
    const m = add(parent, geo, ms[i % ms.length], { cast: false });
    ps.push({ m, x: box[0] + r() * (box[1] - box[0]), z: box[2] + r() * (box[3] - box[2]), vy: 2 + r() * 4,
      vx: (r() - 0.5) * 2, sp: r() * 10, y0: box[4] });
    m.visible = false;
  }
  return {
    set(dt) {
      for (const p of ps) {
        p.m.visible = dt >= 0 && dt < 6;
        if (!p.m.visible) continue;
        const y = p.y0 + p.vy * dt - 2.2 * dt * dt;
        p.m.position.set(p.x + p.vx * dt, Math.max(0.02, y + 0.0), p.z);
        p.m.rotation.set(p.sp + dt * 5, p.sp * 2 + dt * 3, dt * 4);
      }
    },
  };
}

export function snail(parent, o = {}) {
  const g = group(parent, o.x || 0, 0, o.z || 0);
  add(g, new THREE.CapsuleGeometry(0.1, 0.6, 6, 12), mat(0x9ccc65, 0.6), { y: 0.1, rz: Math.PI / 2 });
  add(g, SPH, mat(0x9ccc65, 0.6), { x: 0.4, y: 0.22, sx: 0.12, sy: 0.14, sz: 0.12 });
  for (const s of [-1, 1]) {
    add(g, new THREE.CylinderGeometry(0.015, 0.015, 0.2, 6), mat(0x9ccc65, 0.6), { x: 0.44, y: 0.4, z: s * 0.05, rz: -0.3 });
    add(g, SPH, mat(0x1a1a1a, 0.3), { x: 0.47, y: 0.5, z: s * 0.05, sx: 0.035, sy: 0.035, sz: 0.035 });
  }
  add(g, new THREE.TorusGeometry(0.17, 0.1, 16, 32), mat(0xa0522d, 0.5), { y: 0.32 });
  add(g, SPH, mat(0x8b4513, 0.5), { y: 0.32, sx: 0.12, sy: 0.12, sz: 0.1 });
  g.scale.setScalar(o.s || 1);
  return g;
}

// ---------------------------------------------------------------- 무대 공통
export function stage(o = {}) {
  const sc = new THREE.Scene();
  sc.environment = ENV;
  sc.environmentIntensity = o.env ?? 0.55;
  sc.background = new THREE.Color(o.bg ?? 0xbfe0f7);
  if (o.fog !== false) sc.fog = new THREE.Fog(o.bg ?? 0xbfe0f7, o.fogNear || 22, o.fogFar || 55);
  sc.add(new THREE.HemisphereLight(0xffffff, o.ground ?? 0x8a7a6a, (o.hemi ?? 1.15) * 0.7));
  const key = new THREE.DirectionalLight(o.keyColor ?? 0xfff4e6, o.key ?? 2.2);
  key.position.set(...(o.keyPos || [5, 9, 7]));
  key.castShadow = true;
  key.shadow.mapSize.set(2048, 2048);
  const b = o.shadowBox || 10;
  Object.assign(key.shadow.camera, { left: -b, right: b, top: b, bottom: -b, near: 0.5, far: 40 });
  key.shadow.bias = -0.0004;
  key.shadow.normalBias = 0.02;
  key.shadow.radius = 4;
  if (o.keyTarget) key.target.position.set(...o.keyTarget);
  sc.add(key); sc.add(key.target);
  const rim = new THREE.DirectionalLight(o.rimColor ?? 0xcfe6ff, o.rim ?? 1.0);
  rim.position.set(-6, 5, -6);
  sc.add(rim);
  const floor = add(sc, new THREE.PlaneGeometry(200, 200), mat(o.floor ?? 0xe9dcc8, 0.9), { rx: -Math.PI / 2, cast: false });
  return { sc, key, floor };
}
