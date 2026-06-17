import { ref, onMounted, inject, computed } from 'vue';

export default {
  name: 'ProjectsView',
  template: `
    <div class="projects-page">
      <div class="grid-cols-12">
        <!-- Projects List / Creator -->
        <div v-if="!activeProjectId" class="col-span-12 glass-card">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px;">
            <h3 style="font-family: var(--font-heading); font-size: 1.35rem;">{{ t('projects.workspace.title') }}</h3>
            <button class="btn btn-primary" @click="showCreateModal = true">
              <i class="fas fa-plus"></i> {{ t('projects.workspace.create') }}
            </button>
          </div>

          <div v-if="projects.length === 0" style="text-align: center; padding: 60px 0; color: var(--text-secondary);">
            <i class="fas fa-folder-open" style="font-size: 3.5rem; color: var(--text-muted); margin-bottom: 16px;"></i>
            <p>{{ t('projects.workspace.empty') }}</p>
          </div>

          <div v-else class="grid-cols-12" style="gap: 20px;">
            <div v-for="prj in projects" :key="prj.id" class="col-span-4 glass-card" style="display: flex; flex-direction: column; justify-content: space-between; min-height: 180px;">
              <div>
                <h4 style="font-family: var(--font-heading); font-size: 1.15rem; font-weight: 600; color: var(--accent-cyan);">{{ prj.name }}</h4>
                <p style="font-size: 0.85rem; color: var(--text-secondary); margin-top: 6px; line-height: 1.4;">{{ prj.description || t('common.none') }}</p>
                <div style="font-size: 0.75rem; color: var(--text-muted); margin-top: 12px;">{{ t('projects.workspace.created') }}: {{ formatDate(prj.created_at) }}</div>
              </div>
              
              <div style="display: flex; justify-content: flex-end; gap: 8px; margin-top: 16px; border-top: 1px solid rgba(255,255,255,0.05); padding-top: 12px;">
                <button class="btn btn-primary" style="padding: 6px 12px; font-size: 0.8rem;" @click="openProjectWorkspace(prj.id)">
                  <i class="fas fa-folder-open"></i> {{ t('projects.workspace.enter') }}
                </button>
                <button class="btn btn-danger" style="padding: 6px 12px; font-size: 0.8rem;" @click="deleteProject(prj.id)">
                  <i class="fas fa-trash"></i>
                </button>
              </div>
            </div>
          </div>
        </div>

        <!-- Active Project Workspace View -->
        <div v-else class="col-span-12" style="display: flex; flex-direction: column; gap: 24px;">
          <!-- Active Project Header -->
          <div class="glass-card" style="display: flex; justify-content: space-between; align-items: center; padding: 16px 24px;">
            <div>
              <button class="btn btn-secondary" style="padding: 4px 10px; font-size: 0.75rem; margin-bottom: 6px;" @click="closeProjectWorkspace">
                <i class="fas fa-arrow-left"></i> {{ t('projects.active.back') }}
              </button>
              <h3 style="font-family: var(--font-heading); font-size: 1.4rem; color: var(--text-primary);">
                {{ t('projects.active.projectPrefix') }}: {{ activeProject.name }}
              </h3>
            </div>
            
            <div style="display: flex; gap: 10px;">
              <button class="btn btn-secondary" @click="openExportManifest">
                <i class="fas fa-file-export text-purple"></i> {{ t('projects.active.export') }}
              </button>
            </div>
          </div>

          <!-- Project Workspace Grid -->
          <div class="grid-cols-12" style="gap: 24px;">
            <!-- Left Panel: Script & Storyboard -->
            <div class="col-span-5 glass-card" style="display: flex; flex-direction: column; gap: 20px;">
              <div>
                <h4 style="font-family: var(--font-heading); font-size: 1.1rem; margin-bottom: 12px;">{{ t('projects.active.scriptTitle') }}</h4>
                <textarea class="input-field" style="min-height: 200px; font-family: inherit; line-height: 1.5; font-size: 0.9rem;" 
                          v-model="scriptContent" :placeholder="t('projects.active.scriptPlaceholder')"></textarea>
                <div style="display: flex; justify-content: flex-end; margin-top: 10px;">
                  <button class="btn btn-primary" style="font-size: 0.85rem; padding: 6px 14px;" @click="saveScriptVersion">
                    {{ t('projects.active.saveScript') }}
                  </button>
                </div>
              </div>

              <!-- Project Voiceover Settings -->
              <div style="border-top: 1px solid var(--border-color); padding-top: 16px;">
                <h4 style="font-family: var(--font-heading); font-size: 1.1rem; margin-bottom: 12px;">
                  {{ t('projects.active.projectVoiceoverSettings') }}
                </h4>
                <div style="display: flex; flex-direction: column; gap: 8px;">
                  <label class="input-label" style="margin-bottom: 0;">{{ t('projects.active.defaultVoiceProfile') }}</label>
                  <select class="input-field" style="width: 100%;" v-model="projectDefaultVoiceProfileId" @change="updateProjectDefaultVoice">
                    <option value="">{{ t('projects.active.selectVoiceProfile') }}</option>
                    <option v-for="vp in voiceProfiles" :key="vp.id" :value="vp.id">
                      {{ vp.voice_name }} ({{ vp.provider_id || vp.provider }}) <span v-if="vp.status !== 'active'">[{{ vp.status }}]</span>
                    </option>
                  </select>
                </div>
              </div>

              <!-- Shot creator tool -->
              <div style="border-top: 1px solid var(--border-color); padding-top: 16px;">
                <h4 style="font-family: var(--font-heading); font-size: 1.1rem; margin-bottom: 12px;">{{ t('projects.active.addShot') }}</h4>
                <form @submit.prevent="createShot" style="display: flex; flex-direction: column; gap: 10px;">
                  <input type="text" class="input-field" v-model="newShot.name" required :placeholder="t('projects.active.shotLabel')">
                  <textarea class="input-field" style="min-height: 60px;" v-model="newShot.cue" :placeholder="t('projects.active.shotCue')"></textarea>
                  <button type="submit" class="btn btn-secondary" style="font-size: 0.85rem;">
                    <i class="fas fa-plus"></i> {{ t('projects.active.buttonAddTimeline') }}
                  </button>
                </form>
              </div>
            </div>

            <!-- Right Panel: Shot Timeline & Linked Assets -->
            <div class="col-span-7 glass-card" style="display: flex; flex-direction: column; height: calc(100vh - 270px); overflow: hidden;">
              <h4 style="font-family: var(--font-heading); font-size: 1.1rem; margin-bottom: 16px;">{{ t('projects.active.timelineTitle') }}</h4>
              
              <div style="flex: 1; overflow-y: auto; display: flex; flex-direction: column; gap: 12px; padding-right: 4px;">
                <div v-if="shots.length === 0" style="text-align: center; padding: 40px; color: var(--text-secondary); font-size: 0.85rem;">
                  {{ t('projects.active.timelineEmpty') }}
                </div>
                
                <div v-for="(shot, idx) in shots" :key="shot.id" class="glass-card" style="padding: 12px; background-color: var(--bg-tertiary);">
                  <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 10px;">
                    <div>
                      <h5 style="font-size: 0.9rem; font-weight: 600;">
                        {{ idx + 1 }}. {{ shot.name }}
                      </h5>
                      <p style="font-size: 0.8rem; color: var(--text-secondary); margin-top: 4px; font-style: italic;">
                        "{{ shot.cue }}"
                      </p>
                    </div>
                    
                    <!-- Move buttons -->
                    <div style="display: flex; gap: 4px;">
                      <button class="btn btn-secondary" style="padding: 3px 6px; font-size: 0.65rem;" :disabled="idx === 0" @click="moveShot(idx, -1)">
                        <i class="fas fa-arrow-up"></i>
                      </button>
                      <button class="btn btn-secondary" style="padding: 3px 6px; font-size: 0.65rem;" :disabled="idx === shots.length - 1" @click="moveShot(idx, 1)">
                        <i class="fas fa-arrow-down"></i>
                      </button>
                      <button class="btn btn-danger" style="padding: 3px 6px; font-size: 0.65rem;" @click="deleteShot(shot.id)">
                        <i class="fas fa-trash"></i>
                      </button>
                    </div>
                  </div>

                  <!-- Linked Assets row -->
                  <div style="display: flex; gap: 12px; align-items: center; background-color: var(--bg-primary); padding: 8px; border-radius: 4px; border: 1px solid rgba(255,255,255,0.03);">
                    <div style="width: 45px; height: 45px; background-color: var(--bg-tertiary); border-radius: 4px; overflow: hidden; display: flex; align-items: center; justify-content: center; flex-shrink: 0;">
                      <img v-if="getLinkedAsset(shot)?.asset_type === 'image'" :src="getLinkedAsset(shot).download_path" style="width: 100%; height: 100%; object-fit: cover;">
                      <i v-else-if="getLinkedAsset(shot)?.asset_type === 'audio'" class="fas fa-music text-success"></i>
                      <i v-else-if="getLinkedAsset(shot)?.asset_type === 'video'" class="fas fa-film text-purple"></i>
                      <i v-else class="fas fa-link text-muted"></i>
                    </div>
                    
                    <div style="flex: 1; font-size: 0.8rem;">
                      <div v-if="getLinkedAsset(shot)">
                        <span style="font-weight: 500;">{{ t('projects.active.linkedPrefix') }}: {{ getLinkedAsset(shot).file_name }}</span>
                        <div style="font-size: 0.7rem; color: var(--text-secondary);">Asset ID: {{ getLinkedAsset(shot).id }}</div>
                      </div>
                      <span v-else style="color: var(--text-muted); font-style: italic;">{{ t('projects.active.noAssetLinked') }}</span>
                    </div>

                    <!-- Quick buttons -->
                    <div style="display: flex; gap: 6px;">
                      <!-- Quick Generation -->
                      <button class="btn btn-secondary" style="padding: 4px 8px; font-size: 0.7rem; color: var(--accent-cyan);" 
                              :title="t('projects.active.runQuickGenerateTitle')" @click="runQuickGenerate(shot)">
                        <i class="fas fa-bolt"></i> {{ t('projects.active.generate') }}
                      </button>
                      
                      <!-- Pick from library -->
                      <button class="btn btn-secondary" style="padding: 4px 8px; font-size: 0.7rem;" @click="openAssetPicker(shot)">
                        {{ t('projects.active.shotActions.linkAsset') }}
                      </button>
                    </div>
                  </div>

                  <!-- Shot Voiceover Editor Block -->
                  <div style="margin-top: 12px; padding: 10px; background-color: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.04); border-radius: 4px; display: flex; flex-direction: column; gap: 10px;">
                    <!-- Editable Voiceover Text -->
                    <div style="display: flex; flex-direction: column; gap: 4px;">
                      <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span style="font-size: 0.8rem; font-weight: 600; color: var(--text-secondary);">
                          {{ t('projects.active.scriptTitle') }}
                        </span>
                        <button class="btn btn-secondary" style="padding: 2px 8px; font-size: 0.7rem; height: auto;" @click="saveShotVoiceoverText(shot)">
                          {{ t('projects.active.shotActions.saveShot') }}
                        </button>
                      </div>
                      <textarea class="input-field" style="min-height: 40px; font-size: 0.8rem; padding: 6px; font-family: inherit;" 
                                v-model="shot.voiceover_text" :placeholder="t('projects.active.shotCue')"></textarea>
                    </div>

                    <!-- Voice Profile Override Dropdown -->
                    <div style="display: flex; align-items: center; gap: 10px;">
                      <span style="font-size: 0.8rem; color: var(--text-secondary); min-width: 90px;">
                        {{ t('projects.active.overrideVoiceProfile') }}:
                      </span>
                      <select class="input-field" style="flex: 1; font-size: 0.8rem; padding: 4px 8px; height: auto;" 
                              v-model="shot.metadata_json.voice_profile_id" @change="updateShotVoiceOverride(shot)">
                        <option value="">{{ t('projects.active.selectVoiceProfile') }} ({{ t('common.default') }})</option>
                        <option v-for="vp in voiceProfiles" :key="vp.id" :value="vp.id">
                          {{ vp.voice_name }} ({{ vp.provider_id || vp.provider }}) <span v-if="vp.status !== 'active'">[{{ vp.status }}]</span>
                        </option>
                      </select>
                    </div>

                    <!-- Compliance Safety Warnings -->
                    <div v-if="getShotVoiceWarnings(shot).length > 0" 
                         style="padding: 6px 10px; background-color: rgba(239, 68, 68, 0.08); border-left: 3px solid var(--error); border-radius: 3px; display: flex; flex-direction: column; gap: 4px;">
                      <div v-for="warn in getShotVoiceWarnings(shot)" :key="warn" style="font-size: 0.75rem; color: var(--error); display: flex; align-items: center; gap: 6px;">
                        <i class="fas fa-exclamation-triangle"></i>
                        <span>{{ warn }}</span>
                      </div>
                    </div>

                    <!-- Generation / Player Actions Row -->
                    <div style="display: flex; align-items: center; justify-content: space-between; border-top: 1px solid rgba(255,255,255,0.05); padding-top: 8px; gap: 10px;">
                      <div style="display: flex; align-items: center; gap: 8px;">
                        <button class="btn btn-primary" style="padding: 4px 10px; font-size: 0.75rem;" 
                                :disabled="generatingVoiceoverShotId === shot.id"
                                @click="generateShotVoiceover(shot)">
                          <i v-if="generatingVoiceoverShotId === shot.id" class="fas fa-spinner fa-spin"></i>
                          <i v-else class="fas fa-microphone"></i>
                          {{ generatingVoiceoverShotId === shot.id ? t('projects.active.buttonGeneratingVoiceover') : t('projects.active.generateVoiceover') }}
                        </button>

                        <!-- Explicit Confirmation checkbox for High Risk profiles -->
                        <label v-if="isHighRiskVoiceProfile(shot)" style="display: flex; align-items: center; gap: 6px; font-size: 0.75rem; color: var(--error); cursor: pointer; user-select: none;">
                          <input type="checkbox" v-model="shot.explicit_confirm" style="margin: 0; transform: scale(1.1);">
                          <span>{{ t('common.confirm') }}</span>
                        </label>
                      </div>

                      <!-- Audio Player for generated voiceover audio -->
                      <div v-if="shot.selected_audio_asset_id" style="display: flex; align-items: center;">
                        <audio :src="getAssetDownloadPath(shot.selected_audio_asset_id)" controls style="height: 26px; width: 180px; outline: none;"></audio>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Create Project Modal -->
      <div v-if="showCreateModal" class="modal-overlay">
        <div class="modal-content glass-card" style="max-width: 450px;">
          <div class="modal-header">
            <h3>{{ t('projects.modalCreate.title') }}</h3>
            <button class="toast-close" @click="showCreateModal = false"><i class="fas fa-times"></i></button>
          </div>
          
          <form @submit.prevent="createProject" style="display: flex; flex-direction: column; gap: 14px;">
            <div>
              <label class="input-label">{{ t('projects.modalCreate.name') }}</label>
              <input type="text" class="input-field" v-model="projectForm.name" required :placeholder="t('projects.modalCreate.namePlaceholder')">
            </div>
            <div>
              <label class="input-label">{{ t('projects.modalCreate.desc') }}</label>
              <textarea class="input-field" style="min-height: 80px;" v-model="projectForm.description" :placeholder="t('projects.modalCreate.descPlaceholder')"></textarea>
            </div>
            
            <div style="display: flex; justify-content: flex-end; gap: 10px; margin-top: 10px;">
              <button type="button" class="btn btn-secondary" @click="showCreateModal = false">{{ t('common.cancel') }}</button>
              <button type="submit" class="btn btn-primary">{{ t('projects.modalCreate.buttonCreate') }}</button>
            </div>
          </form>
        </div>
      </div>

      <!-- Asset Picker Modal -->
      <div v-if="pickerShotId" class="modal-overlay">
        <div class="modal-content glass-card" style="max-width: 600px;">
          <div class="modal-header">
            <h3>{{ t('projects.active.assetSelectorTitle') }}</h3>
            <button class="toast-close" @click="closeAssetPicker"><i class="fas fa-times"></i></button>
          </div>
          
          <div style="max-height: 350px; overflow-y: auto; display: flex; flex-direction: column; gap: 10px;">
            <div v-if="libraryAssets.length === 0" style="text-align: center; color: var(--text-muted); padding: 20px;">
              {{ t('projects.active.noAssetsAvailable') }}
            </div>
            <div v-for="ast in libraryAssets" :key="ast.id" 
                 class="glass-card" style="padding: 10px; display: flex; align-items: center; justify-content: space-between; background-color: var(--bg-tertiary);">
              <div style="display: flex; align-items: center; gap: 10px;">
                <div style="width: 40px; height: 40px; background-color: var(--bg-primary); border-radius: 4px; overflow: hidden; display: flex; align-items: center; justify-content: center;">
                  <img v-if="ast.asset_type === 'image'" :src="ast.download_path" style="width: 100%; height: 100%; object-fit: cover;">
                  <i v-else-if="ast.asset_type === 'audio'" class="fas fa-music text-success"></i>
                  <i v-else class="fas fa-film text-purple"></i>
                </div>
                <div>
                  <h5 style="font-size: 0.8rem; font-weight: 600;">{{ ast.file_name }}</h5>
                  <span style="font-size: 0.7rem; color: var(--text-secondary);">{{ t('history.table.type') }}: {{ ast.asset_type }}</span>
                </div>
              </div>
              <button class="btn btn-secondary" style="padding: 4px 10px; font-size: 0.7rem;" @click="linkAssetToShot(ast.id)">
                {{ t('projects.active.linkButton') }}
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Export Manifest Modal -->
      <div v-if="exportModalOpen" class="modal-overlay">
        <div class="modal-content glass-card" style="max-width: 650px;">
          <div class="modal-header">
            <h3>{{ t('projects.exportModal.titlePreview') }}</h3>
            <button class="toast-close" @click="closeExportModal"><i class="fas fa-times"></i></button>
          </div>

          <div v-if="exportManifest" style="display: flex; flex-direction: column; gap: 16px;">
            <!-- Secure License & Warnings Panel -->
            <div v-if="exportManifest.warnings && exportManifest.warnings.length > 0" class="glass-card" style="background-color: rgba(239, 68, 68, 0.05); border-left: 4px solid var(--error); padding: 14px;">
              <h4 style="color: var(--error); font-size: 0.9rem; font-family: var(--font-heading); margin-bottom: 6px;">
                <i class="fas fa-triangle-exclamation"></i> {{ t('projects.exportModal.warningsTitle') }}
              </h4>
              <ul style="font-size: 0.8rem; color: var(--text-secondary); padding-left: 20px; display: flex; flex-direction: column; gap: 4px;">
                <li v-for="warn in exportManifest.warnings" :key="warn">{{ warn }}</li>
              </ul>
            </div>
            
            <div v-else class="glass-card" style="background-color: rgba(16, 185, 129, 0.05); border-left: 4px solid var(--success); padding: 14px;">
              <h4 style="color: var(--success); font-size: 0.9rem; font-family: var(--font-heading);">
                <i class="fas fa-circle-check"></i> {{ t('projects.exportModal.successTitle') }}
              </h4>
              <p style="font-size: 0.8rem; color: var(--text-secondary); margin-top: 4px;">
                {{ t('projects.exportModal.successDesc') }}
              </p>
            </div>

            <!-- Manifest Data Structure Preview -->
            <div>
              <label class="input-label">{{ t('projects.exportModal.payloadLabel') }}</label>
              <textarea class="input-field" readonly style="min-height: 180px; font-family: monospace; font-size: 0.8rem; background-color: var(--bg-primary);" 
                        :value="JSON.stringify(exportManifest, null, 2)"></textarea>
            </div>

            <div style="display: flex; justify-content: flex-end; gap: 10px;">
              <button class="btn btn-secondary" @click="closeExportModal">{{ t('common.close') }}</button>
              <button class="btn btn-primary" @click="triggerDownloadManifest">
                <i class="fas fa-download"></i> {{ t('projects.exportModal.downloadBtn') }}
              </button>
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

    const projects = ref([]);
    const activeProjectId = ref(null);
    const scriptContent = ref('');
    const shots = ref([]);
    
    // Voice profiles settings
    const voiceProfiles = ref([]);
    const projectDefaultVoiceProfileId = ref('');
    const generatingVoiceoverShotId = ref(null);

    // Create Project form
    const showCreateModal = ref(false);
    const projectForm = ref({ name: '', description: '' });

    // Add Shot Card form
    const newShot = ref({ name: '', cue: '' });

    // Link Asset picker
    const pickerShotId = ref(null);
    const libraryAssets = ref([]);

    // Export manifestation
    const exportModalOpen = ref(false);
    const exportManifest = ref(null);

    const activeProject = computed(() => {
      return projects.value.find(p => p.id === activeProjectId.value);
    });

    const loadProjects = async () => {
      try {
        const data = await apiClient.request('/api/projects');
        projects.value = data;
      } catch (err) {
        addToast('error', 'Error loading projects', err.message);
      }
    };

    const loadVoiceProfiles = async () => {
      try {
        const data = await apiClient.request('/api/voice-profiles');
        voiceProfiles.value = data;
      } catch (err) {
        addToast('error', 'Error loading voice profiles', err.message);
      }
    };

    const loadLibraryAssets = async () => {
      try {
        const assets = await apiClient.request('/api/assets');
        libraryAssets.value = assets.filter(a => a.status !== 'discarded' && a.status !== 'deleted');
      } catch (_) {}
    };

    const createProject = async () => {
      try {
        await apiClient.request('/api/projects', {
          method: 'POST',
          body: JSON.stringify({
            name: projectForm.value.name.trim(),
            description: projectForm.value.description.trim()
          })
        });
        addToast('success', 'Project Created', 'New project workspace added.');
        showCreateModal.value = false;
        projectForm.value = { name: '', description: '' };
        loadProjects();
      } catch (err) {
        addToast('error', 'Failed to create project', err.message);
      }
    };

    const deleteProject = async (id) => {
      if (!confirm(t('projects.workspace.deleteConfirm'))) return;
      try {
        // Backend soft-deletes project
        await apiClient.request(`/api/projects/${id}`, { method: 'DELETE' });
        addToast('success', 'Project Deleted', 'Project workspace removed.');
        loadProjects();
      } catch (err) {
        addToast('error', 'Deletion failed', err.message);
      }
    };

    const openProjectWorkspace = async (id) => {
      activeProjectId.value = id;
      try {
        const prj = await apiClient.request(`/api/projects/${id}`);
        scriptContent.value = prj.narrative_script || '';
        projectDefaultVoiceProfileId.value = prj.metadata_json?.default_voice_profile_id || '';
        
        // Load shots & assets
        loadShotsForProject();
        loadLibraryAssets();
        loadVoiceProfiles();
      } catch (err) {
        addToast('error', 'Workspace Loading failed', err.message);
      }
    };

    const closeProjectWorkspace = () => {
      activeProjectId.value = null;
      shots.value = [];
      scriptContent.value = '';
      projectDefaultVoiceProfileId.value = '';
    };

    const loadShotsForProject = async () => {
      try {
        const list = await apiClient.request(`/api/projects/${activeProjectId.value}/shots`);
        shots.value = list.map(s => {
          if (!s.metadata_json) s.metadata_json = {};
          if (s.metadata_json.voice_profile_id === undefined) {
            s.metadata_json.voice_profile_id = '';
          }
          return s;
        }).sort((a, b) => a.order_index - b.order_index);
      } catch (_) {
        shots.value = [];
      }
    };

    const updateProjectDefaultVoice = async () => {
      if (!projectDefaultVoiceProfileId.value) {
        try {
          const updatedPrj = await apiClient.request(`/api/projects/${activeProjectId.value}`, {
            method: 'PATCH',
            body: JSON.stringify({
              metadata_json: {
                ...activeProject.value.metadata_json,
                default_voice_profile_id: null
              }
            })
          });
          const idx = projects.value.findIndex(p => p.id === activeProjectId.value);
          if (idx !== -1) {
            projects.value[idx] = updatedPrj;
          }
          addToast('success', 'Project Default Voice Cleared', 'Successfully cleared the default voice profile.');
        } catch (err) {
          addToast('error', 'Failed to clear default voice profile', err.message);
        }
        return;
      }
      
      try {
        const updatedPrj = await apiClient.request(`/api/voice-profiles/${projectDefaultVoiceProfileId.value}/set-project-default`, {
          method: 'POST',
          body: JSON.stringify({ project_id: activeProjectId.value })
        });
        const idx = projects.value.findIndex(p => p.id === activeProjectId.value);
        if (idx !== -1) {
          projects.value[idx] = updatedPrj;
        }
        addToast('success', 'Project Default Voice Updated', 'Successfully set default voice profile.');
      } catch (err) {
        addToast('error', 'Failed to update default voice profile', err.message);
        projectDefaultVoiceProfileId.value = activeProject.value.metadata_json?.default_voice_profile_id || '';
      }
    };

    const updateShotVoiceOverride = async (shot) => {
      try {
        const updated = await apiClient.request(`/api/projects/${activeProjectId.value}/shots/${shot.id}`, {
          method: 'PATCH',
          body: JSON.stringify({
            metadata_json: {
              ...shot.metadata_json,
              voice_profile_id: shot.metadata_json.voice_profile_id || null
            }
          })
        });
        addToast('success', 'Voice Profile Override Saved', 'Saved voice override setting.');
        shot.metadata_json = updated.metadata_json || {};
      } catch (err) {
        addToast('error', 'Failed to save override setting', err.message);
      }
    };

    const saveShotVoiceoverText = async (shot) => {
      try {
        const updated = await apiClient.request(`/api/projects/${activeProjectId.value}/shots/${shot.id}`, {
          method: 'PATCH',
          body: JSON.stringify({
            voiceover_text: shot.voiceover_text
          })
        });
        addToast('success', 'Voiceover Text Saved', 'Saved voiceover script for shot.');
        shot.voiceover_text = updated.voiceover_text;
      } catch (err) {
        addToast('error', 'Failed to save voiceover text', err.message);
      }
    };

    const getShotVoiceWarnings = (shot) => {
      const vpId = shot.metadata_json?.voice_profile_id || activeProject.value?.metadata_json?.default_voice_profile_id;
      if (!vpId) return [];
      const vp = voiceProfiles.value.find(p => p.id === vpId);
      if (!vp) return [];
      
      const warnings = [];
      if (vp.status === 'revoked' || vp.consent_status === 'revoked') {
        warnings.push(t('voice.profiles.warnings.revoked'));
      } else if (vp.status === 'expired' || vp.consent_status === 'expired') {
        warnings.push(t('voice.profiles.warnings.expired'));
      } else if (vp.expires_at && new Date(vp.expires_at) <= new Date()) {
        warnings.push(t('voice.profiles.warnings.expired'));
      }
      
      if (vp.status === 'testing') {
        warnings.push(t('voice.profiles.warnings.testing'));
      }
      if (vp.risk_level === 'high') {
        warnings.push(t('voice.profiles.warnings.highRisk'));
      }
      if (!vp.commercial_allowed) {
        warnings.push(t('voice.profiles.warnings.commercialWarning'));
      }
      return warnings;
    };

    const isHighRiskVoiceProfile = (shot) => {
      const vpId = shot.metadata_json?.voice_profile_id || activeProject.value?.metadata_json?.default_voice_profile_id;
      if (!vpId) return false;
      const vp = voiceProfiles.value.find(p => p.id === vpId);
      return vp ? vp.risk_level === 'high' : false;
    };

    const generateShotVoiceover = async (shot) => {
      if (!shot.voiceover_text || !shot.voiceover_text.trim()) {
        addToast('warning', 'Narrative Text Empty', 'Please provide narrative text for this shot.');
        return;
      }
      
      const vpId = shot.metadata_json?.voice_profile_id || activeProject.value?.metadata_json?.default_voice_profile_id;
      let commercialUse = false;
      if (vpId) {
        const vp = voiceProfiles.value.find(p => p.id === vpId);
        if (vp) {
          if (vp.status === 'revoked' || vp.consent_status === 'revoked') {
            addToast('error', 'Revoked Voice Profile', 'Cannot generate voiceover using a revoked voice profile.');
            return;
          }
          if (vp.status === 'expired' || vp.consent_status === 'expired' || (vp.expires_at && new Date(vp.expires_at) <= new Date())) {
            addToast('error', 'Expired Voice Profile', 'Cannot generate voiceover using an expired voice profile.');
            return;
          }
          commercialUse = vp.commercial_allowed;
        }
      }

      generatingVoiceoverShotId.value = shot.id;
      try {
        const payload = {
          commercial_use: commercialUse,
          explicit_confirm: !!shot.explicit_confirm
        };
        const updated = await apiClient.request(`/api/projects/${activeProjectId.value}/shots/${shot.id}/generate-voiceover`, {
          method: 'POST',
          body: JSON.stringify(payload)
        });
        addToast('success', 'Voiceover Generated', 'Successfully generated narration audio.');
        shot.selected_audio_asset_id = updated.selected_audio_asset_id;
        loadShotsForProject();
        loadLibraryAssets();
      } catch (err) {
        addToast('error', 'Generation failed', err.message);
      } finally {
        generatingVoiceoverShotId.value = null;
      }
    };

    const getAssetDownloadPath = (assetId) => {
      return `/api/assets/${assetId}/download`;
    };

    const saveScriptVersion = async () => {
      try {
        await apiClient.request(`/api/projects/${activeProjectId.value}`, {
          method: 'PATCH',
          body: JSON.stringify({ narrative_script: scriptContent.value })
        });
        addToast('success', 'Script Saved', 'Created Script version node and synced narrative.');
      } catch (err) {
        addToast('error', 'Script Saving failed', err.message);
      }
    };

    const createShot = async () => {
      try {
        const order = shots.value.length;
        await apiClient.request(`/api/projects/${activeProjectId.value}/shots`, {
          method: 'POST',
          body: JSON.stringify({
            name: newShot.value.name.trim(),
            cue: newShot.value.cue.trim(),
            order_index: order
          })
        });
        addToast('success', 'Shot Added', 'Created timeline shot card.');
        newShot.value = { name: '', cue: '' };
        loadShotsForProject();
      } catch (err) {
        addToast('error', 'Failed to add shot', err.message);
      }
    };

    const deleteShot = async (shotId) => {
      try {
        await apiClient.request(`/api/projects/${activeProjectId.value}/shots/${shotId}`, { method: 'DELETE' });
        loadShotsForProject();
      } catch (err) {
        addToast('error', 'Failed to delete shot', err.message);
      }
    };

    const moveShot = async (index, direction) => {
      const newShots = [...shots.value];
      const targetIdx = index + direction;
      if (targetIdx < 0 || targetIdx >= newShots.length) return;
      
      const temp = newShots[index];
      newShots[index] = newShots[targetIdx];
      newShots[targetIdx] = temp;
      
      newShots.forEach((s, idx) => {
        s.order_index = idx;
      });
      
      shots.value = newShots;

      try {
        await apiClient.request(`/api/projects/${activeProjectId.value}/shots/reorder`, {
          method: 'POST',
          body: JSON.stringify({
            shot_ids: newShots.map(s => s.id)
          })
        });
      } catch (err) {
        addToast('error', 'Failed to save shot order', err.message);
      }
    };

    const openAssetPicker = async (shot) => {
      pickerShotId.value = shot.id;
      try {
        const assets = await apiClient.request('/api/assets');
        libraryAssets.value = assets.filter(a => a.status !== 'discarded' && a.status !== 'deleted');
      } catch (err) {
        addToast('error', 'Error loading assets', err.message);
      }
    };

    const closeAssetPicker = () => {
      pickerShotId.value = null;
    };

    const linkAssetToShot = async (assetId) => {
      try {
        await apiClient.request(`/api/projects/${activeProjectId.value}/shots/${pickerShotId.value}/link`, {
          method: 'POST',
          body: JSON.stringify({ asset_id: assetId })
        });
        addToast('success', 'Asset Linked', 'Linked media file to timeline shot card.');
        closeAssetPicker();
        loadShotsForProject();
      } catch (err) {
        addToast('error', 'Linking failed', err.message);
      }
    };

    const getLinkedAsset = (shot) => {
      if (shot.linked_asset) return shot.linked_asset;
      const assetId = shot.selected_image_asset_id || shot.selected_audio_asset_id || shot.selected_video_asset_id;
      if (!assetId) return null;
      return libraryAssets.value.find(a => a.id === assetId) || {
        id: assetId,
        asset_type: shot.selected_image_asset_id ? 'image' : (shot.selected_video_asset_id ? 'video' : 'audio'),
        file_name: 'Asset ' + assetId,
        download_path: `/api/assets/${assetId}/download`
      };
    };

    const runQuickGenerate = (shot) => {
      if (!shot.cue) {
        addToast('warning', 'Narrative Cue Empty', 'Please provide a shot text cue description to run generation.');
        return;
      }
      
      const scenario = shot.name.toLowerCase().includes('voice') || shot.name.toLowerCase().includes('audio') ? 'voice' : 'image';
      window.location.hash = `#${scenario}`;
      
      localStorage.setItem('aiwm_prefilled_cue', shot.cue);
      addToast('info', 'Redirecting...', `Entering ${scenario.toUpperCase()} Lab with pre-filled shot cues.`);
    };

    const openExportManifest = async () => {
      try {
        const manifest = await apiClient.request(`/api/projects/${activeProjectId.value}/export/manifest`);
        exportManifest.value = manifest;
        exportModalOpen.value = true;
      } catch (err) {
        addToast('error', 'Export Sanitizer failed', err.message);
      }
    };

    const closeExportModal = () => {
      exportModalOpen.value = false;
      exportManifest.value = null;
    };

    const triggerDownloadManifest = () => {
      const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(exportManifest.value, null, 2));
      const downloadAnchor = document.createElement('a');
      downloadAnchor.setAttribute("href", dataStr);
      downloadAnchor.setAttribute("download", `project_${activeProjectId.value}_manifest.json`);
      document.body.appendChild(downloadAnchor);
      downloadAnchor.click();
      downloadAnchor.remove();
      addToast('success', 'Manifest Downloaded', 'Local JSON manifest file saved.');
    };

    const formatDate = (isoStr) => {
      if (!isoStr) return '';
      return new Date(isoStr).toLocaleDateString();
    };

    onMounted(() => {
      loadProjects();
      loadVoiceProfiles();
    });

    return {
      t,
      projects,
      activeProjectId,
      scriptContent,
      shots,
      voiceProfiles,
      projectDefaultVoiceProfileId,
      generatingVoiceoverShotId,
      showCreateModal,
      projectForm,
      newShot,
      pickerShotId,
      libraryAssets,
      exportModalOpen,
      exportManifest,
      activeProject,
      createProject,
      deleteProject,
      openProjectWorkspace,
      closeProjectWorkspace,
      saveScriptVersion,
      createShot,
      deleteShot,
      moveShot,
      openAssetPicker,
      closeAssetPicker,
      linkAssetToShot,
      getLinkedAsset,
      runQuickGenerate,
      openExportManifest,
      closeExportModal,
      triggerDownloadManifest,
      formatDate,
      updateProjectDefaultVoice,
      updateShotVoiceOverride,
      saveShotVoiceoverText,
      getShotVoiceWarnings,
      isHighRiskVoiceProfile,
      generateShotVoiceover,
      getAssetDownloadPath
    };
  }
};
