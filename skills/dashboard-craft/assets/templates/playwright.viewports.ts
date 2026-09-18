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
  { name: 'tv-4k',          width: 3840, height: 2160 },
  { name: 'tv-1080',        width: 1920, height: 1080 },
  { name: 'control-room',   width: 2560, height: 1440 },
  { name: 'laptop',         width: 1366, height: 768  },
] as const;

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
      // 容忍抗锯齿/GPU 差异；按项目实测调整
      maxDiffPixelRatio: 0.01,
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
      deviceScaleFactor: 1,
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
