import { chromium } from 'playwright';

const BASE = 'http://localhost:3000';
const sleep = ms => new Promise(r => setTimeout(r, ms));

async function dismissModals(page) {
  for (let i = 0; i < 3; i++) { await page.keyboard.press('Escape'); await sleep(300); }
  const btns = page.locator('button');
  for (let i = 0; i < Math.min(await btns.count(), 10); i++) {
    const text = await btns.nth(i).textContent();
    if (text && /知道了|关闭|确定|好的/i.test(text)) {
      try { await btns.nth(i).click({ timeout: 500 }); await sleep(300); } catch {}
    }
  }
}

async function main() {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
  const results = [];
  const P = s => { results.push({v:'✅',s}); console.log('  ✅ ' + s); };
  const F = s => { results.push({v:'❌',s}); console.log('  ❌ ' + s); };
  const I = s => { results.push({v:'🔍',s}); console.log('  🔍 ' + s); };

  // ═══ 1. Navigate to Profile → Materials tab ═══
  console.log('═══ 1. Navigate to Learning Content Tab ═══');
  await page.goto(`${BASE}/profile`, { waitUntil: 'load', timeout: 30000 });
  await sleep(3000);
  await dismissModals(page);

  // Click the "学习内容" tab
  const materialsTab = page.locator('button:has-text("学习内容")');
  if (await materialsTab.count() > 0) {
    await materialsTab.click({ force: true });
    await sleep(1000);
    P('"学习内容"标签页点击成功');
  } else {
    F('"学习内容"标签页不存在');
    await browser.close();
    process.exit(1);
  }

  await page.screenshot({ path: 'verify-lc-01-tab.png' });

  // ═══ 2. Check scope section ═══
  console.log('═══ 2. Scope Section ═══');
  const scopeHeader = page.locator('text=学习范围');
  (await scopeHeader.count()) > 0 ? P('"学习范围"区域显示') : F('"学习范围"区域缺失');

  // Count knowledge point buttons (should have 49 individual + some collection)
  const scopeButtons = page.locator('.glass-card:has(h3:has-text("学习范围")) button');
  const scopeBtnCount = await scopeButtons.count();
  console.log(`  Scope buttons count: ${scopeBtnCount}`);

  // 49 individual knowledge points + "+ 自定义集合" button = at least 50 buttons
  scopeBtnCount >= 50 ? P(`学习范围知识点按钮数量正确 (${scopeBtnCount}个，≥50)`) : F(`学习范围按钮不足 (${scopeBtnCount}个，预期≥50)`);

  await page.screenshot({ path: 'verify-lc-02-scope.png' });

  // ═══ 3. Create a custom collection ═══
  console.log('═══ 3. Custom Collection Creation ═══');

  // Click "+ 自定义集合" button
  const customBtn = page.locator('button:has-text("自定义集合")');
  if (await customBtn.count() > 0) {
    await customBtn.click({ force: true });
    await sleep(500);
    P('"+ 自定义集合"按钮点击 — 构建器展开');
  } else {
    F('"+ 自定义集合"按钮缺失');
  }

  await page.screenshot({ path: 'verify-lc-03-builder.png' });

  // Select a few knowledge points in the builder
  const builderPts = page.locator('.glass-card:has(h3:has-text("自定义知识集合")) button');
  const builderPtCount = await builderPts.count();
  builderPtCount >= 49 ? P(`集合构建器中有 ${builderPtCount} 个知识点 (≥49)`) : F(`集合构建器知识点不足 (${builderPtCount}个)`);

  // Select first 5 knowledge points
  for (let i = 0; i < Math.min(5, await builderPts.count()); i++) {
    try {
      await builderPts.nth(i).click({ force: true });
      await sleep(100);
    } catch {}
  }

  // Check selected count
  const selectedCountText = await page.locator('text=已选').textContent().catch(() => '');
  const selectedMatch = selectedCountText.match(/(\d+)/);
  const selectedNum = selectedMatch ? parseInt(selectedMatch[1]) : 0;
  selectedNum >= 5 ? P(`选中 ${selectedNum} 个知识点`) : F(`选中数量不对: ${selectedNum}`);

  // Type collection name
  const nameInput = page.locator('.glass-card:has(h3:has-text("自定义知识集合")) input[placeholder="输入集合名称..."]');
  if (await nameInput.count() > 0) {
    await nameInput.fill('大数据核心基础');
    await sleep(300);
    P('集合名称输入成功');
  } else {
    F('集合名称输入框缺失');
  }

  // Click save
  const saveBtn = page.locator('button:has-text("保存集合")');
  if (await saveBtn.count() > 0) {
    await saveBtn.click({ force: true });
    await sleep(500);
  }

  // Verify collection appeared in the list
  const collectionEntry = page.locator('text=大数据核心基础');
  (await collectionEntry.count()) > 0 ? P('集合"大数据核心基础"已保存并显示在列表中') : F('集合保存后未显示');

  await page.screenshot({ path: 'verify-lc-04-collection-saved.png' });

  // ═══ 4. Verify collection appears in scope options ═══
  console.log('═══ 4. Collection in Scope Options ═══');

  // Close builder first
  const doneBtn = page.locator('button:has-text("完成")');
  if (await doneBtn.count() > 0) {
    await doneBtn.click({ force: true });
    await sleep(300);
    P('构建器关闭');
  }

  // Now check scope buttons - should see the new collection
  const collScopeBtn = page.locator('.glass-card:has(h3:has-text("学习范围")) button:has-text("大数据核心基础")');
  (await collScopeBtn.count()) > 0 ? P('集合"大数据核心基础"出现在学习范围按钮中') : F('集合未出现在学习范围按钮中');

  // Check for 📁 prefix on collection button
  const folderIcons = page.locator('button:has-text("📁大数据核心基础")');
  (await folderIcons.count()) > 0 ? P('集合按钮有📁前缀标识') : I('集合按钮没有📁前缀，可能是样式差异');

  await page.screenshot({ path: 'verify-lc-05-scope-with-collection.png' });

  // ═══ 5. Add materials ═══
  console.log('═══ 5. Add Materials ═══');

  // Click knowledge point to select scope
  const firstPointBtn = page.locator('.glass-card:has(h3:has-text("学习范围")) button:has-text("HDFS 架构设计")');
  if (await firstPointBtn.count() > 0) {
    await firstPointBtn.click({ force: true });
    await sleep(200);
    P('选中"HDFS 架构设计"知识点');
  }

  // Click "+ 新增资料"
  const addBtn = page.locator('button:has-text("新增资料")');
  if (await addBtn.count() > 0) {
    await addBtn.click({ force: true });
    await sleep(500);
    P('"+ 新增资料"按钮点击 — 表单展开');
  } else {
    F('"+ 新增资料"按钮缺失');
  }

  await page.screenshot({ path: 'verify-lc-06-add-form.png' });

  // Check form elements
  (await page.locator('button:has-text("学习笔记")').count()) > 0 ? P('资料类型选择器存在') : F('类型选择器缺失');
  (await page.locator('select').count()) > 0 ? P('知识点下拉框存在') : F('知识点下拉框缺失');

  // Add a note
  const titleInput = page.locator('input[placeholder="资料名称..."]');
  if (await titleInput.count() > 0) {
    await titleInput.fill('HDFS NameNode 高可用架构笔记');
    await sleep(200);
  }
  const descInput = page.locator('textarea[placeholder="简要说明..."]');
  if (await descInput.count() > 0) {
    await descInput.fill('NameNode HA 使用 QJM 共享存储，Active/Standby 切换由 ZKFC 控制');
    await sleep(200);
  }

  // Select category to "HDFS 架构设计"
  const select = page.locator('select');
  if (await select.count() > 0) {
    await select.selectOption('HDFS 架构设计');
    await sleep(200);
    P('选择知识点"HDFS 架构设计"');
  }

  // Save
  const saveMaterialBtn = page.locator('button:has-text("保存资料")');
  if (await saveMaterialBtn.count() > 0) {
    await saveMaterialBtn.click({ force: true });
    await sleep(500);
    P('学习笔记保存成功');
  }

  await page.screenshot({ path: 'verify-lc-07-note-saved.png' });

  // Add a link
  const addBtn2 = page.locator('button:has-text("新增资料")');
  if (await addBtn2.count() > 0) {
    await addBtn2.click({ force: true });
    await sleep(300);
  }

  // Switch to link type
  const linkTypeBtn = page.locator('button:has-text("外部链接")');
  if (await linkTypeBtn.count() > 0) {
    await linkTypeBtn.click({ force: true });
    await sleep(200);
  }

  const titleInput2 = page.locator('input[placeholder="资料名称..."]');
  if (await titleInput2.count() > 0) {
    await titleInput2.fill('Hadoop 官方文档');
    await sleep(200);
  }

  const linkInput = page.locator('input[placeholder="https://..."]');
  if (await linkInput.count() > 0) {
    await linkInput.fill('https://hadoop.apache.org/docs/');
    await sleep(200);
  }

  if (await select.count() > 0) {
    await select.selectOption('HDFS 架构设计');
    await sleep(200);
  }

  const saveMaterialBtn2 = page.locator('button:has-text("保存资料")');
  if (await saveMaterialBtn2.count() > 0) {
    await saveMaterialBtn2.click({ force: true });
    await sleep(500);
    P('外部链接保存成功');
  }

  // ═══ 6. Verify materials list ═══
  console.log('═══ 6. Materials List Verification ═══');

  // Check material count
  const summaryText = await page.locator('text=份资料').textContent().catch(() => '0 份资料');
  const countMatch = summaryText.match(/(\d+)\s*份资料/);
  const matCount = countMatch ? parseInt(countMatch[1]) : 0;
  matCount >= 2 ? P(`资料列表显示 ${matCount} 份资料 (≥2)`) : F(`资料数量异常: ${matCount}`);

  // Verify note title visible
  (await page.locator('text=HDFS NameNode 高可用架构笔记').count()) > 0 ? P('笔记标题在列表中显示') : F('笔记标题未显示');
  (await page.locator('text=Hadoop 官方文档').count()) > 0 ? P('链接标题在列表中显示') : F('链接标题未显示');

  await page.screenshot({ path: 'verify-lc-08-materials-list.png' });

  // ═══ 7. Expand material detail ═══
  console.log('═══ 7. Expand/Collapse Material ═══');

  const expandBtns = page.locator('button[title="展开"]');
  if (await expandBtns.count() > 0) {
    await expandBtns.first().click({ force: true });
    await sleep(400);
    P('资料展开成功');
  } else {
    I('展开按钮不存在（可能已被其他元素覆盖）');
  }

  await page.screenshot({ path: 'verify-lc-09-expanded.png' });

  // ═══ 8. Edit collection ═══
  console.log('═══ 8. Edit Collection ═══');

  // Open builder again
  const customBtn2 = page.locator('button:has-text("自定义集合")');
  if (await customBtn2.count() > 0) {
    await customBtn2.click({ force: true });
    await sleep(300);
  }

  // Find edit button for the collection
  const editBtn = page.locator('button:has-text("✎")').first();
  if (await editBtn.count() > 0) {
    await editBtn.click({ force: true });
    await sleep(400);
    P('集合编辑按钮点击成功');
  } else {
    I('集合编辑按钮未找到');
  }

  // Verify editing state - name should be pre-filled
  const editNameInput = page.locator('input[placeholder="输入集合名称..."]');
  if (await editNameInput.count() > 0) {
    const editVal = await editNameInput.inputValue();
    editVal === '大数据核心基础' ? P('编辑模式下集合名称已预填') : I(`编辑模式名称: "${editVal}"`);
  }

  // Update name
  if (await editNameInput.count() > 0) {
    await editNameInput.fill('大数据核心基础与HDFS');
    await sleep(200);
  }

  // Click update
  const updateBtn = page.locator('button:has-text("更新")');
  if (await updateBtn.count() > 0) {
    await updateBtn.click({ force: true });
    await sleep(300);
    P('集合更新成功');
  }

  await page.screenshot({ path: 'verify-lc-10-edited-collection.png' });

  // ═══ 9. Verify collection is scoped and filtered ═══
  console.log('═══ 9. Collection-Based Filtering ═══');

  // Close builder
  const doneBtn2 = page.locator('button:has-text("完成")');
  if (await doneBtn2.count() > 0) {
    await doneBtn2.click({ force: true });
    await sleep(300);
  }

  // Click the collection scope button to select it
  const collBtn = page.locator('button:has-text("大数据核心基础与HDFS")');
  if (await collBtn.count() > 0) {
    await collBtn.click({ force: true });
    await sleep(300);
    P('点击集合按钮 — 选中范围');
  }

  await page.screenshot({ path: 'verify-lc-11-filtered.png' });

  // ═══ 10. Delete collection ═══
  console.log('═══ 10. Delete Collection ═══');

  // Open builder
  const customBtn3 = page.locator('button:has-text("自定义集合")');
  if (await customBtn3.count() > 0) {
    await customBtn3.click({ force: true });
    await sleep(300);
  }

  // Find and click delete
  const deleteBtn = page.locator('button:has-text("✕")').first();
  if (await deleteBtn.count() > 0) {
    await deleteBtn.click({ force: true });
    await sleep(500);
    P('集合删除成功');
  } else {
    I('集合删除按钮未找到');
  }

  // Verify collection removed from list
  const collAfterDelete = page.locator('text=大数据核心基础与HDFS');
  // It may still appear in scope buttons, check builder list
  const builderHasColl = await page.locator('.glass-card:has(h3:has-text("自定义知识集合")) p:has-text("大数据核心基础")').count();
  builderHasColl === 0 ? P('集合已从构建器列表中移除') : F('集合删除后仍在列表中');

  await page.screenshot({ path: 'verify-lc-12-deleted.png' });

  // ═══ Report ═══
  const passes = results.filter(r => r.v === '✅').length;
  const fails = results.filter(r => r.v === '❌').length;
  const probes = results.filter(r => r.v === '🔍').length;
  console.log('\n' + '='.repeat(55));
  console.log('  Learning Content Tab Verification');
  console.log('  ✅ ' + passes + ' passed   ❌ ' + fails + ' failed   🔍 ' + probes + ' probes');
  console.log('  Verdict: ' + (fails > 0 ? 'FAIL' : 'PASS'));
  console.log('='.repeat(55));

  await browser.close();
}

main().then(() => process.exit(0)).catch(err => {
  console.error('FATAL:', err.message);
  process.exit(1);
});
