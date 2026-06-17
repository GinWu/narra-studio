import test from 'node:test';
import assert from 'node:assert';

// 1. Mock global browser APIs needed by api.js before loading it
const mockLocalStorageStore = {};
global.localStorage = {
  getItem(key) {
    return mockLocalStorageStore[key] || null;
  },
  setItem(key, value) {
    mockLocalStorageStore[key] = String(value);
  },
  removeItem(key) {
    delete mockLocalStorageStore[key];
  },
  clear() {
    for (const key in mockLocalStorageStore) {
      delete mockLocalStorageStore[key];
    }
  }
};

// Mock setInterval so we don't start the background worker timer which would hang Node.js
const activeIntervals = [];
global.setInterval = (callback, delay) => {
  activeIntervals.push({ callback, delay });
  return activeIntervals.length;
};

// Mock global fetch
let fetchMock = null;
global.fetch = async (url, options) => {
  if (fetchMock) {
    return fetchMock(url, options);
  }
  throw new Error('fetch mock not configured');
};

// 2. Import APIClient dynamically to ensure global mocks are applied first
const { APIClient } = await import('../../frontend/api.js');

test('APIClient Class initialization', () => {
  localStorage.clear();
  delete global.window;
  const client = new APIClient();
  
  // Test defaults
  assert.strictEqual(client.getBaseUrl(), '');
  assert.strictEqual(client.isMockMode(), false);

  // Test state setters/getters
  client.setBaseUrl('http://myhost:18080');
  assert.strictEqual(client.getBaseUrl(), 'http://myhost:18080');
  assert.strictEqual(localStorage.getItem('aiwm_api_base_url'), 'http://myhost:18080');

  client.setMockMode(true);
  assert.strictEqual(client.isMockMode(), true);
  assert.strictEqual(localStorage.getItem('aiwm_mock_mode'), 'true');
});

test('APIClient defaults to same-origin API proxy from Docker web port', () => {
  localStorage.clear();
  global.window = {
    location: {
      protocol: 'http:',
      hostname: '192.168.1.20',
      port: '18501',
      origin: 'http://192.168.1.20:18501'
    }
  };

  const client = new APIClient();
  assert.strictEqual(client.getBaseUrl(), '');

  delete global.window;
});

test('APIClient repairs stale localhost API base when opened remotely', () => {
  localStorage.clear();
  localStorage.setItem('aiwm_api_base_url', 'http://localhost:8000');
  global.window = {
    location: {
      protocol: 'http:',
      hostname: '192.168.1.20',
      port: '18501',
      origin: 'http://192.168.1.20:18501'
    }
  };

  const client = new APIClient();
  assert.strictEqual(client.getBaseUrl(), '');
  assert.strictEqual(localStorage.getItem('aiwm_api_base_url'), null);

  delete global.window;
});

test('APIClient repairs stale split-port API base when opened through web proxy', () => {
  localStorage.clear();
  localStorage.setItem('aiwm_api_base_url', 'http://47.107.55.145:18080');
  global.window = {
    location: {
      protocol: 'http:',
      hostname: '47.107.55.145',
      port: '18501',
      origin: 'http://47.107.55.145:18501'
    }
  };

  const client = new APIClient();
  assert.strictEqual(client.getBaseUrl(), '');
  assert.strictEqual(localStorage.getItem('aiwm_api_base_url'), null);

  delete global.window;
});

test('APIClient - Mock Mode Requests', async () => {
  localStorage.clear();
  delete global.window;
  const client = new APIClient();
  client.setMockMode(true);

  // Test GET providers list
  const providers = await client.request('/api/providers');
  assert.ok(Array.isArray(providers));
  assert.ok(providers.some(p => p.name === 'openai'));

  // Test POST a provider
  const newProvider = await client.request('/api/providers', {
    method: 'POST',
    body: JSON.stringify({
      name: 'new_provider',
      display_name: 'New Provider Display',
      provider_type: 'cloud_api'
    })
  });
  assert.strictEqual(newProvider.name, 'new_provider');
  assert.ok(newProvider.id.startsWith('prv_'));

  // Test test provider connection
  const testConn = await client.request(`/api/providers/${newProvider.id}/test-connection`, { method: 'POST' });
  assert.strictEqual(testConn.ok, true);

  // Test GET models list
  const models = await client.request('/api/models');
  assert.ok(Array.isArray(models));
  assert.ok(models.some(m => m.capability_type === 'tts'));

  // Test POST capability run validation error
  await assert.rejects(
    client.request('/api/capabilities/run', {
      method: 'POST',
      body: JSON.stringify({
        capability_type: 'tts',
        model_id: 'mdl_openai_tts',
        input: {} // missing text
      })
    }),
    err => err.error_type === 'VALIDATION_ERROR'
  );

  // Test POST capability run content blocked error
  await assert.rejects(
    client.request('/api/capabilities/run', {
      method: 'POST',
      body: JSON.stringify({
        capability_type: 'tts',
        model_id: 'mdl_openai_tts',
        input: { text: 'some violation here' }
      })
    }),
    err => err.error_type === 'CONTENT_BLOCKED'
  );

  // Test POST capability run sync success
  const syncResult = await client.request('/api/capabilities/run', {
    method: 'POST',
    body: JSON.stringify({
      capability_type: 'tts',
      model_id: 'mdl_openai_tts',
      input: { text: 'Hello world' }
    })
  });
  assert.strictEqual(syncResult.status, 'success');
  assert.strictEqual(syncResult.result_mode, 'sync_file');
  assert.ok(syncResult.assets.length > 0);

  // Test POST capability run async trigger (e.g. video)
  const asyncResult = await client.request('/api/capabilities/run', {
    method: 'POST',
    body: JSON.stringify({
      capability_type: 'video_generation',
      model_id: 'mdl_mock_video',
      input: { prompt: 'A cinematic scene' },
      run_mode: 'async'
    })
  });
  assert.strictEqual(asyncResult.status, 'queued');
  assert.strictEqual(asyncResult.result_mode, 'async_task');
  assert.ok(asyncResult.task_id);

  // Test GET async task status
  const taskStatus = await client.request(`/api/tasks/${asyncResult.task_id}`);
  assert.strictEqual(taskStatus.task_id, asyncResult.task_id);
  assert.ok(['pending', 'queued', 'running'].includes(taskStatus.status));

  // Run the mock setInterval to advance state transitions
  if (activeIntervals.length > 0) {
    // Advance several times to ensure task goes succeeded
    for (let i = 0; i < 10; i++) {
      activeIntervals[0].callback();
    }
  }

  const finishedTaskStatus = await client.request(`/api/tasks/${asyncResult.task_id}`);
  assert.strictEqual(finishedTaskStatus.status, 'succeeded');
  assert.ok(finishedTaskStatus.assets.length > 0);
});

test('APIClient - Real Mode HTTP Request wrapper', async () => {
  localStorage.clear();
  delete global.window;
  const client = new APIClient();
  client.setMockMode(false);

  // Configure fetch mock for a successful query
  fetchMock = async (url, options) => {
    assert.strictEqual(url, '/api/providers');
    return {
      ok: true,
      json: async () => [{ id: 'real_prv_1', name: 'openai' }]
    };
  };

  const providers = await client.request('/api/providers');
  assert.strictEqual(providers[0].id, 'real_prv_1');

  // Configure fetch mock to return a backend structured error
  fetchMock = async (url, options) => {
    return {
      ok: false,
      status: 400,
      json: async () => ({ error_type: 'VALIDATION_ERROR', message: 'Invalid field' })
    };
  };

  await assert.rejects(
    client.request('/api/providers'),
    err => err.error_type === 'VALIDATION_ERROR' && err.message === 'Invalid field'
  );

  // Configure fetch mock to throw network error
  fetchMock = async (url, options) => {
    throw new Error('Connection refused');
  };

  await assert.rejects(
    client.request('/api/providers'),
    err => err.error_type === 'PROVIDER_TIMEOUT' && err.message === 'Connection refused'
  );
});
