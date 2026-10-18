// Blog cover generator: 1200x627 PNG (LinkedIn / og:image) + WebP (site) per article and language.
//
// usage (from the repo root):
//   cd tools && npm install && cd ..
//   node tools/generate_covers.js tools/covers.json
//
// covers.json: [{ "file": "custovox_ai_<short>_fr", "big": "55 %", "bigColor": "teal"|"white",
//                 "sub": "…", "hook": "…", "source": "Source : …" }, …]
// Text is drawn with Inter (tools/fonts, SIL OFL) so accents render the same everywhere.
const fs = require('fs');
const path = require('path');
const { Resvg } = require(path.join(__dirname, 'node_modules', '@resvg', 'resvg-js'));
const sharp = require(path.join(__dirname, 'node_modules', 'sharp'));

const ROOT = path.join(__dirname, '..');
const FONTS = ['Inter-Regular.ttf', 'Inter-SemiBold.ttf', 'Inter-ExtraBold.ttf'].map(f => path.join(__dirname, 'fonts', f));
const W = 1200, H = 627;
const NAVY = '#0D2B6B', TEAL = '#00C48C';

const esc = s => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');

// Greedy wrap on an average glyph width (Inter ≈ 0.55em, a bit more when bold).
function wrap(text, size, maxWidth, factor = 0.56) {
  const max = Math.floor(maxWidth / (size * factor));
  const lines = [];
  let cur = '';
  for (const word of String(text).split(/\s+/)) {
    if (cur && (cur + ' ' + word).length > max) { lines.push(cur); cur = word; } else cur = cur ? cur + ' ' + word : word;
  }
  if (cur) lines.push(cur);
  return lines;
}

function svg(c) {
  const bigSize = c.big.length > 7 ? 130 : 168;
  const sub = wrap(c.sub, 44, 1040, 0.58).slice(0, 3);
  const hook = wrap(c.hook || '', 30, 1040, 0.56).slice(0, 2);
  let y = 72 + bigSize;
  const out = [
    `<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}">`,
    `<rect width="${W}" height="${H}" fill="${NAVY}"/>`,
    `<rect x="0" y="0" width="12" height="${H}" fill="${TEAL}"/>`,
    `<text x="80" y="${y}" font-family="Inter" font-weight="800" font-size="${bigSize}" fill="${c.bigColor === 'white' ? '#FFFFFF' : TEAL}" letter-spacing="-4">${esc(c.big)}</text>`,
  ];
  y += 66;
  for (const line of sub) { out.push(`<text x="80" y="${y}" font-family="Inter" font-weight="600" font-size="44" fill="#FFFFFF">${esc(line)}</text>`); y += 54; }
  y += 14;
  for (const line of hook) { out.push(`<text x="80" y="${y}" font-family="Inter" font-weight="600" font-size="30" fill="${TEAL}">${esc(line)}</text>`); y += 40; }
  const src = wrap(c.source || '', 19, 820, 0.52).slice(0, 2);
  src.forEach((line, i) => out.push(`<text x="80" y="${H - 54 + i * 24 - (src.length - 1) * 24}" font-family="Inter" font-weight="400" font-size="19" fill="#94A3B8">${esc(line)}</text>`));
  out.push(`<rect x="${W - 268}" y="${H - 96}" width="208" height="56" rx="28" fill="${TEAL}"/>`);
  out.push(`<text x="${W - 164}" y="${H - 58}" text-anchor="middle" font-family="Inter" font-weight="800" font-size="26" fill="${NAVY}">custovox.ai</text>`);
  out.push('</svg>');
  return out.join('\n');
}

async function main() {
  const list = JSON.parse(fs.readFileSync(process.argv[2] || path.join(__dirname, 'covers.json'), 'utf8'));
  for (const c of list) {
    const png = new Resvg(svg(c), { font: { fontFiles: FONTS, loadSystemFonts: false, defaultFontFamily: 'Inter' }, fitTo: { mode: 'original' } }).render().asPng();
    const base = path.join(ROOT, 'images', c.file);
    fs.writeFileSync(base + '.png', png);
    await sharp(png).webp({ quality: 82 }).toFile(base + '.webp');
    console.log('cover', c.file);
  }
}

main().catch(e => { console.error(e); process.exit(1); });
