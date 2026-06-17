import { ref, onMounted, inject, computed } from 'vue';

export default {
  name: 'PromptsView',
  template: `
    <div class="prompts-page">
      <div class="grid-cols-12">
        <!-- Prompts Sidebar/List -->
        <div class="col-span-4 glass-card" style="display: flex; flex-direction: column; height: calc(100vh - 180px); overflow: hidden; padding-bottom: 12px;">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
            <h3 style="font-family: var(--font-heading); font-size: 1.15rem;">{{ t('prompts.sidebar.templates') }}</h3>
            <button class="btn btn-primary" style="padding: 6px 12px; font-size: 0.8rem;" @click="createNewPrompt">
              <i class="fas fa-plus"></i> {{ t('prompts.sidebar.new') }}
            </button>
          </div>
          
          <input type="text" class="input-field" v-model="searchQuery" :placeholder="t('prompts.sidebar.search')" style="margin-bottom: 12px; font-size: 0.85rem; padding: 8px 12px;">

          <div style="flex: 1; overflow-y: auto; display: flex; flex-direction: column; gap: 8px; padding-right: 4px;">
            <div v-if="filteredPrompts.length === 0" style="text-align: center; padding: 24px 0; color: var(--text-muted); font-size: 0.85rem;">
              {{ t('prompts.sidebar.empty') }}
            </div>
            
            <div v-for="pmt in filteredPrompts" :key="pmt.id" 
                  class="glass-card" 
                  style="padding: 12px; cursor: pointer; background-color: var(--bg-tertiary);"
                  :style="{ borderColor: selectedPromptId === pmt.id ? 'var(--accent-cyan)' : 'var(--glass-border)' }"
                  @click="selectPrompt(pmt.id)">
              <div style="display: flex; justify-content: space-between; align-items: start;">
                <h4 style="font-size: 0.9rem; font-weight: 600; text-overflow: ellipsis; overflow: hidden; white-space: nowrap; max-width: 180px;">
                  {{ pmt.name }}
                </h4>
                <div style="display: flex; gap: 6px; align-items: center;">
                  <i class="fas fa-star" :class="pmt.is_favorite ? 'rating-star-active' : ''" style="font-size: 0.75rem;" @click.stop="toggleFavorite(pmt)"></i>
                  <span class="badge badge-purple" style="font-size: 0.55rem; padding: 1px 4px;">v{{ pmt.version }}</span>
                </div>
              </div>
              <p style="font-size: 0.75rem; color: var(--text-secondary); margin-top: 6px; text-overflow: ellipsis; overflow: hidden; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; line-height: 1.3;">
                {{ pmt.template }}
              </p>
              <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 8px; font-size: 0.65rem; color: var(--text-muted);">
                <span>{{ t('prompts.sidebar.scenario') }}: {{ pmt.scenario }}</span>
                <span>{{ t('prompts.sidebar.usedCount', { count: pmt.usage_count || 0 }) }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Prompt Editor / Details -->
        <div class="col-span-8 glass-card" style="height: calc(100vh - 180px); overflow-y: auto;">
          <div v-if="!selectedPrompt" style="display: flex; flex-direction: column; justify-content: center; align-items: center; height: 100%; color: var(--text-secondary);">
            <i class="fas fa-terminal" style="font-size: 3rem; color: var(--text-muted); margin-bottom: 16px;"></i>
            <p>{{ t('prompts.editor.selectPlaceholder') }}</p>
          </div>
          
          <div v-else>
            <!-- Header actions -->
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; border-bottom: 1px solid var(--border-color); padding-bottom: 16px;">
              <div>
                <span class="badge badge-cyan" style="font-size: 0.65rem; text-transform: uppercase; margin-bottom: 4px;">{{ selectedPrompt.scenario }}</span>
                <h3 style="font-family: var(--font-heading); font-size: 1.35rem; display: flex; align-items: center; gap: 10px;">
                  {{ selectedPrompt.name }}
                  <span style="font-size: 0.85rem; color: var(--text-muted); font-weight: normal;">(Version: v{{ selectedPrompt.version }})</span>
                </h3>
              </div>
              
              <div style="display: flex; gap: 8px;">
                <button class="btn btn-secondary" style="padding: 6px 12px; font-size: 0.75rem;" @click="duplicatePrompt(selectedPrompt.id)">
                  <i class="fas fa-copy"></i> {{ t('prompts.editor.duplicate') }}
                </button>
                <button class="btn btn-danger" style="padding: 6px 12px; font-size: 0.75rem;" @click="deletePrompt(selectedPrompt.id)">
                  <i class="fas fa-trash"></i> {{ t('prompts.editor.delete') }}
                </button>
              </div>
            </div>

            <!-- Form -->
            <div style="display: flex; flex-direction: column; gap: 16px;">
              <div class="grid-cols-12" style="gap: 16px;">
                <div class="col-span-6">
                  <label class="input-label">{{ t('prompts.editor.labelName') }}</label>
                  <input type="text" class="input-field" v-model="editForm.name">
                </div>
                <div class="col-span-6">
                  <label class="input-label">{{ t('prompts.editor.labelScenario') }}</label>
                  <select class="select-field" v-model="editForm.scenario">
                    <option value="image_generation">Image Generation (image_generation)</option>
                    <option value="tts_style">Voice Narrative (tts_style)</option>
                    <option value="video_generation">Video Narrative (video_generation)</option>
                  </select>
                </div>
              </div>

              <div>
                <label class="input-label">{{ t('prompts.editor.labelTemplate') }}</label>
                <textarea class="input-field" style="min-height: 120px; font-family: inherit; line-height: 1.5;" v-model="editForm.template" placeholder="Create a beautiful image of a {{theme}} in a {{setting}} background..."></textarea>
              </div>

              <div>
                <label class="input-label">{{ t('prompts.editor.labelVariablesSchema') }}</label>
                <textarea class="input-field" style="font-family: monospace; min-height: 120px;" v-model="editForm.variables_schema_str" placeholder='{
  "type": "object",
  "properties": {
    "theme": { "type": "string", "label": "Subject Theme" }
  },
  "required": ["theme"]
}'></textarea>
              </div>

              <div>
                <label class="input-label">{{ t('prompts.editor.labelDefaultValues') }}</label>
                <textarea class="input-field" style="font-family: monospace; min-height: 80px;" v-model="editForm.default_values_json_str" placeholder='{ "theme": "cyberpunk robot" }'></textarea>
              </div>

              <div style="display: flex; justify-content: space-between; align-items: center; border-top: 1px solid var(--border-color); padding-top: 16px; margin-top: 10px;">
                <!-- Rating -->
                <div style="display: flex; align-items: center; gap: 10px;">
                  <span style="font-size: 0.85rem; color: var(--text-secondary);">{{ t('prompts.editor.labelRating') }}:</span>
                  <div class="rating-stars" style="font-size: 1.1rem; cursor: pointer;">
                    <i v-for="i in 5" :key="i" class="fas fa-star" 
                       :class="i <= editForm.rating ? 'rating-star-active' : ''" 
                       @click="updateRating(i)"></i>
                  </div>
                </div>
                
                <div style="display: flex; gap: 12px;">
                  <button class="btn btn-secondary" @click="resetEditForm">{{ t('prompts.editor.actionReset') }}</button>
                  <button class="btn btn-primary" @click="savePromptChanges">
                    <i class="fas fa-floppy-disk"></i> {{ t('prompts.editor.actionSave') }}
                  </button>
                </div>
              </div>
            </div>

            <!-- Version Trace Section -->
            <div style="margin-top: 32px; border-top: 1px solid var(--border-color); padding-top: 24px;">
              <h4 style="font-family: var(--font-heading); font-size: 1.1rem; margin-bottom: 12px; display: flex; align-items: center; gap: 8px;">
                <i class="fas fa-code-branch text-purple"></i> {{ t('prompts.revisions.title') }}
              </h4>
              <div v-if="versionHistory.length <= 1" style="font-size: 0.85rem; color: var(--text-muted);">
                {{ t('prompts.revisions.empty') }}
              </div>
              <div v-else style="display: flex; flex-direction: column; gap: 8px;">
                <div v-for="ver in versionHistory" :key="ver.id" 
                     class="glass-card" 
                     style="padding: 10px 14px; display: flex; justify-content: space-between; align-items: center; font-size: 0.85rem; background-color: rgba(255,255,255,0.02);"
                     :style="{ borderLeft: ver.is_latest ? '3px solid var(--accent-cyan)' : '1px solid var(--border-color)' }">
                  <div>
                    <span style="font-weight: 600;">v{{ ver.version }}</span>
                    <span v-if="ver.is_latest" class="badge badge-cyan" style="margin-left: 8px; font-size: 0.6rem; vertical-align: middle;">{{ t('prompts.revisions.current') }}</span>
                    <span style="font-size: 0.75rem; color: var(--text-muted); margin-left: 10px; font-family: monospace;">Hash: {{ ver.content_hash }}</span>
                  </div>
                  <div style="display: flex; gap: 10px; align-items: center;">
                    <span style="font-size: 0.75rem; color: var(--text-secondary);">Created: {{ formatDateShort(ver.created_at) }}</span>
                    <button v-if="!ver.is_latest" class="btn btn-secondary" style="padding: 3px 8px; font-size: 0.7rem;" @click="selectPrompt(ver.id)">
                      {{ t('prompts.revisions.actionSwitch') }}
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  `,
  setup() {
    const apiClient = inject('apiClient');
    const addToast = inject('addToast');
    const t = inject('t');
    const prompts = ref([]);
    const selectedPromptId = ref(null);
    const searchQuery = ref('');
    const versionHistory = ref([]);

    const editForm = ref({
      name: '',
      scenario: 'image_generation',
      template: '',
      variables_schema_str: '',
      default_values_json_str: '',
      rating: 0
    });

    const normalizePrompt = (prompt) => {
      if (!prompt) return prompt;
      const capability = prompt.capability_type || prompt.scenario || 'image_generation';
      const content = prompt.content ?? prompt.template ?? '';
      const variablesSchema = prompt.variables_schema_json || prompt.variables_schema || {};
      return {
        ...prompt,
        capability_type: capability,
        scenario: capability,
        content,
        template: content,
        variables_schema_json: variablesSchema,
        variables_schema: variablesSchema,
        default_values_json: prompt.default_values_json || {},
        usage_count: prompt.usage_count || 0,
        is_favorite: Boolean(prompt.is_favorite)
      };
    };

    const stableJson = (value) => {
      if (Array.isArray(value)) {
        return `[${value.map(stableJson).join(',')}]`;
      }
      if (value && typeof value === 'object') {
        return `{${Object.keys(value).sort().map(key => `${JSON.stringify(key)}:${stableJson(value[key])}`).join(',')}}`;
      }
      return JSON.stringify(value);
    };

    const loadPrompts = async () => {
      try {
        const data = await apiClient.request('/api/prompts');
        prompts.value = data.map(normalizePrompt);
        
        // Auto select first latest template if none is selected
        if (data.length > 0 && !selectedPromptId.value) {
          const latest = data.find(p => p.is_latest) || data[0];
          selectPrompt(latest.id);
        }
      } catch (err) {
        addToast('error', 'Failed to load prompts', err.message);
      }
    };

    const filteredPrompts = computed(() => {
      const q = searchQuery.value.toLowerCase().trim();
      // Filter out templates and group versions (show latest in list, older versions only shown in history trace)
      const latestPrompts = prompts.value.filter(p => p.is_latest);
      if (!q) return latestPrompts;
      return latestPrompts.filter(p => 
        p.name.toLowerCase().includes(q) || 
        (p.template || '').toLowerCase().includes(q)
      );
    });

    const selectedPrompt = computed(() => {
      return prompts.value.find(p => p.id === selectedPromptId.value);
    });

    const selectPrompt = async (id) => {
      selectedPromptId.value = id;
      resetEditForm();
      
      // Load version history (same group id)
      const current = selectedPrompt.value;
      if (current) {
        versionHistory.value = prompts.value
          .filter(p => p.version_group_id === current.version_group_id)
          .sort((a, b) => Number(b.version || 0) - Number(a.version || 0));
      }
    };

    const resetEditForm = () => {
      const pmt = selectedPrompt.value;
      if (pmt) {
        editForm.value = {
          name: pmt.name,
          scenario: pmt.scenario,
          template: pmt.template,
          variables_schema_str: JSON.stringify(pmt.variables_schema || {}, null, 2),
          default_values_json_str: JSON.stringify(pmt.default_values_json || {}, null, 2),
          rating: pmt.rating || 0
        };
      }
    };

    const updateRating = async (val) => {
      editForm.value.rating = val;
    };

    const toggleFavorite = async (pmt) => {
      try {
        const updated = await apiClient.request(`/api/prompts/${pmt.id}`, {
          method: 'PATCH',
          body: JSON.stringify({ is_favorite: !pmt.is_favorite })
        });
        Object.assign(pmt, normalizePrompt(updated));
        addToast('success', 'Favorite status updated', pmt.is_favorite ? 'Added to favorites' : 'Removed from favorites');
      } catch (err) {
        addToast('error', 'Request failed', err.message);
      }
    };

    const createNewPrompt = () => {
      // Mock unique ID
      const tempId = 'temp_pmt_new';
      const newPmt = {
        id: tempId,
        name: 'Untitled Prompt',
        capability_type: 'image_generation',
        scenario: 'image_generation',
        content: 'Standard narrative with {{variable}}',
        template: 'Standard narrative with {{variable}}',
        variables_schema_json: { type: 'object', properties: { variable: { type: 'string', label: 'Var' } } },
        variables_schema: { type: 'object', properties: { variable: { type: 'string', label: 'Var' } } },
        default_values_json: { variable: 'sample' },
        version: 1,
        version_group_id: 'grp_new_' + Math.random().toString(36).substring(7),
        is_latest: true,
        usage_count: 0,
        is_favorite: false
      };
      
      prompts.value.unshift(newPmt);
      selectedPromptId.value = tempId;
      resetEditForm();
    };

    const duplicatePrompt = async (id) => {
      try {
        const source = prompts.value.find(p => p.id === id);
        if (!source) throw new Error('Prompt template not found.');
        const duplicate = await apiClient.request('/api/prompts', {
          method: 'POST',
          body: JSON.stringify({
            name: `${source.name} (Copy)`,
            capability_type: source.scenario,
            content: source.template,
            variables_schema_json: source.variables_schema || {},
            default_values_json: source.default_values_json || {},
            description: source.description,
            notes: source.notes,
            metadata_json: source.metadata_json || {}
          })
        });
        addToast('success', 'Prompt Duplicated', `Created copy: ${duplicate.name}`);
        selectedPromptId.value = duplicate.id;
        loadPrompts();
      } catch (err) {
        addToast('error', 'Duplication failed', err.message);
      }
    };

    const deletePrompt = async (id) => {
      if (!confirm('Are you sure you want to delete this prompt template? (This will soft delete the selected version)')) return;
      try {
        if (String(id).startsWith('temp_')) {
          prompts.value = prompts.value.filter(p => p.id !== id);
          selectedPromptId.value = null;
          addToast('success', 'Prompt Deleted', 'Draft template removed.');
          return;
        }
        await apiClient.request(`/api/prompts/${id}`, { method: 'DELETE' });
        addToast('success', 'Prompt Deleted', 'Template version successfully removed.');
        selectedPromptId.value = null;
        loadPrompts();
      } catch (err) {
        addToast('error', 'Deletion failed', err.message);
      }
    };

    const savePromptChanges = async () => {
      const pmt = selectedPrompt.value;
      if (!pmt) return;

      try {
        let varsSchema = {};
        let defaultVals = {};
        try {
          varsSchema = JSON.parse(editForm.value.variables_schema_str || '{}');
        } catch (_) {
          throw new Error('Variables Schema JSON string is invalid.');
        }
        try {
          defaultVals = JSON.parse(editForm.value.default_values_json_str || '{}');
        } catch (_) {
          throw new Error('Default Values JSON string is invalid.');
        }

        const templateText = editForm.value.template.trim();
        const templateName = editForm.value.name.trim();
        if (!templateName) throw new Error('Template name is required.');
        if (!templateText) throw new Error('Template text is required.');

        const semanticChanged = 
          templateText !== pmt.template ||
          stableJson(varsSchema) !== stableJson(pmt.variables_schema || {}) ||
          stableJson(defaultVals) !== stableJson(pmt.default_values_json || {});

        if (pmt.id === 'temp_pmt_new') {
          // Creating a new template on the backend
          const created = await apiClient.request('/api/prompts', {
            method: 'POST',
            body: JSON.stringify({
              name: editForm.value.name.trim(),
              capability_type: editForm.value.scenario,
              content: templateText,
              variables_schema_json: varsSchema,
              default_values_json: defaultVals
            })
          });
          if (editForm.value.rating > 0) {
            await apiClient.request(`/api/prompts/${created.id}`, {
              method: 'PATCH',
              body: JSON.stringify({ rating: editForm.value.rating })
            });
          }
          addToast('success', 'Prompt Saved', `Created template: ${created.name}`);
          selectedPromptId.value = created.id;
          loadPrompts();
        } else if (semanticChanged) {
          // Trigger a new version
          const newVer = await apiClient.request(`/api/prompts/${pmt.id}`, {
            method: 'PATCH',
            body: JSON.stringify({
              name: templateName,
              capability_type: editForm.value.scenario,
              content: templateText,
              variables_schema_json: varsSchema,
              default_values_json: defaultVals
            })
          });
          // Also patch non-semantic fields if name / rating changed
          if (editForm.value.rating !== (pmt.rating || 0)) {
            await apiClient.request(`/api/prompts/${newVer.id}`, {
              method: 'PATCH',
              body: JSON.stringify({
                rating: editForm.value.rating
              })
            });
          }
          addToast('success', 'New Version Created', `Prompt template contents changed, saved as v${newVer.version}.`);
          selectedPromptId.value = newVer.id;
          loadPrompts();
        } else {
          // Save in-place for non-semantic fields (name, scenario, rating)
          const updated = await apiClient.request(`/api/prompts/${pmt.id}`, {
            method: 'PATCH',
            body: JSON.stringify({
              name: editForm.value.name.trim(),
              capability_type: editForm.value.scenario,
              rating: editForm.value.rating
            })
          });
          addToast('success', 'Prompt Updated', `Saved changes for ${updated.name}`);
          loadPrompts();
        }
      } catch (err) {
        addToast('error', 'Failed to save prompt', err.message);
      }
    };

    const formatDateShort = (isoStr) => {
      if (!isoStr) return 'Just now';
      const date = new Date(isoStr);
      return date.toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' });
    };

    onMounted(() => {
      loadPrompts();
    });

    return {
      t,
      prompts,
      selectedPromptId,
      searchQuery,
      editForm,
      versionHistory,
      filteredPrompts,
      selectedPrompt,
      selectPrompt,
      resetEditForm,
      updateRating,
      toggleFavorite,
      createNewPrompt,
      duplicatePrompt,
      deletePrompt,
      savePromptChanges,
      formatDateShort
    };
  }
};
