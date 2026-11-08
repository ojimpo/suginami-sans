// Optional UI verification: Playwright and an installed Edge/Chrome or Chromium.
// NODE_PATH may point to a runtime providing playwright. No user browser profile is used.
const fs = require('node:fs');
const path = require('node:path');
const http = require('node:http');
const crypto = require('node:crypto');
const assert = require('node:assert/strict');
const { chromium } = require('playwright');
const root = path.resolve(__dirname, '..');
const option = process.argv.indexOf('--package-root');
const packageRoot = option < 0 ? null : path.resolve(process.argv[option + 1]);
const servingRoot = packageRoot || root;
const proofPath = packageRoot ? '/specimen/index.html' : '/proofs/index.html';
const hash = file => crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex');
const types = { '.html': 'text/html; charset=utf-8', '.js': 'text/javascript', '.css': 'text/css', '.otf': 'font/otf', '.ttf': 'font/ttf', '.png': 'image/png' };
const server = http.createServer((req, res) => {
  const file = path.resolve(servingRoot, '.' + decodeURIComponent(new URL(req.url, 'http://localhost').pathname));
  if (!file.startsWith(servingRoot + path.sep) || !fs.existsSync(file) || !fs.statSync(file).isFile()) {
    res.writeHead(404); res.end(); return;
  }
  res.writeHead(200, { 'Content-Type': types[path.extname(file)] || 'application/octet-stream' });
  fs.createReadStream(file).pipe(res);
});

async function main() {
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  const browser = await chromium.launch({ headless: true, channel: process.env.SPECIMEN_BROWSER_CHANNEL || 'msedge' });
  const page = await browser.newPage({ viewport: { width: 1440, height: 1100 }, deviceScaleFactor: 1 });
  const errors = [], failedRequests = [], checks = [];
  page.on('pageerror', error => errors.push(error.message));
  page.on('requestfailed', request => failedRequests.push(request.url()));
  const base = 'http://127.0.0.1:' + server.address().port;
  const passed = (name, detail = true) => checks.push({ name, detail });
  try {
    await page.goto(base + proofPath);
    await page.waitForFunction(() => document.getElementById('font-status').textContent === 'OTF 読込済み');
    assert.equal(await page.locator('#paragraphs p').count(), 3);
    const words = (await page.locator('#paragraphs').innerText()).trim().split(/\s+/).length;
    assert(words >= 180); passed('three coherent paragraphs', { words });
    for (const size of ['16', '24', '32']) {
      await page.selectOption('#reading-size', size);
      assert.equal(await page.locator('#paragraphs').evaluate(e => getComputedStyle(e).fontSize), size + 'px');
    }
    for (const leading of ['1.3', '1.6', '1.9']) {
      await page.selectOption('#leading', leading);
      assert(Math.abs(await page.locator('#paragraphs').evaluate(e => parseFloat(getComputedStyle(e).lineHeight)) - 32 * Number(leading)) < .02);
    }
    passed('paragraph size and leading controls');
    await page.click('#reset');
    const measurements = [];
    for (const format of ['otf', 'ttf']) {
      await page.selectOption('#format', format);
      await page.waitForFunction(format => document.getElementById('font-status').textContent === format.toUpperCase() + ' 読込済み', format);
      const widths = await page.evaluate(() => {
        const ids = { default: 'compare-default', alternate: 'compare-alternate', kern_on: 'compare-kern-on', kern_off: 'compare-kern-off' };
        const actual = {};
        for (const [key, id] of Object.entries(ids)) {
          const e = document.getElementById(id);
          e.style.fontSize = '100px';
          actual[key] = e.getBoundingClientRect().width;
          e.style.fontSize = '';
        }
        return { actual, expected: JSON.parse(document.getElementById('specimen-data').textContent).expected_widths_100px };
      });
      for (const [key, actual] of Object.entries(widths.actual)) assert(Math.abs(actual - widths.expected[format][key]) < .04, `${format}/${key}: ${actual}`);
      assert(widths.actual.kern_on < widths.actual.kern_off);
      assert.notEqual(widths.actual.default, widths.actual.alternate);
      measurements.push({ format, ...widths });
    }
    passed('OTF/TTF, ss01 and kerning agree with HarfBuzz', measurements);
    const value = 'A quiet city.\nType freely.';
    await page.fill('#text-input', value);
    assert.equal(await page.locator('#preview').textContent(), value);
    await page.check('#alternate'); await page.uncheck('#kern');
    assert(await page.locator('#preview').evaluate(e => e.classList.contains('alternate')));
    assert.equal(await page.locator('#preview').evaluate(e => getComputedStyle(e).fontKerning), 'none');
    await page.locator('#size').fill('120');
    assert.equal(await page.locator('#preview').evaluate(e => getComputedStyle(e).fontSize), '120px');
    passed('multiline input, alternate y, kerning and size');
    await page.fill('#text-input', '日本語🙂'); assert(await page.locator('#unsupported').isVisible());
    await page.fill('#text-input', '<img src=x onerror=alert(1)>');
    assert.equal(await page.locator('#preview img').count(), 0);
    assert(await page.locator('#unsupported').isHidden());
    passed('unsupported-character warning and literal text input');
    await page.check('#reverse');
    assert(await page.locator('body').evaluate(e => e.classList.contains('reversed')));
    const contrast = await page.locator('.reading').evaluate(e => {
      const style = getComputedStyle(e);
      const luminance = color => color.match(/[\d.]+/g).slice(0, 3).map(Number)
        .map(c => c / 255).map(c => c <= .04045 ? c / 12.92 : ((c + .055) / 1.055) ** 2.4)
        .reduce((sum, c, i) => sum + c * [.2126, .7152, .0722][i], 0);
      const a = luminance(style.color), b = luminance(style.backgroundColor);
      return (Math.max(a, b) + .05) / (Math.min(a, b) + .05);
    });
    assert(contrast >= 4.5, 'Reversed article contrast too low: ' + contrast);
    fs.mkdirSync(path.join(root, 'work'), { recursive: true });
    await page.locator('#reading').screenshot({ path: path.join(root, 'work/specimen-dark.png') });
    await page.click('#reset');
    assert.equal(await page.inputValue('#size'), '32');
    assert.equal(await page.inputValue('#reading-size'), '24');
    assert.equal(await page.inputValue('#leading'), '1.6');
    assert(!await page.isChecked('#alternate') && await page.isChecked('#kern') && !await page.isChecked('#reverse'));
    assert((await page.inputValue('#text-input')).length > 300);
    passed('reverse and complete reset');
    for (const width of [1440, 768, 390]) {
      await page.setViewportSize({ width, height: 1000 });
      assert(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth), `page overflows at ${width}`);
      assert.equal(await page.locator('.glyph').count(), 97);
    }
    passed('desktop, tablet and mobile layouts; all 97 drawn glyphs');
    await page.evaluate(() => window.scrollTo({ top: 0, behavior: 'instant' }));
    await page.screenshot({ path: path.join(root, 'work/specimen-mobile.png') });
    await page.setViewportSize({ width: 1440, height: 1100 });
    await page.evaluate(() => window.scrollTo(0, 0));
    await page.screenshot({ path: path.join(root, 'work/specimen-desktop.png') });
    assert.deepEqual(errors, []); assert.deepEqual(failedRequests, []);
    const files = ['proofs/index.html', 'proofs/specimen.css', 'proofs/specimen.js', 'fonts/SuginamiSans-ExtendedBold.otf', 'fonts/SuginamiSans-ExtendedBold.ttf'];
    const report = { result: 'PASS', date_jst: '2026-11-08', browser: 'Microsoft Edge ' + browser.version(),
      playwright: require('playwright/package.json').version, package_copy: Boolean(packageRoot), checks,
      errors, failed_requests: failedRequests, source_files: Object.fromEntries(files.map(file => [file, hash(path.join(root, file))])) };
    fs.writeFileSync(path.join(root, 'docs', packageRoot ? 'PACKAGE_BROWSER_VALIDATION.json' : 'BROWSER_SPECIMEN_VALIDATION.json'), JSON.stringify(report, null, 2) + '\n');
    console.log('PASS: ' + checks.length + ' browser checks; ' + words + ' prose words; ' + (packageRoot ? 'distribution ZIP specimen' : 'repository specimen'));
  } finally {
    await browser.close();
  }
}
main().catch(error => { console.error(error); process.exitCode = 1; }).finally(() => server.close());
