import { ref, onMounted, inject, computed } from 'vue';

export default {
  name: 'VideoView',
  template: `
    <div class="video-lab-page">
      <div class="lab-two-column">
        <!-- Configuration Panel -->
        <div class="lab-config-panel glass-card">
          <h3 style="font-family: var(--font-heading); font-size: 1.25rem; margin-bottom: 20px;">{{ t('video.config.title') }}</h3>
          
          <form @submit.prevent="generateVideo" style="display: flex; flex-direction: column; gap: 16px;">
            <!-- Model Select -->
            <div>
              <label class="input-label">{{ t('video.config.model') }}</label>
              <select class="select-field" v-model="selectedModelId" required @change="onModelChange">
                <option value="" disabled>No enabled video models available</option>
                <option v-for="m in models" :key="m.id" :value="m.id">
                  {{ m.display_name }} ({{ m.pricing_hint }})
                </option>
              </select>
              <p v-if="models.length === 0" style="font-size: 0.75rem; color: var(--warning); margin-top: 4px;">
                No enabled video models found. Configure models or switch to Mock Mode.
              </p>
            </div>

            <!-- Video prompt input -->
            <div>
              <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                <label class="input-label" style="margin-bottom: 0;">{{ t('video.config.prompt') }}</label>
                <span style="font-size: 0.75rem; color: var(--text-muted);">
                  {{ rawPrompt.length }} / 800
                </span>
              </div>
              <textarea class="input-field" style="min-height: 100px; line-height: 1.4;" 
                        v-model="rawPrompt" required placeholder="Describe the scene motion, camera zoom/pan, lighting, style..."></textarea>
            </div>

            <!-- Start Frame Image Select (Image to Video workflow) -->
            <div>
              <label class="input-label">{{ t('video.config.startFrame') }}</label>
              <div style="display: flex; gap: 10px;">
                <div v-if="selectedStartFrame" style="width: 50px; height: 50px; border-radius: 4px; overflow: hidden; border: 1px solid var(--accent-cyan); background-color: var(--bg-primary);">
                  <img :src="selectedStartFrame.download_path" style="width: 100%; height: 100%; object-fit: cover;">
                </div>
                <div style="flex: 1;">
                  <button type="button" class="btn btn-secondary" style="width: 100%; justify-content: space-between; font-size: 0.85rem;" @click="openImagePicker">
                    <span>{{ selectedStartFrame ? t('video.config.changeFrame') : t('video.config.selectFrame') }}</span>
                    <i class="fas" :class="selectedStartFrame ? 'fa-check text-success' : 'fa-image'"></i>
                  </button>
                </div>
                <button v-if="selectedStartFrame" type="button" class="btn btn-danger" style="padding: 10px;" @click="clearStartFrame">
                  <i class="fas fa-times"></i>
                </button>
              </div>
            </div>

            <!-- Model specific dynamic parameters based on Schema -->
            <div v-if="uiSchema" style="background-color: var(--bg-tertiary); padding: 14px; border-radius: 8px; border: 1px solid var(--border-color); display: flex; flex-direction: column; gap: 14px;">
              <h4 style="font-size: 0.8rem; text-transform: uppercase; color: var(--text-secondary); margin-bottom: 4px;">{{ t('video.config.settings') }}</h4>
              
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

            <button type="submit" class="btn btn-primary" style="margin-top: 8px; font-size: 1rem; padding: 12px 20px;" :disabled="submitting || !selectedModelId">
              <i class="fas" :class="submitting ? 'fa-spinner animate-spin' : 'fa-video'"></i>
              {{ submitting ? t('video.config.buttonSubmitting') : t('video.config.buttonGenerate') }}
            </button>
          </form>
        </div>

        <!-- Video Outputs Gallery & Processing Queues -->
        <div class="lab-results-panel glass-card">
          <h3 style="font-family: var(--font-heading); font-size: 1.25rem; margin-bottom: 20px;">{{ t('video.history.title') }}</h3>
          
          <div style="flex: 1; overflow-y: auto; padding-right: 4px; display: flex; flex-direction: column; gap: 20px;">
            <div v-if="videoHistory.length === 0" style="text-align: center; padding: 80px 0; color: var(--text-secondary);">
              <i class="fas fa-film" style="font-size: 3.5rem; color: var(--text-muted); margin-bottom: 16px;"></i>
              <p>{{ t('video.history.empty') }}</p>
            </div>
            
            <div v-for="item in videoHistory" :key="item.exp.id" class="glass-card" style="padding: 16px; display: flex; gap: 20px; flex-direction: row; align-items: stretch;">
              <!-- Left side: video playback or status visual -->
              <div style="width: 240px; aspect-ratio: 16/9; background-color: var(--bg-primary); border-radius: 6px; overflow: hidden; display: flex; align-items: center; justify-content: center; position: relative; border: 1px solid var(--border-color); flex-shrink: 0;">
                
                <!-- If succeeded, render HTML5 Video -->
                <video v-if="item.asset" controls style="width: 100%; height: 100%; object-fit: contain;">
                  <source :src="item.asset.download_path" type="video/mp4">
                  Your browser does not support HTML5 video.
                </video>
                
                <!-- If processing / polling, show loading spinner with task progress -->
                <div v-else-if="['pending', 'queued', 'running', 'provider_pending', 'provider_running'].includes(item.exp.status)" 
                     style="text-align: center; width: 100%; padding: 12px; display: flex; flex-direction: column; gap: 10px;">
                  <i class="fas fa-spinner animate-spin text-cyan" style="font-size: 1.5rem;"></i>
                  <span style="font-size: 0.8rem; font-weight: 500;">
                    Task State: {{ item.exp.status.toUpperCase().replace('_', ' ') }}
                  </span>
                  <div class="task-progress-bar" style="max-width: 150px; margin: 0 auto;">
                    <div class="task-progress-fill" :style="{ width: (item.task?.progress || 10) + '%' }"></div>
                  </div>
                  <span style="font-size: 0.75rem; color: var(--text-muted);">{{ item.task?.progress || 0 }}%</span>
                </div>

                <!-- If failed / cancelled -->
                <div v-else style="text-align: center; color: var(--text-muted); padding: 16px;">
                  <i class="fas" :class="item.exp.status === 'cancelled' ? 'fa-ban text-purple' : 'fa-circle-xmark text-danger'" style="font-size: 1.75rem; margin-bottom: 8px;"></i>
                  <p style="font-size: 0.8rem; font-weight: 600;">Job {{ item.exp.status.toUpperCase() }}</p>
                  <p v-if="item.exp.failed_reason" style="font-size: 0.7rem; color: var(--error); margin-top: 4px;">{{ item.exp.failed_reason }}</p>
                </div>
              </div>

              <!-- Right side: details and actions -->
              <div style="flex: 1; display: flex; flex-direction: column; justify-content: space-between;">
                <div>
                  <div style="display: flex; justify-content: space-between; align-items: start;">
                    <div>
                      <h4 style="font-size: 0.95rem; font-weight: 600; text-overflow: ellipsis; overflow: hidden; max-width: 280px;" :title="item.exp.input_text">
                        {{ item.exp.input_text }}
                      </h4>
                      <span style="font-size: 0.75rem; color: var(--text-muted); display: block; margin-top: 2px;">
                        Model: {{ getModelDisplayName(item.exp.model_id) }} | Start image: {{ item.exp.input_json?.input_image_asset_id ? 'Enabled' : 'None' }}
                      </span>
                    </div>
                    
                    <div style="display: flex; gap: 4px;">
                      <span v-if="item.exp.is_best" class="badge badge-success" style="font-size: 0.65rem;">{{ t('voice.history.badgeBest') }}</span>
                      <span v-if="item.exp.is_failed_case" class="badge badge-danger" style="font-size: 0.65rem;" :title="item.exp.failed_reason">{{ t('voice.history.badgeFailed') }}</span>
                    </div>
                  </div>
                  
                  <div v-if="item.asset" style="display: flex; justify-content: space-between; align-items: center; font-size: 0.8rem; margin-top: 12px; background-color: rgba(255,255,255,0.02); padding: 6px 12px; border-radius: 4px;">
                    <span style="color: var(--text-secondary);">{{ t('video.history.rateUsability') }}</span>
                    <div class="rating-stars" style="cursor: pointer;">
                      <i v-for="i in 5" :key="i" class="fas fa-star" 
                         :class="i <= (item.asset.rating || 0) ? 'rating-star-active' : ''" 
                         @click="rateAsset(item.asset.id, i)"></i>
                    </div>
                  </div>
                </div>

                <!-- Action row -->
                <div style="display: flex; justify-content: flex-end; gap: 8px; border-top: 1px solid rgba(255,255,255,0.04); padding-top: 10px; margin-top: 10px;">
                  <button class="btn btn-secondary" style="padding: 4px 10px; font-size: 0.75rem;" @click="rerunExperiment(item.exp)">
                    {{ t('voice.history.actionRerun') }}
                  </button>
                  
                  <!-- Cancel active task -->
                  <button v-if="['pending', 'queued', 'running', 'provider_pending', 'provider_running'].includes(item.exp.status) && item.task" 
                          class="btn btn-danger" style="padding: 4px 10px; font-size: 0.75rem;" @click="cancelTask(item.task.id)">
                    {{ t('video.history.actionCancel') }}
                  </button>
                  
                  <!-- Toggle flags -->
                  <button v-if="item.asset && !item.exp.is_best" class="btn btn-secondary" style="padding: 4px 10px; font-size: 0.75rem; color: var(--success);" @click="markAsBest(item.exp.id)">
                    {{ t('voice.history.actionMarkBest') }}
                  </button>
                  <button v-if="item.asset && !item.exp.is_failed_case" class="btn btn-secondary" style="padding: 4px 10px; font-size: 0.75rem; color: var(--error);" @click="openFailModal(item.exp.id)">
                    {{ t('voice.history.actionMarkFailure') }}
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Start Frame Image Picker Modal -->
      <div v-if="imagePickerOpen" class="modal-overlay">
        <div class="modal-content glass-card" style="max-width: 700px;">
          <div class="modal-header">
            <h3>{{ t('video.frameModal.title') }}</h3>
            <button class="toast-close" @click="closeImagePicker"><i class="fas fa-times"></i></button>
          </div>
          
          <div style="max-height: 450px; overflow-y: auto;">
            <div v-if="availableImages.length === 0" style="text-align: center; padding: 40px; color: var(--text-muted);">
              {{ t('video.frameModal.empty') }}
            </div>
            <div v-else class="image-gallery-grid" style="grid-template-columns: repeat(4, 1fr);">
              <div v-for="img in availableImages" :key="img.id" class="image-card" 
                   style="cursor: pointer; border: 2px solid transparent;"
                   :style="{ borderColor: tempSelectedImageId === img.id ? 'var(--accent-cyan)' : 'transparent' }"
                   @click="tempSelectedImageId = img.id">
                <img :src="img.download_path" style="width: 100%; height: 100%; object-fit: cover;">
                <div style="position: absolute; bottom: 0; left: 0; right: 0; background-color: rgba(0,0,0,0.6); padding: 4px; font-size: 0.65rem; color: white; text-align: center; text-overflow: ellipsis; overflow: hidden; white-space: nowrap;">
                  {{ img.file_name }}
                </div>
              </div>
            </div>
          </div>
          
          <div style="display: flex; justify-content: flex-end; gap: 10px; margin-top: 20px; border-top: 1px solid var(--border-color); padding-top: 14px;">
            <button class="btn btn-secondary" @click="closeImagePicker">{{ t('common.cancel') }}</button>
            <button class="btn btn-primary" @click="confirmImageSelect" :disabled="!tempSelectedImageId">{{ t('common.select') }}</button>
          </div>
        </div>
      </div>

      <!-- Mark Failure Reason Modal -->
      <div v-if="failModalExpId" class="modal-overlay">
        <div class="modal-content glass-card" style="max-width: 450px;">
          <div class="modal-header">
            <h3>{{ t('video.failModal.title') }}</h3>
            <button class="toast-close" @click="closeFailModal"><i class="fas fa-times"></i></button>
          </div>
          <div style="display: flex; flex-direction: column; gap: 14px;">
            <p style="font-size: 0.85rem; color: var(--text-secondary);">
              {{ t('video.failModal.desc') }}
            </p>
            <div>
              <label class="input-label">{{ t('video.failModal.labelCategory') }}</label>
              <select class="select-field" v-model="failReasonCategory">
                <option value="flickering_artifacts">{{ t('video.failModal.categories.flickering_artifacts') }}</option>
                <option value="deformed_motion">{{ t('video.failModal.categories.deformed_motion') }}</option>
                <option value="bad_morphing">{{ t('video.failModal.categories.bad_morphing') }}</option>
                <option value="poor_resolution">{{ t('video.failModal.categories.poor_resolution') }}</option>
                <option value="other">{{ t('video.failModal.categories.other') }}</option>
              </select>
            </div>
            <div>
              <label class="input-label">{{ t('video.failModal.labelDetail') }}</label>
              <textarea class="input-field" style="min-height: 80px;" v-model="failReasonDetail" placeholder="Describe the video issue details..."></textarea>
            </div>
            <div style="display: flex; justify-content: flex-end; gap: 10px; margin-top: 10px;">
              <button class="btn btn-secondary" @click="closeFailModal">{{ t('common.cancel') }}</button>
              <button class="btn btn-primary" @click="submitFailureCase">{{ t('video.failModal.buttonFlag') }}</button>
            </div>
          </div>
        </div>
      </div>
    </div>
  `,
  setup() {
    const apiClient = inject('apiClient');
    const addToast = inject('addToast');
    const registerTaskPolling = inject('registerTaskPolling');
    const t = inject('t');

    const models = ref([]);
    const selectedModelId = ref('');
    const rawPrompt = ref('');
    const params = ref({});
    const submitting = ref(false);
    
    // Start Frame Asset Selection
    const selectedStartFrame = ref(null);
    const imagePickerOpen = ref(false);
    const availableImages = ref([]);
    const tempSelectedImageId = ref(null);

    const videoHistory = ref([]);
    
    // Failure modal helper
    const failModalExpId = ref(null);
    const failReasonCategory = ref('flickering_artifacts');
    const failReasonDetail = ref('');

    const selectedModel = computed(() => {
      return models.value.find(m => m.id === selectedModelId.value);
    });

    const uiSchema = computed(() => {
      return selectedModel.value?.param_ui_schema || null;
    });

    const loadVideoData = async () => {
      try {
        // Load enabled video models
        const modelsData = await apiClient.request('/api/models');
        models.value = modelsData.filter(m => m.capability_type === 'video_generation' && m.enabled);
        if (models.value.length > 0) {
          selectedModelId.value = models.value.find(m => m.is_default)?.id || models.value[0].id;
          onModelChange();
        }

        // Load generated video history
        loadVideoHistory();
      } catch (err) {
        addToast('error', 'Error initializing Video Lab', err.message);
      }
    };

    const loadVideoHistory = async () => {
      try {
        const experiments = await apiClient.request('/api/experiments');
        const assets = await apiClient.request('/api/assets');
        
        let tasks = [];
        try {
          tasks = await apiClient.request('/api/tasks');
        } catch (_) {
          tasks = [];
        }

        const videoExps = experiments.filter(e => e.capability_type === 'video_generation');
        
        videoHistory.value = videoExps.map(exp => {
          const ref = exp.output_asset_refs_json?.[0];
          const asset = ref ? assets.find(a => a.id === ref.asset_id) : null;
          const task = Array.isArray(tasks) ? tasks.find(t => t.experiment_id === exp.id) : null;

          return { exp, asset, task };
        });
      } catch (err) {
        console.error('Failed to load video history:', err);
      }
    };

    const onModelChange = () => {
      const model = selectedModel.value;
      if (model) {
        params.value = { ...model.default_params };
      }
    };

    const openImagePicker = async () => {
      try {
        const assets = await apiClient.request('/api/assets');
        availableImages.value = assets.filter(a => a.asset_type === 'image' && a.status !== 'discarded' && a.status !== 'deleted');
        tempSelectedImageId.value = selectedStartFrame.value?.id || null;
        imagePickerOpen.value = true;
      } catch (err) {
        addToast('error', 'Failed to load image library', err.message);
      }
    };

    const closeImagePicker = () => {
      imagePickerOpen.value = false;
    };

    const confirmImageSelect = () => {
      const img = availableImages.value.find(a => a.id === tempSelectedImageId.value);
      if (img) {
        selectedStartFrame.value = img;
      }
      closeImagePicker();
    };

    const clearStartFrame = () => {
      selectedStartFrame.value = null;
    };

    const generateVideo = async () => {
      const cleanPrompt = rawPrompt.value.trim();
      if (!cleanPrompt) {
        addToast('error', 'Validation Error', 'Video prompt is required.');
        return;
      }
      if (cleanPrompt.length > 800) {
        addToast('error', 'Validation Error', 'Video prompt is restricted to 800 characters.');
        return;
      }

      submitting.value = true;
      try {
        const payload = {
          capability_type: 'video_generation',
          model_id: selectedModelId.value,
          run_mode: 'async',
          input: {
            prompt: cleanPrompt,
            input_image_asset_id: selectedStartFrame.value?.id || null
          },
          params: params.value
        };

        const result = await apiClient.request('/api/capabilities/run', {
          method: 'POST',
          body: JSON.stringify(payload)
        });

        if (result.task_id) {
          addToast('success', 'Job Submitted', `Celery async job started. Task ID: ${result.task_id}`);
          registerTaskPolling(result.task_id);
          setTimeout(loadVideoHistory, 1000);
        } else {
          addToast('error', 'Submission Failed', 'No Celery task ID returned from backend.');
        }
      } catch (err) {
        addToast('error', 'Generation Submission Failed', err.message || 'Check network connection.');
      } finally {
        submitting.value = false;
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
        addToast('success', 'Rating Saved', `Video quality score rated: ${score}/5`);
        loadVideoHistory();
      } catch (err) {
        addToast('error', 'Failed to save rating', err.message);
      }
    };

    const markAsBest = async (expId) => {
      try {
        await apiClient.request(`/api/experiments/${expId}/mark-best`, { method: 'POST' });
        addToast('success', 'Best Flag Set', 'This experiment was marked as the Best Output.');
        loadVideoHistory();
      } catch (err) {
        addToast('error', 'Request failed', err.message);
      }
    };

    const openFailModal = (expId) => {
      failModalExpId.value = expId;
      failReasonCategory.value = 'flickering_artifacts';
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
        loadVideoHistory();
      } catch (err) {
        addToast('error', 'Request failed', err.message);
      }
    };

    const rerunExperiment = (exp) => {
      selectedModelId.value = exp.model_id;
      onModelChange();
      rawPrompt.value = exp.input_text;
      
      const startImgId = exp.input_json?.input_image_asset_id;
      if (startImgId) {
        apiClient.request(`/api/assets/${startImgId}`).then(img => {
          selectedStartFrame.value = img;
        }).catch(() => {
          selectedStartFrame.value = null;
        });
      } else {
        selectedStartFrame.value = null;
      }
      
      params.value = { ...exp.params_json };
      addToast('info', 'Parameters Restored', 'Copied experiment parameters into configuration panel.');
    };

    const cancelTask = async (taskId) => {
      try {
        await apiClient.request(`/api/tasks/${taskId}/cancel`, { method: 'POST' });
        addToast('warning', 'Task Cancel Requested', `Sent cancellation request for task ${taskId}`);
        loadVideoHistory();
      } catch (err) {
        addToast('error', 'Cancellation Failed', err.message);
      }
    };

    const getModelDisplayName = (modelId) => {
      const model = models.value.find(m => m.id === modelId);
      return model ? model.display_name : modelId;
    };

    onMounted(() => {
      loadVideoData();
      const interval = setInterval(loadVideoHistory, 5000);
      return () => clearInterval(interval);
    });

    return {
      t,
      models,
      selectedModelId,
      rawPrompt,
      params,
      submitting,
      selectedStartFrame,
      imagePickerOpen,
      availableImages,
      tempSelectedImageId,
      videoHistory,
      failModalExpId,
      failReasonCategory,
      failReasonDetail,
      selectedModel,
      uiSchema,
      onModelChange,
      openImagePicker,
      closeImagePicker,
      confirmImageSelect,
      clearStartFrame,
      generateVideo,
      rateAsset,
      markAsBest,
      openFailModal,
      closeFailModal,
      submitFailureCase,
      rerunExperiment,
      cancelTask,
      getModelDisplayName
    };
  }
};
