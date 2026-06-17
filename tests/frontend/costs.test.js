import test from 'node:test';
import assert from 'node:assert';

import { normalizeCostSummary, sumEstimatedCosts } from '../../frontend/utils/costs.js';

test('normalizeCostSummary accepts backend by_currency response', () => {
  const normalized = normalizeCostSummary({
    record_count: 2,
    unknown_cost_count: 1,
    by_currency: [
      { currency: 'USD', estimated_cost_total: '0.1250', count: 2 }
    ]
  });

  assert.strictEqual(normalized.record_count, 2);
  assert.strictEqual(normalized.unknown_cost_count, 1);
  assert.deepStrictEqual(normalized.items, [
    {
      currency: 'USD',
      estimated_cost_total: '0.1250',
      count: 2,
      capability_type: 'USD',
      estimated_total_cost: 0.125,
      known_cost_count: 2,
      unknown_cost_count: 0
    }
  ]);
  assert.strictEqual(sumEstimatedCosts(normalized.items), 0.125);
});

test('normalizeCostSummary accepts frontend/mock items response', () => {
  const normalized = normalizeCostSummary({
    items: [
      { capability_type: 'tts', currency: 'USD', estimated_total_cost: 0.01 },
      { capability_type: 'image_generation', currency: 'USD', estimated_total_cost: '0.02' }
    ]
  });

  assert.strictEqual(sumEstimatedCosts(normalized.items), 0.03);
});

test('normalizeCostSummary is safe for invalid or empty response bodies', () => {
  assert.deepStrictEqual(normalizeCostSummary(null).items, []);
  assert.strictEqual(sumEstimatedCosts(undefined), 0);
  assert.strictEqual(sumEstimatedCosts([{ estimated_total_cost: 'not-a-number' }]), 0);
});
