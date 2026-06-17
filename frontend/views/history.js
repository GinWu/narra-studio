import { ref, onMounted, inject, computed } from 'vue';

export default {
  name: 'HistoryView',
  template: `
    <div class="history-page">
      <!-- Filters row -->
      <div class="glass-card" style="margin-bottom: 24px; display: flex; gap: 12px; align-items: center; flex-wrap: wrap; padding: 16px 24px;">
        <div style="width: 150px;">
          <select class="select-field" v-model="filterCap" style="padding: 8px 12px; font-size: 0.85rem;">
            <option value="">{{ t('history.filters.allLabs') }}</option>
            <option value="tts">{{ t('history.filters.voice') }}</option>
            <option value="image_generation">{{ t('history.filters.image') }}</option>
            <option value="video_generation">{{ t('history.filters.video') }}</option>
          </select>
        </div>
        
        <div style="width: 150px;">
          <select class="select-field" v-model="filterStatus" style="padding: 8px 12px; font-size: 0.85rem;">
            <option value="">{{ t('history.filters.allStatuses') }}</option>
            <option value="success">{{ t('common.success') }}</option>
            <option value="failed">{{ t('common.failed') }}</option>
            <option value="cancelled">{{ t('common.cancelled') }}</option>
            <option value="running">{{ t('common.running') }}</option>
          </select>
        </div>

        <div style="flex-grow: 1; max-width: 250px;">
          <input type="text" class="input-field" v-model="searchQuery" :placeholder="t('history.filters.searchPlaceholder')" style="padding: 8px 12px; font-size: 0.85rem;">
        </div>

        <div style="display: flex; gap: 8px; font-size: 0.85rem; color: var(--text-secondary);">
          <input type="checkbox" id="show-only-best" v-model="showOnlyBest">
          <label for="show-only-best" style="cursor: pointer;">{{ t('history.filters.showOnlyBest') }}</label>
        </div>
      </div>

      <!-- History Table -->
      <div class="glass-card">
        <div v-if="filteredExperiments.length === 0" style="text-align: center; padding: 60px 0; color: var(--text-secondary);">
          <i class="fas fa-history" style="font-size: 3rem; color: var(--text-muted); margin-bottom: 16px;"></i>
          <p>{{ t('history.table.empty') }}</p>
        </div>
        
        <table v-else class="premium-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>{{ t('history.table.titleInput') }}</th>
              <th>{{ t('history.table.type') }}</th>
              <th>{{ t('history.table.status') }}</th>
              <th>{{ t('history.table.latency') }}</th>
              <th>{{ t('history.table.tags') }}</th>
              <th>{{ t('common.actions') }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="exp in filteredExperiments" :key="exp.id" style="cursor: pointer;" @click="viewDetails(exp)">
              <td style="font-family: monospace; font-size: 0.8rem;">{{ exp.id }}</td>
              <td style="max-width: 320px; text-overflow: ellipsis; overflow: hidden; white-space: nowrap;" :title="exp.input_text">
                <strong>{{ exp.title }}</strong><br>
                <span style="font-size: 0.8rem; color: var(--text-secondary);">"{{ exp.input_text }}"</span>
              </td>
              <td>
                <span class="badge" :class="getCapabilityBadgeClass(exp.capability_type)">
                  {{ exp.capability_type }}
                </span>
              </td>
              <td>
                <span class="badge" :class="getStatusBadgeClass(exp.status)">
                  {{ exp.status }}
                </span>
              </td>
              <td>{{ (exp.latency_ms / 1000).toFixed(2) }}s</td>
              <td>
                <div style="display: flex; gap: 4px;">
                  <span v-if="exp.is_best" class="badge badge-success" style="font-size: 0.6rem;">{{ t('history.table.best') }}</span>
                  <span v-if="exp.is_failed_case" class="badge badge-danger" style="font-size: 0.6rem;" :title="exp.failed_reason">{{ t('history.table.failCase') }}</span>
                </div>
              </td>
              <td @click.stop>
                <div style="display: flex; gap: 8px;">
                  <button class="btn btn-secondary" style="padding: 4px 8px; font-size: 0.75rem;" @click="viewDetails(exp)">
                    {{ t('history.table.btnDetails') }}
                  </button>
                  <button class="btn btn-secondary" style="padding: 4px 8px; font-size: 0.75rem; color: var(--accent-cyan);" @click="rerunExperiment(exp)">
                    {{ t('common.rerun') }}
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Experiment Details & Invocation Log Modal -->
      <div v-if="detailModalOpen" class="modal-overlay">
        <div class="modal-content glass-card" style="max-width: 700px;">
          <div class="modal-header">
            <h3>{{ t('history.modal.title') }}</h3>
            <button class="toast-close" @click="closeDetails"><i class="fas fa-times"></i></button>
          </div>

          <div v-if="selectedExp" style="display: flex; flex-direction: column; gap: 20px;">
            <!-- Top Summary Card -->
            <div class="glass-card" style="padding: 16px; background-color: var(--bg-tertiary);">
              <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                <h4 style="font-family: var(--font-heading); font-size: 1.1rem;">{{ selectedExp.title }}</h4>
                <span class="badge" :class="getStatusBadgeClass(selectedExp.status)">{{ selectedExp.status }}</span>
              </div>
              <div style="font-size: 0.8rem; color: var(--text-secondary); display: flex; flex-direction: column; gap: 4px;">
                <div><strong>{{ t('history.table.expId') }}:</strong> <span style="font-family: monospace;">{{ selectedExp.id }}</span></div>
                <div><strong>{{ t('history.table.time') }}:</strong> {{ formatDateLong(selectedExp.created_at) }}</div>
                <div><strong>{{ t('history.table.latency') }}:</strong> {{ (selectedExp.latency_ms / 1000).toFixed(2) }} seconds</div>
              </div>
            </div>

            <!-- Tab Headers -->
            <div style="display: flex; border-bottom: 1px solid var(--border-color); gap: 16px;">
              <button v-for="tab in ['Configuration', 'Output Preview', 'Invocation Logs']" 
                      :key="tab"
                      class="btn"
                      :class="activeTab === tab ? 'btn-primary' : 'btn-secondary'"
                      style="padding: 6px 12px; font-size: 0.85rem; border-bottom-left-radius: 0; border-bottom-right-radius: 0; border: none; box-shadow: none;"
                      @click="activeTab = tab">
                {{ tab === 'Configuration' ? t('history.modal.tabDetails') : (tab === 'Output Preview' ? t('history.modal.tabOutput') : t('history.modal.tabLogs')) }}
              </button>
            </div>

            <!-- Tab Content 1: Configuration -->
            <div v-if="activeTab === 'Configuration'" style="display: flex; flex-direction: column; gap: 12px; font-size: 0.85rem;">
              <div>
                <strong>{{ t('history.modal.synthesisScriptLabel') }}</strong>
                <blockquote style="background-color: var(--bg-primary); padding: 10px; border-radius: 4px; border: 1px solid var(--border-color); margin-top: 6px; font-style: italic;">
                  "{{ selectedExp.input_text }}"
                </blockquote>
              </div>
              
              <div class="grid-cols-12" style="gap: 16px; margin-top: 10px;">
                <div class="col-span-6">
                  <strong>{{ t('history.modal.modelConfigLabel') }}</strong>
                  <pre style="background-color: var(--bg-primary); padding: 8px; border-radius: 4px; border: 1px solid var(--border-color); font-family: monospace; font-size: 0.75rem; margin-top: 6px; overflow-x: auto;">
{{ t('history.modal.labelProvider') }}: {{ selectedExp.provider_id }}
{{ t('history.modal.labelModel') }}: {{ selectedExp.model_id }}
{{ t('history.modal.labelAdapter') }}: {{ selectedExp.adapter_name }} (v{{ selectedExp.adapter_version }})
                  </pre>
                </div>
                <div class="col-span-6">
                  <strong>{{ t('history.modal.inputParamsLabel') }}</strong>
                  <pre style="background-color: var(--bg-primary); padding: 8px; border-radius: 4px; border: 1px solid var(--border-color); font-family: monospace; font-size: 0.75rem; margin-top: 6px; overflow-x: auto;">{{ JSON.stringify(selectedExp.params_json || {}, null, 2) }}</pre>
                </div>
              </div>
            </div>

            <!-- Tab Content 2: Output Preview -->
            <div v-if="activeTab === 'Output Preview'" style="display: flex; flex-direction: column; align-items: center; gap: 16px;">
              <div v-if="linkedAsset" style="width: 100%; max-width: 480px;">
                <img v-if="linkedAsset.asset_type === 'image'" :src="linkedAsset.download_path" style="width: 100%; border-radius: 6px; border: 1px solid var(--border-color);">
                <video v-else-if="linkedAsset.asset_type === 'video'" controls style="width: 100%; border-radius: 6px; border: 1px solid var(--border-color);">
                  <source :src="linkedAsset.download_path" type="video/mp4">
                </video>
                <div v-else-if="linkedAsset.asset_type === 'audio'">
                  <audio :src="linkedAsset.download_path" controls style="width: 100%; margin-bottom: 12px;"></audio>
                </div>

                <div class="glass-card" style="padding: 12px; margin-top: 16px; background-color: var(--bg-tertiary); font-size: 0.8rem;">
                  <h5 style="margin-bottom: 6px; font-weight: 600;">{{ t('history.modal.linkedAssetRef') }}</h5>
                  <div><strong>{{ t('history.modal.fileLabel') }}</strong> {{ linkedAsset.file_name }}</div>
                  <div><strong>{{ t('history.modal.mimeLabel') }}</strong> {{ linkedAsset.mime_type }} | {{ t('history.modal.sizeLabel') }} {{ formatBytes(linkedAsset.size_bytes) }}</div>
                  <div style="display: flex; gap: 10px; margin-top: 10px;">
                    <a :href="linkedAsset.download_path" target="_blank" class="btn btn-secondary" style="padding: 4px 10px; font-size: 0.75rem;">
                      <i class="fas fa-download"></i> {{ t('history.modal.downloadAsset') }}
                    </a>
                  </div>
                </div>
              </div>
              <div v-else style="color: var(--text-muted); padding: 40px 0;">
                {{ t('history.modal.noOutputAsset') }}
              </div>
            </div>

            <!-- Tab Content 3: Invocation Logs Timeline -->
            <div v-if="activeTab === 'Invocation Logs'" style="display: flex; flex-direction: column; gap: 14px;">
              <div v-if="loadingLogs" style="text-align: center; padding: 20px;">
                <i class="fas fa-spinner animate-spin text-cyan"></i> {{ t('history.modal.loadingLogs') }}
              </div>
              <div v-else-if="logs.length === 0" style="color: var(--text-muted); text-align: center; padding: 20px;">
                {{ t('history.modal.noLogs') }}
              </div>
              
              <!-- Timeline component -->
              <div v-else style="display: flex; flex-direction: column; gap: 12px; border-left: 2px solid var(--border-color); padding-left: 16px; margin-left: 8px;">
                <div v-for="(log, idx) in logs" :key="idx" style="position: relative;">
                  <!-- bullet marker -->
                  <div style="position: absolute; left: -22px; top: 4px; width: 10px; height: 10px; border-radius: 50%; background-color: var(--accent-cyan); box-shadow: 0 0 6px var(--accent-cyan);"></div>
                  
                  <div style="font-size: 0.85rem; font-weight: 600; display: flex; justify-content: space-between;">
                    <span>{{ t('history.modal.stepLabel') }} {{ log.event_type || 'Status log' }}</span>
                    <span style="font-family: monospace; font-size: 0.75rem; color: var(--text-muted);">{{ log.status }}</span>
                  </div>
                  <p style="font-size: 0.8rem; color: var(--text-secondary); margin-top: 4px;">
                    {{ log.message || 'Processing event logged.' }}
                  </p>
                </div>
              </div>
            </div>

            <!-- Modal footer actions -->
            <div style="display: flex; justify-content: flex-end; gap: 10px; border-top: 1px solid var(--border-color); padding-top: 16px; margin-top: 10px;">
              <button class="btn btn-secondary" @click="closeDetails">{{ t('common.close') }}</button>
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

    const experiments = ref([]);
    const assets = ref([]);
    const filterCap = ref('');
    const filterStatus = ref('');
    const searchQuery = ref('');
    const showOnlyBest = ref(false);

    // Modal details ref
    const detailModalOpen = ref(false);
    const selectedExp = ref(null);
    const linkedAsset = ref(null);
    const activeTab = ref('Configuration');
    
    // Logs state
    const logs = ref([]);
    const loadingLogs = ref(false);

    const loadHistoryData = async () => {
      try {
        const experimentsData = await apiClient.request('/api/experiments');
        const assetsData = await apiClient.request('/api/assets');
        
        experiments.value = experimentsData;
        assets.value = assetsData;
      } catch (err) {
        addToast('error', 'Error loading history logs', err.message);
      }
    };

    const filteredExperiments = computed(() => {
      return experiments.value.filter(exp => {
        // Soft delete filters or others (they should be filtered out by backend already)
        if (exp.deleted_at) return false;

        const matchCap = !filterCap.value || exp.capability_type === filterCap.value;
        const matchStatus = !filterStatus.value || exp.status === filterStatus.value;
        
        const q = searchQuery.value.toLowerCase().trim();
        const matchQuery = !q || 
          exp.title.toLowerCase().includes(q) ||
          exp.input_text.toLowerCase().includes(q);

        const matchBest = !showOnlyBest.value || exp.is_best;

        return matchCap && matchStatus && matchQuery && matchBest;
      });
    });

    const getCapabilityBadgeClass = (cap) => {
      switch (cap) {
        case 'tts': return 'badge-success';
        case 'image_generation': return 'badge-cyan';
        case 'video_generation': return 'badge-purple';
        default: return 'badge-cyan';
      }
    };

    const getStatusBadgeClass = (status) => {
      switch (status) {
        case 'success':
        case 'succeeded': return 'badge-success';
        case 'failed': return 'badge-danger';
        case 'cancelled': return 'badge-purple';
        default: return 'badge-warning';
      }
    };

    const viewDetails = async (exp) => {
      selectedExp.value = exp;
      activeTab.value = 'Configuration';
      
      // Find output asset
      const refItem = exp.output_asset_refs_json?.[0];
      linkedAsset.value = refItem ? assets.value.find(a => a.id === refItem.asset_id) : null;
      
      detailModalOpen.value = true;
      
      // Load logs timeline async
      loadLogsTimeline(exp);
    };

    const loadLogsTimeline = async (exp) => {
      loadingLogs.value = true;
      logs.value = [];
      try {
        // Query invocation logs timeline or fallback mock tasks logs
        // Check if there is an associated celery task
        // We call GET /api/tasks/{task_id}/logs if it has a task, or GET /api/invocation_logs?experiment_id={id}
        // Let's try GET /api/tasks/ matching exp.id first. Or mock logs.
        
        let logsData = [];
        if (apiClient.isMockMode()) {
          // Mock timeline log
          logsData = [
            { event_type: 'request_received', status: 'running', message: 'Narrative payload received and sanitized. Verified parameters.' },
            { event_type: 'experiment_created', status: 'running', message: `Experiment record initialized with ID: ${exp.id}` },
            { event_type: 'credential_resolved', status: 'running', message: 'Credential resolver fetched API token secret reference successfully.' },
            { event_type: 'adapter_invoked', status: exp.status === 'failed' ? 'failed' : 'success', message: `Model ${exp.model_id} invoked. Request completed in ${exp.latency_ms} ms.` }
          ];
          if (exp.status === 'success') {
            logsData.push({ event_type: 'asset_finalized', status: 'success', message: 'Asset file local verification passed, sha256 checksum saved.' });
          } else if (exp.status === 'failed') {
            logsData.push({ event_type: 'adapter_failed', status: 'failed', message: `Adapter execution halted. Error: ${exp.failed_reason || 'Unknown error'}` });
          }
        } else {
          // Real HTTP request
          logsData = await apiClient.request(`/api/experiments/${exp.id}/logs`);
        }
        
        logs.value = logsData;
      } catch (err) {
        console.error('Failed to load logs timeline:', err);
      } finally {
        loadingLogs.value = false;
      }
    };

    const closeDetails = () => {
      detailModalOpen.value = false;
      selectedExp.value = null;
      linkedAsset.value = null;
      logs.value = [];
    };

    const rerunExperiment = (exp) => {
      // Prefill into labs
      const scenario = exp.capability_type === 'tts' ? 'voice' : (exp.capability_type === 'image_generation' ? 'image' : 'video');
      window.location.hash = `#${scenario}`;
      
      //Prefill text via localStorage
      localStorage.setItem('aiwm_prefilled_cue', exp.input_text);
      addToast('info', 'Rerun Restoration', `Copied parameters to ${scenario.toUpperCase()} Lab.`);
    };

    const formatBytes = (bytes) => {
      if (!bytes) return '0 B';
      const k = 1024;
      const sizes = ['B', 'KB', 'MB', 'GB'];
      const i = Math.floor(Math.log(bytes) / Math.log(k));
      return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    };

    const formatDateLong = (isoStr) => {
      if (!isoStr) return '';
      return new Date(isoStr).toLocaleString();
    };

    onMounted(() => {
      loadHistoryData();
    });

    return {
      t,
      filterCap,
      filterStatus,
      searchQuery,
      showOnlyBest,
      detailModalOpen,
      selectedExp,
      linkedAsset,
      activeTab,
      logs,
      loadingLogs,
      filteredExperiments,
      getCapabilityBadgeClass,
      getStatusBadgeClass,
      viewDetails,
      closeDetails,
      rerunExperiment,
      formatBytes,
      formatDateLong
    };
  }
};
