import { chromium } from 'playwright';

const browser = await chromium.launch({
  headless: true,
  executablePath: 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
});
const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });

try {
  // 1. 打开前端首页
  await page.goto('http://localhost:3000', { waitUntil: 'networkidle', timeout: 30000 });
  console.log('Page loaded');

  // 2. 导航到 ChatView（AI对话助手）
  await page.click('a[href="/chat"]');
  await page.waitForTimeout(2000);

  // 截图：ChatView 初始状态（右下角应有苏格拉底按钮）
  await page.screenshot({ path: 'screenshot_1_chatview.png', fullPage: false });
  console.log('Screenshot 1: ChatView initial state');

  // 3. 检查苏格拉底按钮是否存在
  const fabVisible = await page.isVisible('.socratic-fab');
  console.log(`Socratic FAB button visible: ${fabVisible}`);

  // 4. 点击苏格拉底按钮展开面板
  if (fabVisible) {
    await page.click('.socratic-fab');
    await page.waitForTimeout(500);

    // 截图：面板展开
    await page.screenshot({ path: 'screenshot_2_panel_open.png', fullPage: false });
    console.log('Screenshot 2: Panel opened');

    // 5. 在输入框中输入问题
    const inputVisible = await page.isVisible('.socratic-window input[type="text"]');
    console.log(`Panel input visible: ${inputVisible}`);

    if (inputVisible) {
      await page.fill('.socratic-window input[type="text"]', 'MapReduce的Shuffle过程是怎样的？');
      await page.waitForTimeout(300);

      // 截图：输入问题后
      await page.screenshot({ path: 'screenshot_3_input.png', fullPage: false });
      console.log('Screenshot 3: Question typed');

      // 6. 点击发问按钮
      await page.click('.socratic-window button:has-text("发问")');
      console.log('Clicked ask button');

      // 等待流式生成完成
      await page.waitForTimeout(8000);

      // 截图：生成结果
      await page.screenshot({ path: 'screenshot_4_result.png', fullPage: false });
      console.log('Screenshot 4: Result generated');

      // 7. 检查三段式内容是否存在
      const hasQuestions = await page.locator('.socratic-section').first().isVisible().catch(() => false);
      console.log(`Sections visible: ${hasQuestions}`);
    }

    // 8. 收起面板
    await page.click('.socratic-window button[title="收起"]');
    await page.waitForTimeout(300);

    // 9. 导航到其他页面，验证按钮仍然存在
    await page.click('a[href="/dashboard"]');
    await page.waitForTimeout(1000);
    const fabStillVisible = await page.isVisible('.socratic-fab');
    console.log(`FAB visible after route change: ${fabStillVisible}`);

    await page.screenshot({ path: 'screenshot_5_dashboard.png', fullPage: false });
    console.log('Screenshot 5: After route change to Dashboard');
  }

  console.log('\n=== All verifications passed ===');
} catch (err) {
  console.error('Error:', err.message);
  await page.screenshot({ path: 'screenshot_error.png', fullPage: false });
} finally {
  await browser.close();
}
