import { ref, onMounted, inject, computed } from 'vue';

export default {
  name: 'CompareView',
  template: `
    <div class="compare-page">
      <!-- Top controls: selection and setup -->
      <div class="glass-card" style="margin-bottom: 24px;">
        <h3 style="font-family: var(--font-heading); font-size: 1.15rem; margin-bottom: 12px;">{{ t('compare.workspace.title') }}</h3>
        <p style="font-size: 0.85rem; color: var(--text-secondary); margin-bottom: 16px;">
          {{ t('compare.workspace.desc') }}
        </p>
        
        <div style="display: flex; gap: 12px; align-items: center; flex-wrap: wrap;">
          <button class="btn btn-primary" @click="openAssetSelector">
            <i class="fas fa-plus"></i> {{ t('compare.workspace.select') }}
          </button>
          
          <button v-if="selectedAssets.length > 0" class="btn btn-secondary" @click="clearCompareList">
            {{ t('compare.workspace.clear') }}
          </button>

          <span v-if="selectedAssets.length > 0" style="font-size: 0.85rem; color: var(--text-muted);">
            {{ t('compare.workspace.comparing', { count: selectedAssets.length }) }}
          </span>
        </div>
      </div>

      <!-- Compare Grid -->
      <div v-if="selectedAssets.length === 0" class="glass-card text-center" style="padding: 80px 0;">
        <i class="fas fa-balance-scale" style="font-size: 3.5rem; color: var(--text-muted); margin-bottom: 16px;"></i>
        <p style="color: var(--text-secondary);">{{ t('compare.workspace.empty') }}</p>
      </div>

      <div style="display: flex; flex-direction: column; gap: 24px;" v-else>
        <!-- Side-by-side cards grid -->
        <div class="grid-cols-12" style="gap: 20px;">
          <div v-for="ast in selectedAssets" :key="ast.id" :class="gridClass" class="glass-card" 
               style="display: flex; flex-direction: column; justify-content: space-between; border-top: 3px solid transparent;"
               :style="{ borderTopColor: isGroupBest(ast.id) ? 'var(--success)' : 'transparent' }">
            
            <div>
              <!-- Header info with group best marker -->
              <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 12px;">
                <div>
                  <h4 style="font-size: 0.9rem; font-weight: 600; text-overflow: ellipsis; overflow: hidden; white-space: nowrap; max-width: 140px;">
                    {{ ast.file_name }}
                  </h4>
                  <span style="font-family: monospace; font-size: 0.75rem; color: var(--text-muted);">ID: {{ ast.id }}</span>
                </div>
                <button class="btn" :class="isGroupBest(ast.id) ? 'btn-primary' : 'btn-secondary'" 
                        style="padding: 4px 8px; font-size: 0.7rem;" @click="markGroupBest(ast.id)">
                  <i class="fas" :class="isGroupBest(ast.id) ? 'fa-award text-success' : 'fa-award'"></i>
                  {{ isGroupBest(ast.id) ? t('compare.card.best') : t('compare.card.markBest') }}
                </button>
              </div>

              <!-- Media render -->
              <div style="aspect-ratio: 16/9; background-color: var(--bg-primary); border-radius: 6px; overflow: hidden; display: flex; align-items: center; justify-content: center; border: 1px solid var(--border-color); margin-bottom: 16px;">
                <img v-if="ast.asset_type === 'image'" :src="ast.download_path" style="width: 100%; height: 100%; object-fit: contain;">
                <video v-else-if="ast.asset_type === 'video'" controls style="width: 100%; height: 100%; object-fit: contain;">
                  <source :src="ast.download_path" type="video/mp4">
                </video>
                <div v-else style="padding: 20px; text-align: center;">
                  <i class="fas fa-file-audio text-success" style="font-size: 2rem; margin-bottom: 6px;"></i>
                  <audio :src="ast.download_path" controls style="max-width: 100%; height: 32px;"></audio>
                </div>
              </div>

              <!-- Multi-dimensional rating sliders -->
              <div style="display: flex; flex-direction: column; gap: 12px; margin-bottom: 16px;">
                <h5 style="font-size: 0.8rem; text-transform: uppercase; color: var(--text-secondary);">Dimension Scores</h5>
                
                <!-- Dimension: Usability -->
                <div>
                  <div style="display: flex; justify-content: space-between; font-size: 0.75rem; margin-bottom: 4px;">
                    <span>{{ t('compare.card.usability') }}</span>
                    <span style="color: var(--accent-cyan);">{{ getEvalScore(ast.id, 'Usability') }}/5</span>
                  </div>
                  <input type="range" min="1" max="5" step="1" class="slider-field" 
                         :value="getEvalScore(ast.id, 'Usability')" 
                         @input="e => updateDimensionScore(ast.id, 'Usability', parseInt(e.target.value))">
                </div>

                <!-- Dimension: Fidelity -->
                <div>
                  <div style="display: flex; justify-content: space-between; font-size: 0.75rem; margin-bottom: 4px;">
                    <span>{{ t('compare.card.fidelity') }}</span>
                    <span style="color: var(--accent-cyan);">{{ getEvalScore(ast.id, 'Fidelity') }}/5</span>
                  </div>
                  <input type="range" min="1" max="5" step="1" class="slider-field" 
                         :value="getEvalScore(ast.id, 'Fidelity')" 
                         @input="e => updateDimensionScore(ast.id, 'Fidelity', parseInt(e.target.value))">
                </div>

                <!-- Dimension: Technical Quality -->
                <div>
                  <div style="display: flex; justify-content: space-between; font-size: 0.75rem; margin-bottom: 4px;">
                    <span>{{ t('compare.card.quality') }}</span>
                    <span style="color: var(--accent-cyan);">{{ getEvalScore(ast.id, 'Quality') }}/5</span>
                  </div>
                  <input type="range" min="1" max="5" step="1" class="slider-field" 
                         :value="getEvalScore(ast.id, 'Quality')" 
                         @input="e => updateDimensionScore(ast.id, 'Quality', parseInt(e.target.value))">
                </div>
              </div>
            </div>

            <!-- Detail stats -->
            <div style="font-size: 0.75rem; color: var(--text-muted); border-top: 1px solid rgba(255,255,255,0.05); padding-top: 8px; display: flex; justify-content: space-between;">
              <span>Type: {{ ast.asset_type }}</span>
              <button class="btn btn-danger" style="padding: 2px 6px; font-size: 0.65rem;" @click="removeCompareAsset(ast.id)">
                {{ t('common.delete') }}
              </button>
            </div>
          </div>
        </div>

        <!-- Evaluation Conclusion Panel -->
        <div class="glass-card">
          <h3 style="font-family: var(--font-heading); font-size: 1.15rem; margin-bottom: 12px;">{{ t('compare.card.conclusion') }}</h3>
          <div style="display: flex; flex-direction: column; gap: 12px;">
            <textarea class="input-field" style="min-height: 80px;" v-model="conclusion" :placeholder="t('compare.card.commentPlaceholder')"></textarea>
            <div style="display: flex; justify-content: flex-end;">
              <button class="btn btn-primary" @click="saveConclusion" :disabled="saving">
                <i class="fas" :class="saving ? 'fa-spinner animate-spin' : 'fa-floppy-disk'"></i>
                {{ saving ? t('compare.card.buttonSaving') : t('compare.card.buttonSave') }}
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Asset Selector Modal -->
      <div v-if="selectorOpen" class="modal-overlay">
        <div class="modal-content glass-card" style="max-width: 650px;">
          <div class="modal-header">
            <h3>{{ t('compare.selector.title') }}</h3>
            <button class="toast-close" @click="closeAssetSelector"><i class="fas fa-times"></i></button>
          </div>
          
          <div style="max-height: 400px; overflow-y: auto; display: flex; flex-direction: column; gap: 10px; padding-right: 4px;">
            <div v-if="availableAssets.length === 0" style="text-align: center; color: var(--text-muted); padding: 24px;">
              {{ t('compare.selector.empty') }}
            </div>
            <div v-for="ast in availableAssets" :key="ast.id" 
                 class="glass-card" style="padding: 10px; display: flex; align-items: center; justify-content: space-between; background-color: var(--bg-tertiary);">
              <div style="display: flex; align-items: center; gap: 12px;">
                <div style="width: 50px; height: 50px; background-color: var(--bg-primary); border-radius: 4px; overflow: hidden; display: flex; align-items: center; justify-content: center;">
                  <img v-if="ast.asset_type === 'image'" :src="ast.download_path" style="width: 100%; height: 100%; object-fit: cover;">
                  <i v-else-if="ast.asset_type === 'audio'" class="fas fa-music text-success"></i>
                  <i v-else class="fas fa-film text-purple"></i>
                </div>
                <div>
                  <h5 style="font-size: 0.85rem; font-weight: 600;">{{ ast.file_name }}</h5>
                  <span style="font-size: 0.75rem; color: var(--text-secondary);">Type: {{ ast.asset_type }} | ID: {{ ast.id }}</span>
                </div>
              </div>
              
              <button class="btn" :class="isAssetSelected(ast.id) ? 'btn-primary' : 'btn-secondary'" 
                      style="padding: 4px 10px; font-size: 0.75rem;" @click="toggleAssetSelection(ast)">
                {{ isAssetSelected(ast.id) ? t('common.added') : t('common.add') }}
              </button>
            </div>
          </div>
          
          <div style="display: flex; justify-content: flex-end; margin-top: 16px; border-top: 1px solid var(--border-color); padding-top: 12px;">
            <button class="btn btn-primary" @click="closeAssetSelector">{{ t('common.confirm') }}</button>
          </div>
        </div>
      </div>
    </div>
  `,
  setup() {
    const apiClient = inject('apiClient');
    const addToast = inject('addToast');
    const t = inject('t');

    const selectedAssets = ref([]);
    const availableAssets = ref([]);
    const selectorOpen = ref(false);
    
    // Group evaluations mapping: { assetId: { dimensionName: scoreValue } }
    const groupEvaluations = ref({});
    // Group best asset ID
    const bestAssetId = ref(null);
    const conclusion = ref('');
    const saving = ref(false);

    // Group ID for this evaluation set
    const compareGroupId = ref('cmp_group_' + Math.random().toString(36).substring(7).toUpperCase());

    const gridClass = computed(() => {
      const len = selectedAssets.value.length;
      if (len <= 1) return 'col-span-12';
      if (len === 2) return 'col-span-6';
      return 'col-span-4';
    });

    const loadAvailableAssets = async () => {
      try {
        const assets = await apiClient.request('/api/assets');
        availableAssets.value = assets.filter(a => a.status !== 'discarded' && a.status !== 'deleted');
      } catch (err) {
        addToast('error', 'Error loading assets', err.message);
      }
    };

    const openAssetSelector = () => {
      loadAvailableAssets();
      selectorOpen.value = true;
    };

    const closeAssetSelector = () => {
      selectorOpen.value = false;
    };

    const isAssetSelected = (id) => {
      return selectedAssets.value.some(a => a.id === id);
    };

    const toggleAssetSelection = (ast) => {
      const index = selectedAssets.value.findIndex(a => a.id === ast.id);
      if (index !== -1) {
        selectedAssets.value.splice(index, 1);
        delete groupEvaluations.value[ast.id];
        if (bestAssetId.value === ast.id) bestAssetId.value = null;
      } else {
        selectedAssets.value.push(ast);
        // Initialize scores
        groupEvaluations.value[ast.id] = {
          Usability: 3,
          Fidelity: 3,
          Quality: 3
        };
      }
    };

    const removeCompareAsset = (id) => {
      selectedAssets.value = selectedAssets.value.filter(a => a.id !== id);
      delete groupEvaluations.value[id];
      if (bestAssetId.value === id) bestAssetId.value = null;
    };

    const clearCompareList = () => {
      selectedAssets.value = [];
      groupEvaluations.value = {};
      bestAssetId.value = null;
    };

    const getEvalScore = (assetId, dimension) => {
      return groupEvaluations.value[assetId]?.[dimension] || 3;
    };

    const updateDimensionScore = (assetId, dimension, score) => {
      if (!groupEvaluations.value[assetId]) {
        groupEvaluations.value[assetId] = {};
      }
      groupEvaluations.value[assetId][dimension] = score;
    };

    const isGroupBest = (assetId) => {
      return bestAssetId.value === assetId;
    };

    const markGroupBest = (assetId) => {
      bestAssetId.value = bestAssetId.value === assetId ? null : assetId;
    };

    const saveConclusion = async () => {
      if (selectedAssets.value.length === 0) {
        addToast('error', 'Validation Error', 'At least one asset must be selected to save report.');
        return;
      }

      saving.value = true;
      try {
        for (const ast of selectedAssets.value) {
          const evalSet = groupEvaluations.value[ast.id] || {};
          
          for (const [dimension, score] of Object.entries(evalSet)) {
            await apiClient.request('/api/evaluations/upsert', {
              method: 'POST',
              body: JSON.stringify({
                target_type: 'asset',
                target_id: ast.id,
                dimension,
                score,
                is_best: bestAssetId.value === ast.id,
                compare_group_id: compareGroupId.value
              })
            });
          }
        }

        if (conclusion.value.trim()) {
          await apiClient.request('/api/evaluations/compare/conclusion', {
            method: 'POST',
            body: JSON.stringify({
              target_ids: selectedAssets.value.map(a => a.id),
              comment: conclusion.value.trim(),
              compare_group_id: compareGroupId.value,
              evaluator_id: 'local'
            })
          });
        }
        
        addToast('success', 'Report Saved', `Successfully logged side-by-side evaluation metrics under Group ID: ${compareGroupId.value}`);
      } catch (err) {
        addToast('error', 'Failed to save evaluation', err.message);
      } finally {
        saving.value = false;
      }
    };

    return {
      t,
      selectedAssets,
      availableAssets,
      selectorOpen,
      conclusion,
      saving,
      gridClass,
      openAssetSelector,
      closeAssetSelector,
      isAssetSelected,
      toggleAssetSelection,
      removeCompareAsset,
      clearCompareList,
      getEvalScore,
      updateDimensionScore,
      isGroupBest,
      markGroupBest,
      saveConclusion
    };
  }
};
