// 장면·카메라·화면 위 글자. window.renderAt(t) 가 한 프레임을 그려 JPEG dataURL 로 돌려준다.
import * as THREE from './three.module.js';
import {
  P, clamp, lerp, eio, eout, ein, back, elastic, rng, mat, add, group, SPH, SPH_LO, label, textCanvas,
  makeCity, makeBag, makeCoach, makeEverton, makeLion, makeOwl, paperStack, trophy, balance, envelope,
  smokePuffs, confetti, snail, stage, GOLD, setRenderer,
} from './lib.js';

const TL = await (await fetch('timeline.json')).json();
for (const [f, w] of [['SemiBold', 600], ['Bold', 700], ['Black', 900]]) {
  const ff = new FontFace('Pretendard', `url(fonts/Pretendard-${f}.otf)`, { weight: String(w) });
  document.fonts.add(await ff.load());
}
const W = 1920, H = 1080;
const M = TL.marks, L = TL.lines;
const SC = Object.fromEntries(TL.scenes.map(s => [s.name, s]));
const END = s => SC[s].start + SC[s].dur;

const glc = document.getElementById('gl');
const out = document.getElementById('out');
const ctx = out.getContext('2d');
const R = new THREE.WebGLRenderer({ canvas: glc, antialias: true, preserveDrawingBuffer: true });
R.setPixelRatio(1);
R.setSize(W, H, false);
R.shadowMap.enabled = true;
R.shadowMap.type = THREE.PCFSoftShadowMap;
R.toneMapping = THREE.NeutralToneMapping;
R.toneMappingExposure = 1.1;
setRenderer(R);
const cam = new THREE.PerspectiveCamera(40, W / H, 0.1, 200);

// ---------------------------------------------------------------- 대사·카메라 도구
const BY = {};
for (const [id, l] of Object.entries(L)) (BY[l.spk] ||= []).push(l);
function talk(spk, t) {
  for (const l of BY[spk] || []) {
    if (t >= l.t && t < l.end) {
      const f = (t - l.t) * 30, i = Math.floor(f);
      const a = l.env[i] || 0, b = l.env[i + 1] || 0;
      return clamp(lerp(a, b, f - i) * 1.1);
    }
  }
  return 0;
}
function camPath(keys) {
  return (t) => {
    let a = keys[0], b = keys[keys.length - 1];
    if (t <= a[0]) b = a;
    else if (t >= b[0]) a = b;
    else for (let i = 0; i < keys.length - 1; i++) if (t >= keys[i][0] && t < keys[i + 1][0]) { a = keys[i]; b = keys[i + 1]; break; }
    const k = a === b ? 0 : eio(clamp((t - a[0]) / (b[0] - a[0])));
    const l = a[2].map((v, i) => lerp(v, b[2][i], k));
    const p = a[1].map((v, i) => l[i] + (lerp(v, b[1][i], k) - l[i]) * 1.12);
    cam.position.set(p[0] + Math.sin(t * 0.43) * 0.05, p[1] + Math.sin(t * 0.61) * 0.03, p[2]);
    cam.lookAt(l[0], l[1], l[2]);
  };
}
const BOX = (w, h, d) => new THREE.BoxGeometry(w, h, d);
const CYL = (a, b, h, n = 32) => new THREE.CylinderGeometry(a, b, h, n);

function mini(parent, col, x, z, seed) {
  const g = group(parent, x, 0, z);
  add(g, new THREE.CapsuleGeometry(0.2, 0.22, 6, 12), mat(col, 0.5), { y: 0.35 });
  add(g, SPH, mat(0xf1c7a1, 0.6), { y: 0.82, sx: 0.2, sy: 0.2, sz: 0.2 });
  add(g, new THREE.SphereGeometry(0.21, 16, 8, 0, Math.PI * 2, 0, Math.PI / 2), mat([0x2a1a10, 0x6b4a2a, 0x111111][seed % 3], 0.7), { y: 0.86 });
  for (const s of [-1, 1]) add(g, SPH_LO, mat(0x111111, 0.3), { x: s * 0.07, y: 0.84, z: 0.18, sx: 0.03, sy: 0.04, sz: 0.02, cast: false });
  return g;
}
function coins(parent, n, seed, spread = 0.5) {
  const r = rng(seed);
  const g = group(parent);
  const gm = GOLD();
  for (let i = 0; i < n; i++)
    add(g, CYL(0.16, 0.16, 0.05, 24), gm, { x: (r() - 0.5) * spread, y: 0.1 + Math.floor(i / 4) * 0.05, z: (r() - 0.5) * spread, rx: (r() - 0.5) * 0.3 });
  return g;
}
function wall(sc, col, z = -3.2) {
  add(sc, new THREE.PlaneGeometry(80, 20), mat(col, 0.95), { y: 10, z, cast: false });
}

// ================================================================ 1. 서류 도착
function sArrive() {
  const { sc } = stage({ bg: 0xf6e7cf, floor: 0xc49a6c, shadowBox: 8 });
  wall(sc, 0xf8e9d0);
  add(sc, BOX(80, 0.3, 0.1), mat(0xffffff, 0.6), { y: 0.15, z: -3.15 });
  const win = group(sc, 3.6, 3.0, -3.12);
  add(win, BOX(2.3, 1.7, 0.08), mat(0xffffff, 0.5), {});
  add(win, new THREE.PlaneGeometry(2.1, 1.5), new THREE.MeshBasicMaterial({ color: 0x9fd3ff }), { z: 0.05, cast: false });
  add(win, BOX(0.06, 1.5, 0.05), mat(0xffffff, 0.5), { z: 0.07 });
  add(win, BOX(2.1, 0.06, 0.05), mat(0xffffff, 0.5), { z: 0.07 });
  add(sc, BOX(3.4, 0.12, 0.6), mat(0x8b5a2b, 0.6), { x: -3.4, y: 2.4, z: -2.85 });
  for (let i = 0; i < 5; i++) trophy(sc, { x: -4.7 + i * 0.65, y: 2.46, z: -2.85, s: 0.55 });
  label(sc, '우승 트로피', 0.26, { bg: '#ffffff', color: '#6b4a12', size: 80, pad: 16, radius: 12, x: -3.4, y: 2.1, z: -2.52 });
  const desk = group(sc, 0.9, 0, 0.2);
  add(desk, BOX(2.9, 0.12, 1.4), mat(0x7a4b2a, 0.55), { y: 0.95 });
  for (const [x, z] of [[-1.3, -0.6], [1.3, -0.6], [-1.3, 0.6], [1.3, 0.6]]) add(desk, BOX(0.12, 0.9, 0.12), mat(0x5e391f, 0.6), { x, y: 0.45, z });
  const stack = paperStack(sc, 48, { h: 2.3, w: 1.3, d: 0.9, text: '혐의 115건' });
  stack.position.set(0.9, 1.01, 0.25);
  const notes = [[0.45, 0.35, 0.12], [-0.42, 0.85, -0.1], [0.35, 1.75, 0.06]].map(([x, y, r]) =>
    label(stack, '사인 ✎', 0.2, { bg: '#ffe066', color: '#5a4300', size: 80, pad: 16, radius: 6, x, y, z: 0.5, rz: r }));
  const city = makeCity(); sc.add(city.root); city.root.position.set(-1.7, 0, 0.7); city.root.rotation.y = 0.35;
  const lion = makeLion(); sc.add(lion.root); lion.root.position.set(3.7, 0, 0.6); lion.root.rotation.y = -0.55;
  const td = M.drop;
  return {
    sc,
    cam: camPath([
      [0, [0.2, 3.4, 11.5], [0.6, 1.6, 0]], [td - 0.3, [0.2, 3.4, 11.5], [0.6, 1.6, 0]],
      [td + 0.9, [0.6, 2.7, 7.6], [0.7, 1.5, 0]], [L.n1.end, [0.4, 2.6, 7.9], [0.5, 1.5, 0]],
      [L.c1.t, [-1.0, 2.2, 4.8], [-1.5, 1.6, 0.5]], [L.c1.end, [-1.0, 2.2, 4.7], [-1.5, 1.6, 0.5]],
      [L.l1.t + 0.3, [2.5, 2.3, 6.2], [2.4, 1.7, 0.3]], [M.title - 0.1, [2.4, 2.3, 6.0], [2.4, 1.7, 0.3]],
      [M.title + 1.8, [0.5, 4.6, 12.5], [0.6, 2.0, 0]]]),
    update(t) {
      const kw = P(t, M.bell - 0.2, 1.4);
      lion.root.position.x = lerp(8.5, 3.7, eout(kw));
      const k = P(t, td - 0.15, 0.4);
      stack.visible = t > td - 0.15;
      stack.position.y = lerp(9, 1.01, ein(k));
      const q = P(t, td + 0.25, 0.7);
      const sq = t > td + 0.25 ? Math.sin(q * Math.PI * 3) * (1 - q) : 0;
      stack.scale.set(1 + sq * 0.12, 1 - sq * 0.2, 1 + sq * 0.12);
      desk.scale.y = 1 - sq * 0.08;
      [M.sign1, M.sign2, M.sign3].forEach((ts, i) => { const s = back(P(t, ts, 0.3)); notes[i].visible = s > 0.01; notes[i].scale.setScalar(Math.max(0.01, s)); });
      const jump = Math.sin(P(t, td + 0.25, 0.45) * Math.PI) * 0.7;
      const shocked = t > td + 0.25;
      city.update(t, { talk: talk('city', t), look: t < M.bell ? [0, 0] : [0.9, -0.1], hop: jump, eyeScale: shocked ? 1.22 : 1,
        browUp: shocked ? 0.7 : 0, brow: shocked ? -0.15 : 0, armL: shocked ? 1.1 : 0.35, armR: shocked ? 1.1 : 0.35 });
      const pointing = [M.sign1, M.sign2, M.sign3].some(ts => t > ts - 0.15 && t < ts + 0.35);
      lion.update(t, { talk: talk('lion', t), look: [-0.7, 0], hop: kw < 1 ? Math.abs(Math.sin(t * 11)) * 0.08 : 0,
        armL: pointing ? 1.3 : 0.25, armLx: pointing ? -0.9 : 0, brow: 0.1, lid: 0.25 });
    },
  };
}

// ================================================================ 2. 규칙
function sRule() {
  const { sc } = stage({ bg: 0xcfe9ff, floor: 0xf3e6cf });
  wall(sc, 0xcfe9ff, -4);
  const bal = balance(sc, { x: 0.6, h: 3.4, L: 2.4, drop: 1.5 });
  coins(bal.pans[0].g, 14, 5, 0.9);
  const players = [0, 1, 2, 3, 4].map(i => mini(bal.pans[1].g, 0x6cabdd, [-0.45, 0.4, 0, -0.3, 0.35][i], [0.2, 0.25, -0.35, -0.2, -0.3][i], i));
  const city = makeCity(); sc.add(city.root); city.root.position.set(-4.2, 0, 1.4); city.root.rotation.y = 0.5;
  const drops = players.map((_, i) => M.buy + 0.3 + i * 0.45);
  return {
    sc,
    cam: camPath([
      [SC.rule.start, [0.2, 3.9, 12.8], [0.3, 2.3, 0]], [L.n3.t, [0.5, 3.5, 10.8], [0.5, 2.3, 0]],
      [L.n3.end, [0.8, 3.2, 9.8], [0.7, 2.1, 0]], [L.c2.t, [-2.6, 2.4, 6.8], [-2.4, 1.9, 0.5]],
      [END('rule'), [-2.4, 2.4, 6.5], [-2.4, 1.9, 0.5]]]),
    update(t) {
      let ang = 0;
      players.forEach((p, i) => {
        const k = P(t, drops[i], 0.35);
        p.visible = t > drops[i];
        p.position.y = lerp(5, 0.08, ein(k));
        ang -= 0.04 * k;
        if (k >= 1) ang += Math.sin((t - drops[i] - 0.35) * 14) * Math.exp(-(t - drops[i] - 0.35) * 5) * 0.03;
      });
      const kt = P(t, M.tilt, 0.7);
      ang -= 0.17 * back(kt);
      bal.set(ang);
      const whine = t > L.c2.t - 0.2;
      city.update(t, { talk: talk('city', t), look: [0.8, 0.3], hop: whine ? Math.abs(Math.sin(t * 8)) * 0.18 : 0,
        armL: whine ? 2.5 + Math.sin(t * 16) * 0.2 : 0.35, armR: whine ? 2.5 - Math.sin(t * 16) * 0.2 : 0.35, brow: whine ? 0.4 : 0 });
    },
    overlay(t) {
      infoCard(t, L.n2.t + 1.4, END('rule'), '규칙', ['번 만큼만 써라']);
      infoCard(t, L.n3.t + 0.3, END('rule'), 'PSR (수익성·지속가능성 규정)', ['3년 손실 한도 £1억 500만'], 170);
    },
  };
}

// ================================================================ 3. 스폰서 변장(54건)
function sSponsor() {
  const { sc } = stage({ bg: 0xe3f0d8, floor: 0xf1e2c8, shadowBox: 12 });
  wall(sc, 0xe3f0d8, -4);
  const vault = group(sc, -4.8, 0, -0.8);
  const steel = mat(0x8a96a4, 0.35, 0.5);
  add(vault, BOX(2.4, 2.6, 1.6), steel, { y: 1.3 });
  add(vault, new THREE.CircleGeometry(0.88, 48), new THREE.MeshBasicMaterial({ color: 0xffd35a }), { y: 1.3, z: 0.805, cast: false });
  const hinge = group(vault, -0.9, 1.3, 0.82);
  const door = group(hinge, 0.9, 0, 0);
  add(door, CYL(0.9, 0.9, 0.2, 48), mat(0x8f9aa7, 0.3, 0.7), { rx: Math.PI / 2 });
  add(door, CYL(0.25, 0.25, 0.1, 32), mat(0x3a4450, 0.3, 0.6), { z: 0.14, rx: Math.PI / 2 });
  for (let i = 0; i < 3; i++) add(door, BOX(0.9, 0.06, 0.06), mat(0xcfd6dd, 0.3, 0.7), { z: 0.2, rz: (i * Math.PI) / 3 });
  label(vault, '구단주 금고', 0.4, { bg: '#f2c14e', color: '#3b2a00', size: 90, pad: 20, radius: 16, y: 2.95, z: 0.82 });
  const bal = balance(sc, { x: 3.3, h: 3.4, L: 2.2, drop: 1.5, left: '수입', right: '지출' });
  coins(bal.pans[0].g, 6, 8, 0.7);
  [0, 1, 2, 3, 4].forEach(i => mini(bal.pans[1].g, 0x6cabdd, [-0.45, 0.4, 0, -0.3, 0.35][i], [0.2, 0.25, -0.35, -0.2, -0.3][i], i));
  const bag = makeBag(); sc.add(bag.root);
  const city = makeCity(); sc.add(city.root); city.root.position.set(-1.6, 0, 1.3); city.root.rotation.y = -0.45;
  const lion = makeLion(); sc.add(lion.root); lion.root.rotation.y = -0.7; lion.clip.visible = false;
  const mag = group(lion.arms[1], 0.05, -0.95, 0.25);
  add(mag, new THREE.TorusGeometry(0.26, 0.05, 12, 32), mat(0x333333, 0.4, 0.3), {});
  add(mag, new THREE.CircleGeometry(0.24, 32), mat(0xbfe6ff, 0.05, 0, { transparent: true, opacity: 0.35 }), { cast: false });
  add(mag, CYL(0.04, 0.04, 0.4, 12), mat(0x5a3718, 0.5), { y: -0.44 });
  const smoke = smokePuffs(sc, 12, 9);
  const B0 = [-2.8, 0, 1.5];
  const panWorld = () => [bal.g.position.x + bal.pans[0].g.position.x, bal.pans[0].g.position.y + 0.08, bal.pans[0].g.position.z];
  return {
    sc,
    cam: camPath([
      [SC.sponsor.start, [0, 3.7, 13.5], [0, 1.9, 0]], [M.walk, [-2.8, 2.5, 8], [-3.4, 1.3, 0]],
      [L.c3.t, [-2.4, 2.0, 5.6], [-2.4, 1.3, 1.0]], [M.hop, [-2.3, 2.0, 5.8], [-2.3, 1.3, 1.0]],
      [M.land, [0.9, 3.1, 10], [1.4, 1.9, 0]], [L.l2.t - 0.3, [3.4, 3.0, 9.4], [3.9, 2.1, 0]],
      [M.fall + 1.0, [3.4, 3.0, 9.2], [3.9, 2.1, 0]], [L.n6.t + 1.2, [0.4, 3.6, 13], [0.5, 1.9, 0]]]),
    update(t) {
      hinge.rotation.y = -1.7 * eout(P(t, M.vault, 0.9));
      bag.root.visible = t > M.walk - 0.1;
      const kw = P(t, M.walk, 1.4);
      let bp = [lerp(-4.8, B0[0], kw), 0, lerp(-0.1, B0[2], kw)];
      let hop = kw > 0 && kw < 1 ? Math.abs(Math.sin(t * 12)) * 0.14 : 0;
      let scale = 1;
      if (t > M.hop) {
        const kh = P(t, M.hop, M.land - M.hop);
        const pw = panWorld();
        bp = [lerp(B0[0], pw[0], kh), lerp(0, pw[1], kh) + Math.sin(kh * Math.PI) * 3.2, lerp(B0[2], pw[2], kh)];
        scale = lerp(1, 0.72, kh);
        hop = 0;
      }
      bag.root.position.set(...bp);
      bag.root.scale.setScalar(scale);
      bag.root.rotation.y = t < M.hop ? 0.3 : lerp(0.3, -0.2, P(t, M.hop, 0.5));
      smoke.g.position.set(B0[0], 1.2, B0[2]);
      smoke.set(P(t, M.poof, 0.8));
      bag.disguise.visible = t > M.poof + 0.08;
      if (t > M.fall) {
        const kf = P(t, M.fall, 0.55);
        bag.mustache.position.set(0.1 * kf, lerp(0.9, 0.12, eout(kf)) + Math.sin(kf * Math.PI) * 0.3, 0.74 + 0.2 * kf);
        bag.mustache.rotation.z = kf * 2.5;
      }
      const landed = t > M.land;
      let ang = -0.26;
      if (landed) {
        const kb = P(t, M.land, M.balance - M.land + 0.6);
        ang = lerp(-0.26, 0, eout(kb)) + Math.sin((t - M.land) * 9) * Math.exp(-(t - M.land) * 3) * 0.06;
      }
      bal.set(ang);
      const whisper = t > L.c3.t - 0.3 && t < L.c3.end + 0.2;
      city.update(t, { talk: talk('city', t), look: t > M.hop ? [0.8, 0.4] : [-0.9, -0.2], lean: whisper ? 0.22 : 0,
        armR: whisper ? 1.9 : 0.35, armRx: whisper ? -0.6 : 0, smile: t > M.poof ? 1 : 0, lid: whisper ? 0.3 : 0 });
      bag.update(t, { talk: 0, look: t < M.poof ? [0.9, 0.1] : [0.3, 0], hop, eyeScale: t > M.poof && t < M.poof + 1.2 ? 1.25 : 1,
        brow: t > M.fall ? 0.35 : -0.1, smile: t > M.poof && t < M.fall ? 1 : 0 });
      const kl = P(t, L.l2.t - 0.8, 0.7);
      lion.root.position.set(lerp(9.5, 6.4, eout(kl)), 0, 0.9);
      const sus = t > L.l2.t - 0.5;
      lion.update(t, { talk: talk('lion', t), look: [-0.9, -0.1], lid: sus && t < M.fall + 0.3 ? 0.45 : 0, brow: sus ? 0.3 : 0,
        armR: sus ? 1.5 : 0.25, armRx: sus ? -0.8 : 0, eyeScale: t > M.fall + 0.3 ? 1.25 : 1, headTilt: sus ? 0.12 : 0 });
    },
    overlay(t) {
      stampFx(t, M.stamp54, ['재무 정보 부정확', '54건'], 1340, 330, -0.12, CATS[0]);
    },
  };
}

// ================================================================ 4. 보수(14) + UEFA(5) + PSR(7)
function sSalary() {
  const { sc } = stage({ bg: 0xf8e1e6, floor: 0xefe3cf });
  wall(sc, 0xf8e1e6, -3.5);
  const counter = group(sc, -3.3, 0, -0.3);
  add(counter, BOX(2.4, 1.1, 1.1), mat(0xe2c79d, 0.6), { y: 0.55 });
  add(counter, BOX(2.6, 0.08, 1.3), mat(0x8b5a2b, 0.5), { y: 1.14 });
  add(counter, BOX(2.4, 1.6, 0.08), mat(0xffffff, 0.5), { y: 2.0, z: -0.5 });
  label(counter, '공식 월급', 0.42, { bg: '#1f6fd1', color: '#ffffff', size: 90, pad: 22, radius: 18, y: 3.1, z: -0.4 });
  const coach = makeCoach(); sc.add(coach.root); coach.root.position.set(-0.2, 0, 0.7); coach.root.rotation.y = -0.15;
  label(sc, '선수·감독', 0.32, { bg: '#1d2433', color: '#ffffff', size: 80, pad: 18, radius: 16, x: -0.2, y: 3.35, z: 0.7 });
  const pipe = group(sc, 1.9, 0, 0.6);
  const green = mat(0x2f9e55, 0.35);
  add(pipe, CYL(0.36, 0.36, 5, 32), green, { y: 5.7 });
  add(pipe, CYL(0.46, 0.46, 0.4, 32), green, { y: 3.15 });
  label(pipe, ['별도', '계약'], 0.62, { bg: '#ffffff', color: '#1d6b3a', size: 80, pad: 14, radius: 12, x: 0, y: 4.1, z: 0.37 });
  const small = envelope(sc, { w: 0.5, h: 0.32 });
  const big = envelope(sc, { w: 1.1, h: 0.7, color: 0xfff3c4, flap: 0xf2dc8a, text: '별도 계약' });
  const stars = group(sc);
  for (let i = 0; i < 4; i++) add(stars, SPH_LO, mat(0xffd84d, 0.3, 0, { emissive: 0xffc400, emissiveIntensity: 0.5 }), { sx: 0.09, sy: 0.09, sz: 0.09, cast: false });
  const city = makeCity(); sc.add(city.root); city.root.rotation.y = 0.5;
  const sweat = add(city.body, SPH, mat(0x8fd3ff, 0.1, 0, { transparent: true, opacity: 0.9 }), { x: 0.75, y: 2.35, z: 0.5, sx: 0.09, sy: 0.14, sz: 0.09 });
  const bonk = M.pipe + 0.75;
  return {
    sc,
    cam: camPath([
      [SC.salary.start, [-0.4, 3.0, 10], [-0.8, 1.7, 0]], [M.env1, [-1.4, 2.6, 7.8], [-1.4, 1.5, 0.3]],
      [M.pipe - 0.6, [0.8, 2.8, 8.4], [0.8, 2.1, 0.3]], [bonk + 1.4, [0.6, 2.7, 8.2], [0.5, 1.9, 0.3]],
      [L.c4.t - 0.2, [-2.8, 2.4, 7.6], [-3.1, 1.6, 0.6]], [L.n8.t + 0.3, [-0.8, 3.1, 11], [-0.9, 1.8, 0]]]),
    update(t) {
      const ks = P(t, M.env1, 0.8);
      small.visible = t > M.env1 - 0.1;
      small.position.set(lerp(-3.0, -0.75, eout(ks)), 1.22 + Math.sin(ks * Math.PI) * 0.3, lerp(-0.2, 1.3, eout(ks)));
      small.rotation.set(-0.3, 0.2, 0);
      big.visible = t > M.pipe;
      if (t < bonk) {
        const k = P(t, M.pipe, 0.75);
        big.position.set(lerp(1.9, -0.2, k), lerp(2.95, 3.0, k) + Math.sin(k * Math.PI) * 0.5, 0.7);
        big.rotation.set(0, 0, k * 6);
      } else {
        const k = P(t, bonk, 0.7);
        big.position.set(lerp(-0.2, 0.35, k), lerp(3.0, 1.3, eout(k)) + Math.sin(k * Math.PI) * 0.6, lerp(0.7, 1.4, k));
        big.rotation.set(-0.3 * k, -0.2 * k, lerp(6, 6.28, k));
      }
      const hit = t > bonk;
      stars.visible = hit && t < bonk + 1.6;
      stars.children.forEach((s, i) => { const a = t * 6 + (i * Math.PI) / 2; s.position.set(-0.2 + Math.cos(a) * 0.7, 3.0, 0.7 + Math.sin(a) * 0.7); });
      coach.update(t, { talk: 0, look: t < M.pipe ? [-0.6, -0.3] : hit ? [0.3, -0.4] : [0.8, 0.8], squash: hit ? Math.sin(P(t, bonk, 0.3) * Math.PI) * 0.12 : 0,
        eyeScale: hit ? 1.2 : 1, smile: hit ? 1 : 0, brow: t > M.env1 + 0.8 && !hit ? 0.3 : -0.1,
        armL: t > M.env1 + 0.6 ? 0.9 : 0.35, armR: hit ? 1.0 : 0.35, armLx: t > M.env1 + 0.6 ? -0.8 : 0, armRx: hit ? -0.8 : 0 });
      const kc = P(t, L.c4.t - 0.7, 0.5);
      city.root.position.set(lerp(-7.5, -4.7, eout(kc)), 0, 1.4);
      sweat.visible = kc > 0.5;
      sweat.position.y = 2.35 - ((t * 0.8) % 0.5);
      const nerv = t > L.c4.t - 0.2 && t < L.c4.end + 0.4;
      city.update(t, { talk: talk('city', t), look: [0.6, 0], brow: 0.35, armL: nerv ? 1.6 + Math.sin(t * 14) * 0.4 : 0.35,
        armR: nerv ? 1.6 - Math.sin(t * 14) * 0.4 : 0.35, smile: nerv ? 0.5 : 0 });
    },
    overlay(t) {
      stampFx(t, M.st14, ['보수 미공개', '14건'], 420, 330, -0.1, CATS[1]);
      stampFx(t, M.st5, ['UEFA 규정 위반', '5건'], 960, 300, 0.06, CATS[2]);
      stampFx(t, M.st7, ['PSR 위반', '7건'], 1500, 330, -0.08, CATS[3]);
    },
  };
}

// ================================================================ 5. 비협조(35건)
function sDoor() {
  const { sc } = stage({ bg: 0xcde6f7, floor: 0x9ccc7a, ground: 0x6f8f5a, shadowBox: 10 });
  const bld = group(sc, 0, 0, -1.5);
  add(bld, BOX(12, 6, 3), mat(0xf4f7fb, 0.7), { y: 3 });
  add(bld, BOX(12.2, 0.5, 3.2), mat(0x6cabdd, 0.5), { y: 6.1 });
  for (let r = 0; r < 2; r++) for (let c = 0; c < 6; c++) {
    if (r === 0 && (c === 2 || c === 3)) continue;
    add(bld, BOX(1.1, 1.0, 0.1), mat(0x8fc3e8, 0.15, 0.2, { emissive: 0x284a66, emissiveIntensity: 0.3 }), { x: -4.8 + c * 1.92, y: 1.9 + r * 2.2, z: 1.52 });
  }
  label(bld, '시티 사무실', 0.5, { bg: '#1c2c4c', color: '#ffffff', size: 90, pad: 22, radius: 14, y: 3.45, z: 1.56 });
  const hinge = group(sc, -0.7, 0, 0.02);
  const door = group(hinge, 0.7, 0, 0);
  add(door, BOX(1.4, 2.6, 0.12), mat(0x3f6f99, 0.5), { y: 1.3 });
  add(door, SPH, GOLD(), { x: 0.5, y: 1.25, z: 0.1, sx: 0.08, sy: 0.08, sz: 0.08 });
  const cal = group(sc, -2.3, 2.3, 0.06);
  add(cal, BOX(1.3, 1.5, 0.06), mat(0xffffff, 0.8), {});
  add(cal, BOX(1.3, 0.3, 0.07), mat(0xd23b3b, 0.5), { y: 0.6 });
  const years = [2018, 2019, 2020, 2021, 2022, 2023];
  const pages = years.map(y => label(cal, [String(y)], 0.46, { color: '#1d2433', size: 120, pad: 10, y: -0.1, z: 0.04 }));
  const flipPiv = group(cal, 0, 0.45, 0.05);
  const flipPages = years.map(y => label(flipPiv, [String(y)], 0.46, { bg: '#ffffff', color: '#1d2433', size: 120, pad: 10, radius: 0, w: 380, h: 280, y: -0.55, z: 0.01 }));
  const tree = group(sc, -4.7, 0, 1.4);
  add(tree, CYL(0.18, 0.26, 2.2, 16), mat(0x7a5230, 0.8), { y: 1.1 });
  const leaf = mat(0x57a64a, 0.7);
  const leaves = [[0, 2.7, 0, 1.0], [-0.6, 2.3, 0.1, 0.7], [0.6, 2.35, -0.1, 0.72]].map(([x, y, z, s]) => add(tree, SPH, leaf, { x, y, z, sx: s, sy: s * 0.9, sz: s }));
  const snowG = group(sc);
  const r = rng(12);
  const flakes = [];
  for (let i = 0; i < 90; i++) flakes.push({ m: add(snowG, SPH_LO, mat(0xffffff, 0.8), { sx: 0.04, sy: 0.04, sz: 0.04, cast: false }), x: -7 + r() * 14, z: -0.5 + r() * 5, s: r() * 6, v: 0.8 + r() * 0.6 });
  const lion = makeLion(); sc.add(lion.root); lion.root.position.set(2.5, 0, 1.3); lion.root.rotation.y = -0.85;
  const city = makeCity(); sc.add(city.root); city.root.position.set(0.55, 0, -0.35); city.root.scale.setScalar(0.9);
  const sn = snail(sc, { s: 1.0, z: 3.2 });
  const tY0 = M.years, tY1 = M.yearsend, seg = (tY1 - tY0) / 6;
  const seasonCol = [0x7cc36a, 0x3f9b3a, 0xe07b28, 0xffffff];
  const mane0 = new THREE.Color(0xb8651f), mane1 = new THREE.Color(0xbdbdbd);
  return {
    sc,
    cam: camPath([
      [SC.door.start, [0.4, 2.9, 11], [0.2, 2.1, 0]], [M.knock - 0.2, [0.0, 2.4, 7.4], [1.0, 1.9, 0.4]],
      [L.c5.end + 0.2, [-0.1, 2.4, 7.2], [0.9, 1.8, 0.4]], [tY0 + 0.8, [0, 3.1, 11.5], [0, 2.1, 0]],
      [tY1, [0.2, 3.0, 11], [0.1, 2.0, 0]], [L.l4.t, [1.6, 2.8, 6.2], [2.4, 2.5, 1.2]], [END('door'), [1.6, 2.8, 6.0], [2.4, 2.5, 1.2]]]),
    update(t) {
      const openK = t < L.c5.end ? eout(P(t, L.c5.t - 0.4, 0.35)) : 1 - ein(P(t, L.c5.end + 0.15, 0.2));
      hinge.rotation.y = 0.95 * openK;
      city.root.visible = openK > 0.05;
      city.root.position.x = 0.35 + 0.35 * openK;
      city.update(t, { talk: talk('city', t), look: [0.8, 0], lean: -0.28, smile: 1, lid: 0.2 });
      const kY = P(t, tY0, tY1 - tY0);
      const yi = t < tY0 ? 0 : Math.min(5, Math.floor((t - tY0) / seg));
      const ph = t < tY0 ? 0.3 : t > tY1 ? 0.62 : ((t - tY0) / seg) % 1;
      pages.forEach((p, i) => { p.visible = i === yi; });
      flipPages.forEach((p, i) => { p.visible = i === yi - 1 && ph < 0.3; });
      flipPiv.rotation.x = -Math.PI * 0.95 * eout(clamp(ph / 0.3));
      const si = Math.min(3, Math.floor(ph * 4));
      const c0 = new THREE.Color(seasonCol[si]);
      leaf.color.copy(c0);
      leaves.forEach(l => { l.visible = si !== 3 || t < tY0 || t > tY1; });
      if (t > tY1) leaf.color.set(0xe07b28);
      const snowing = t >= tY0 && t <= tY1 && si === 3;
      snowG.visible = snowing;
      for (const f of flakes) f.m.position.set(f.x + Math.sin(t + f.s) * 0.2, 6 - (((t * f.v) + f.s) % 6), f.z);
      lion.mane.color.copy(mane0).lerp(mane1, kY);
      lion.beard.scale.setScalar(Math.max(0.01, kY * 1.3));
      const knocking = t > M.knock && t < M.knock + 1.1;
      lion.update(t, { talk: talk('lion', t), look: t > L.l4.t - 0.3 ? [0.2, 0] : [-0.8, 0], armL: knocking ? 1.9 + Math.sin(t * 24) * 0.25 : 0.25,
        armLx: knocking ? -0.5 : 0, lid: t > tY0 ? lerp(0, 0.5, kY) : 0, brow: t > tY0 ? -0.35 * kY : 0.1,
        nod: t > tY1 ? 0.12 : 0, hop: -0.1 * kY });
      sn.position.x = lerp(-7, 6, P(t, tY0 - 1, END('door') - tY0 + 1));
    },
    overlay(t) {
      stampFx(t, L.n9.t + (L.n9.end - L.n9.t) * 0.55, ['조사 비협조', '35건'], 1480, 330, -0.1, CATS[4]);
      if (t > M.years && t < M.yearsend + 0.8) {
        const k = P(t, M.years, 0.4) * (1 - P(t, M.yearsend + 0.4, 0.4));
        pill(t, 960, 250, '리그: "자료 주세요" … 2018년 12월 ~ 2023년', k);
      }
    },
  };
}

// ================================================================ 6. 타임라인
function sTimeline() {
  const { sc } = stage({ bg: 0xd5eafa, floor: 0xdfe9d6, ground: 0x7d8f6a, shadowBox: 14, keyPos: [8, 10, 8] });
  const road = group(sc);
  add(road, BOX(80, 0.04, 2.6), mat(0x58626f, 0.8), { x: 18, y: 0.02, z: 0.4 });
  for (let i = -10; i < 60; i++) add(road, BOX(0.9, 0.01, 0.1), mat(0xffffff, 0.6), { x: i * 1.6, y: 0.05, z: 0.4, cast: false });
  const ST = [
    [0, '2018', ['독일 슈피겔 보도', '유출된 내부 이메일']],
    [9, '2020', ['UEFA 2년 출전 금지', '→ CAS가 뒤집음']],
    [18, '2023.2', ['프리미어리그', '115건 기소']],
    [27, '2024 가을', ['비공개 청문회', '10주']],
    [36, '2026.9', ['판결까지', '스무 달 넘게']],
  ];
  for (const [x, yr, txt] of ST) {
    add(sc, CYL(0.08, 0.08, 3.2, 12), mat(0x6b5a4a, 0.7), { x: x - 2.2, y: 1.6, z: -1.6 });
    label(sc, [yr, ...txt], 1.7, { bg: '#ffffff', border: '#1c2c4c', borderW: 10, color: '#1d2433', colors: ['#1f6fd1'],
      size: 70, sizes: [110, 64, 64], pad: 36, radius: 24, x: x - 2.2, y: 3.2, z: -1.5, lit: true, cast: true });
  }
  // 2018 신문
  const news = group(sc, 0.6, 0, 0.5);
  add(news, BOX(1.9, 0.05, 1.3), mat(0xf5f1e6, 0.9), {});
  label(news, ['속보', '유출된 이메일'], 0.9, { color: '#1d2433', colors: ['#c62828'], size: 90, pad: 18, y: 0.03, rx: -Math.PI / 2 });
  // 2020 출전 금지 표지판
  const ban = group(sc, 9.4, 0, 0.5);
  const banBoard = group(ban);
  add(banBoard, CYL(0.05, 0.05, 1.2, 10), mat(0x777777, 0.5), { y: 0.6 });
  label(banBoard, ['UEFA', '2년 출전 금지'], 0.9, { bg: '#ffffff', border: '#c62828', borderW: 14, color: '#c62828', size: 80, pad: 26, radius: 18, y: 1.55, z: 0.03, lit: true, cast: true });
  const casStamp = label(banBoard, ['CAS: 취소!'], 0.45, { bg: '#1f6fd1', color: '#ffffff', size: 90, pad: 18, radius: 12, y: 1.55, z: 0.1, rz: -0.2 });
  // 2023 서류 더미
  const st23 = paperStack(sc, 30, { h: 1.3, w: 1.1, d: 0.8, text: '115건', seed: 9 });
  st23.position.set(18.6, 0, 0.5);
  // 2024 청문회 부스
  const booth = group(sc, 27.4, 0, 0.1);
  add(booth, BOX(1.8, 2.3, 1.4), mat(0x3d4552, 0.6), { y: 1.15 });
  add(booth, BOX(0.8, 1.6, 0.05), mat(0x6b4a2a, 0.6), { y: 0.8, z: 0.72 });
  label(booth, '비공개', 0.34, { bg: '#c62828', color: '#ffffff', size: 90, pad: 18, radius: 10, y: 2.0, z: 0.73 });
  const zz = label(booth, 'Zzz…', 0.4, { color: '#1d2433', size: 100, pad: 10, x: 1.1, y: 2.6, z: 0.5 });
  const sn = snail(sc, { s: 1.2, z: 1.0 });
  const hourglass = group(sc, 37.6, 0, 0.3);
  add(hourglass, CYL(0.4, 0.05, 0.6, 24), mat(0xbfe6ff, 0.05, 0, { transparent: true, opacity: 0.5 }), { y: 1.0 });
  add(hourglass, CYL(0.05, 0.4, 0.6, 24), mat(0xbfe6ff, 0.05, 0, { transparent: true, opacity: 0.5 }), { y: 0.4 });
  const sand = add(hourglass, CYL(0.3, 0.05, 0.4, 24), mat(0xe0b35a, 0.8), { y: 0.95 });
  for (const y of [0.08, 1.32]) add(hourglass, CYL(0.46, 0.46, 0.08, 24), mat(0x7a5230, 0.6), { y });
  return {
    sc,
    cam: camPath([
      [SC.timeline.start, [-5.5, 3.8, 8.5], [0, 1.6, 0]], [M.p2018 - 0.2, [1.0, 2.6, 7.0], [-0.3, 1.8, 0]],
      [M.p2020 - 0.4, [10.2, 2.6, 7.0], [8.6, 1.8, 0]], [M.cas + 1.6, [10.0, 2.6, 7.0], [8.6, 1.7, 0]],
      [M.p2023 - 0.2, [19.2, 2.6, 7.0], [17.6, 1.8, 0]], [M.p2024 - 0.2, [28.2, 2.6, 7.0], [26.6, 1.8, 0]],
      [M.snail - 0.2, [37.4, 2.3, 6.4], [35.8, 1.4, 0]], [END('timeline'), [37.3, 2.0, 5.6], [36.4, 1.0, 0.4]]]),
    update(t) {
      const kn = P(t, M.p2018, 0.9);
      news.visible = t > M.p2018;
      news.position.y = lerp(3.5, 0.6, eout(kn));
      news.rotation.set(lerp(0, -0.9, kn) * -1 + 0.9 - 0.9 * 0, kn < 1 ? (1 - kn) * 12 : 0, 0);
      news.rotation.x = lerp(0, 0.9, eout(kn));
      news.scale.setScalar(Math.max(0.01, eout(kn)));
      const kb = back(P(t, M.p2020, 0.4));
      ban.scale.setScalar(Math.max(0.01, kb));
      const kc = P(t, M.cas, 0.25);
      casStamp.visible = t > M.cas;
      casStamp.scale.setScalar(lerp(2.2, 1, eout(kc)));
      banBoard.rotation.x = -1.5 * ein(P(t, M.cas + 1.0, 0.5));
      const ks = P(t, M.p2023 - 0.15, 0.4);
      st23.visible = t > M.p2023 - 0.15;
      st23.position.y = lerp(6, 0, ein(ks));
      zz.position.y = 2.6 + Math.sin(t * 2) * 0.1;
      zz.visible = t > M.p2024;
      sn.position.x = lerp(34.4, 35.6, P(t, M.snail, END('timeline') - M.snail));
      sand.scale.y = 1 - 0.8 * P(t, M.snail - 1, 6);
    },
  };
}

// ================================================================ 7. 판결
const STAMP_TIMES = (() => { const a = []; let t = M.stamps, dt = 0.22; for (let i = 0; i < 24; i++) { a.push(t); t += dt; dt = Math.max(0.06, dt * 0.88); } return a; })();
function sVerdict() {
  const { sc } = stage({ bg: 0x4a3226, floor: 0x7a2d2d, ground: 0x3a2418, hemi: 0.9, key: 2.4, keyPos: [3, 9, 8], fogNear: 18, fogFar: 40 });
  const wood = mat(0x6b4226, 0.6);
  add(sc, new THREE.PlaneGeometry(40, 16), mat(0x5c3a22, 0.8), { y: 8, z: -4, cast: false });
  for (let i = -8; i <= 8; i++) add(sc, BOX(0.12, 6, 0.1), mat(0x4a2c18, 0.7), { x: i * 1.3, y: 3, z: -3.95 });
  add(sc, BOX(8, 1.9, 1.2), wood, { y: 0.95, z: -1.6 });
  add(sc, BOX(8.2, 0.12, 1.4), mat(0x4a2c18, 0.5), { y: 1.95, z: -1.6 });
  label(sc, '독립위원회', 0.44, { bg: '#f2c14e', color: '#3b2a00', size: 90, pad: 22, radius: 14, y: 1.2, z: -0.98 });
  const owls = [-2.3, 0, 2.3].map((x, i) => { const o = makeOwl(i + 2); sc.add(o.root); o.root.position.set(x, 1.05, -2.4); return o; });
  owls[1].gavel.visible = true;
  add(sc, CYL(0.25, 0.25, 0.1, 24), mat(0x4a2c18, 0.5), { x: 0.75, y: 2.06, z: -1.2 });
  const city = makeCity(); sc.add(city.root); city.root.position.set(-3.4, 0, 2.0); city.root.rotation.y = 0.45;
  add(sc, BOX(1.2, 0.8, 0.5), wood, { x: -3.2, y: 0.4, z: 2.95 });
  const pile = paperStack(sc, 20, { h: 0.9, w: 1.0, d: 0.75, seed: 21 });
  pile.position.set(2.3, 0, 1.6);
  add(sc, BOX(1.4, 0.5, 1.1), wood, { x: 2.3, y: -0.2, z: 1.6 });
  const stamp = group(sc, 2.3, 0, 1.6);
  add(stamp, BOX(0.9, 0.22, 0.65), mat(0xc62828, 0.5), { y: 0.11 });
  add(stamp, CYL(0.09, 0.12, 0.7, 16), mat(0x7a4b2a, 0.5), { y: 0.55 });
  add(stamp, SPH, mat(0x7a4b2a, 0.5), { y: 0.95, sx: 0.2, sy: 0.18, sz: 0.2 });
  label(stamp, '인정', 0.2, { color: '#ffffff', size: 90, pad: 8, y: 0.11, z: 0.33 });
  const sheet = group(sc, 2.3, 0.95, 1.6);
  add(sheet, BOX(1.0, 0.02, 0.75), mat(0xffffff, 0.8), {});
  label(sheet, '?', 0.5, { color: '#c62828', size: 150, pad: 6, y: 0.02, rx: -Math.PI / 2 });
  const conf = confetti(sc, 120, 44, [-5, -1.5, 0.5, 3.5, 0.5]);
  const freeze = M.scratch;
  return {
    sc,
    cam: camPath([
      [SC.verdict.start, [0, 3.5, 11.5], [0, 2.0, -0.5]], [M.gavel - 0.4, [0, 3.1, 7.8], [0, 2.4, -1.6]],
      [L.o1.t + 0.3, [0, 2.9, 5.8], [0, 2.6, -2]], [M.stamps - 0.1, [3.4, 2.6, 6.4], [2.2, 1.2, 1.4]],
      [M.stampend + 1.0, [3.3, 2.6, 6.3], [2.2, 1.2, 1.4]], [L.c6.t - 0.1, [-2.4, 2.3, 6.4], [-3.1, 1.7, 2]],
      [L.o2.t - 0.1, [0, 2.9, 5.8], [0, 2.6, -2]], [L.c7.t - 0.1, [-1.6, 2.7, 8.2], [-2.4, 1.9, 1.5]],
      [freeze, [-1.6, 2.7, 8.2], [-2.4, 1.9, 1.5]], [END('verdict'), [-0.4, 3.2, 10.5], [-0.8, 2.0, 0]]]),
    update(t) {
      const tf = Math.min(t, freeze);
      let lastHit = -1e9, nextHit = 1e9;
      for (const h of STAMP_TIMES) { if (h <= t) lastHit = h; else { nextHit = h; break; } }
      let y = 0.95;
      if (t > STAMP_TIMES[0] - 0.3 && t < M.stampend) {
        if (lastHit < 0) y = lerp(1.8, 0.95, eout(P(t, STAMP_TIMES[0] - 0.3, 0.3)));
        else { const span = Math.min(nextHit, M.stampend) - lastHit; const ph = clamp((t - lastHit) / span); y = 0.95 + Math.sin(ph * Math.PI) * Math.min(0.8, span * 3); }
      } else y = t < STAMP_TIMES[0] ? 1.9 : lerp(0.95, 1.9, eout(P(t, M.stampend, 0.4)));
      stamp.position.y = y;
      const ks = P(t, M.stampend + 0.2, 0.6);
      sheet.visible = t > M.stampend + 0.2;
      sheet.position.set(lerp(2.3, 3.8, eout(ks)), lerp(0.95, 0.35, eout(ks)) + Math.sin(ks * Math.PI) * 0.5, lerp(1.6, 2.6, ks));
      sheet.rotation.y = ks * 0.6;
      const g0 = M.gavel;
      const gv = t > g0 - 0.3 && t < g0 + 0.8 ? (t < g0 ? 1.4 * P(t, g0 - 0.3, 0.3) : Math.abs(Math.cos((t - g0) * Math.PI / 0.35)) * 1.2 * (1 - P(t, g0 + 0.5, 0.3))) : 0;
      owls.forEach((o, i) => o.update(t, { talk: talk('owl', t) * (i === 1 ? 1 : 0), look: [i === 0 ? 0.5 : i === 2 ? -0.5 : 0, -0.2],
        armR: i === 1 ? 0.3 + gv : 0.3, armRx: i === 1 ? -gv * 0.6 : 0, lid: 0.2 }));
      const cheering = t > L.c7.t - 0.1;
      const hop = cheering ? Math.abs(Math.sin((tf - L.c7.t) * 9)) * 0.55 : 0;
      city.update(cheering ? tf : t, { talk: t < freeze ? talk('city', t) : 0.6, look: t > L.c6.t - 0.5 && t < L.o2.end ? [0.5, 0.4] : [0.6, 0.2], hop,
        armL: cheering ? 2.6 : 0.35, armR: cheering ? 2.6 : 0.35, smile: cheering ? 1 : 0, eyeScale: t > M.stampend && t < L.c6.t ? 1.25 : 1,
        brow: t < L.o2.end ? 0.3 : -0.2, browUp: t > L.c6.t && t < L.o2.end ? 0.5 : 0 });
      conf.set(t > M.cheer ? Math.min(t, freeze) - M.cheer : -1);
    },
    overlay(t) {
      if (t > M.stamps - 0.2 && t < L.c6.t) {
        const n = Math.round(114 * eout(P(t, M.stamps, M.stampend - M.stamps)));
        const a = P(t, M.stamps - 0.2, 0.3) * (1 - P(t, L.c6.t - 0.4, 0.4));
        counter(t, a, n);
      }
      if (t > freeze + 0.15) scoreboard(t, freeze + 0.15);
      if (t > freeze) { ctx.fillStyle = `rgba(20,20,30,${0.18 * P(t, freeze, 0.1)})`; ctx.fillRect(0, 0, W, H); }
    },
  };
}

// ================================================================ 8. 징계 룰렛
function sWheel() {
  const { sc } = stage({ bg: 0x23265e, floor: 0x333775, ground: 0x1c1e44, hemi: 0.8, key: 2.2, keyPos: [2, 10, 9], fogNear: 20, fogFar: 45 });
  for (const [x, c] of [[-6, 0xff5aa0], [6, 0x5ad1ff]]) {
    const sp = new THREE.SpotLight(c, 60, 30, 0.45, 0.6); sp.position.set(x, 9, 4); sp.target.position.set(0, 2, 0);
    sc.add(sp); sc.add(sp.target);
  }
  const wheel = group(sc, 0, 3.2, -0.4);
  const cv = document.createElement('canvas'); cv.width = cv.height = 1024;
  const g = cv.getContext('2d');
  const segs = [['벌금', '#3987e5'], ['승점 삭감', '#d95926'], ['리그 퇴출', '#c0392b'], ['벌금', '#199e70'], ['승점 삭감', '#c98500'], ['???', '#d55181']];
  segs.forEach(([txt, col], i) => {
    const a0 = (i / segs.length) * Math.PI * 2 - Math.PI / 2, a1 = ((i + 1) / segs.length) * Math.PI * 2 - Math.PI / 2;
    g.beginPath(); g.moveTo(512, 512); g.arc(512, 512, 512, a0, a1); g.closePath(); g.fillStyle = col; g.fill();
    g.lineWidth = 8; g.strokeStyle = '#ffffff'; g.stroke();
    g.save(); g.translate(512, 512); g.rotate((a0 + a1) / 2); g.fillStyle = '#ffffff'; g.font = '900 64px Pretendard';
    g.textAlign = 'right'; g.textBaseline = 'middle'; g.fillText(txt, 470, 0); g.restore();
  });
  const tex = new THREE.CanvasTexture(cv); tex.colorSpace = THREE.SRGBColorSpace; tex.anisotropy = 8;
  const disc = new THREE.Mesh(CYL(2.5, 2.5, 0.25, 96), [mat(0xf2c14e, 0.3, 0.7), mat(0xffffff, 0.5, 0, { map: tex }), mat(0x222222, 0.5)]);
  disc.rotation.x = Math.PI / 2; disc.castShadow = true; wheel.add(disc);
  add(wheel, new THREE.TorusGeometry(2.55, 0.1, 16, 96), GOLD(), {});
  const spinner = group(wheel);
  spinner.add(disc);
  for (let i = 0; i < 24; i++) { const a = (i / 24) * Math.PI * 2; add(spinner, SPH_LO, GOLD(), { x: Math.cos(a) * 2.38, y: Math.sin(a) * 2.38, z: 0.16, sx: 0.07, sy: 0.07, sz: 0.07 }); }
  add(wheel, CYL(0.35, 0.35, 0.35, 32), GOLD(), { z: 0.15, rx: Math.PI / 2 });
  add(sc, new THREE.ConeGeometry(0.3, 0.6, 24), mat(0xe03a3a, 0.4), { y: 5.95, z: -0.2, rx: Math.PI });
  for (const s of [-1, 1]) add(sc, BOX(0.25, 3.4, 0.25), mat(0x9aa3b5, 0.3, 0.6), { x: s * 1.6, y: 1.5, z: -0.7, rz: s * 0.35 });
  const city = makeCity(); sc.add(city.root); city.root.rotation.y = 0.45;
  const efc = makeEverton(); sc.add(efc.root); efc.root.position.set(4.0, 0, 1.3); efc.root.rotation.y = -0.4;
  const efSign = group(sc, 4.95, 0, 1.3);
  add(efSign, CYL(0.04, 0.04, 1.6, 10), mat(0x7a5230, 0.6), { y: 0.8 });
  label(efSign, ['에버튼', '1건 → 승점 −6'], 0.62, { bg: '#ffffff', border: '#2747a8', borderW: 12, color: '#1d2433', colors: ['#2747a8'], size: 70, pad: 24, radius: 16, y: 1.75, z: 0.03, lit: true, cast: true });
  const lion = makeLion(); sc.add(lion.root); lion.root.position.set(6.6, 0, -0.6); lion.root.rotation.y = -0.5; lion.clip.visible = false;
  const scroll = group(lion.arms[1], 0.05, -0.9, 0.2);
  add(scroll, CYL(0.12, 0.12, 0.7, 20), mat(0xf5ecd6, 0.8), { rz: Math.PI / 2 });
  label(sc, ['판결문', '(미공개)'], 0.55, { bg: '#ffffff', color: '#3d195b', size: 70, pad: 18, radius: 12, x: 6.6, y: 4.2, z: -0.6 });
  const appeal = group(sc, -4.9, 0, 2.3);
  add(appeal, CYL(0.05, 0.05, 1.4, 10), mat(0x7a5230, 0.6), { y: 0.7 });
  label(appeal, '항소!', 0.7, { bg: '#e03a3a', color: '#ffffff', size: 120, pad: 26, radius: 18, y: 1.7, z: 0.03, rz: 0.08, lit: true, cast: true });
  const w0 = 7.5, kk = 0.17;
  const angAt = (t) => {
    if (t < M.spin) return 0;
    const dt = Math.min(t, M.grab) - M.spin;
    let a = (w0 / kk) * (1 - Math.exp(-kk * dt));
    if (t > M.grab) { const wg = w0 * Math.exp(-kk * (M.grab - M.spin)); a += (wg / 12) * (1 - Math.exp(-12 * (t - M.grab))); }
    return a;
  };
  return {
    sc,
    cam: camPath([
      [SC.wheel.start, [0, 3.8, 12.5], [0, 3.0, 0]], [L.n18.t, [0, 3.8, 12.2], [0.3, 2.9, 0]],
      [L.n18.t + 2.0, [2.9, 2.5, 7.4], [3.8, 1.7, 1.1]], [L.e1.end + 0.2, [2.9, 2.5, 7.2], [3.8, 1.7, 1.1]],
      [L.c8.t - 0.1, [-2.2, 2.9, 7.8], [-2.5, 2.2, 0.4]], [M.appeal + 1.4, [-2.4, 2.8, 8.2], [-3.0, 2.0, 0.8]],
      [L.n19.t + 1.2, [-0.6, 3.6, 13.5], [-0.6, 2.5, 0]], [END('wheel'), [-0.4, 3.6, 13.2], [-0.5, 2.5, 0]]]),
    update(t) {
      spinner.rotation.z = -angAt(t);
      const kg = P(t, M.grab - 0.5, 0.5);
      city.root.position.set(lerp(-4.0, -2.95, eout(kg)), 0, lerp(1.4, 0.9, kg));
      const grab = t > M.grab - 0.2;
      city.update(t, { talk: talk('city', t), look: grab ? [0.7, 0.6] : [0.6, 0.4], armR: grab ? 2.4 : 0.35, armRx: grab ? -0.5 : 0,
        brow: grab ? -0.3 : 0.2, eyeScale: grab ? 1.15 : 1, armL: t > M.appeal ? 2.0 : 0.35 });
      efc.update(t, { talk: talk('efc', t), look: [-0.7, 0.3], brow: 0.45, lid: 0.25 });
      lion.update(t, { talk: 0, look: [-0.8, 0], lid: 0.3, armR: 1.0, armRx: -0.7 });
      const ka = P(t, M.appeal, 0.5);
      appeal.visible = t > M.appeal;
      appeal.scale.set(1, Math.max(0.01, elastic(ka)), 1);
    },
  };
}

// ================================================================ 9. 마무리
function sOutro() {
  const { sc } = stage({ bg: 0xf6d6a8, floor: 0xead3ae, keyColor: 0xffe2b8, keyPos: [-6, 7, 8], hemi: 1.0, shadowBox: 12 });
  const pod = group(sc, -2.6, 0, 0);
  add(pod, BOX(2.4, 1.5, 1.6), mat(0x6cabdd, 0.45), { y: 0.75 });
  add(pod, BOX(2.5, 0.1, 1.7), mat(0xffffff, 0.5), { y: 1.52 });
  label(pod, ['리그 1위'], 0.62, { color: '#ffffff', size: 110, pad: 10, y: 0.78, z: 0.81 });
  for (const [x, z, ry] of [[-1.75, 0.7, 0.3], [1.75, 0.7, -0.4], [-1.6, -0.6, 0.1], [1.6, -0.6, 0.7]]) trophy(pod, { x, z, s: 1.0, ry });
  for (const [x, ry] of [[-0.8, 0.2], [0.85, -0.3]]) trophy(pod, { x, y: 1.57, z: -0.3, s: 0.8, ry });
  const city = makeCity(); sc.add(city.root); city.root.position.set(-2.6, 1.57, 0.2); city.root.rotation.y = 0.25;
  const tower = paperStack(sc, 60, { h: 4.4, w: 1.4, d: 1.0, text: '115건', seed: 31 });
  tower.position.set(2.3, 0, -0.4);
  const lion = makeLion(); sc.add(lion.root); lion.root.position.set(4.5, 0, 1.2); lion.root.rotation.y = -0.6;
  return {
    sc,
    cam: (t) => {
      const k = P(t, SC.outro.start, SC.outro.dur);
      const a = lerp(-0.32, 0.22, eio(k));
      const r = lerp(13.5, 12, k);
      cam.position.set(Math.sin(a) * r, 3.6, Math.cos(a) * r);
      cam.lookAt(0, 2.4, 0);
    },
    update(t) {
      city.shadesOn(eout(P(t, L.c9.t - 0.4, 0.4)));
      city.update(t, { talk: talk('city', t), look: [0.3, 0], smile: 1, lean: t > L.c9.t - 0.4 ? -0.08 : 0, armL: 1.2, armR: t > L.c9.t - 0.2 ? 2.4 : 1.2 });
      const sigh = P(t, L.l5.t - 0.1, 0.6);
      lion.update(t, { talk: talk('lion', t), look: [-0.7, 0.4], lid: lerp(0.2, 0.6, sigh), brow: -0.3, nod: 0.18 * sigh, armL: 0.1, armR: 0.1 });
    },
    overlay(t) { if (t > M.end) endCard(t, M.end); },
  };
}

// ================================================================ 화면 위 글자
const CATS = ['#3987e5', '#d95926', '#199e70', '#c98500', '#d55181'];
const SPK = { city: ['시티', '#6cabdd'], lion: ['리그 사자', '#8e5bd6'], owl: ['부엉이 판사', '#b07a45'], efc: ['에버튼', '#3f63d0'] };
function rr(x, y, w, h, r) { ctx.beginPath(); ctx.roundRect(x, y, w, h, r); }
function font(w, s) { ctx.font = `${w} ${s}px Pretendard`; }
function wrap(s, maxW) {
  if (ctx.measureText(s).width <= maxW) return [s];
  const words = s.split(' ');
  let best = null;
  for (let i = 1; i < words.length; i++) {
    const a = words.slice(0, i).join(' '), b = words.slice(i).join(' ');
    const d = Math.abs(ctx.measureText(a).width - ctx.measureText(b).width);
    if (!best || d < best[0]) best = [d, [a, b]];
  }
  return best ? best[1] : [s];
}
function subtitle(t) {
  let cur = null;
  for (const l of Object.values(L)) if (t >= l.t - 0.05 && t < l.end + 0.3) cur = l;
  if (!cur) return;
  const a = P(t, cur.t - 0.05, 0.12) * (1 - P(t, cur.end + 0.15, 0.15));
  font(600, 42);
  const lines = wrap(cur.sub, 1400);
  const sp = SPK[cur.spk];
  const chipW = sp ? (font(800, 30), ctx.measureText(sp[0]).width + 36) : 0;
  font(600, 42);
  const tw = Math.max(...lines.map(s => ctx.measureText(s).width));
  const bw = tw + 70 + (sp ? chipW + 18 : 0), bh = 40 + lines.length * 56;
  const x0 = W / 2 - bw / 2, y0 = H - 54 - bh;
  ctx.globalAlpha = a;
  ctx.fillStyle = 'rgba(12,18,34,0.78)'; rr(x0, y0, bw, bh, 18); ctx.fill();
  let tx = x0 + 35;
  if (sp) {
    font(800, 30); ctx.fillStyle = sp[1]; rr(tx, y0 + bh / 2 - 23, chipW, 46, 23); ctx.fill();
    ctx.fillStyle = '#0c1222'; ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; ctx.fillText(sp[0], tx + chipW / 2, y0 + bh / 2 + 1);
    tx += chipW + 18;
  }
  font(600, 42); ctx.fillStyle = '#ffffff'; ctx.textAlign = 'left'; ctx.textBaseline = 'middle';
  lines.forEach((s, i) => ctx.fillText(s, tx, y0 + 20 + 28 + i * 56));
  ctx.globalAlpha = 1;
}
function stampFx(t, t0, lines, x, y, rot, col) {
  if (t < t0) return;
  const k = P(t, t0, 0.22);
  const s = lerp(2.4, 1, eout(k));
  const shake = t - t0 < 0.4 ? Math.sin((t - t0) * 60) * 6 * (1 - P(t, t0 + 0.2, 0.2)) : 0;
  ctx.save(); ctx.translate(x + shake, y); ctx.rotate(rot); ctx.scale(s, s); ctx.globalAlpha = clamp(k * 1.5);
  font(900, 44);
  const w = Math.max(...lines.map((l, i) => (font(900, i ? 78 : 40), ctx.measureText(l).width))) + 70;
  const h = 170;
  ctx.fillStyle = 'rgba(255,255,255,0.92)'; rr(-w / 2, -h / 2, w, h, 16); ctx.fill();
  ctx.lineWidth = 9; ctx.strokeStyle = col; rr(-w / 2 + 8, -h / 2 + 8, w - 16, h - 16, 12); ctx.stroke();
  ctx.fillStyle = '#1d2433'; ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
  font(800, 40); ctx.fillText(lines[0], 0, -34);
  font(900, 78); ctx.fillStyle = col; ctx.fillText(lines[1], 0, 30);
  ctx.restore();
}
function infoCard(t, t0, t1, title, body, dy = 0) {
  if (t < t0 || t > t1) return;
  const k = eout(P(t, t0, 0.4)) * (1 - P(t, t1 - 0.3, 0.3));
  const x = lerp(-520, 70, k), y = 110 + dy;
  ctx.globalAlpha = clamp(k * 1.2);
  font(700, 30); const w1 = ctx.measureText(title).width;
  font(900, 52); const w2 = Math.max(...body.map(b => ctx.measureText(b).width));
  const w = Math.max(w1, w2) + 70;
  ctx.fillStyle = 'rgba(255,255,255,0.94)'; rr(x, y, w, 150, 20); ctx.fill();
  ctx.fillStyle = '#6cabdd'; rr(x, y, 12, 150, 6); ctx.fill();
  ctx.textAlign = 'left'; ctx.textBaseline = 'alphabetic';
  font(700, 30); ctx.fillStyle = '#51607a'; ctx.fillText(title, x + 40, y + 52);
  font(900, 52); ctx.fillStyle = '#1d2433'; body.forEach((b, i) => ctx.fillText(b, x + 40, y + 118 + i * 60));
  ctx.globalAlpha = 1;
}
function pill(t, x, y, s, a) {
  ctx.globalAlpha = a; font(700, 36);
  const w = ctx.measureText(s).width + 60;
  ctx.fillStyle = 'rgba(12,18,34,0.8)'; rr(x - w / 2, y - 34, w, 68, 34); ctx.fill();
  ctx.fillStyle = '#ffffff'; ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; ctx.fillText(s, x, y + 1);
  ctx.globalAlpha = 1;
}
function tally(t) {
  const s0 = SC.sponsor.start, s1 = END('door');
  if (t < s0 || t > s1) return;
  const n9 = L.n9.t + (L.n9.end - L.n9.t) * 0.55;
  const parts = [[54, M.stamp54], [14, M.st14], [5, M.st5], [7, M.st7], [35, n9]];
  const shown = parts.map(([n, ts]) => n * eout(P(t, ts + 0.1, 0.5)));
  const total = Math.round(shown.reduce((a, b) => a + b, 0));
  const a = P(t, s0 + 0.3, 0.4) * (1 - P(t, s1 - 0.4, 0.3));
  ctx.globalAlpha = a;
  const x = W - 70 - 560, y = 60;
  ctx.fillStyle = 'rgba(12,18,34,0.8)'; rr(x, y, 560, 120, 20); ctx.fill();
  ctx.textAlign = 'left'; ctx.textBaseline = 'alphabetic';
  font(700, 28); ctx.fillStyle = '#b9c6e0'; ctx.fillText('혐의 누적', x + 30, y + 48);
  font(900, 44); ctx.fillStyle = '#ffffff'; ctx.textAlign = 'right'; ctx.fillText(`${total}`, x + 450, y + 52);
  font(700, 28); ctx.fillStyle = '#b9c6e0'; ctx.textAlign = 'left'; ctx.fillText('/ 115', x + 462, y + 50);
  let bx = x + 30; const bw = 500;
  ctx.fillStyle = 'rgba(255,255,255,0.12)'; rr(bx, y + 76, bw, 18, 9); ctx.fill();
  shown.forEach((n, i) => { const w = (bw * n) / 115; if (w > 1) { ctx.fillStyle = CATS[i]; rr(bx, y + 76, Math.max(4, w - 2), 18, 4); ctx.fill(); } bx += (bw * n) / 115; });
  ctx.globalAlpha = 1;
}
function counter(t, a, n) {
  ctx.globalAlpha = a;
  const x = W - 90 - 520, y = 90;
  ctx.fillStyle = 'rgba(12,18,34,0.82)'; rr(x, y, 520, 200, 24); ctx.fill();
  ctx.textAlign = 'left'; ctx.textBaseline = 'alphabetic';
  font(700, 32); ctx.fillStyle = '#b9c6e0'; ctx.fillText('인정된 혐의 (보도)', x + 36, y + 58);
  font(900, 110); ctx.fillStyle = '#ffffff'; ctx.fillText(String(n), x + 36, y + 170);
  const w = ctx.measureText(String(n)).width;
  font(800, 50); ctx.fillStyle = '#7f8db0'; ctx.fillText('/ 115', x + 50 + w, y + 168);
  ctx.globalAlpha = 1;
}
function scoreboard(t, t0) {
  const k = back(P(t, t0, 0.35));
  ctx.save(); ctx.translate(W / 2, 200); ctx.scale(k, k);
  ctx.fillStyle = '#0c1222'; rr(-420, -95, 840, 190, 26); ctx.fill();
  ctx.fillStyle = '#6cabdd'; rr(-420, -95, 840, 14, 7); ctx.fill();
  ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
  font(900, 120); ctx.fillStyle = '#ffffff'; ctx.fillText('114 : 1', 0, 12);
  font(700, 30); ctx.fillStyle = '#b9c6e0'; ctx.fillText('인정', -300, 10); ctx.fillText('불인정', 300, 10);
  ctx.restore();
}
function titleCard(t) {
  const t0 = M.title;
  if (t < t0 || t > END('arrive')) return;
  const k = back(P(t, t0, 0.5));
  const a = 1 - P(t, END('arrive') - 0.35, 0.3);
  ctx.save(); ctx.globalAlpha = a; ctx.translate(W / 2, 400); ctx.scale(k, k);
  ctx.fillStyle = 'rgba(12,18,34,0.86)'; rr(-640, -170, 1280, 330, 36); ctx.fill();
  ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
  font(700, 38); ctx.fillStyle = '#6cabdd'; ctx.fillText('3D로 풀어 보는', 0, -95);
  font(900, 110); ctx.fillStyle = '#ffffff'; ctx.fillText('맨시티 115개 혐의', 0, 10);
  font(600, 32); ctx.fillStyle = '#b9c6e0'; ctx.fillText('2026.09.26 기준 · 보도 내용을 바탕으로 한 풍자 애니메이션', 0, 110);
  ctx.restore();
}
function chapter(t, idx) {
  const names = [null, '규칙', '스폰서 수입 · 54건', '보수 14 · UEFA 5 · PSR 7건', '조사 비협조 · 35건', '타임라인', '판결 (보도)', '징계는?', '정리'];
  const s = TL.scenes[idx];
  if (!names[idx]) return;
  const a = P(t, s.start + 0.3, 0.4) * (1 - P(t, s.start + s.dur - 0.4, 0.3));
  ctx.globalAlpha = a;
  font(800, 30);
  const txt = names[idx];
  const w = ctx.measureText(txt).width;
  ctx.fillStyle = 'rgba(12,18,34,0.78)'; rr(60, 1080 - 1080 + 40, w + 110, 58, 29); ctx.fill();
  ctx.fillStyle = '#6cabdd'; ctx.beginPath(); ctx.arc(60 + 32, 40 + 29, 17, 0, Math.PI * 2); ctx.fill();
  ctx.fillStyle = '#0c1222'; font(900, 22); ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; ctx.fillText(String(idx), 92, 70);
  font(800, 30); ctx.fillStyle = '#ffffff'; ctx.textAlign = 'left'; ctx.fillText(txt, 60 + 62, 70);
  ctx.globalAlpha = 1;
}
function endCard(t, t0) {
  const a = P(t, t0, 0.6);
  ctx.fillStyle = `rgba(10,15,30,${0.88 * a})`; ctx.fillRect(0, 0, W, H);
  ctx.globalAlpha = a; ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
  font(900, 64); ctx.fillStyle = '#ffffff'; ctx.fillText('114 : 1, 그리고 항소', W / 2, 330);
  font(600, 32); ctx.fillStyle = '#b9c6e0';
  ['이 영상은 보도 내용을 바탕으로 만든 풍자 애니메이션입니다.', '혐의 설명은 프리미어리그가 제기한 내용이며, 판결문은 공개되지 않았습니다.',
    '징계는 정해지지 않았고 맨시티는 항소할 방침입니다. (2026.09.26 기준)'].forEach((s, i) => ctx.fillText(s, W / 2, 450 + i * 54));
  font(800, 40); ctx.fillStyle = '#6cabdd'; ctx.fillText('제작 · 타튼햄', W / 2, 720);
  ctx.globalAlpha = 1;
}
function iris(t) {
  for (let i = 1; i < TL.scenes.length; i++) {
    const b = TL.scenes[i].start;
    let r = null;
    if (t >= b - 0.32 && t < b) r = lerp(1200, 0, eio(P(t, b - 0.32, 0.32)));
    else if (t >= b && t < b + 0.34) r = lerp(0, 1200, eio(P(t, b, 0.34)));
    if (r !== null) {
      ctx.fillStyle = '#0c1222';
      ctx.beginPath(); ctx.rect(0, 0, W, H); ctx.arc(W / 2, H / 2, Math.max(0.1, r), 0, Math.PI * 2, true); ctx.fill('evenodd');
    }
  }
}

// ================================================================ 조립
const SCENES = [sArrive(), sRule(), sSponsor(), sSalary(), sDoor(), sTimeline(), sVerdict(), sWheel(), sOutro()];
window.TOTAL = TL.total;
window.renderAt = (t, fmt = 'image/jpeg') => {
  let idx = 0;
  for (let i = 0; i < TL.scenes.length; i++) if (t >= TL.scenes[i].start) idx = i;
  const S = SCENES[idx];
  S.update(t);
  S.cam(t);
  R.render(S.sc, cam);
  ctx.drawImage(glc, 0, 0);
  if (S.overlay) S.overlay(t);
  titleCard(t);
  chapter(t, idx);
  tally(t);
  subtitle(t);
  iris(t);
  return out.toDataURL(fmt, 0.93);
};
window.ready = true;
