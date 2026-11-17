// Synthetic stream matching the reported interaction; not captured API data.
import { test, expect } from '@playwright/test';

async function boot(page, text = '', reasoning = '先核对问题。') {
  await page.goto('/assets/chat_webview/index.html');
  await page.waitForFunction(() => !!window.bridge);
  await page.evaluate(([text, reasoning]) => {
    window.streamPacket = (text, reasoning, typing = true) => JSON.stringify({
      id: 'thinking-reply', role: 'assistant', text, reasoning,
      timestamp: 1767225600000, displayName: 'Alice',
      isUser: false, isAssistant: true, isSystem: false, isError: false,
      isHidden: false, isTyping: typing, isGenerating: typing,
      isPostGenRunning: false,
    });
    window.bridge.setMessages(JSON.stringify([]));
    window.bridge.appendMessage(window.streamPacket(text, reasoning));
  }, [text, reasoning]);
}

async function update(page, text, reasoning, typing = true) {
  await page.evaluate(([text, reasoning, typing]) =>
    window.bridge.updateMessage(window.streamPacket(text, reasoning, typing)),
    [text, reasoning, typing]);
  await page.waitForTimeout(60);
}

for (const interaction of ['untouched', 'expanded', 'toggled repeatedly']) {
  test(`split reasoning keeps the answer outside reasoning when ${interaction}`, async ({ page }) => {
    await boot(page);
    const header = page.locator('[data-action="toggle-reasoning"]');
    if (interaction !== 'untouched') await header.click();
    await update(page, '', '先核对问题。再检查条件。');
    if (interaction === 'toggled repeatedly') {
      await header.click();
      await header.click();
    }
    await update(page, '最终答复：', '先核对问题。再检查条件。');
    await update(page, '最终答复：答案是四。', '先核对问题。再检查条件。', false);
    await expect(page.locator('.msg-body > .message-content .glaze-message')).toHaveText('最终答复：答案是四。');
    await expect(page.locator('.msg-reasoning .glaze-message')).toHaveText('先核对问题。再检查条件。');
    await expect(page.locator('.msg-reasoning .msg-body')).toHaveCount(0);
  });
}

test('inline think details stay readable while the answer streams outside them', async ({ page }) => {
  await boot(page, '<think>先核对问题。</think>', null);
  const details = page.locator('.msg-body details.reasoning-block');
  await details.locator('summary').click();
  await expect(details).toHaveAttribute('open', '');
  await update(page, '<think>先核对问题。</think>最终答复：', null);
  await expect(details).toHaveAttribute('open', '');
  await update(page, '<think>先核对问题。</think>最终答复：答案是四。', null, false);
  await expect(page.locator('.msg-body .reasoning-content')).toHaveText('先核对问题。');
  await expect(page.locator('.msg-body .glaze-message')).toContainText('最终答复：答案是四。');
  await expect(details).toHaveAttribute('open', '');
});
