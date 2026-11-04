// Stills from a graphic page at chosen times, as PNGs and/or one contact sheet.
//   node stills.js page.html OUTDIR t1 t2 ... [--sheet sheet.png] [--over still.jpg|#hex]
// Transparent pages are composited over --over (a frame of the sermon footage is the honest test),
// or a mid grey, so you judge the graphic where it will actually live.
// Adapted from Barty-Bart/motion-graphics (MIT), engine/beats.js.
const {chromium} = require('playwright');
const path = require('path');
const fs = require('fs');
const {execFileSync} = require('child_process');

(async () => {
  const args = process.argv.slice(2);
  const opt = n => { const i = args.indexOf(n); return i >= 0 ? args.splice(i, 2)[1] : null; };
  const sheet = opt('--sheet'); const over = opt('--over');
  const [html, outDir, ...ts] = args;
  if (!html || !outDir || !ts.length) { console.error('usage: node stills.js page.html OUTDIR t1 [t2 ...] [--sheet s.png] [--over img|#hex]'); process.exit(2); }
  fs.mkdirSync(outDir, {recursive: true});
  const b = await chromium.launch();
  const p = await b.newPage({viewport: {width: 1920, height: 1080}});
  const errs = []; p.on('pageerror', e => errs.push(e.message));
  await p.goto('file://' + path.resolve(html) + '?render');
  await p.evaluate(() => document.fonts.ready);
  const dims = await p.evaluate(() => ({W: document.getElementById('stage').offsetWidth, H: document.getElementById('stage').offsetHeight}));
  await p.setViewportSize({width: dims.W, height: dims.H});
  await p.evaluate(() => { if (window.measure) measure(); });
  await p.evaluate(({over, data}) => {
    if (!document.documentElement.classList.contains('alpha')) return;
    const st = document.getElementById('stage');
    st.style.background = data ? `url(${data}) center/cover` : (over || '#7A7A7A');
  }, {over: over && over.startsWith('#') ? over : null,
      data: over && !over.startsWith('#') ? 'data:image/' + (over.endsWith('.png') ? 'png' : 'jpeg') + ';base64,' + fs.readFileSync(over).toString('base64') : null});
  const files = [];
  for (const t of ts) {
    await p.evaluate(t => seek(t), +t);
    const f = path.join(outDir, `${path.basename(html, '.html')}_${(+t).toFixed(2)}.png`);
    await p.screenshot({path: f}); files.push(f); console.log(f);
  }
  await b.close();
  if (sheet) {
    const cols = Math.min(3, files.length), rows = Math.ceil(files.length / cols);
    const inputs = files.flatMap(f => ['-i', f]);
    const fc = files.map((_, i) => `[${i}]scale=640:-1[s${i}]`).join(';') + ';' + files.map((_, i) => `[s${i}]`).join('') +
      `xstack=inputs=${files.length}:layout=` + files.map((_, i) => `${(i % cols) ? Array(i % cols).fill('w0').join('+') : '0'}_${Math.floor(i / cols) ? Array(Math.floor(i / cols)).fill('h0').join('+') : '0'}`).join('|') + ':fill=white';
    if (files.length === 1) execFileSync('ffmpeg', ['-loglevel', 'error', '-y', '-i', files[0], '-vf', 'scale=640:-1', sheet]);
    else execFileSync('ffmpeg', ['-loglevel', 'error', '-y', ...inputs, '-filter_complex', fc, sheet]);
    console.log(sheet);
  }
  if (errs.length) { console.error('page errors:\n' + errs.join('\n')); process.exit(1); }
})().catch(e => { console.error(e); process.exit(1); });
