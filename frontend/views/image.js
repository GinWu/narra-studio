import { ref, onMounted, inject, computed } from 'vue';

export default {
  name: 'ImageView',
  template: `
    <div class="image-lab-page">
      <div class="lab-two-column">
        <!-- Input Form -->
        <div class="lab-config-panel glass-card">
          <h3 style="font-family: var(--font-heading); font-size: 1.25rem; margin-bottom: 20px;">{{ t('image.config.title') }}</h3>
          
          <form @submit.prevent="generateImage" style="display: flex; flex-direction: column; gap: 16px;">
            <!-- Model Select -->
            <div>
              <label class="input-label">{{ t('image.config.model') }}</label>
              <select class="select-field" v-model="selectedModelId" required @change="onModelChange">
                <option value="" disabled>No enabled image models available</option>
                <option v-for="m in models" :key="m.id" :value="m.id">
                  {{ m.display_name }} ({{ m.pricing_hint }})
                </option>
              </select>
              <p v-if="models.length === 0" style="font-size: 0.75rem; color: var(--warning); margin-top: 4px;">
                No enabled image models found. Configure models or switch to Mock Mode.
              </p>
            </div>

            <!-- Prompt Template Options -->
            <div>
              <label class="input-label">{{ t('image.config.template') }}</label>
              <select class="select-field" v-model="selectedPromptId" @change="onPromptTemplateChange">
                <option value="">{{ t('image.config.directPromptMode') }}</option>
                <option v-for="p in promptTemplates" :key="p.id" :value="p.id">
                  {{ p.name }} (v{{ p.version }})
                </option>
              </select>
            </div>

            <!-- Dynamic Variables Input -->
            <div v-if="selectedPrompt && Object.keys(templateVariables).length > 0" 
                 style="background-color: var(--bg-tertiary); padding: 14px; border-radius: 8px; border: 1px solid var(--border-color); display: flex; flex-direction: column; gap: 12px;">
              <h4 style="font-size: 0.8rem; text-transform: uppercase; color: var(--text-secondary); margin-bottom: 4px;">{{ t('image.config.variables') }}</h4>
              <div v-for="(val, varName) in templateVariables" :key="varName">
                <label class="input-label" style="font-size: 0.8rem;">{{ getVariableLabel(varName) }}</label>
                <input type="text" class="input-field" v-model="templateVariables[varName]" @input="assemblePrompt" required>
              </div>
            </div>

            <!-- Prompt text input -->
            <div>
              <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                <label class="input-label" style="margin-bottom: 0;">{{ t('image.config.prompt') }}</label>
                <span style="font-size: 0.75rem; color: var(--text-muted);">
                  {{ rawPrompt.length }} / 800
                </span>
              </div>
              <textarea class="input-field" style="min-height: 100px; line-height: 1.4;" 
                        v-model="rawPrompt" required placeholder="Describe the image you want to generate..."
                        :disabled="!!selectedPromptId"></textarea>
            </div>

            <!-- Negative prompt input -->
            <div>
              <label class="input-label">{{ t('image.config.negative') }}</label>
              <input type="text" class="input-field" v-model="negativePrompt" placeholder="Elements to avoid in the image...">
            </div>

            <!-- Model specific dynamic parameters based on Schema -->
            <div v-if="uiSchema" style="background-color: var(--bg-tertiary); padding: 14px; border-radius: 8px; border: 1px solid var(--border-color); display: flex; flex-direction: column; gap: 14px;">
              <h4 style="font-size: 0.8rem; text-transform: uppercase; color: var(--text-secondary); margin-bottom: 4px;">{{ t('image.config.settings') }}</h4>
              
              <div v-for="(schema, key) in uiSchema" :key="key">
                <!-- Select UI -->
                <div v-if="schema.type === 'select'">
                  <label class="input-label">{{ schema.label }}</label>
                  <select class="select-field" v-model="params[key]">
                    <option v-for="opt in schema.options" :key="opt" :value="opt">{{ opt }}</option>
                  </select>
                </div>
              </div>
            </div>

            <!-- Count input -->
            <div>
              <label class="input-label">{{ t('image.config.count') }}</label>
              <input type="number" class="input-field" v-model.number="n" min="1" max="4" required>
              <p v-if="selectedModelId.includes('dall-e-3')" style="font-size: 0.75rem; color: var(--warning); margin-top: 4px;">
                Note: DALL-E 3 adapter enforces N=1 per API guidelines.
              </p>
            </div>

            <button type="submit" class="btn btn-primary" style="margin-top: 8px; font-size: 1rem; padding: 12px 20px;" :disabled="generating || !selectedModelId">
              <i class="fas" :class="generating ? 'fa-spinner animate-spin' : 'fa-image'"></i>
              {{ generating ? t('image.config.buttonGenerating') : t('image.config.buttonGenerate') }}
            </button>
          </form>
        </div>

        <!-- Image Results Gallery -->
        <div class="lab-results-panel glass-card">
          <h3 style="font-family: var(--font-heading); font-size: 1.25rem; margin-bottom: 20px;">{{ t('image.history.title') }}</h3>
          
          <div style="flex: 1; overflow-y: auto; padding-right: 4px;">
            <div v-if="imageHistory.length === 0" style="text-align: center; padding: 80px 0; color: var(--text-secondary);">
              <i class="fas fa-images" style="font-size: 3.5rem; color: var(--text-muted); margin-bottom: 16px;"></i>
              <p>{{ t('image.history.empty') }}</p>
            </div>
            
            <div v-else class="image-gallery-grid">
              <div v-for="item in imageHistory" :key="item.exp.id" class="image-card" 
                   style="height: auto; aspect-ratio: auto; display: flex; flex-direction: column; justify-content: space-between; padding: 12px; background-color: var(--bg-tertiary); position: relative;">
                
                <!-- Display generated image -->
                <div v-if="item.asset" style="aspect-ratio: 1; position: relative; border-radius: 6px; overflow: hidden; background-color: var(--bg-primary); cursor: pointer;" 
                     @click="openLightbox(item.asset.download_path)">
                  <img :src="item.asset.download_path" alt="Generated" style="width: 100%; height: 100%; object-fit: cover;">
                  
                  <!-- Quality Star badge overlay top right -->
                  <div v-if="item.asset.rating" style="position: absolute; top: 8px; right: 8px; background-color: rgba(0,0,0,0.6); padding: 2px 6px; border-radius: 4px; font-size: 0.75rem; color: var(--warning); display: flex; align-items: center; gap: 4px;">
                    <i class="fas fa-star"></i> {{ item.asset.rating }}
                  </div>
                </div>
                <div v-else style="aspect-ratio: 1; background-color: var(--bg-primary); border-radius: 6px; display: flex; align-items: center; justify-content: center; color: var(--text-muted); font-size: 0.8rem;">
                  No preview asset
                </div>

                <!-- Text metadata -->
                <div style="margin-top: 8px; flex: 1;">
                  <span class="badge badge-cyan" style="font-size: 0.55rem;">{{ getModelDisplayName(item.exp.model_id) }}</span>
                  <p style="font-size: 0.75rem; color: var(--text-secondary); margin-top: 4px; text-overflow: ellipsis; overflow: hidden; white-space: nowrap;" :title="item.exp.input_text">
                    {{ item.exp.input_text }}
                  </p>
                </div>

                <!-- Rating and state flags -->
                <div style="margin-top: 8px; border-top: 1px solid rgba(255,255,255,0.05); padding-top: 8px;">
                  <div style="display: flex; justify-content: space-between; align-items: center; font-size: 0.75rem; margin-bottom: 6px;">
                    <span style="color: var(--text-muted);">{{ t('image.history.rateQuality') }}</span>
                    <div class="rating-stars" style="font-size: 0.8rem; cursor: pointer;">
                      <i v-for="i in 5" :key="i" class="fas fa-star" 
                         :class="i <= (item.asset?.rating || 0) ? 'rating-star-active' : ''" 
                         @click="rateAsset(item.asset.id, i)"></i>
                    </div>
                  </div>

                  <!-- Badges for Best/Failed -->
                  <div style="display: flex; gap: 4px; margin-bottom: 8px; flex-wrap: wrap;">
                    <span v-if="item.exp.is_best" class="badge badge-success" style="font-size: 0.6rem; padding: 2px 6px;">{{ t('voice.history.badgeBest') }}</span>
                    <span v-if="item.exp.is_failed_case" class="badge badge-danger" style="font-size: 0.6rem; padding: 2px 6px;" :title="item.exp.failed_reason">{{ t('voice.history.badgeFailed') }}</span>
                  </div>

                  <!-- Mini action buttons row -->
                  <div style="display: flex; justify-content: space-between; align-items: center; gap: 4px;">
                    <button class="btn btn-secondary" style="padding: 4px 6px; font-size: 0.7rem; flex: 1;" @click="rerunExperiment(item.exp)">
                      <i class="fas fa-rotate-left"></i> {{ t('voice.history.actionRerun') }}
                    </button>
                    <button v-if="!item.exp.is_best" class="btn btn-secondary" style="padding: 4px 6px; font-size: 0.7rem; color: var(--success); flex: 1;" @click="markAsBest(item.exp.id)">
                      {{ t('voice.history.badgeBest') }}
                    </button>
                    <button v-if="!item.exp.is_failed_case" class="btn btn-secondary" style="padding: 4px 6px; font-size: 0.7rem; color: var(--error); flex: 1;" @click="openFailModal(item.exp.id)">
                      {{ t('voice.history.badgeFailed') }}
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Lightbox preview -->
      <div v-if="lightboxSrc" class="modal-overlay" @click="closeLightbox" style="background-color: rgba(0,0,0,0.95);">
        <img :src="lightboxSrc" style="max-width: 90vw; max-height: 90vh; border-radius: 8px; border: 1px solid var(--border-color); box-shadow: 0 10px 40px rgba(0,0,0,0.8);" @click.stop>
      </div>

      <!-- Mark Failure Reason Modal -->
      <div v-if="failModalExpId" class="modal-overlay">
        <div class="modal-content glass-card" style="max-width: 450px;">
          <div class="modal-header">
            <h3>{{ t('image.failModal.title') }}</h3>
            <button class="toast-close" @click="closeFailModal"><i class="fas fa-times"></i></button>
          </div>
          <div style="display: flex; flex-direction: column; gap: 14px;">
            <p style="font-size: 0.85rem; color: var(--text-secondary);">
              {{ t('image.failModal.desc') }}
            </p>
            <div>
              <label class="input-label">{{ t('image.failModal.labelCategory') }}</label>
              <select class="select-field" v-model="failReasonCategory">
                <option value="deformed_anatomy">{{ t('image.failModal.categories.deformed_anatomy') }}</option>
                <option value="poor_details">{{ t('image.failModal.categories.poor_details') }}</option>
                <option value="blurry_image">{{ t('image.failModal.categories.blurry_image') }}</option>
                <option value="prompt_mismatch">{{ t('image.failModal.categories.prompt_mismatch') }}</option>
                <option value="other">{{ t('image.failModal.categories.other') }}</option>
              </select>
            </div>
            <div>
              <label class="input-label">{{ t('image.failModal.labelDetail') }}</label>
              <textarea class="input-field" style="min-height: 80px;" v-model="failReasonDetail" placeholder="Describe the image issue details..."></textarea>
            </div>
            <div style="display: flex; justify-content: flex-end; gap: 10px; margin-top: 10px;">
              <button class="btn btn-secondary" @click="closeFailModal">{{ t('common.cancel') }}</button>
              <button class="btn btn-primary" @click="submitFailureCase">{{ t('image.failModal.buttonFlag') }}</button>
            </div>
          </div>
        </div>
      </div>
    </div>
  `,
  setup() {
    const apiClient = inject('apiClient');
    const addToast = inject('addToast');
    const loadCosts = inject('loadCosts');
    const t = inject('t');

    const models = ref([]);
    const promptTemplates = ref([]);
    
    const selectedModelId = ref('');
    const selectedPromptId = ref('');
    
    const templateVariables = ref({});
    const rawPrompt = ref('');
    const negativePrompt = ref('');
    const params = ref({});
    const n = ref(1);
    const generating = ref(false);
    
    const imageHistory = ref([]);
    const lightboxSrc = ref(null);

    // Failure modal helper
    const failModalExpId = ref(null);
    const failReasonCategory = ref('poor_details');
    const failReasonDetail = ref('');

    // Computed UI schema from selected model
    const selectedModel = computed(() => {
      return models.value.find(m => m.id === selectedModelId.value);
    });

    const uiSchema = computed(() => {
      return selectedModel.value?.param_ui_schema || null;
    });

    const selectedPrompt = computed(() => {
      return promptTemplates.value.find(p => p.id === selectedPromptId.value);
    });

    const normalizePrompt = (prompt) => {
      const capability = prompt.capability_type || prompt.scenario || '';
      const content = prompt.content ?? prompt.template ?? '';
      const variablesSchema = prompt.variables_schema_json || prompt.variables_schema || {};
      return {
        ...prompt,
        scenario: capability,
        template: content,
        variables_schema: variablesSchema,
        default_values_json: prompt.default_values_json || {}
      };
    };

    const loadImageData = async () => {
      try {
        // Load only enabled image generation models
        const modelsData = await apiClient.request('/api/models');
        models.value = modelsData.filter(m => m.capability_type === 'image_generation' && m.enabled);
        if (models.value.length > 0) {
          selectedModelId.value = models.value.find(m => m.is_default)?.id || models.value[0].id;
          onModelChange();
        }

        // Load prompts for image_generation
        const promptsData = await apiClient.request('/api/prompts');
        promptTemplates.value = promptsData
          .map(normalizePrompt)
          .filter(p => p.scenario === 'image_generation' && p.is_latest);

        // Load generated image history
        loadImageHistory();
      } catch (err) {
        addToast('error', 'Error initializing Image Lab', err.message);
      }
    };

    const loadImageHistory = async () => {
      try {
        const experiments = await apiClient.request('/api/experiments');
        const assets = await apiClient.request('/api/assets');

        // Filter image experiments
        const imageExps = experiments.filter(e => e.capability_type === 'image_generation');
        
        imageHistory.value = imageExps.map(exp => {
          // Find output asset
          const ref = exp.output_asset_refs_json?.[0];
          const asset = ref ? assets.find(a => a.id === ref.asset_id) : null;
          return { exp, asset };
        });
      } catch (err) {
        console.error('Failed to load history:', err);
      }
    };

    const onModelChange = () => {
      const model = selectedModel.value;
      if (model) {
        // Initialize default parameters
        params.value = { ...model.default_params };
        if (model.id.includes('dall-e-3')) {
          n.value = 1; // Enforce N=1 for DALL-E 3
        }
      }
    };

    const onPromptTemplateChange = () => {
      const pmt = selectedPrompt.value;
      if (pmt) {
        // Parse template variables
        const variables = {};
        if (pmt.variables_schema && pmt.variables_schema.properties) {
          Object.keys(pmt.variables_schema.properties).forEach(k => {
            variables[k] = pmt.default_values_json?.[k] || '';
          });
        }
        templateVariables.value = variables;
        assemblePrompt();
      } else {
        templateVariables.value = {};
        rawPrompt.value = '';
      }
    };

    const getVariableLabel = (name) => {
      const prop = selectedPrompt.value?.variables_schema?.properties?.[name];
      return prop?.label || name;
    };

    const assemblePrompt = () => {
      const pmt = selectedPrompt.value;
      if (!pmt) return;
      
      let assembled = pmt.template;
      Object.keys(templateVariables.value).forEach(k => {
        assembled = assembled.replace(new RegExp(`{{\\s*${k}\\s*}}`, 'g'), templateVariables.value[k]);
      });
      rawPrompt.value = assembled;
    };

    const generateImage = async () => {
      // Validate inputs
      const cleanPrompt = rawPrompt.value.trim();
      if (!cleanPrompt) {
        addToast('error', 'Validation Error', 'Image prompt is required.');
        return;
      }
      if (cleanPrompt.length > 800) {
        addToast('error', 'Validation Error', 'Image Lab prompt inputs are restricted to 800 characters.');
        return;
      }

      // N constraints
      if (selectedModelId.value.includes('dall-e-3') && n.value !== 1) {
        addToast('error', 'Constraint Violation', 'DALL-E 3 adapter enforces image generation count N=1 per execution.');
        return;
      }

      generating.value = true;
      try {
        const payload = {
          capability_type: 'image_generation',
          model_id: selectedModelId.value,
          input: {
            prompt: cleanPrompt,
            negative_prompt: negativePrompt.value.trim() || null,
            prompt_template_id: selectedPromptId.value || null,
            template_variables: selectedPromptId.value ? templateVariables.value : null
          },
          params: {
            ...params.value,
            n: n.value
          }
        };

        const result = await apiClient.request('/api/capabilities/run', {
          method: 'POST',
          body: JSON.stringify(payload)
        });

        if (result.status === 'success') {
          addToast('success', 'Generation Succeeded', 'Image generated successfully!');
          loadCosts(); // Refresh global cost
          loadImageHistory();
        } else {
          addToast('warning', 'Generation incomplete', 'Model completed but output asset is missing.');
        }
      } catch (err) {
        // Map backend safety error
        if (err.error_type === 'CONTENT_BLOCKED') {
          addToast('error', 'Safety Violation', 'Safety block triggered by provider filters. Action blocked.');
        } else {
          addToast('error', `Generation Failed (${err.error_type || 'Error'})`, err.message || 'Request failed.');
        }
      } finally {
        generating.value = false;
      }
    };

    const rateAsset = async (assetId, score) => {
      try {
        await apiClient.request('/api/evaluations/upsert', {
          method: 'POST',
          body: JSON.stringify({
            target_type: 'asset',
            target_id: assetId,
            dimension: 'overall',
            score: score
          })
        });
        addToast('success', 'Rating Saved', `Image quality score rated: ${score}/5`);
        loadImageHistory();
      } catch (err) {
        addToast('error', 'Failed to save rating', err.message);
      }
    };

    const markAsBest = async (expId) => {
      try {
        await apiClient.request(`/api/experiments/${expId}/mark-best`, { method: 'POST' });
        addToast('success', 'Best Flag Set', 'This experiment was marked as the Best Output.');
        loadImageHistory();
      } catch (err) {
        addToast('error', 'Request failed', err.message);
      }
    };

    const openFailModal = (expId) => {
      failModalExpId.value = expId;
      failReasonCategory.value = 'poor_details';
      failReasonDetail.value = '';
    };

    const closeFailModal = () => {
      failModalExpId.value = null;
    };

    const submitFailureCase = async () => {
      try {
        const reason = `${failReasonCategory.value}: ${failReasonDetail.value}`.trim();
        await apiClient.request(`/api/experiments/${failModalExpId.value}/mark-failed-case`, {
          method: 'POST',
          body: JSON.stringify({ failure_reason: reason })
        });
        addToast('success', 'Failure Case Logged', 'Experiment tagged as failure case for debugging.');
        closeFailModal();
        loadImageHistory();
      } catch (err) {
        addToast('error', 'Request failed', err.message);
      }
    };

    const rerunExperiment = (exp) => {
      // Restore settings
      selectedModelId.value = exp.model_id;
      onModelChange();
      
      if (exp.input_json?.prompt_template_id) {
        selectedPromptId.value = exp.input_json.prompt_template_id;
        templateVariables.value = { ...exp.input_json.template_variables };
        rawPrompt.value = exp.input_text;
      } else {
        selectedPromptId.value = '';
        templateVariables.value = {};
        rawPrompt.value = exp.input_text;
      }
      
      // Restore negative prompt and other params
      negativePrompt.value = exp.input_json?.negative_prompt || '';
      params.value = { ...exp.params_json };
      if (exp.params_json?.n) n.value = exp.params_json.n;
      
      addToast('info', 'Parameters Restored', 'Copied experiment parameters into configuration panel.');
    };

    const getModelDisplayName = (modelId) => {
      const model = models.value.find(m => m.id === modelId);
      return model ? model.display_name : modelId;
    };

    const openLightbox = (src) => {
      lightboxSrc.value = src;
    };

    const closeLightbox = () => {
      lightboxSrc.value = null;
    };

    onMounted(() => {
      loadImageData();
    });

    return {
      t,
      models,
      promptTemplates,
      selectedModelId,
      selectedPromptId,
      templateVariables,
      rawPrompt,
      negativePrompt,
      params,
      n,
      generating,
      imageHistory,
      lightboxSrc,
      failModalExpId,
      failReasonCategory,
      failReasonDetail,
      selectedModel,
      uiSchema,
      selectedPrompt,
      onModelChange,
      onPromptTemplateChange,
      getVariableLabel,
      assemblePrompt,
      generateImage,
      rateAsset,
      markAsBest,
      openFailModal,
      closeFailModal,
      submitFailureCase,
      rerunExperiment,
      getModelDisplayName,
      openLightbox,
      closeLightbox
    };
  }
};
