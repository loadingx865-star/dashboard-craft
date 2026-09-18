// playwright.viewports.ts
// 看板类项目的视口矩阵与视觉回归配置样例。
// 按项目真实终端替换 projects 列表。
// 依赖：@playwright/test

import { defineConfig, devices } from '@playwright/test';

/**
 * 视口矩阵：与阶段 0 的环境约束卡、验收矩阵保持一致。
 * 注意：视觉回归基线必须在统一环境（相同浏览器版本/相同容器）生成与比对，
 * 跨机器比对需容忍一定像素差异，否则会产生大量误报。
 */
export const DASHBOARD_VIEWPORTS = [
  { name: 'tv-4k',          width: 3840, height: 2160, dpr: 1 },
  { name: 'tv-4k-hidpi',    width: 3840, height: 2160, dpr: 2 }, // 高 DPI：字体回退/图表模糊只在这档暴露
  { name: 'tv-1080',        width: 1920, height: 1080, dpr: 1 },
  { name: 'control-room',   width: 2560, height: 1440, dpr: 1 },
  { name: 'laptop',         width: 1366, height: 768,  dpr: 1 },
] as const;

/**
 * 视觉回归容差按视口分档。
 * 原因：maxDiffPixelRatio 是比例，同一数值在大屏上会放大成极宽的绝对容差——
 * 0.01 在 3840×2160 上等于约 8.3 万像素，足以吞掉真实回归。
 * 大屏是看板最需要严格比对的场景，所以大屏用固定像素上限。
 */
const TOLERANCE: Record<string, { maxDiffPixels?: number; maxDiffPixelRatio?: number }> = {
  'tv-4k':       { maxDiffPixels: 2000 },
  'tv-4k-hidpi': { maxDiffPixels: 2500 }, // 高 DPI 抗锯齿差异更大，单独放宽
  'tv-1080':     { maxDiffPixels: 1500 },
  'control-room':{ maxDiffPixels: 1500 },
  'laptop':      { maxDiffPixelRatio: 0.002 },
};

export default defineConfig({
  testDir: './e2e',
  // 视觉回归对渲染差异敏感，统一使用 chromium 并固定浏览器版本
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  reporter: process.env.CI ? [['html'], ['list']] : [['list']],

  // 视觉回归期望值目录
  snapshotDir: './e2e/__screenshots__',
  expect: {
    toHaveScreenshot: {
      // 默认容差（未在 TOLERANCE 中单独分档时生效）
      maxDiffPixelRatio: 0.002,
      animations: 'disabled',
      // 关闭动画与光标闪烁，避免非确定性差异
      caret: 'hide',
    },
  },

  use: {
    baseURL: process.env.BASE_URL ?? 'http://localhost:5173',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
  },

  projects: DASHBOARD_VIEWPORTS.map((v) => ({
    name: v.name,
    use: {
      ...devices['Desktop Chrome'],
      viewport: { width: v.width, height: v.height },
      // DPR 必须进矩阵：阶段 0 记录的缩放/DPI 不覆盖，等于没测电视与高分屏
      deviceScaleFactor: v.dpr,
    },
    // 按视口分档的容差（Playwright 支持在 project 级覆盖 expect）
    expect: {
      toHaveScreenshot: {
        ...TOLERANCE[v.name],
        animations: 'disabled',
        caret: 'hide',
      },
    },
  })),

  // 本地开发时自动起服务；CI 中通常已由流水线启动
  webServer: process.env.CI
    ? undefined
    : {
        command: 'npm run dev',
        url: 'http://localhost:5173',
        reuseExistingServer: true,
      },
});

/**
 * 可在测试中直接对每个视口截图：
 *
 *   import { test, expect } from '@playwright/test';
 *   test('dashboard snapshot', async ({ page }) => {
 *     await page.goto('/');
 *     await expect(page).toHaveScreenshot('dashboard.png', { fullPage: true });
 *   });
 *
 * 溢出检测（每条关键容器都建议做）：
 *
 *   const overflowing = await page.evaluate(() =>
 *     [...document.querySelectorAll('*')]
 *       .filter((el) => el.scrollWidth > el.clientWidth + 1)
 *       .map((el) => el.className || el.tagName)
 *   );
 *   expect(overflowing).toEqual([]);
 */
