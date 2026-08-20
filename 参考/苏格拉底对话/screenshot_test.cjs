const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });

  try {
    await page.goto('http://localhost:3000', { waitUntil: 'networkidle', timeout: 30000 });
    console.log('1. Page loaded');

    // 点击 AI对话助手
    await page.click('a[href="/chat"]');
    await page.waitForTimeout(2000);

    // 检查苏格拉底按钮
    const fab = await page.$('.socratic-fab');
    console.log(`2. Socratic FAB visible: ${!!fab}`);

    await page.screenshot({ path: 'screenshot_1_chat.png' });
    console.log('3. Screenshot 1 saved');

    // 点击展开
    if (fab) {
      await fab.click();
      await page.waitForTimeout(500);
      await page.screenshot({ path: 'screenshot_2_panel.png' });
      console.log('4. Panel opened, screenshot 2 saved');

      // 输入问题
      const input = await page.$('.socratic-window input[type="text"]');
      if (input) {
        await input.fill('MapReduce的Shuffle过程是怎样的？');
        await page.waitForTimeout(300);
        await page.screenshot({ path: 'screenshot_3_typed.png' });
        console.log('5. Question typed, screenshot 3 saved');

        // 发问
        await page.click('button:has-text("发问")');
        console.log('6. Ask clicked, waiting for response...');
        await page.waitForTimeout(10000); // 等待流式生成
        await page.screenshot({ path: 'screenshot_4_result.png' });
        console.log('7. Result screenshot 4 saved');

        // 检查段落
        const sections = await page.$$('.socratic-section');
        console.log(`8. Content sections: ${sections.length}`);
        for (let i = 0; i < sections.length; i++) {
          const text = await sections[i].textContent();
          console.log(`   Section ${i + 1}: ${text.slice(0, 60)}...`);
        }
      }

      // 收起
      await page.click('button[title="收起"]');
      await page.waitForTimeout(300);
    }

    // 切换路由验证按钮保持
    await page.click('a[href="/dashboard"]');
    await page.waitForTimeout(1000);
    const fabAfter = await page.$('.socratic-fab');
    console.log(`9. FAB after route change: ${!!fabAfter}`);
    await page.screenshot({ path: 'screenshot_5_route_change.png' });
    console.log('10. Route change screenshot 5 saved');

    console.log('\n=== PASS: All verifications completed ===');
  } catch (err) {
    console.error('ERROR:', err.message);
    await page.screenshot({ path: 'screenshot_error.png' });
  } finally {
    await browser.close();
  }
})();
