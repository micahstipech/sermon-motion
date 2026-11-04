// Render a graphic page (from `mg.py build --html`) frame by frame.
//   node render.js page.html out.mov  [--fps 24000/1001] [--blur]
//   .mov  -> ProRes 4444 with alpha (transparent page; the Resolve fallback)
//   .mp4  -> H.264 preview (use a page built with --bg for a background)
// --blur averages 4 subframes across a 180° shutter (only worth it for fast moves; restraint rarely needs it).
// Adapted from Barty-Bart/motion-graphics (MIT), engine/render.js.
const {chromium} = require('playwright');
const {spawn} = require('child_process');
const path = require('path');

(async () => {
  const args = process.argv.slice(2);
  const fi = args.indexOf('--fps');
  const fpsArg = fi >= 0 ? args.splice(fi, 2)[1] : '24';
  const K = args.includes('--blur') ? 4 : 1;
  const [html, out] = args.filter(a => !a.startsWith('--'));
  if (!html || !out) { console.error('usage: node render.js page.html out.(mov|mp4) [--fps 24000/1001] [--blur]'); process.exit(2); }
  const FPS = fpsArg.includes('/') ? fpsArg.split('/')[0] / fpsArg.split('/')[1] : +fpsArg;
  const b = await chromium.launch();
  const p = await b.newPage({viewport: {width: 1920, height: 1080}});
  const errs = []; p.on('pageerror', e => errs.push(e.message));
  await p.goto('file://' + path.resolve(html) + '?render');
  await p.evaluate(() => document.fonts.ready);
  const info = await p.evaluate(() => ({T: window.DURATION, W: document.getElementById('stage').offsetWidth,
    H: document.getElementById('stage').offsetHeight, alpha: document.documentElement.classList.contains('alpha')}));
  await p.setViewportSize({width: info.W, height: info.H});
  await p.evaluate(() => { if (window.measure) measure(); });
  const N = Math.round(info.T * FPS);
  const sub = 1 / (FPS * 2 * K);
  const alpha = out.toLowerCase().endsWith('.mov');
  const inRate = fpsArg.includes('/') ? `${fpsArg.split('/')[0] * K}/${fpsArg.split('/')[1]}` : String(FPS * K);
  const vf = K > 1 ? [`format=gbrap,tmix=frames=${K}:weights='${Array(K).fill(1).join(' ')}',select='eq(mod(n\\,${K})\\,${K - 1})',setpts=N/(${fpsArg})/TB`] : [];
  const enc = alpha
    ? ['-c:v', 'prores_ks', '-profile:v', '4', '-pix_fmt', 'yuva444p10le', '-vendor', 'apl0']
    : ['-c:v', 'libx264', '-crf', '16', '-preset', 'medium', '-pix_fmt', 'yuv420p', '-movflags', '+faststart'];
  const ff = spawn('ffmpeg', ['-loglevel', 'error', '-y', '-f', 'image2pipe', '-framerate', inRate, '-c:v', 'png', '-i', '-',
    ...(vf.length ? ['-vf', vf[0]] : []), '-r', fpsArg, ...enc, out]);
  ff.stderr.on('data', d => process.stderr.write(d));
  let code = null; const closed = new Promise(r => ff.on('close', c => { code = c; r(); })); ff.stdin.on('error', () => {});
  for (let f = 0; f < N && code === null; f++) {
    for (let k = 0; k < K && code === null; k++) {
      const t = Math.max(0, f / FPS + (K > 1 ? (k - (K - 1) / 2) * sub : 0));
      await p.evaluate(t => seek(t), t);
      const buf = await p.screenshot({type: 'png', omitBackground: alpha && info.alpha});
      if (!ff.stdin.write(buf)) await Promise.race([new Promise(r => ff.stdin.once('drain', r)), closed]);
    }
  }
  ff.stdin.end(); await closed; await b.close();
  if (code !== 0) { console.error(`ffmpeg failed (exit ${code}); ${out} is incomplete`); process.exit(1); }
  if (errs.length) { console.error('page errors:\n' + errs.join('\n')); process.exit(1); }
  console.log(`rendered ${out}: ${N} frames at ${fpsArg} fps${alpha ? ' (ProRes 4444 + alpha)' : ''}`);
})().catch(e => { console.error(e); process.exit(1); });
