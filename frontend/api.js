/**
 * API Client for Narra Studio
 * Supports real backend Fetch calls and standalone Mock fallback mode.
 */

// Helper to generate IDs
const genId = (prefix) => `${prefix}_${Math.random().toString(36).substring(2, 11).toUpperCase()}`;

const normalizeBaseUrl = (url) => String(url || '').trim().replace(/\/+$/, '');

const getStorageValue = (key) => {
  try {
    return typeof globalThis.localStorage !== 'undefined' ? globalThis.localStorage.getItem(key) : null;
  } catch (_) {
    return null;
  }
};

const setStorageValue = (key, value) => {
  try {
    if (typeof globalThis.localStorage !== 'undefined') {
      globalThis.localStorage.setItem(key, value);
    }
  } catch (_) {
    // Storage may be unavailable in hardened browser contexts.
  }
};

const inferDefaultApiBaseUrl = () => {
  const fallback = '';
  const browserWindow = globalThis.window;
  if (!browserWindow?.location) {
    return fallback;
  }

  const configured = normalizeBaseUrl(browserWindow.AIWM_CONFIG?.apiBaseUrl);
  if (configured) {
    return configured;
  }

  return '';
};

const shouldReplaceSavedApiBaseUrl = (savedUrl, inferredUrl) => {
  const browserWindow = globalThis.window;
  if (!savedUrl || !browserWindow?.location) {
    return false;
  }

  try {
    const saved = new URL(savedUrl);
    const current = browserWindow.location;
    const currentIsLocal = current.hostname === 'localhost' || current.hostname === '127.0.0.1';
    const savedIsLocal = saved.hostname === 'localhost' || saved.hostname === '127.0.0.1';

    if (!currentIsLocal && savedIsLocal) {
      return true;
    }

    if (current.port === '18501' && saved.port === '8000' &&
        (saved.hostname === current.hostname || savedIsLocal)) {
      return true;
    }

    if (current.port === '18501' && saved.port === '18080' &&
        saved.hostname === current.hostname) {
      return true;
    }

    if (saved.origin === current.origin) {
      return true;
    }

    return false;
  } catch (_) {
    return Boolean(inferredUrl);
  }
};

// Memory store for mock data to simulate state changes in mock mode
const mockStore = {
  providers: [
    {
      id: 'prv_openai',
      name: 'openai',
      display_name: 'OpenAI',
      provider_type: 'cloud_api',
      api_base: null,
      auth_type: 'bearer_token',
      credential_source: 'docker_secret',
      credential_ref: 'openai_api_key',
      credential_file: '/run/secrets/openai_api_key',
      masked_credential: 'env:OPENAI_API_KEY',
      enabled: true,
      status: 'active',
      timeout_seconds: 60,
      capability_summary: ['tts', 'image_generation']
    },
    {
      id: 'prv_elevenlabs',
      name: 'elevenlabs',
      display_name: 'ElevenLabs',
      provider_type: 'cloud_api',
      api_base: null,
      auth_type: 'api_key',
      credential_source: 'docker_secret',
      credential_ref: 'elevenlabs_api_key',
      credential_file: '/run/secrets/elevenlabs_api_key',
      masked_credential: 'env:ELEVENLABS_API_KEY',
      enabled: false,
      status: 'testing',
      timeout_seconds: 120,
      capability_summary: ['tts']
    },
    {
      id: 'prv_fal',
      name: 'fal',
      display_name: 'fal.ai',
      provider_type: 'model_gateway',
      api_base: null,
      auth_type: 'api_key',
      credential_source: 'env',
      credential_ref: 'FAL_KEY',
      masked_credential: 'env:FAL_KEY',
      enabled: true,
      status: 'active',
      timeout_seconds: 300,
      capability_summary: ['image_generation', 'video_generation', 'image_to_video']
    },
    {
      id: 'prv_mock',
      name: 'mock',
      display_name: 'Local Mock',
      provider_type: 'mock',
      api_base: null,
      auth_type: 'none',
      credential_source: 'none',
      masked_credential: 'none',
      enabled: true,
      status: 'active',
      timeout_seconds: 30,
      capability_summary: ['tts', 'image_generation', 'video_generation']
    }
  ],
  models: [
    {
      id: 'mdl_openai_tts',
      provider_id: 'prv_openai',
      provider_name: 'openai',
      name: 'openai_tts_default',
      display_name: 'OpenAI TTS Default',
      model_code: 'gpt-4o-mini-tts',
      capability_type: 'tts',
      enabled: true,
      status: 'active',
      is_default: true,
      is_recommended: true,
      requires_verification: false,
      default_params: { voice: 'alloy', format: 'mp3' },
      param_ui_schema: {
        voice: { label: '声音 (Voice)', type: 'select', options: ['alloy', 'echo', 'fable', 'onyx', 'nova', 'shimmer'] },
        speed: { label: '语速 (Speed)', type: 'slider', min: 0.5, max: 2.0, step: 0.1, default: 1.0 }
      },
      cost_unit: 'character',
      pricing_hint: '0.015 USD per 1K characters'
    },
    {
      id: 'mdl_elevenlabs_tts',
      provider_id: 'prv_elevenlabs',
      provider_name: 'elevenlabs',
      name: 'elevenlabs_tts_default',
      display_name: 'ElevenLabs TTS Default',
      model_code: 'eleven_multilingual_v2',
      capability_type: 'tts',
      enabled: true,
      status: 'testing',
      is_default: false,
      is_recommended: false,
      requires_verification: true,
      default_params: { output_format: 'mp3_44100_128' },
      param_ui_schema: {
        voice_id: { label: '声音 ID (Voice ID)', type: 'select', options: ['21m00Tcm4TlvDq8ikWAM', 'AZnzlk1XvdvUeBnXmlld', 'EXAVITQu4vr4xnSDxMaL'] }
      },
      cost_unit: 'character',
      pricing_hint: '0.15 USD per 1K characters'
    },
    {
      id: 'mdl_openai_image',
      provider_id: 'prv_openai',
      provider_name: 'openai',
      name: 'openai_image_default',
      display_name: 'OpenAI Image Default',
      model_code: 'dall-e-3',
      capability_type: 'image_generation',
      enabled: true,
      status: 'active',
      is_default: true,
      is_recommended: true,
      requires_verification: false,
      default_params: { size: '1024x1024', quality: 'standard' },
      param_ui_schema: {
        size: { label: '尺寸', type: 'select', options: ['1024x1024', '1024x1792', '1792x1024'] },
        quality: { label: '质量', type: 'select', options: ['standard', 'hd'] }
      },
      cost_unit: 'image',
      pricing_hint: '0.040 USD per image'
    },
    {
      id: 'mdl_fal_flux',
      provider_id: 'prv_fal',
      provider_name: 'fal',
      name: 'fal_flux_dev',
      display_name: 'Flux Dev (fal.ai)',
      model_code: 'black-forest-labs/flux-dev',
      capability_type: 'image_generation',
      enabled: true,
      status: 'active',
      is_default: false,
      is_recommended: true,
      requires_verification: false,
      default_params: { size: '1024x1024' },
      param_ui_schema: {
        aspect_ratio: { label: '纵横比', type: 'select', options: ['1:1', '9:16', '16:9', '4:3', '3:4'] }
      },
      cost_unit: 'image',
      pricing_hint: '0.025 USD per image'
    },
    {
      id: 'mdl_mock_video',
      provider_id: 'prv_mock',
      provider_name: 'mock',
      name: 'mock_video_generation',
      display_name: 'Mock Video Generator',
      model_code: 'mock-video-model',
      capability_type: 'video_generation',
      enabled: true,
      status: 'active',
      is_default: true,
      is_recommended: true,
      requires_verification: false,
      default_params: { duration_seconds: 5, aspect_ratio: '16:9' },
      param_ui_schema: {
        duration_seconds: { label: '时长(秒)', type: 'select', options: [3, 5, 8, 10] },
        aspect_ratio: { label: '比例', type: 'select', options: ['16:9', '9:16', '1:1'] }
      },
      cost_unit: 'video_second',
      pricing_hint: 'Free (mock)'
    }
  ],
  experiments: [],
  assets: [],
  evaluations: [],
  costRecords: [],
  prompts: [
    {
      id: 'pmt_1',
      name: '小红书科技风封面',
      capability_type: 'image_generation',
      scenario: 'image_generation',
      content: '科幻未来感芯片，深蓝与霓虹橙偏光，极简扁平构图，{{theme}} 概念核心。',
      template: '科幻未来感芯片，深蓝与霓虹橙偏光，极简扁平构图，{{theme}} 概念核心。',
      variables_schema_json: {
        type: 'object',
        properties: { theme: { type: 'string', label: '主题' } },
        required: ['theme']
      },
      variables_schema: {
        type: 'object',
        properties: { theme: { type: 'string', label: '主题' } },
        required: ['theme']
      },
      default_values_json: { theme: 'AI Agent' },
      version: 1,
      version_group_id: 'grp_pmt_1',
      parent_template_id: null,
      content_hash: 'h_pmt_1',
      is_latest: true,
      status: 'active',
      rating: 5,
      usage_count: 8,
      is_favorite: true
    },
    {
      id: 'pmt_2',
      name: '专业短视频旁白润色',
      capability_type: 'tts_style',
      scenario: 'tts_style',
      content: '「注意断句和知识颗粒感，稍带一些磁性语调」：下面我们要讲的是关于{{topic}}的事实。',
      template: '「注意断句和知识颗粒感，稍带一些磁性语调」：下面我们要讲的是关于{{topic}}的事实。',
      variables_schema_json: {
        type: 'object',
        properties: { topic: { type: 'string', label: '话题' } },
        required: ['topic']
      },
      variables_schema: {
        type: 'object',
        properties: { topic: { type: 'string', label: '话题' } },
        required: ['topic']
      },
      default_values_json: { topic: '内容流水线' },
      version: 1,
      version_group_id: 'grp_pmt_2',
      parent_template_id: null,
      content_hash: 'h_pmt_2',
      is_latest: true,
      status: 'active',
      rating: 4,
      usage_count: 5,
      is_favorite: false
    }
  ],
  tasks: {},
  projects: []
};

// Polling simulation worker state updates
setInterval(() => {
  Object.keys(mockStore.tasks).forEach((taskId) => {
    const task = mockStore.tasks[taskId];
    if (['succeeded', 'failed', 'timeout', 'cancelled'].includes(task.status)) return;

    // Transition mock state machines
    if (task.status === 'pending') {
      task.status = 'queued';
      task.progress = 5;
    } else if (task.status === 'queued') {
      task.status = 'running';
      task.progress = 20;
    } else if (task.status === 'running') {
      task.status = 'provider_pending';
      task.progress = 35;
    } else if (task.status === 'provider_pending') {
      task.status = 'provider_running';
      task.progress = 60;
    } else if (task.status === 'provider_running') {
      task.progress += 10;
      if (task.progress >= 90) {
        task.status = 'succeeded';
        task.progress = 100;
        task.finished_at = new Date().toISOString();

        // Create asset and link experiment on task finish
        const exp = mockStore.experiments.find((e) => e.id === task.experiment_id);
        if (exp) {
          exp.status = 'success';
          const assetId = genId('ast');
          const asset = {
            id: assetId,
            asset_type: exp.capability_type === 'video_generation' ? 'video' : 'image',
            role: exp.capability_type === 'video_generation' ? 'video_output' : 'image_output',
            source_type: 'generated',
            source_experiment_id: exp.id,
            file_name: `${assetId}.mp4`,
            mime_type: exp.capability_type === 'video_generation' ? 'video/mp4' : 'image/png',
            extension: exp.capability_type === 'video_generation' ? 'mp4' : 'png',
            storage_backend: 'local_volume',
            relative_path: exp.capability_type === 'video_generation'
              ? `assets/video/2026/06/16/${assetId}.mp4`
              : `assets/image/2026/06/16/${assetId}.png`,
            download_path: `/api/assets/${assetId}/download`,
            thumbnail_path: `/api/assets/${assetId}/thumbnail`,
            size_bytes: 4890123,
            sha256: 'mock_sha256_hash_value_for_verification',
            width: 1920,
            height: 1080,
            duration_seconds: 5,
            rating: null,
            is_featured: false,
            is_discarded: false,
            status: 'active',
            created_at: new Date().toISOString()
          };
          mockStore.assets.unshift(asset);
          exp.output_asset_refs_json = [{ asset_id: asset.id, asset_type: asset.asset_type, role: asset.role }];
          task.result_json = { asset_id: asset.id };

          // Create mock cost records
          const costId = genId('cost');
          const cost = {
            id: costId,
            experiment_id: exp.id,
            provider_id: exp.provider_id,
            model_id: exp.model_id,
            capability_type: exp.capability_type,
            cost_type: 'model_call',
            unit_type: exp.capability_type === 'video_generation' ? 'video_second' : 'image',
            input_units: 0,
            output_units: 5,
            total_units: 5,
            estimated_cost: 0.12,
            currency: 'USD',
            pricing_snapshot_json: {},
            created_at: new Date().toISOString()
          };
          mockStore.costRecords.unshift(cost);
        }
      }
    }
  });
}, 3000);

export class APIClient {
  constructor() {
    const defaultUrl = inferDefaultApiBaseUrl();
    let savedUrl = normalizeBaseUrl(getStorageValue('aiwm_api_base_url'));

    if (shouldReplaceSavedApiBaseUrl(savedUrl, defaultUrl)) {
      savedUrl = defaultUrl;
      setStorageValue('aiwm_api_base_url', defaultUrl);
    }

    this.baseUrl = savedUrl || defaultUrl;
    this.mockMode = getStorageValue('aiwm_mock_mode') === 'true';
  }


  setBaseUrl(url) {
    this.baseUrl = normalizeBaseUrl(url);
    setStorageValue('aiwm_api_base_url', this.baseUrl);
  }

  getBaseUrl() {
    return this.baseUrl;
  }

  getDisplayBaseUrl() {
    return this.baseUrl || `${globalThis.window?.location?.origin || ''} (same-origin /api proxy)`;
  }

  setMockMode(enabled) {
    this.mockMode = enabled;
    setStorageValue('aiwm_mock_mode', enabled ? 'true' : 'false');
  }

  isMockMode() {
    return this.mockMode;
  }

  resolvePaths(obj) {
    if (!obj) return obj;
    if (Array.isArray(obj)) {
      return obj.map(item => this.resolvePaths(item));
    }
    if (typeof obj === 'object') {
      const result = {};
      for (const key in obj) {
        let val = obj[key];
        if (typeof val === 'string' && 
            (key === 'download_path' || key === 'thumbnail_path' || key === 'download_url') && 
            val.startsWith('/')) {
          val = `${this.baseUrl}${val}`;
        } else if (typeof val === 'object' && val !== null) {
          val = this.resolvePaths(val);
        }
        result[key] = val;
      }
      return result;
    }
    return obj;
  }

  async request(path, options = {}) {
    if (this.mockMode) {
      return this.resolvePaths(this.handleMock(path, options));
    }

    const url = `${this.baseUrl}${path}`;
    const headers = {
      'Content-Type': 'application/json',
      ...options.headers
    };

    try {
      const response = await fetch(url, { ...options, headers });
      if (!response.ok) {
        let errData;
        try {
          errData = await response.json();
        } catch (_) {
          errData = { error_type: 'UNKNOWN_ERROR', message: `HTTP error ${response.status}` };
        }
        throw errData;
      }
      const data = await response.json();
      return this.resolvePaths(data);
    } catch (error) {
      if (error.error_type) throw error;
      throw {
        error_type: 'PROVIDER_TIMEOUT',
        message: error.message || 'Network request failed or timed out.'
      };
    }
  }

  // Handle Mock Logic Offline
  handleMock(path, options) {
    const method = options.method || 'GET';
    const params = options.body ? JSON.parse(options.body) : {};

    // 1. Providers
    if (path.startsWith('/api/providers')) {
      if (path === '/api/providers') {
        if (method === 'GET') {
          return mockStore.providers;
        } else if (method === 'POST') {
          const prv = {
            id: genId('prv'),
            ...params,
            status: 'testing',
            masked_credential: params.credential_ref ? `env:${params.credential_ref}` : 'none'
          };
          mockStore.providers.push(prv);
          return prv;
        }
      }
      const match = path.match(/\/api\/providers\/([^/]+)/);
      if (match) {
        const id = match[1];
        const index = mockStore.providers.findIndex((p) => p.id === id);
        if (index === -1) throw { error_type: 'PROVIDER_NOT_FOUND', message: 'Provider not found' };

        if (path.endsWith('/test-connection')) {
          if (mockStore.providers[index].name === 'elevenlabs' && !mockStore.providers[index].enabled) {
            throw { error_type: 'CREDENTIAL_NOT_FOUND', message: 'Key reference invalid or empty' };
          }
          mockStore.providers[index].status = 'active';
          return { ok: true, status: 'active', message: 'Provider connection test passed' };
        }

        if (method === 'GET') return mockStore.providers[index];
        if (method === 'PATCH') {
          mockStore.providers[index] = { ...mockStore.providers[index], ...params };
          return mockStore.providers[index];
        }
        if (method === 'DELETE') {
          mockStore.providers.splice(index, 1);
          return { ok: true };
        }
      }
    }

    // 2. Models
    if (path.startsWith('/api/models')) {
      if (path === '/api/models') {
        if (method === 'GET') return mockStore.models;
        if (method === 'POST') {
          const mdl = {
            id: genId('mdl'),
            ...params,
            is_default: false,
            is_recommended: false,
            status: 'testing',
            requires_verification: true
          };
          mockStore.models.push(mdl);
          return mdl;
        }
      }
      const match = path.match(/\/api\/models\/([^/]+)/);
      if (match) {
        const id = match[1];
        const index = mockStore.models.findIndex((m) => m.id === id);
        if (index === -1) throw { error_type: 'MODEL_NOT_FOUND', message: 'Model not found' };



        if (method === 'GET') return mockStore.models[index];
        if (method === 'PATCH') {
          mockStore.models[index] = { ...mockStore.models[index], ...params };
          return mockStore.models[index];
        }
        if (method === 'DELETE') {
          mockStore.models.splice(index, 1);
          return { ok: true };
        }
      }
    }

    // 3. Capabilities / Models query
    if (path.startsWith('/api/capabilities/models')) {
      const type = new URLSearchParams(path.split('?')[1]).get('type');
      return mockStore.models.filter((m) => m.capability_type === type && m.enabled);
    }

    // 4. Capability Run (Standard Synchronous / Mock Async Task Trigger)
    if (path === '/api/capabilities/run') {
      const model = mockStore.models.find((m) => m.id === params.model_id);
      if (!model) throw { error_type: 'MODEL_NOT_FOUND', message: 'Model registry item missing' };

      const expId = genId('exp');
      const latency = Math.floor(Math.random() * 2000) + 500;

      // Check validation constraints
      if (params.capability_type === 'tts' && (!params.input || !params.input.text)) {
        throw { error_type: 'VALIDATION_ERROR', message: 'TTS prompt text is required' };
      }
      if (params.capability_type === 'image_generation' && (!params.input || !params.input.prompt)) {
        throw { error_type: 'VALIDATION_ERROR', message: 'Image prompt string is required' };
      }

      // Check simulated blocked prompts
      if (params.input && (params.input.text || params.input.prompt || '').toLowerCase().includes('violation')) {
        throw { error_type: 'CONTENT_BLOCKED', message: 'Prompt blocked by safety filter.' };
      }

      const exp = {
        id: expId,
        request_id: genId('req'),
        title: `${params.capability_type.toUpperCase()} - ${model.display_name} - Mock`,
        capability_type: params.capability_type,
        status: params.run_mode === 'async' ? 'pending' : 'success',
        result_mode: params.run_mode === 'async' ? 'async_task' : 'sync_file',
        provider_id: model.provider_id,
        model_id: model.id,
        adapter_name: model.adapter_name || 'mock',
        adapter_version: '0.1.0',
        input_text: params.input.text || params.input.prompt,
        input_json: params.input,
        params_json: params.params || {},
        final_params_json: { ...model.default_params, ...params.params },
        output_asset_refs_json: [],
        latency_ms: latency,
        created_at: new Date().toISOString()
      };
      mockStore.experiments.unshift(exp);

      if (params.run_mode === 'async') {
        const taskId = genId('task');
        const task = {
          id: taskId,
          experiment_id: expId,
          provider_id: model.provider_id,
          model_id: model.id,
          capability_type: params.capability_type,
          task_type: 'video_generation',
          status: 'pending',
          progress: 0,
          celery_task_id: genId('celery'),
          provider_task_id: genId('pred'),
          request_json: params,
          result_json: null,
          created_at: new Date().toISOString()
        };
        mockStore.tasks[taskId] = task;
        return {
          request_id: exp.request_id,
          experiment_id: expId,
          task_id: taskId,
          status: 'queued',
          result_mode: 'async_task'
        };
      }

      // Synchronous creation of final Assets
      const assetId = genId('ast');
      const asset = {
        id: assetId,
        asset_type: params.capability_type === 'tts' ? 'audio' : 'image',
        role: params.capability_type === 'tts' ? 'audio_output' : 'image_output',
        source_type: 'generated',
        source_experiment_id: expId,
        file_name: params.capability_type === 'tts' ? `${assetId}.mp3` : `${assetId}.png`,
        mime_type: params.capability_type === 'tts' ? 'audio/mpeg' : 'image/png',
        extension: params.capability_type === 'tts' ? 'mp3' : 'png',
        storage_backend: 'local_volume',
        relative_path: params.capability_type === 'tts'
          ? `assets/audio/2026/06/16/${assetId}.mp3`
          : `assets/image/2026/06/16/${assetId}.png`,
        download_path: `/api/assets/${assetId}/download`,
        thumbnail_path: `/api/assets/${assetId}/thumbnail`,
        size_bytes: params.capability_type === 'tts' ? 245000 : 1024000,
        sha256: 'mock_sha256_hash_value_for_verification',
        width: params.capability_type === 'tts' ? null : 1024,
        height: params.capability_type === 'tts' ? null : 1024,
        duration_seconds: params.capability_type === 'tts' ? 12.5 : null,
        rating: null,
        is_featured: false,
        is_discarded: false,
        status: 'active',
        created_at: new Date().toISOString()
      };
      mockStore.assets.unshift(asset);
      exp.output_asset_refs_json = [{ asset_id: assetId, asset_type: asset.asset_type, role: asset.role }];

      // Create cost record
      const costId = genId('cost');
      const cost = {
        id: costId,
        experiment_id: expId,
        provider_id: model.provider_id,
        model_id: model.id,
        capability_type: params.capability_type,
        cost_type: 'model_call',
        unit_type: params.capability_type === 'tts' ? 'character' : 'image',
        input_units: params.capability_type === 'tts' ? exp.input_text.length : 0,
        output_units: params.capability_type === 'tts' ? 0 : 1,
        total_units: params.capability_type === 'tts' ? exp.input_text.length : 1,
        estimated_cost: params.capability_type === 'tts' ? exp.input_text.length * 0.000015 : 0.04,
        currency: 'USD',
        pricing_snapshot_json: {},
        created_at: new Date().toISOString()
      };
      mockStore.costRecords.unshift(cost);

      return {
        request_id: exp.request_id,
        experiment_id: expId,
        status: 'success',
        result_mode: 'sync_file',
        assets: [{
          asset_id: assetId,
          asset_type: asset.asset_type,
          download_url: asset.download_path
        }],
        latency_ms: latency,
        error: null
      };
    }

    // 5. Experiments
    if (path.startsWith('/api/experiments')) {
      if (path === '/api/experiments') {
        return mockStore.experiments;
      }
      const match = path.match(/\/api\/experiments\/([^/]+)/);
      if (match) {
        const id = match[1];
        const index = mockStore.experiments.findIndex((e) => e.id === id);
        if (index === -1) throw { error_type: 'MODEL_NOT_FOUND', message: 'Experiment not found' };

        if (path.endsWith('/mark-best')) {
          mockStore.experiments[index].is_best = true;
          return mockStore.experiments[index];
        }
        if (path.endsWith('/mark-failed-case')) {
          mockStore.experiments[index].is_failed_case = true;
          mockStore.experiments[index].failed_reason = params.failure_reason;
          return mockStore.experiments[index];
        }
        if (path.endsWith('/rerun')) {
          const orig = mockStore.experiments[index];
          return this.handleMock('/api/capabilities/run', {
            method: 'POST',
            body: JSON.stringify({
              capability_type: orig.capability_type,
              model_id: orig.model_id,
              input: orig.input_json,
              params: { ...orig.final_params_json, ...params.override_params },
              run_mode: orig.result_mode === 'async_task' ? 'async' : 'sync'
            })
          });
        }

        if (method === 'GET') {
          return mockStore.experiments[index];
        }
        if (method === 'PATCH') {
          mockStore.experiments[index] = { ...mockStore.experiments[index], ...params };
          return mockStore.experiments[index];
        }
      }
    }

    // 6. Assets
    if (path.startsWith('/api/assets')) {
      if (path === '/api/assets') {
        return mockStore.assets;
      }
      const match = path.match(/\/api\/assets\/([^/]+)/);
      if (match) {
        const id = match[1];
        const index = mockStore.assets.findIndex((a) => a.id === id);
        if (index === -1) throw { error_type: 'FILE_NOT_FOUND', message: 'Asset not found' };

        if (path.endsWith('/download')) {
          // In mock mode, we just return dummy metadata or trigger virtual file download
          return { download_url: mockStore.assets[index].relative_path };
        }
        if (path.endsWith('/rate')) {
          mockStore.assets[index].rating = params.score;
          // Synchronize standard Usability Evaluation
          this.handleMock('/api/evaluations/upsert', {
            method: 'POST',
            body: JSON.stringify({
              target_type: 'asset',
              target_id: id,
              dimension: 'overall',
              score: params.score
            })
          });
          return mockStore.assets[index];
        }
        if (path.endsWith('/discard')) {
          mockStore.assets[index].status = 'discarded';
          mockStore.assets[index].is_discarded = true;
          return mockStore.assets[index];
        }
        if (path.endsWith('/delete')) {
          mockStore.assets[index].status = 'deleted';
          mockStore.assets[index].deleted_at = new Date().toISOString();
          return mockStore.assets[index];
        }

        if (method === 'GET') return mockStore.assets[index];
        if (method === 'PATCH') {
          mockStore.assets[index] = { ...mockStore.assets[index], ...params };
          return mockStore.assets[index];
        }
      }
    }

    // 7. Prompts
    if (path.startsWith('/api/prompts')) {
      if (path === '/api/prompts') {
        if (method === 'GET') return mockStore.prompts;
        if (method === 'POST') {
          const now = new Date().toISOString();
          const content = params.content ?? params.template ?? '';
          const capability = params.capability_type || params.scenario || 'image_generation';
          const variablesSchema = params.variables_schema_json || params.variables_schema || {};
          const created = {
            id: genId('pmt'),
            name: params.name,
            capability_type: capability,
            scenario: capability,
            content,
            template: content,
            variables_schema_json: variablesSchema,
            variables_schema: variablesSchema,
            default_values_json: params.default_values_json || {},
            version: 1,
            version_group_id: genId('grp_pmt'),
            parent_template_id: null,
            content_hash: genId('h_pmt'),
            is_latest: true,
            status: 'active',
            rating: null,
            usage_count: 0,
            success_count: 0,
            failure_count: 0,
            is_favorite: false,
            notes: params.notes || null,
            description: params.description || null,
            metadata_json: params.metadata_json || {},
            created_at: now,
            updated_at: now
          };
          mockStore.prompts.unshift(created);
          return created;
        }
      }
      const match = path.match(/\/api\/prompts\/([^/]+)/);
      if (match) {
        const id = match[1];
        const index = mockStore.prompts.findIndex((p) => p.id === id);
        if (index === -1) throw { error_type: 'MODEL_NOT_FOUND', message: 'Prompt Template not found' };

        if (path.endsWith('/duplicate')) {
          const copy = {
            ...mockStore.prompts[index],
            id: genId('pmt'),
            name: `${mockStore.prompts[index].name} (Copy)`,
            version_group_id: genId('grp_pmt'),
            parent_template_id: id,
            is_latest: true
          };
          mockStore.prompts.push(copy);
          return copy;
        }

        if (path.endsWith('/new-version')) {
          mockStore.prompts[index].is_latest = false;
          const content = params.content ?? params.template ?? mockStore.prompts[index].content ?? mockStore.prompts[index].template;
          const variablesSchema = params.variables_schema_json || params.variables_schema || mockStore.prompts[index].variables_schema_json || mockStore.prompts[index].variables_schema || {};
          const next = {
            ...mockStore.prompts[index],
            id: genId('pmt'),
            version: Number(mockStore.prompts[index].version || 1) + 1,
            parent_template_id: id,
            is_latest: true,
            content,
            template: content,
            variables_schema_json: variablesSchema,
            variables_schema: variablesSchema,
            default_values_json: params.default_values_json || mockStore.prompts[index].default_values_json || {},
            updated_at: new Date().toISOString()
          };
          mockStore.prompts.push(next);
          return next;
        }

        if (method === 'GET') return mockStore.prompts[index];
        if (method === 'PATCH') {
          const hasSemanticFields = ['content', 'template', 'variables_schema_json', 'variables_schema', 'default_values_json'].some((key) => key in params);
          if (hasSemanticFields) {
            mockStore.prompts[index].is_latest = false;
            const content = params.content ?? params.template ?? mockStore.prompts[index].content ?? mockStore.prompts[index].template;
            const capability = params.capability_type || params.scenario || mockStore.prompts[index].capability_type || mockStore.prompts[index].scenario;
            const variablesSchema = params.variables_schema_json || params.variables_schema || mockStore.prompts[index].variables_schema_json || mockStore.prompts[index].variables_schema || {};
            const next = {
              ...mockStore.prompts[index],
              id: genId('pmt'),
              name: params.name || mockStore.prompts[index].name,
              capability_type: capability,
              scenario: capability,
              content,
              template: content,
              variables_schema_json: variablesSchema,
              variables_schema: variablesSchema,
              default_values_json: params.default_values_json || mockStore.prompts[index].default_values_json || {},
              version: Number(mockStore.prompts[index].version || 1) + 1,
              parent_template_id: id,
              is_latest: true,
              updated_at: new Date().toISOString()
            };
            mockStore.prompts.push(next);
            return next;
          }
          const capability = params.capability_type || params.scenario || mockStore.prompts[index].capability_type || mockStore.prompts[index].scenario;
          mockStore.prompts[index] = {
            ...mockStore.prompts[index],
            ...params,
            capability_type: capability,
            scenario: capability,
            updated_at: new Date().toISOString()
          };
          return mockStore.prompts[index];
        }
        if (method === 'DELETE') {
          mockStore.prompts[index].status = 'deleted';
          mockStore.prompts[index].is_latest = false;
          return mockStore.prompts[index];
        }
      }
    }

    // 8. Evaluations
    if (path.startsWith('/api/evaluations')) {
      if (path.startsWith('/api/evaluations?')) {
        const query = new URLSearchParams(path.split('?')[1]);
        const targetType = query.get('target_type');
        const targetId = query.get('target_id');
        return mockStore.evaluations.filter((ev) => ev.target_type === targetType && ev.target_id === targetId);
      }
      if (method === 'POST') {
        if (path.endsWith('/compare/conclusion')) {
          const ev = {
            id: genId('eval'),
            target_type: 'compare_conclusion',
            target_id: params.compare_group_id || 'default_group',
            dimension: 'conclusion',
            comment: params.comment,
            metadata_json: { target_ids: params.target_ids },
            created_at: new Date().toISOString()
          };
          mockStore.evaluations.push(ev);
          return ev;
        }
        // General upsert
        const existingIndex = mockStore.evaluations.findIndex(
          (ev) => ev.target_type === params.target_type &&
                  ev.target_id === params.target_id &&
                  ev.dimension === params.dimension
        );
        if (existingIndex !== -1) {
          mockStore.evaluations[existingIndex] = { ...mockStore.evaluations[existingIndex], ...params, updated_at: new Date().toISOString() };
          return mockStore.evaluations[existingIndex];
        }
        const ev = {
          id: genId('eval'),
          ...params,
          created_at: new Date().toISOString()
        };
        mockStore.evaluations.push(ev);
        return ev;
      }
    }

    // 9. Costs
    if (path === '/api/costs/summary') {
      const summary = {
        group_by: 'capability_type',
        items: ['tts', 'image_generation', 'video_generation'].map((type) => {
          const records = mockStore.costRecords.filter((r) => r.capability_type === type);
          const sum = records.reduce((acc, curr) => acc + (curr.estimated_cost || 0), 0);
          return {
            capability_type: type,
            currency: 'USD',
            estimated_total_cost: sum,
            known_cost_count: records.length,
            unknown_cost_count: 0,
            unit_summary: {}
          };
        })
      };
      return summary;
    }

    // 10. Async Tasks status
    if (path.startsWith('/api/tasks/')) {
      const match = path.match(/\/api\/tasks\/([^/]+)/);
      if (match) {
        const id = match[1];
        const task = mockStore.tasks[id];
        if (!task) throw { error_type: 'VALIDATION_ERROR', message: 'Task not found' };

        if (path.endsWith('/cancel')) {
          task.status = 'cancelled';
          const exp = mockStore.experiments.find((e) => e.id === task.experiment_id);
          if (exp) exp.status = 'cancelled';
          return { task_id: id, status: 'cancelled', message: 'Cancelled' };
        }
        if (path.endsWith('/retry')) {
          return this.handleMock('/api/capabilities/run', {
            method: 'POST',
            body: JSON.stringify(task.request_json)
          });
        }
        if (path.endsWith('/logs')) {
          return [
            { event_type: 'request_received', status: 'running', message: 'Received task.' },
            { event_type: 'task_started', status: 'running', message: 'Processing task on worker.' },
            { event_type: 'provider_status_updated', status: 'running', message: `Progress update: ${task.progress}%` }
          ];
        }

        return {
          task_id: id,
          experiment_id: task.experiment_id,
          status: task.status,
          experiment_status: mockStore.experiments.find((e) => e.id === task.experiment_id)?.status || 'running',
          progress: task.progress,
          provider_task_id: task.provider_task_id,
          provider_status: task.status,
          error: task.status === 'failed' ? { error_type: 'PROVIDER_INTERNAL_ERROR', message: 'Mock error occurred' } : null,
          assets: task.status === 'succeeded' ? [{ asset_id: task.result_json.asset_id }] : []
        };
      }
    }

    // 11. Projects (v0.4+)
    if (path.startsWith('/api/projects')) {
      if (path === '/api/projects') {
        if (method === 'GET') return mockStore.projects;
        if (method === 'POST') {
          const prj = {
            id: genId('prj'),
            name: params.name,
            description: params.description,
            status: 'idea',
            created_at: new Date().toISOString()
          };
          mockStore.projects.push(prj);
          return prj;
        }
      }
      const match = path.match(/\/api\/projects\/([^/]+)/);
      if (match) {
        const id = match[1];
        const index = mockStore.projects.findIndex((p) => p.id === id);
        if (index === -1) throw { error_type: 'VALIDATION_ERROR', message: 'Project not found' };

        if (path.endsWith('/export/manifest')) {
          return {
            project_id: id,
            name: mockStore.projects[index].name,
            selected_script_id: null,
            warnings: [],
            shots: [],
            assets: []
          };
        }

        if (method === 'GET') return mockStore.projects[index];
        if (method === 'PATCH') {
          mockStore.projects[index] = { ...mockStore.projects[index], ...params };
          return mockStore.projects[index];
        }
        if (method === 'DELETE') {
          mockStore.projects.splice(index, 1);
          return { ok: true };
        }
      }
    }

    // Fallback for unhandled mock endpoints
    return { mock: true, path, method };
  }
}
