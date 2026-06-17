import { ref, onMounted, inject, computed } from 'vue';

export default {
  name: 'ModelsView',
  template: `
    <div class="models-page">
      <!-- Filters and Actions -->
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px; gap: 16px; flex-wrap: wrap;">
        <!-- Filters -->
        <div style="display: flex; gap: 12px; flex-grow: 1;">
          <div style="width: 200px;">
            <select class="select-field" v-model="filter.capability">
              <option value="">{{ t('models.filters.allCaps') }}</option>
              <option value="tts">Voice (TTS)</option>
              <option value="image_generation">Image Generation</option>
              <option value="video_generation">Video Generation</option>
            </select>
          </div>
          <div style="width: 200px;">
            <select class="select-field" v-model="filter.provider">
              <option value="">{{ t('models.filters.allPrvs') }}</option>
              <option v-for="p in providers" :key="p.name" :value="p.name">
                {{ p.display_name }}
              </option>
            </select>
          </div>
        </div>
        
        <!-- Toggle register panel -->
        <button class="btn btn-primary" @click="showRegisterModal = true">
          <i class="fas fa-plus"></i> {{ t('models.filters.register') }}
        </button>
      </div>

      <!-- Models Grid -->
      <div class="grid-cols-12">
        <div v-if="filteredModels.length === 0" class="col-span-12 glass-card text-center" style="padding: 60px 0;">
          <i class="fas fa-sliders" style="font-size: 3rem; color: var(--text-muted); margin-bottom: 16px;"></i>
          <p style="color: var(--text-secondary);">{{ t('models.filters.empty') }}</p>
        </div>
        
        <div v-for="mdl in filteredModels" :key="mdl.id" class="col-span-4 glass-card" 
             style="display: flex; flex-direction: column; justify-content: space-between; min-height: 250px;"
             :style="{ 
               borderTop: mdl.is_default ? '3px solid var(--accent-cyan)' : '1px solid var(--border-color)' 
             }">
          <div>
            <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 12px;">
              <div>
                <h3 style="font-family: var(--font-heading); font-size: 1.15rem; font-weight: 600;">
                  {{ mdl.display_name }}
                </h3>
                <span style="font-family: monospace; font-size: 0.75rem; color: var(--text-muted);">
                  {{ mdl.model_code }}
                </span>
              </div>
              <span class="badge" :class="mdl.enabled ? 'badge-success' : 'badge-warning'" style="font-size: 0.65rem;">
                {{ mdl.enabled ? t('models.card.actionDisable') : t('models.card.actionEnable') }}
              </span>
            </div>

            <!-- Recommendation & Verification Badges -->
            <div style="display: flex; gap: 6px; margin-bottom: 16px; flex-wrap: wrap;">
              <span v-if="mdl.is_default" class="badge badge-cyan" style="font-size: 0.6rem;">{{ t('models.card.default') }}</span>
              <span v-if="mdl.is_recommended" class="badge badge-purple" style="font-size: 0.6.rem;">{{ t('models.card.recommended') }}</span>
              <span v-if="mdl.requires_verification" class="badge badge-warning" style="font-size: 0.6rem;" 
                    title="Needs manual verification for production use">{{ t('models.card.verification') }}</span>
            </div>

            <!-- Parameters Overview -->
            <div style="font-size: 0.8rem; color: var(--text-secondary); display: flex; flex-direction: column; gap: 6px; margin-bottom: 16px;">
              <div><strong>{{ t('models.card.provider') }}:</strong> {{ getProviderDisplayName(mdl.provider_name) }}</div>
              <div><strong>{{ t('models.card.capability') }}:</strong> <span class="badge badge-cyan" style="font-size: 0.65rem;">{{ mdl.capability_type }}</span></div>
              <div v-if="mdl.pricing_hint"><strong>{{ t('models.card.pricing') }}:</strong> {{ mdl.pricing_hint }}</div>
            </div>
          </div>

          <!-- Card Actions -->
          <div style="display: flex; justify-content: space-between; align-items: center; border-top: 1px solid rgba(255,255,255,0.05); padding-top: 12px; margin-top: 12px;">
            <button class="btn btn-secondary" style="padding: 6px 12px; font-size: 0.75rem;" @click="toggleEnabled(mdl)">
              {{ mdl.enabled ? t('models.card.actionDisable') : t('models.card.actionEnable') }}
            </button>
            <div style="display: flex; gap: 8px;">
              <button class="btn btn-secondary" style="padding: 6px 12px; font-size: 0.75rem;" @click="editModel(mdl)">
                <i class="fas fa-edit"></i>
              </button>
              <button class="btn btn-danger" style="padding: 6px 12px; font-size: 0.75rem;" @click="deleteModel(mdl.id)">
                <i class="fas fa-trash"></i>
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Register / Edit Modal -->
      <div v-if="showRegisterModal || editingModelId" class="modal-overlay">
        <div class="modal-content glass-card">
          <div class="modal-header">
            <h3>{{ editingModelId ? t('models.modal.titleEdit') : t('models.modal.titleAdd') }}</h3>
            <button class="toast-close" @click="closeModal"><i class="fas fa-times"></i></button>
          </div>
          
          <form @submit.prevent="submitModel" style="display: flex; flex-direction: column; gap: 16px;">
            <div class="grid-cols-12" style="gap: 16px;">
              <div class="col-span-6">
                <label class="input-label">{{ t('models.modal.labelDisplay') }} *</label>
                <input type="text" class="input-field" v-model="form.display_name" required placeholder="e.g. DALL-E 3 HD">
              </div>
              <div class="col-span-6">
                <label class="input-label">{{ t('models.modal.labelCode') }} *</label>
                <input type="text" class="input-field" v-model="form.model_code" required placeholder="e.g. dall-e-3">
              </div>
            </div>

            <div class="grid-cols-12" style="gap: 16px;">
              <div class="col-span-6">
                <label class="input-label">{{ t('models.modal.labelCapability') }} *</label>
                <select class="select-field" v-model="form.capability_type" required :disabled="editingModelId">
                  <option value="tts">Voice (TTS)</option>
                  <option value="image_generation">Image Generation</option>
                  <option value="video_generation">Video Generation</option>
                </select>
              </div>
              <div class="col-span-6">
                <label class="input-label">{{ t('models.modal.labelProvider') }} *</label>
                <select class="select-field" v-model="form.provider_id" required :disabled="editingModelId">
                  <option v-for="p in providers" :key="p.id" :value="p.id">
                    {{ p.display_name }} ({{ p.name }})
                  </option>
                </select>
              </div>
            </div>

            <div>
              <label class="input-label">{{ t('models.modal.labelPricingHint') }}</label>
              <input type="text" class="input-field" v-model="form.pricing_hint" placeholder="e.g. $0.04 per image">
            </div>

            <div class="grid-cols-12" style="gap: 16px;">
              <div class="col-span-4" style="display: flex; align-items: center; gap: 8px;">
                <input type="checkbox" id="chk-default" v-model="form.is_default">
                <label for="chk-default" class="input-label" style="margin-bottom: 0; cursor: pointer;">{{ t('models.card.default') }}</label>
              </div>
              <div class="col-span-4" style="display: flex; align-items: center; gap: 8px;">
                <input type="checkbox" id="chk-recommended" v-model="form.is_recommended">
                <label for="chk-recommended" class="input-label" style="margin-bottom: 0; cursor: pointer;">{{ t('models.card.recommended') }}</label>
              </div>
              <div class="col-span-4" style="display: flex; align-items: center; gap: 8px;">
                <input type="checkbox" id="chk-verification" v-model="form.requires_verification">
                <label for="chk-verification" class="input-label" style="margin-bottom: 0; cursor: pointer;">{{ t('models.card.verification') }}</label>
              </div>
            </div>

            <div>
              <label class="input-label">{{ t('models.modal.labelDefaultParams') }}</label>
              <textarea class="input-field" style="font-family: monospace;" v-model="form.default_params_str" placeholder='{ "quality": "standard" }'></textarea>
            </div>

            <div>
              <label class="input-label">{{ t('models.modal.labelUiSchema') }}</label>
              <textarea class="input-field" style="font-family: monospace;" v-model="form.param_ui_schema_str" placeholder='{ "quality": { "label": "Quality", "type": "select", "options": ["standard", "hd"] } }'></textarea>
            </div>

            <div style="display: flex; justify-content: flex-end; gap: 12px; margin-top: 12px;">
              <button type="button" class="btn btn-secondary" @click="closeModal">{{ t('common.cancel') }}</button>
              <button type="submit" class="btn btn-primary">{{ t('common.save') }}</button>
            </div>
          </form>
        </div>
      </div>
    </div>
  `,
  setup() {
    const apiClient = inject('apiClient');
    const addToast = inject('addToast');
    const t = inject('t');
    const models = ref([]);
    const providers = ref([]);
    const showRegisterModal = ref(false);
    const editingModelId = ref(null);

    const filter = ref({
      capability: '',
      provider: ''
    });

    const form = ref({
      display_name: '',
      model_code: '',
      capability_type: 'tts',
      provider_id: '',
      pricing_hint: '',
      is_default: false,
      is_recommended: false,
      requires_verification: false,
      default_params_str: '{}',
      param_ui_schema_str: '{}'
    });

    const loadData = async () => {
      try {
        const modelsData = await apiClient.request('/api/models');
        const providersData = await apiClient.request('/api/providers');
        
        models.value = modelsData;
        providers.value = providersData;

        // Auto select first provider in form if empty
        if (providersData.length > 0 && !form.value.provider_id) {
          form.value.provider_id = providersData[0].id;
        }
      } catch (err) {
        addToast('error', 'Error loading data', err.message || 'Check connection');
      }
    };

    const filteredModels = computed(() => {
      return models.value.filter(mdl => {
        const matchCap = !filter.value.capability || mdl.capability_type === filter.value.capability;
        const matchPrv = !filter.value.provider || mdl.provider_name === filter.value.provider;
        return matchCap && matchPrv;
      });
    });

    const getProviderDisplayName = (prvName) => {
      const prv = providers.value.find(p => p.name === prvName);
      return prv ? prv.display_name : prvName;
    };

    const toggleEnabled = async (mdl) => {
      try {
        const updated = await apiClient.request(`/api/models/${mdl.id}`, {
          method: 'PATCH',
          body: JSON.stringify({ enabled: !mdl.enabled })
        });
        addToast('success', 'Model Updated', `${mdl.display_name} has been ${updated.enabled ? 'enabled' : 'disabled'}.`);
        loadData();
      } catch (err) {
        addToast('error', 'Action failed', err.message || 'Update request failed.');
      }
    };

    const deleteModel = async (id) => {
      if (!confirm('Are you sure you want to delete this model registry entry?')) return;
      try {
        await apiClient.request(`/api/models/${id}`, { method: 'DELETE' });
        addToast('success', 'Model Deleted', 'Registry entry removed.');
        loadData();
      } catch (err) {
        addToast('error', 'Deletion failed', err.message || 'Delete request failed.');
      }
    };

    const editModel = (mdl) => {
      editingModelId.value = mdl.id;
      
      const prv = providers.value.find(p => p.name === mdl.provider_name);
      
      form.value = {
        display_name: mdl.display_name,
        model_code: mdl.model_code,
        capability_type: mdl.capability_type,
        provider_id: prv ? prv.id : '',
        pricing_hint: mdl.pricing_hint || '',
        is_default: mdl.is_default || false,
        is_recommended: mdl.is_recommended || false,
        requires_verification: mdl.requires_verification || false,
        default_params_str: JSON.stringify(mdl.default_params || {}, null, 2),
        param_ui_schema_str: JSON.stringify(mdl.param_ui_schema || {}, null, 2)
      };
      
      showRegisterModal.value = true;
    };

    const submitModel = async () => {
      try {
        // Parse params
        let default_params = {};
        let param_ui_schema = {};
        try {
          default_params = JSON.parse(form.value.default_params_str || '{}');
        } catch (_) {
          throw new Error('Default parameters JSON is invalid.');
        }
        try {
          param_ui_schema = JSON.parse(form.value.param_ui_schema_str || '{}');
        } catch (_) {
          throw new Error('Param UI Schema JSON is invalid.');
        }

        const selectedPrv = providers.value.find(p => p.id === form.value.provider_id);
        if (!selectedPrv) throw new Error('Selected provider invalid');

        const params = {
          name: form.value.display_name.toLowerCase().replace(/\s+/g, '_'),
          display_name: form.value.display_name,
          model_code: form.value.model_code,
          capability_type: form.value.capability_type,
          provider_id: form.value.provider_id,
          provider_name: selectedPrv.name,
          pricing_hint: form.value.pricing_hint || null,
          is_default: form.value.is_default,
          is_recommended: form.value.is_recommended,
          requires_verification: form.value.requires_verification,
          default_params,
          param_ui_schema
        };

        if (editingModelId.value) {
          await apiClient.request(`/api/models/${editingModelId.value}`, {
            method: 'PATCH',
            body: JSON.stringify(params)
          });
          addToast('success', 'Model Saved', `Successfully updated: ${params.display_name}`);
        } else {
          await apiClient.request('/api/models', {
            method: 'POST',
            body: JSON.stringify(params)
          });
          addToast('success', 'Model Registered', `Successfully added: ${params.display_name}`);
        }

        closeModal();
        loadData();
      } catch (err) {
        addToast('error', 'Failed to save model configuration', err.message);
      }
    };

    const closeModal = () => {
      showRegisterModal.value = false;
      editingModelId.value = null;
      form.value = {
        display_name: '',
        model_code: '',
        capability_type: 'tts',
        provider_id: providers.value.length > 0 ? providers.value[0].id : '',
        pricing_hint: '',
        is_default: false,
        is_recommended: false,
        requires_verification: false,
        default_params_str: '{}',
        param_ui_schema_str: '{}'
      };
    };

    onMounted(() => {
      loadData();
    });

    return {
      t,
      models,
      providers,
      filter,
      form,
      showRegisterModal,
      editingModelId,
      filteredModels,
      getProviderDisplayName,
      toggleEnabled,
      deleteModel,
      editModel,
      submitModel,
      closeModal
    };
  }
};
