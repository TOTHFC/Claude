// 사용법: node render.mjs preview <출력폴더> <시각...>   |   node render.mjs video [작업자 수]
import { chromium } from 'playwright-core';
import fs from 'fs';
import path from 'path';
import { spawn, execSync } from 'child_process';

const HERE = path.dirname(new URL(import.meta.url).pathname);
const WEB = path.join(HERE, 'web');
const TYPES = { '.html': 'text/html', '.js': 'text/javascript', '.json': 'application/json', '.otf': 'font/otf' };
const CHROME = '/opt/pw-browsers/chromium-1194/chrome-linux/chrome';
const FFMPEG = execSync('python3 -c "import imageio_ffmpeg;print(imageio_ffmpeg.get_ffmpeg_exe())"').toString().trim();

async function open() {
  const b = await chromium.launch({ executablePath: CHROME, args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
  const p = await b.newPage({ viewport: { width: 1920, height: 1080 } });
  p.on('console', m => { if (m.type() === 'error' || m.type() === 'warning') console.log('[page]', m.text()); });
  p.on('pageerror', e => console.log('[pageerror]', e.message));
  await p.route('http://app/**', r => {
    const f = path.join(WEB, decodeURIComponent(new URL(r.request().url()).pathname));
    r.fulfill({ body: fs.readFileSync(f), contentType: TYPES[path.extname(f)] || 'application/octet-stream' });
  });
  await p.goto('http://app/index.html');
  await p.waitForFunction('window.ready === true', null, { timeout: 120000 });
  return { b, p };
}
const grab = async (p, t, fmt) => Buffer.from((await p.evaluate(([t, f]) => window.renderAt(t, f), [t, fmt])).split(',')[1], 'base64');

const mode = process.argv[2];
if (mode === 'preview') {
  const dir = process.argv[3];
  fs.mkdirSync(dir, { recursive: true });
  const { b, p } = await open();
  for (const s of process.argv.slice(4)) {
    const t0 = Date.now();
    fs.writeFileSync(path.join(dir, `f_${(+s).toFixed(2).padStart(7, '0')}.jpg`), await grab(p, +s, 'image/jpeg'));
    console.log(s, Date.now() - t0, 'ms');
  }
  await b.close();
} else {
  const workers = +(process.argv[3] || 2);
  const tl = JSON.parse(fs.readFileSync(path.join(WEB, 'timeline.json')));
  const n = Math.round(tl.total * 30);
  const per = Math.ceil(n / workers);
  const parts = [];
  await Promise.all([...Array(workers).keys()].map(async w => {
    const a = w * per, z = Math.min(n, a + per);
    const seg = path.join(HERE, `_part${w}.mp4`);
    parts[w] = seg;
    const ff = spawn(FFMPEG, ['-y', '-v', 'error', '-f', 'image2pipe', '-c:v', 'mjpeg', '-r', '30', '-i', '-', '-c:v', 'libx264',
      '-preset', 'medium', '-crf', '16', '-pix_fmt', 'yuv420p', seg], { stdio: ['pipe', 'inherit', 'inherit'] });
    const { b, p } = await open();
    const t0 = Date.now();
    for (let i = a; i < z; i++) {
      const buf = await grab(p, i / 30, 'image/jpeg');
      if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
      if ((i - a) % 300 === 0) console.log(`w${w} ${i - a}/${z - a} ${((Date.now() - t0) / Math.max(1, i - a)).toFixed(0)}ms/f`);
    }
    ff.stdin.end();
    await new Promise(r => ff.on('close', r));
    await b.close();
  }));
  const list = path.join(HERE, '_parts.txt');
  fs.writeFileSync(list, parts.map(s => `file '${s}'`).join('\n'));
  execSync(`"${FFMPEG}" -y -v error -f concat -safe 0 -i "${list}" -i "${path.join(HERE, '_audio.wav')}" -c:v libx264 -preset slow -crf 23 -pix_fmt yuv420p -c:a aac -b:a 192k -shortest -movflags +faststart "${path.join(HERE, 'mancity_3d.mp4')}"`, { stdio: 'inherit' });
  for (const s of parts) fs.unlinkSync(s);
  fs.unlinkSync(list);
  console.log('done', n, 'frames');
}
