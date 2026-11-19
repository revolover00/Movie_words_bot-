import { test } from 'node:test';
import assert from 'node:assert/strict';
import { INTERVALS, intervalKeyboard, intervalLabel, validInterval, levelKeyboard, text } from '../bot_ui.js';

test('both interfaces offer the same seven preset intervals with readable labels', () => {
  for (const lang of ['ar', 'en']) {
    const buttons = intervalKeyboard('setup_interval', lang).inline_keyboard.flat();
    assert.equal(buttons.length, 7);
    assert.deepEqual(buttons.map(button => button.callback_data), INTERVALS.map(minutes => `setup_interval:${minutes}`));
    for (const minutes of INTERVALS) {
      assert.ok(validInterval(String(minutes)));
      assert.ok(intervalLabel(minutes, lang).length > 0);
    }
    assert.equal(levelKeyboard('setup_level', lang).inline_keyboard.length, 5);
  }
});

test('review and completion templates substitute user choices in both languages', () => {
  for (const lang of ['ar', 'en']) {
    const interval = intervalLabel(1440, lang);
    const review = text(lang, 'review', { learn: 'Español', explain: 'العربية', level: 'B2', interval });
    assert.ok(review.includes('Español'));
    assert.ok(review.includes('B2'));
    assert.ok(review.includes(interval));
    assert.ok(!review.includes('{'));
    assert.ok(text(lang, 'done', { interval }).includes(interval));
  }
});

test('old custom preferences remain readable but cannot be selected in callbacks', () => {
  assert.equal(intervalLabel(45, 'en'), '45 minutes');
  assert.equal(validInterval('45'), false);
});
