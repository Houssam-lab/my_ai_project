#!/usr/bin/env node
/**
 * «مركز العملة الصعبة» في متصفّحٍ حقيقي (D-305) — لقطاتٌ دليلٌ يُرى لا ادّعاء.
 *
 * يدخل المدير من نموذج الدخول نفسه، ويفتح المركز من قائمته، ويمرّ على التبويبات الأربعة
 * (الجبهة · الفوترة برفع ملفّ العرض FR · قرار CBAM برقم منشأة · أصناف الاختراق) نهاراً
 * وليلاً وبعرض هاتف؛ ثمّ يدخل الطالب ويُثبت أنّ المدخل غائبٌ عن قائمته.
 *
 * ⛔ بيانات الدخول من البيئة وحدها: E2E_ADMIN_EMAIL · E2E_ADMIN_PASSWORD ·
 * E2E_STUDENT_EMAIL · E2E_STUDENT_PASSWORD · E2E_FRONTEND · E2E_SCREENSHOTS.
 *
 *   NODE_PATH=/opt/node22/lib/node_modules node scripts/e2e/hard_currency_center_ui.cjs
 */
'use strict';

const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');

const REPO = path.resolve(__dirname, '..', '..');
const BASE = process.env.E2E_FRONTEND || 'http://127.0.0.1:5000';
const OUT = process.env.E2E_SCREENSHOTS || '/tmp/hc-ui';
const CHROMIUM = '/opt/pw-browsers/chromium';
const DEMO_FR = path.join(REPO, 'docs/commercial/outreach/demo/DEMO_20_FICHES.csv');

function need(name) {
    const value = (process.env[name] || '').trim();
    if (!value) {
        console.error(`❌ ${name} غير مضبوط — بيانات الدخول من البيئة وحدها.`);
        process.exit(2);
    }
    return value;
}

const checks = [];
function record(name, ok, detail) {
    checks.push({ name, ok, detail });
    console.log(`${ok ? '✅' : '❌'} ${name} — ${detail}`);
}

async function login(page, email, password) {
    await page.goto(BASE, { waitUntil: 'networkidle' });
    await page.fill('input[type="email"]', email);
    await page.fill('input[type="password"]', password);
    await page.click('form button');
    await page.waitForSelector('.header-menu-btn', { timeout: 30000 });
}

async function openMenu(page) {
    await page.click('.header-menu-btn');
    await page.waitForSelector('.header-menu', { timeout: 10000 });
}

async function shot(page, name) {
    const file = path.join(OUT, `${name}.png`);
    await page.screenshot({ path: file, fullPage: true });
    return file;
}

/** بزرّ الواجهة الحقيقي لا بتعديل السمة يدوياً — كي تُختبَر السمة كما يراها المستخدم. */
async function setTheme(page, theme) {
    const current = await page.evaluate(() => document.documentElement.dataset.theme);
    if (current !== theme) {
        await page.click('.header-theme-btn');
        await page.waitForFunction((t) => document.documentElement.dataset.theme === t, theme);
        // انتقالات الألوان في الواجهة القديمة أطول من رموز التصميم — اللقطة بعد استقرارها.
        await page.waitForTimeout(1200);
    }
}

async function adminJourney(browser, consoleErrors) {
    const context = await browser.newContext({ viewport: { width: 1280, height: 900 }, locale: 'ar' });
    const page = await context.newPage();
    page.on('console', (msg) => msg.type() === 'error' && consoleErrors.push(msg.text()));

    await login(page, need('E2E_ADMIN_EMAIL'), need('E2E_ADMIN_PASSWORD'));
    record('دخول المدير من نموذج الواجهة', true, 'وصل إلى لوحة المحادثة');

    await openMenu(page);
    const entry = page.getByRole('button', { name: 'مركز العملة الصعبة' });
    record('مدخل المركز في قائمة المدير', (await entry.count()) === 1, `${await entry.count()} مدخل`);
    await entry.click();

    await page.getByRole('heading', { name: 'خريطة الجبهة' }).waitFor({ timeout: 30000 });
    const cards = await page.getByRole('button', { name: 'عرض الأدلّة' }).count();
    const banner = (await page.locator('[role="note"]').first().innerText()).replace(/\s+/g, ' ');
    record('خريطة الجبهة', cards === 25, `${cards} مساراً · «${banner.slice(0, 110)}…»`);
    await page.getByRole('button', { name: 'عرض الأدلّة' }).first().click();
    await setTheme(page, 'light');
    await shot(page, '01-admin-frontier-light');
    await setTheme(page, 'dark');
    await shot(page, '02-admin-frontier-dark');
    await setTheme(page, 'light');

    await page.getByRole('tab', { name: 'ورشة الفوترة' }).click();
    await page.setInputFiles('#einvoicing-file', DEMO_FR);
    await page.getByRole('button', { name: 'دقّق الملفّ' }).click();
    await page.getByRole('button', { name: 'تنزيل الملفّ المنظَّف' }).waitFor({ timeout: 30000 });
    const rows = await page.locator('table tbody tr').count();
    record('ورشة الفوترة FR', rows > 0, `${rows} شذوذاً معروضاً في الجدول`);
    const [download] = await Promise.all([
        page.waitForEvent('download', { timeout: 15000 }),
        page.getByRole('button', { name: 'تنزيل الملفّ المنظَّف' }).click(),
    ]);
    const saved = path.join(OUT, download.suggestedFilename());
    await download.saveAs(saved);
    const head = fs.readFileSync(saved);
    record(
        'تنزيل الملفّ المنظَّف (UTF-8 بعلامة BOM)',
        head[0] === 0xef && head[1] === 0xbb && head[2] === 0xbf,
        `${download.suggestedFilename()} · ${head.length} بايت`,
    );
    await shot(page, '03-admin-einvoicing');

    await page.setInputFiles('#einvoicing-file', {
        name: 'notes.txt',
        mimeType: 'text/plain',
        buffer: Buffer.from('hello'),
    });
    await page.getByRole('button', { name: 'دقّق الملفّ' }).click();
    const localError = await page.locator('[role="alert"]').first().innerText();
    record('ملفٌّ غير CSV يُرفَض بنصّه', localError.includes('CSV'), `«${localError.trim()}»`);

    await page.getByRole('tab', { name: 'قرار CBAM' }).click();
    await page.locator('#cbam-code').waitFor({ timeout: 30000 });
    await page.selectOption('#cbam-code', '2523100090');
    await page.getByText('عتبة العبور', { exact: false }).first().waitFor({ timeout: 30000 });
    await page.fill('#cbam-plant', '0.6');
    await page.getByRole('button', { name: 'احسب أوّل سنةٍ أرخص' }).click();
    const result = page.locator('p[aria-live="polite"]').filter({ hasText: 'برقم' });
    await result.waitFor({ timeout: 30000 });
    const text = (await result.innerText()).replace(/\s+/g, ' ');
    record('قرار CBAM 2523100090 برقم 0.6', text.includes('2026'), `«${text.slice(0, 120)}…»`);
    await page.locator('svg[role="img"] rect[tabindex="0"]').nth(3).hover();
    const tooltip = await page.locator('[role="status"]').filter({ hasText: 'عتبة العبور' }).count();
    record('تلميح الرسم عند الحوم', tooltip > 0, `${tooltip} تلميح`);
    await shot(page, '04-admin-cbam-light');
    await setTheme(page, 'dark');
    await shot(page, '05-admin-cbam-dark');
    await setTheme(page, 'light');

    await page.getByRole('tab', { name: 'أصناف الاختراق' }).click();
    await page.getByRole('heading', { name: 'أصناف الاختراق العربي/الفرنسي' }).waitFor({ timeout: 30000 });
    const classes = await page.locator('ul li').filter({ hasText: 'المصادر' }).count();
    record('أصناف الاختراق', classes === 5, `${classes} أصناف`);
    await shot(page, '06-admin-redteam');

    await page.setViewportSize({ width: 375, height: 812 });
    await page.getByRole('tab', { name: 'قرار CBAM' }).click();
    await page.locator('#cbam-code').waitFor({ timeout: 30000 });
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
    record('عرض هاتف 375px بلا تمريرٍ أفقي', overflow <= 1, `فائض ${overflow}px`);
    await shot(page, '07-admin-cbam-mobile');
    await context.close();
}

async function studentJourney(browser) {
    const context = await browser.newContext({ viewport: { width: 1280, height: 900 }, locale: 'ar' });
    const page = await context.newPage();
    await login(page, need('E2E_STUDENT_EMAIL'), need('E2E_STUDENT_PASSWORD'));
    await openMenu(page);
    const entry = await page.getByRole('button', { name: 'مركز العملة الصعبة' }).count();
    record('الطالب لا يرى مدخل المركز', entry === 0, `${entry} مدخل`);
    await shot(page, '08-student-menu');
    await context.close();
}

(async () => {
    fs.mkdirSync(OUT, { recursive: true });
    const browser = await chromium.launch({ executablePath: CHROMIUM, args: ['--no-sandbox'] });
    const consoleErrors = [];
    try {
        await adminJourney(browser, consoleErrors);
        await studentJourney(browser);
    } catch (error) {
        record('الرحلة اكتملت', false, String(error && error.message).slice(0, 300));
    } finally {
        await browser.close();
    }
    const failed = checks.filter((c) => !c.ok);
    if (consoleErrors.length) console.log(`⚠️ أخطاء وحدة التحكّم: ${consoleErrors.slice(0, 5).join(' | ').slice(0, 400)}`);
    console.log(`\n${failed.length ? '❌' : '✅'} ${checks.length - failed.length}/${checks.length} فحصاً ناجحاً · اللقطات في ${OUT}`);
    fs.writeFileSync(path.join(OUT, 'ui-checks.json'), JSON.stringify({ checks, consoleErrors }, null, 2));
    process.exit(failed.length ? 1 : 0);
})();
