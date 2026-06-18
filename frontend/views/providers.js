import { ref, onMounted, inject, computed } from 'vue';

export default {
  name: 'ProvidersView',
  template: `
    <div class="providers-page">
      <!-- Security Banner Alert -->
      <div class="glass-card text-left" style="margin-bottom: 24px; border-left: 4px solid var(--accent-cyan); background-color: rgba(0, 240, 255, 0.03);">
        <h4 style="color: var(--accent-cyan); font-family: var(--font-heading); margin-bottom: 6px;">
          <i class="fas fa-shield-halved"></i> {{ t('providers.policy.title') }}
        </h4>
        <p style="font-size: 0.85rem; color: var(--text-secondary); line-height: 1.4;">
          {{ t('providers.policy.desc') }}
        </p>
      </div>

      <div class="grid-cols-12">
        <!-- Providers List -->
        <div class="col-span-8 glass-card">
          <h3 style="font-family: var(--font-heading); font-size: 1.25rem; margin-bottom: 20px;">{{ t('providers.title') }}</h3>
          
          <div v-if="providers.length === 0" style="text-align: center; padding: 40px; color: var(--text-secondary);">
            <i class="fas fa-key" style="font-size: 2.5rem; color: var(--text-muted); margin-bottom: 12px;"></i>
            <p>{{ t('common.none') }}</p>
          </div>
          
          <div v-else style="display: flex; flex-direction: column; gap: 16px;">
            <div v-for="prv in providers" :key="prv.id" class="glass-card" style="padding: 16px; background-color: var(--bg-tertiary);">
              <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 12px;">
                <div>
                  <h4 style="font-family: var(--font-heading); font-size: 1.1rem; display: flex; align-items: center; gap: 8px;">
                    {{ prv.display_name }} 
                    <span class="badge" :class="prv.enabled ? 'badge-success' : 'badge-warning'" style="font-size: 0.65rem;">
                      {{ prv.enabled ? t('providers.status.enabled') : t('providers.status.disabled') }}
                    </span>
                    <span class="badge badge-cyan" style="font-size: 0.65rem; text-transform: uppercase;">
                      {{ prv.provider_type }}
                    </span>
                  </h4>
                  <p style="font-size: 0.8rem; color: var(--text-secondary); margin-top: 4px; font-family: monospace;">
                    {{ t('providers.modal.labelName') }}: {{ prv.name }}
                  </p>
                </div>
                <div style="display: flex; gap: 8px;">
                  <button class="btn btn-secondary" style="padding: 6px 12px; font-size: 0.75rem;" 
                          @click="startEdit(prv)">
                    <i class="fas fa-pen"></i>
                    {{ t('common.edit') }}
                  </button>
                  <button class="btn btn-secondary" style="padding: 6px 12px; font-size: 0.75rem;" 
                          @click="testConnection(prv.id)" :disabled="testingId === prv.id">
                    <i class="fas" :class="testingId === prv.id ? 'fa-spinner animate-spin' : 'fa-vial'"></i>
                    {{ t('providers.buttons.test') }}
                  </button>
                  <button class="btn btn-secondary" style="padding: 6px 12px; font-size: 0.75rem; color: var(--accent-cyan);" 
                          @click="toggleEnabled(prv)">
                    {{ prv.enabled ? t('providers.actions.disable') : t('providers.actions.enable') }}
                  </button>
                  <button class="btn btn-danger" style="padding: 6px 12px; font-size: 0.75rem;" 
                          @click="deleteProvider(prv.id)">
                    <i class="fas fa-trash"></i>
                  </button>
                </div>
              </div>

              <!-- Metadata & Config Grid -->
              <div class="grid-cols-12" style="font-size: 0.85rem; color: var(--text-secondary); gap: 12px;">
                <div class="col-span-6">
                  <strong>{{ t('providers.modal.labelBase') }}:</strong> <span style="font-family: monospace;">{{ prv.api_base || t('common.default') }}</span>
                </div>
                <div class="col-span-6">
                  <strong>{{ t('providers.modal.labelAuth') }}:</strong> {{ prv.auth_type }}
                </div>
                <div class="col-span-6">
                  <strong>{{ t('providers.modal.labelSource') }}:</strong> <span class="badge badge-purple" style="font-size: 0.7rem; text-transform: none;">{{ prv.credential_source }}</span>
                </div>
                <div class="col-span-6">
                  <strong>{{ t('providers.modal.labelRef') }}:</strong> <span style="font-family: monospace;">{{ displayCredentialReference(prv) }}</span>
                </div>
                <div class="col-span-12" style="margin-top: 8px; border-top: 1px solid rgba(255,255,255,0.05); padding-top: 8px;">
                  <strong>{{ t('models.card.capability') }}:</strong> 
                  <span v-for="cap in getCapabilitySummary(prv)" :key="cap" class="badge badge-cyan" style="margin-left: 6px; font-size: 0.7rem;">
                    {{ cap }}
                  </span>
                  <span v-if="getCapabilitySummary(prv).length === 0" style="font-size: 0.75rem; color: var(--text-muted);">{{ t('common.none') }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Add Provider Form -->
        <div class="col-span-4 glass-card">
          <div style="display: flex; justify-content: space-between; align-items: center; gap: 12px; margin-bottom: 20px;">
            <h3 style="font-family: var(--font-heading); font-size: 1.25rem;">{{ editingId ? t('providers.modal.titleEdit') : t('providers.modal.titleAdd') }}</h3>
            <button v-if="editingId" type="button" class="btn btn-secondary" style="padding: 6px 10px; font-size: 0.75rem;" @click="cancelEdit">
              {{ t('common.cancel') }}
            </button>
          </div>
          
          <form @submit.prevent="saveProvider" style="display: flex; flex-direction: column; gap: 16px;">
            <div>
              <label class="input-label">{{ t('providers.modal.labelDisplay') }} *</label>
              <input type="text" class="input-field" v-model="form.display_name" required placeholder="e.g. OpenAI Cloud">
            </div>

            <div>
              <label class="input-label">{{ t('providers.modal.labelName') }} *</label>
              <input type="text" class="input-field" v-model="form.name" required :disabled="!!editingId" placeholder="e.g. openai">
              <p v-if="editingId" style="font-size: 0.75rem; color: var(--text-muted); margin-top: 4px;">
                {{ t('providers.help.codeLocked') }}
              </p>
            </div>

            <div>
              <label class="input-label">{{ t('providers.modal.labelType') }} *</label>
              <select class="select-field" v-model="form.provider_type" required>
                <option value="cloud_api">Cloud API</option>
                <option value="model_gateway">Model Gateway</option>
                <option value="local_model">Local Model Server</option>
                <option value="mock">Mock Sandbox</option>
              </select>
            </div>

            <div>
              <label class="input-label">{{ t('providers.modal.labelAuth') }} *</label>
              <select class="select-field" v-model="form.auth_type" required>
                <option value="bearer_token">Bearer Token (Authorization Header)</option>
                <option value="api_key">API Key (Custom Header / Param)</option>
                <option value="none">None / No Credentials</option>
              </select>
            </div>

            <div>
              <label class="input-label">{{ t('providers.modal.labelBase') }}</label>
              <input type="text" class="input-field" v-model="form.api_base" placeholder="Use default official if empty">
            </div>

            <div>
              <label class="input-label">{{ t('providers.modal.labelSource') }} *</label>
              <select class="select-field" v-model="form.credential_source" required>
                <option value="env">Environment Variable</option>
                <option value="docker_secret">Docker Container Secret File</option>
                <option value="file">Local System File Path</option>
                <option value="none">None</option>
              </select>
              <div style="margin-top: 8px; padding: 10px 12px; border: 1px solid rgba(0,240,255,0.18); border-radius: 8px; background: rgba(0,240,255,0.04); color: var(--text-secondary); font-size: 0.78rem; line-height: 1.45;">
                <strong style="color: var(--accent-cyan); display: block; margin-bottom: 4px;">{{ credentialHelpTitle }}</strong>
                {{ credentialHelpText }}
              </div>
            </div>

            <div v-if="form.credential_source === 'env' || form.credential_source === 'docker_secret'">
              <label class="input-label">{{ t('providers.modal.labelRef') }} *</label>
              <input type="text" class="input-field" v-model="form.credential_ref" :required="form.credential_source !== 'none'" :placeholder="credentialRefPlaceholder">
            </div>

            <div v-if="form.credential_source === 'docker_secret' || form.credential_source === 'file'">
              <label class="input-label">{{ form.credential_source === 'file' ? t('providers.modal.labelFile') : t('providers.modal.labelFileOptional') }}</label>
              <input type="text" class="input-field" v-model="form.credential_file" :required="form.credential_source === 'file'" :placeholder="credentialFilePlaceholder">
            </div>

            <button type="submit" class="btn btn-primary" style="margin-top: 10px;">
              <i class="fas" :class="editingId ? 'fa-save' : 'fa-plus'"></i> {{ editingId ? t('providers.actions.saveChanges') : t('common.save') }}
            </button>
          </form>
        </div>
      </div>
    </div>
  `,
  setup() {
    const apiClient = inject('apiClient');
    const addToast = inject('addToast');
    const t = inject('t');
    const providers = ref([]);
    const testingId = ref(null);
    const editingId = ref(null);

    const emptyForm = () => ({
      name: '',
      display_name: '',
      provider_type: 'cloud_api',
      auth_type: 'bearer_token',
      api_base: '',
      credential_source: 'env',
      credential_ref: '',
      credential_file: '',
      enabled: true
    });

    const form = ref(emptyForm());

    const loadProviders = async () => {
      try {
        const data = await apiClient.request('/api/providers');
        providers.value = data;
      } catch (err) {
        addToast('error', 'Error loading providers', err.message || 'Check network connection.');
      }
    };

    const buildProviderPayload = () => {
      const source = form.value.credential_source;
      return {
        name: form.value.name.toLowerCase().trim(),
        display_name: form.value.display_name.trim(),
        provider_type: form.value.provider_type,
        auth_type: form.value.auth_type,
        api_base: form.value.api_base.trim() || null,
        credential_source: source,
        credential_ref: ['env', 'docker_secret'].includes(source) ? (form.value.credential_ref.trim() || null) : null,
        credential_file: ['docker_secret', 'file'].includes(source) ? (form.value.credential_file.trim() || null) : null,
        enabled: !!form.value.enabled
      };
    };

    const resetForm = () => {
      form.value = emptyForm();
      editingId.value = null;
    };

    const saveProvider = async () => {
      try {
        const params = buildProviderPayload();

        if (editingId.value) {
          const { name, ...updateParams } = params;
          await apiClient.request(`/api/providers/${editingId.value}`, {
            method: 'PATCH',
            body: JSON.stringify(updateParams)
          });
          addToast('success', 'Provider Updated', `Saved provider: ${params.display_name}`);
        } else {
          await apiClient.request('/api/providers', {
            method: 'POST',
            body: JSON.stringify(params)
          });
          addToast('success', 'Provider Created', `Successfully added provider: ${params.display_name}`);
        }

        resetForm();
        loadProviders();
      } catch (err) {
        addToast('error', editingId.value ? 'Failed to update provider' : 'Failed to create provider', err.message || 'Invalid parameters.');
      }
    };

    const startEdit = (prv) => {
      editingId.value = prv.id;
      form.value = {
        name: prv.name || '',
        display_name: prv.display_name || '',
        provider_type: prv.provider_type || 'cloud_api',
        auth_type: prv.auth_type || 'bearer_token',
        api_base: prv.api_base || '',
        credential_source: prv.credential_source || 'none',
        credential_ref: prv.credential_ref || '',
        credential_file: prv.credential_file || '',
        enabled: !!prv.enabled
      };
    };

    const cancelEdit = () => {
      resetForm();
    };

    const toggleEnabled = async (prv) => {
      try {
        const updated = await apiClient.request(`/api/providers/${prv.id}`, {
          method: 'PATCH',
          body: JSON.stringify({ enabled: !prv.enabled })
        });
        addToast('success', 'Status Changed', `${prv.display_name} has been ${updated.enabled ? 'enabled' : 'disabled'}.`);
        loadProviders();
      } catch (err) {
        addToast('error', 'Failed to update provider status', err.message || 'Request failed.');
      }
    };

    const deleteProvider = async (id) => {
      if (!confirm('Are you sure you want to delete this provider configuration? This cannot be undone.')) return;
      try {
        await apiClient.request(`/api/providers/${id}`, { method: 'DELETE' });
        addToast('success', 'Provider Deleted', 'Configuration successfully deleted.');
        loadProviders();
      } catch (err) {
        addToast('error', 'Deletion Failed', err.message || 'Request failed.');
      }
    };

    const testConnection = async (id) => {
      testingId.value = id;
      try {
        const result = await apiClient.request(`/api/providers/${id}/test-connection`, { method: 'POST' });
        addToast('success', 'Connection Test Succeeded', result.message || 'API connection test passed!');
      } catch (err) {
        // Map backend errors (e.g. CREDENTIAL_NOT_FOUND, PROVIDER_TIMEOUT, etc.)
        let userMsg = err.message || 'Connection test failed.';
        if (err.error_type === 'CREDENTIAL_NOT_FOUND') {
          userMsg = `Missing Credentials: The backend environment key reference could not be resolved. Check docker environment settings.`;
        } else if (err.error_type === 'PROVIDER_TIMEOUT') {
          userMsg = `Timeout: Connection to provider timed out. Check network proxy settings or API endpoint base url.`;
        }
        addToast('error', `Test Failed (${err.error_type || 'Error'})`, userMsg);
      } finally {
        testingId.value = null;
      }
    };

    const displayCredentialReference = (prv) => {
      return prv.masked_credential || prv.credential_ref || prv.credential_file || t('common.none');
    };

    const getCapabilitySummary = (prv) => {
      return prv.capability_summary || prv.capability_summary_json || [];
    };

    const credentialHelpTitle = computed(() => {
      return t(`providers.credentialHelp.${form.value.credential_source}.title`);
    });

    const credentialHelpText = computed(() => {
      return t(`providers.credentialHelp.${form.value.credential_source}.desc`);
    });

    const credentialRefPlaceholder = computed(() => {
      return form.value.credential_source === 'docker_secret' ? 'e.g. openai_api_key' : 'e.g. OPENAI_API_KEY';
    });

    const credentialFilePlaceholder = computed(() => {
      return form.value.credential_source === 'docker_secret' ? 'Optional, default: /run/secrets/<secret_name>' : 'e.g. /app/secrets/openai_api_key';
    });

    onMounted(() => {
      loadProviders();
    });

    return {
      t,
      providers,
      form,
      testingId,
      editingId,
      saveProvider,
      startEdit,
      cancelEdit,
      toggleEnabled,
      deleteProvider,
      testConnection,
      displayCredentialReference,
      getCapabilitySummary,
      credentialHelpTitle,
      credentialHelpText,
      credentialRefPlaceholder,
      credentialFilePlaceholder
    };
  }
};
