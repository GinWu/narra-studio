import { ref, onMounted, inject, computed, watch } from 'vue';
import AudioPlayer from '../components/player.js';

export default {
  name: 'VoiceView',
  components: {
    AudioPlayer
  },
  template: `
    <div class="voice-lab-page" style="padding: 20px; display: flex; flex-direction: column; gap: 20px; height: calc(100vh - var(--header-height)); overflow-y: auto;">
      <!-- Tab Navigation Header -->
      <div class="tabs-header-container" style="display: flex; gap: 8px; border-bottom: 1px solid var(--border-color); padding-bottom: 12px; margin-bottom: 8px; flex-shrink: 0;">
        <button v-for="(tabLabel, tabId) in tabs" :key="tabId" 
                class="btn" :class="activeTab === tabId ? 'btn-primary' : 'btn-secondary'" 
                style="padding: 8px 18px; font-size: 0.9rem; border-radius: 6px; cursor: pointer; transition: var(--transition-smooth);"
                @click="switchTab(tabId)">
          <i :class="getTabIcon(tabId)" style="margin-right: 6px;"></i>
          {{ tabLabel }}
        </button>
      </div>

      <!-- Main Tab Content viewport -->
      <div style="flex: 1; min-height: 0;">
        
        <!-- ==================== TAB 1: TTS SYNTHESIS ==================== -->
        <div v-if="activeTab === 'tts'" class="lab-two-column" style="display: grid; grid-template-columns: 1fr 1fr; gap: 24px; height: 100%;">
          <!-- TTS Config Panel -->
          <div class="lab-config-panel glass-card" style="padding: 20px; overflow-y: auto;">
            <h3 style="font-family: var(--font-heading); font-size: 1.25rem; margin-bottom: 20px;">{{ t('voice.config.title') }}</h3>
            
            <form @submit.prevent="generateSpeech" style="display: flex; flex-direction: column; gap: 16px;">
              <!-- Model Select -->
              <div>
                <label class="input-label">{{ t('voice.config.model') }}</label>
                <select class="select-field" v-model="selectedModelId" required @change="onModelChange">
                  <option value="" disabled>No enabled TTS models available</option>
                  <option v-for="m in models" :key="m.id" :value="m.id">
                    {{ m.display_name }} ({{ m.pricing_hint }})
                  </option>
                </select>
                <p v-if="models.length === 0" style="font-size: 0.75rem; color: var(--warning); margin-top: 4px;">
                  No enabled TTS models found. Configure models or switch to Mock Mode.
                </p>
              </div>

              <!-- Voice Profile Select -->
              <div>
                <label class="input-label">{{ t('projects.active.selectVoiceProfile') }}</label>
                <select class="select-field" v-model="selectedVoiceProfileId" @change="onVoiceProfileChange">
                  <option value="">-- {{ t('common.none') }} (Use Model Default Voice) --</option>
                  <option v-for="vp in voiceProfiles" :key="vp.id" :value="vp.id">
                    {{ vp.display_name }} ({{ vp.provider }}) - {{ vp.status }}
                  </option>
                </select>
                
                <!-- Compliance Warnings Area -->
                <div v-if="selectedVoiceProfile" style="margin-top: 10px; display: flex; flex-direction: column; gap: 8px;">
                  <!-- Provider Mismatch -->
                  <div v-if="providerMismatch" class="badge badge-danger" style="display: flex; align-items: center; gap: 6px; padding: 8px 12px; font-size: 0.8rem; border-radius: 4px; font-weight: 500; line-height: 1.3; white-space: normal; text-align: left;">
                    <i class="fas fa-triangle-exclamation"></i>
                    <span>{{ t('voice.profiles.warnings.providerMismatch') }}</span>
                  </div>
                  
                  <!-- Revoked -->
                  <div v-if="selectedVoiceProfile.status === 'revoked'" class="badge badge-danger" style="display: flex; align-items: center; gap: 6px; padding: 8px 12px; font-size: 0.8rem; border-radius: 4px; font-weight: 500; line-height: 1.3; white-space: normal; text-align: left;">
                    <i class="fas fa-ban"></i>
                    <span>{{ t('voice.profiles.warnings.revoked') }}</span>
                  </div>

                  <!-- Expired -->
                  <div v-if="selectedVoiceProfile.status === 'expired' || isExpired(selectedVoiceProfile.expires_at)" class="badge badge-warning" style="display: flex; align-items: center; gap: 6px; padding: 8px 12px; font-size: 0.8rem; border-radius: 4px; font-weight: 500; line-height: 1.3; color: var(--bg-primary); white-space: normal; text-align: left;">
                    <i class="fas fa-calendar-times"></i>
                    <span>{{ t('voice.profiles.warnings.expired') }}</span>
                  </div>

                  <!-- Testing -->
                  <div v-if="selectedVoiceProfile.status === 'testing'" class="badge badge-cyan" style="display: flex; align-items: center; gap: 6px; padding: 8px 12px; font-size: 0.8rem; border-radius: 4px; font-weight: 500; line-height: 1.3; color: var(--bg-primary); white-space: normal; text-align: left;">
                    <i class="fas fa-vial"></i>
                    <span>{{ t('voice.profiles.warnings.testing') }}</span>
                  </div>

                  <!-- Commercial Restricted -->
                  <div v-if="!selectedVoiceProfile.commercial_allowed" class="badge badge-warning" style="display: flex; align-items: center; gap: 6px; padding: 8px 12px; font-size: 0.8rem; border-radius: 4px; font-weight: 500; line-height: 1.3; color: var(--bg-primary); white-space: normal; text-align: left;">
                    <i class="fas fa-shield-halved"></i>
                    <span>{{ t('voice.profiles.warnings.commercialWarning') }}</span>
                  </div>

                  <!-- High Risk -->
                  <div v-if="selectedVoiceProfile.risk_level === 'high'" class="badge badge-warning" style="display: flex; align-items: center; gap: 6px; padding: 8px 12px; font-size: 0.8rem; border-radius: 4px; font-weight: 500; line-height: 1.3; color: var(--bg-primary); white-space: normal; text-align: left;">
                    <i class="fas fa-biohazard"></i>
                    <span>{{ t('voice.profiles.warnings.highRisk') }}</span>
                  </div>
                </div>
              </div>

              <!-- Prompt Template Options -->
              <div>
                <label class="input-label">{{ t('voice.config.template') }}</label>
                <select class="select-field" v-model="selectedPromptId" @change="onPromptTemplateChange">
                  <option value="">{{ t('voice.config.directTextMode') }}</option>
                  <option v-for="p in promptTemplates" :key="p.id" :value="p.id">
                    {{ p.name }} (v{{ p.version }})
                  </option>
                </select>
              </div>

              <!-- Dynamic Variables Input -->
              <div v-if="selectedPrompt && Object.keys(templateVariables).length > 0" 
                   style="background-color: var(--bg-tertiary); padding: 14px; border-radius: 8px; border: 1px solid var(--border-color); display: flex; flex-direction: column; gap: 12px;">
                <h4 style="font-size: 0.8rem; text-transform: uppercase; color: var(--text-secondary); margin-bottom: 4px;">{{ t('voice.config.variables') }}</h4>
                <div v-for="(val, varName) in templateVariables" :key="varName">
                  <label class="input-label" style="font-size: 0.8rem;">{{ getVariableLabel(varName) }}</label>
                  <input type="text" class="input-field" v-model="templateVariables[varName]" @input="assemblePrompt" required>
                </div>
              </div>

              <!-- Narrative text to synthesize -->
              <div>
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                  <label class="input-label" style="margin-bottom: 0;">{{ t('voice.config.speechText') }}</label>
                  <span style="font-size: 0.75rem; color: var(--text-muted);">
                    {{ t('voice.config.chars', { count: rawText.length }) }}
                  </span>
                </div>
                <textarea class="input-field" style="min-height: 120px; line-height: 1.4;" 
                          v-model="rawText" required placeholder="Type the narration script here..."
                          :disabled="!!selectedPromptId"></textarea>
              </div>

              <!-- Model specific dynamic parameters based on Schema -->
              <div v-if="uiSchema" style="background-color: var(--bg-tertiary); padding: 14px; border-radius: 8px; border: 1px solid var(--border-color); display: flex; flex-direction: column; gap: 14px;">
                <h4 style="font-size: 0.8rem; text-transform: uppercase; color: var(--text-secondary); margin-bottom: 4px;">{{ t('voice.config.settings') }}</h4>
                
                <div v-for="(schema, key) in uiSchema" :key="key">
                  <!-- Select UI -->
                  <div v-if="schema.type === 'select'">
                    <label class="input-label">{{ schema.label }}</label>
                    <select class="select-field" v-model="params[key]">
                      <option v-for="opt in schema.options" :key="opt" :value="opt">{{ opt }}</option>
                    </select>
                  </div>
                  
                  <!-- Slider UI -->
                  <div v-else-if="schema.type === 'slider'">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                      <label class="input-label" style="margin-bottom: 0;">{{ schema.label }}</label>
                      <span style="font-family: monospace; font-size: 0.8rem; color: var(--accent-cyan);">{{ params[key] }}</span>
                    </div>
                    <div class="slider-container">
                      <input type="range" class="slider-field" 
                             :min="schema.min" :max="schema.max" :step="schema.step" 
                             v-model.number="params[key]">
                    </div>
                  </div>
                </div>
              </div>

              <!-- Compliance & Commercial Settings -->
              <div v-if="selectedVoiceProfile" style="display: flex; flex-direction: column; gap: 10px; background-color: var(--bg-tertiary); padding: 14px; border-radius: 8px; border: 1px solid var(--border-color);">
                <h4 style="font-size: 0.8rem; text-transform: uppercase; color: var(--text-secondary); margin-bottom: 4px;">{{ t('voice.profiles.title') }} - Compliance Check</h4>
                
                <div style="display: flex; align-items: center; gap: 8px;">
                  <input type="checkbox" id="chk-commercial" v-model="commercialUse">
                  <label for="chk-commercial" class="input-label" style="margin-bottom: 0; cursor: pointer; font-size: 0.85rem;">
                    Generate for Commercial Purposes (商业项目用途)
                  </label>
                </div>

                <div v-if="selectedVoiceProfile.risk_level === 'high' || !selectedVoiceProfile.commercial_allowed" style="display: flex; align-items: center; gap: 8px; margin-top: 4px;">
                  <input type="checkbox" id="chk-confirm" v-model="explicitConfirm">
                  <label for="chk-confirm" class="input-label" style="margin-bottom: 0; cursor: pointer; font-size: 0.85rem; color: var(--warning);">
                    I explicitly confirm usage rights and accept AI safety compliance requirements.
                  </label>
                </div>
              </div>

              <button type="submit" class="btn btn-primary" style="margin-top: 8px; font-size: 1rem; padding: 12px 20px;" :disabled="generating || !selectedModelId || ttsButtonBlocked">
                <i class="fas" :class="generating ? 'fa-spinner animate-spin' : 'fa-microphone'"></i>
                {{ generating ? t('voice.config.buttonGenerating') : t('voice.config.buttonSpeech') }}
              </button>
            </form>
          </div>

          <!-- TTS Audio Results Timeline -->
          <div class="lab-results-panel glass-card" style="padding: 20px; overflow-y: auto;">
            <h3 style="font-family: var(--font-heading); font-size: 1.25rem; margin-bottom: 20px;">{{ t('voice.history.title') }}</h3>
            
            <div style="flex: 1; display: flex; flex-direction: column; gap: 16px; padding-right: 4px;">
              <div v-if="voiceHistory.length === 0" style="text-align: center; padding: 60px 0; color: var(--text-secondary);">
                <i class="fas fa-music" style="font-size: 3rem; color: var(--text-muted); margin-bottom: 16px;"></i>
                <p>{{ t('voice.history.empty') }}</p>
              </div>
              
              <div v-for="item in voiceHistory" :key="item.exp.id" class="glass-card" style="padding: 16px; position: relative;">
                <!-- Header -->
                <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 12px;">
                  <div>
                    <h4 style="font-size: 0.95rem; font-weight: 600;">{{ item.exp.title || 'TTS Synthesis Experiment' }}</h4>
                    <span style="font-size: 0.75rem; color: var(--text-secondary); display: block; margin-top: 2px;">
                      {{ t('voice.history.labelModel') }}: {{ getModelDisplayName(item.exp.model_id) }} | {{ t('voice.history.labelLatency') }}: {{ (item.exp.latency_ms / 1000).toFixed(2) }}s
                    </span>
                    <span v-if="item.exp.metadata_json?.voice_profile_id" style="font-size: 0.7rem; color: var(--accent-cyan); font-family: monospace;">
                      Profile: {{ item.exp.metadata_json.voice_profile_id }}
                    </span>
                  </div>
                  <div style="display: flex; gap: 6px; align-items: center;">
                    <!-- Best Flag -->
                    <span v-if="item.exp.is_best" class="badge badge-success" style="font-size: 0.65rem;">
                      <i class="fas fa-award"></i> {{ t('voice.history.badgeBest') }}
                    </span>
                    <!-- Failed Case Flag -->
                    <span v-if="item.exp.is_failed_case" class="badge badge-danger" style="font-size: 0.65rem;" :title="'Failed reason: ' + item.exp.failed_reason">
                      <i class="fas fa-triangle-exclamation"></i> {{ t('voice.history.badgeFailed') }}
                    </span>
                  </div>
                </div>

                <!-- Narration snippet -->
                <blockquote style="font-size: 0.85rem; color: var(--text-secondary); border-left: 2px solid var(--border-color); padding-left: 10px; margin-bottom: 12px; font-style: italic;">
                  "{{ item.exp.input_text || (item.exp.input_json ? item.exp.input_json.text : '') }}"
                </blockquote>

                <!-- Audio Player component -->
                <div v-if="item.asset" style="margin-bottom: 12px;">
                  <audio-player :src="item.asset.download_path" :assetId="item.asset.id" 
                                :initialRating="item.asset.rating || 0" @rated="onAssetRated" />
                </div>
                
                <!-- Bottom Actions -->
                <div style="display: flex; justify-content: flex-end; gap: 8px; border-top: 1px solid rgba(255,255,255,0.04); padding-top: 10px; margin-top: 8px;">
                  <button class="btn btn-secondary" style="padding: 4px 10px; font-size: 0.75rem;" @click="rerunExperiment(item.exp)">
                    <i class="fas fa-rotate-left"></i> {{ t('voice.history.actionRerun') }}
                  </button>
                  <button v-if="!item.exp.is_best" class="btn btn-secondary" style="padding: 4px 10px; font-size: 0.75rem; color: var(--success);" @click="markAsBest(item.exp.id)">
                    <i class="fas fa-award"></i> {{ t('voice.history.actionMarkBest') }}
                  </button>
                  <button v-if="!item.exp.is_failed_case" class="btn btn-secondary" style="padding: 4px 10px; font-size: 0.75rem; color: var(--error);" @click="openFailModal(item.exp.id)">
                    <i class="fas fa-bug"></i> {{ t('voice.history.actionMarkFailure') }}
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- ==================== TAB 2: STT TRANSCRIPTION ==================== -->
        <div v-if="activeTab === 'stt'" class="lab-two-column" style="display: grid; grid-template-columns: 1fr 1fr; gap: 24px; height: 100%;">
          <!-- STT Config Panel -->
          <div class="lab-config-panel glass-card" style="padding: 20px; overflow-y: auto;">
            <h3 style="font-family: var(--font-heading); font-size: 1.25rem; margin-bottom: 20px;">{{ t('voice.stt.title') }}</h3>
            
            <form @submit.prevent="runTranscription" style="display: flex; flex-direction: column; gap: 16px;">
              <!-- Audio Source Selector -->
              <div>
                <label class="input-label">{{ t('voice.stt.audioSource') }}</label>
                <div style="display: flex; gap: 10px; margin-bottom: 12px;">
                  <button type="button" class="btn" style="flex: 1;"
                          :class="sttSourceType === 'upload' ? 'btn-primary' : 'btn-secondary'"
                          @click="sttSourceType = 'upload'">
                    <i class="fas fa-upload" style="margin-right: 6px;"></i>{{ t('voice.stt.uploadFile') }}
                  </button>
                  <button type="button" class="btn" style="flex: 1;"
                          :class="sttSourceType === 'library' ? 'btn-primary' : 'btn-secondary'"
                          @click="sttSourceType = 'library'">
                    <i class="fas fa-folder-open" style="margin-right: 6px;"></i>{{ t('voice.stt.selectAsset') }}
                  </button>
                </div>

                <!-- Source 1: File Upload -->
                <div v-if="sttSourceType === 'upload'">
                  <input type="file" class="input-field" accept="audio/*" @change="onSttFileChange" required>
                </div>

                <!-- Source 2: Select Asset from Library -->
                <div v-if="sttSourceType === 'library'">
                  <select class="select-field" v-model="sttAssetId" required>
                    <option value="" disabled>-- Select Audio Asset --</option>
                    <option v-for="asset in availableAudioAssets" :key="asset.id" :value="asset.id">
                      {{ asset.file_name }} ({{ (asset.size_bytes / 1024 / 1024).toFixed(2) }} MB)
                    </option>
                  </select>
                </div>
              </div>

              <!-- Model select -->
              <div>
                <label class="input-label">{{ t('voice.stt.model') }}</label>
                <select class="select-field" v-model="sttModelId" required>
                  <option value="" disabled>-- Select STT Model --</option>
                  <option v-for="m in sttModels" :key="m.id" :value="m.id">
                    {{ m.display_name }} ({{ m.pricing_hint }})
                  </option>
                </select>
              </div>

              <!-- Language & format -->
              <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px;">
                <div>
                  <label class="input-label">{{ t('voice.stt.language') }}</label>
                  <select class="select-field" v-model="sttLanguage">
                    <option value="">Auto Detect</option>
                    <option value="zh">Chinese (中文)</option>
                    <option value="en">English (EN)</option>
                  </select>
                </div>
                <div>
                  <label class="input-label">{{ t('voice.stt.format') }}</label>
                  <select class="select-field" v-model="sttFormat">
                    <option value="text">Plain Text</option>
                    <option value="json">Detailed JSON</option>
                    <option value="srt">Subtitles SRT</option>
                    <option value="vtt">Subtitles VTT</option>
                  </select>
                </div>
              </div>

              <button type="submit" class="btn btn-primary" style="margin-top: 8px; font-size: 1rem; padding: 12px 20px;" :disabled="transcribing || !sttModelId">
                <i class="fas" :class="transcribing ? 'fa-spinner animate-spin' : 'fa-list-check'"></i>
                {{ transcribing ? t('voice.stt.buttonTranscribing') : t('voice.stt.buttonTranscribe') }}
              </button>
            </form>
          </div>

          <!-- STT Transcript Results View -->
          <div class="lab-results-panel glass-card" style="padding: 20px; display: flex; flex-direction: column; gap: 16px; overflow-y: auto;">
            <h3 style="font-family: var(--font-heading); font-size: 1.25rem;">{{ t('voice.stt.transcriptTitle') }}</h3>

            <div v-if="!sttTranscript" style="flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: center; color: var(--text-muted); padding: 40px; text-align: center;">
              <i class="fas fa-file-audio" style="font-size: 3rem; margin-bottom: 16px; color: rgba(255,255,255,0.06);"></i>
              <p>Configure transcription parameters and run轉写 to see results here.</p>
            </div>

            <div v-else style="flex: 1; display: flex; flex-direction: column; gap: 16px;">
              <!-- Transcript box -->
              <div style="flex: 1; min-height: 150px; background: rgba(0,0,0,0.2); border: 1px solid var(--border-color); border-radius: 6px; padding: 16px; font-family: monospace; font-size: 0.9rem; line-height: 1.5; white-space: pre-wrap; overflow-y: auto;">
                {{ sttTranscript }}
              </div>
              
              <!-- Quick actions -->
              <div style="display: flex; gap: 12px; justify-content: flex-end;">
                <button class="btn btn-secondary" style="padding: 8px 16px;" @click="copyTranscript">
                  <i class="fas fa-copy" style="margin-right: 6px;"></i>{{ t('voice.stt.copyBtn') }}
                </button>
                <button class="btn btn-primary" style="padding: 8px 16px;" @click="openConvertModal">
                  <i class="fas fa-file-import" style="margin-right: 6px;"></i>{{ t('voice.stt.convertToScript') }}
                </button>
              </div>

              <!-- History/Log backlink -->
              <div v-if="sttTranscriptAssetId" style="font-size: 0.75rem; color: var(--text-muted); display: flex; justify-content: space-between; border-top: 1px solid var(--border-color); padding-top: 10px;">
                <span>Asset ID: <code style="color: var(--accent-cyan);">{{ sttTranscriptAssetId }}</code></span>
                <a :href="'#history'" style="color: var(--accent-cyan); text-decoration: none;">View in history logs <i class="fas fa-chevron-right" style="font-size: 0.65rem;"></i></a>
              </div>
            </div>
          </div>
        </div>

        <!-- ==================== TAB 3: VOICE CLONE ==================== -->
        <div v-if="activeTab === 'voiceClone'" class="lab-config-panel glass-card" style="padding: 20px; max-width: 700px; margin: 0 auto; overflow-y: auto; height: 100%;">
          <h3 style="font-family: var(--font-heading); font-size: 1.25rem; margin-bottom: 20px;">{{ t('voice.clone.title') }}</h3>
          
          <form @submit.prevent="runVoiceClone" style="display: flex; flex-direction: column; gap: 18px;">
            <!-- Disclaimer -->
            <div class="badge badge-warning" style="display: flex; align-items: start; gap: 8px; padding: 12px 16px; font-size: 0.85rem; border-radius: 6px; color: var(--bg-primary); white-space: normal; text-align: left; line-height: 1.4;">
              <i class="fas fa-circle-info" style="font-size: 1.1rem; margin-top: 2px;"></i>
              <span>{{ t('voice.clone.legalDisclaimer') }}</span>
            </div>

            <!-- Model Selection -->
            <div>
              <label class="input-label">{{ t('voice.clone.title') }} Model *</label>
              <select class="select-field" v-model="cloneModelId" required>
                <option value="" disabled>-- Select Voice Clone Model --</option>
                <option v-for="m in cloneModels" :key="m.id" :value="m.id">
                  {{ m.display_name }} ({{ m.pricing_hint }})
                </option>
              </select>
            </div>

            <!-- Sample Upload -->
            <div>
              <label class="input-label">{{ t('voice.clone.sampleSource') }}</label>
              <div style="display: flex; gap: 10px; margin-bottom: 12px;">
                <button type="button" class="btn" style="flex: 1;"
                        :class="cloneSourceType === 'upload' ? 'btn-primary' : 'btn-secondary'"
                        @click="cloneSourceType = 'upload'">
                  <i class="fas fa-upload" style="margin-right: 6px;"></i>{{ t('voice.clone.uploadSample') }}
                </button>
                <button type="button" class="btn" style="flex: 1;"
                        :class="cloneSourceType === 'library' ? 'btn-primary' : 'btn-secondary'"
                        @click="cloneSourceType = 'library'">
                  <i class="fas fa-folder-open" style="margin-right: 6px;"></i>{{ t('voice.clone.selectAsset') }}
                </button>
              </div>

              <div v-if="cloneSourceType === 'upload'">
                <input type="file" class="input-field" accept="audio/*" @change="onCloneFileChange" required>
              </div>

              <div v-if="cloneSourceType === 'library'">
                <select class="select-field" v-model="cloneAssetId" required>
                  <option value="" disabled>-- Select Audio Asset --</option>
                  <option v-for="asset in availableAudioAssets" :key="asset.id" :value="asset.id">
                    {{ asset.file_name }} ({{ (asset.size_bytes / 1024).toFixed(1) }} KB)
                  </option>
                </select>
              </div>
            </div>

            <!-- Voice profiling metadata -->
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px;">
              <div>
                <label class="input-label">{{ t('voice.clone.voiceName') }}</label>
                <input type="text" class="input-field" v-model="cloneVoiceName" required placeholder="e.g. My Narrator Voice">
              </div>
              <div>
                <label class="input-label">{{ t('voice.clone.displayName') }}</label>
                <input type="text" class="input-field" v-model="cloneDisplayName" placeholder="e.g. Studio Narrator (alloy)">
              </div>
            </div>

            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px;">
              <div>
                <label class="input-label">{{ t('voice.clone.sourceType') }}</label>
                <select class="select-field" v-model="cloneSourceTypeSelection">
                  <option value="self_voice">Self Voice (本人的声音)</option>
                  <option value="authorized_voice">Authorized Voice (受托授权声音)</option>
                  <option value="designed_voice">Designed Voice (自主设计音色)</option>
                  <option value="platform_builtin">Platform Built-in (平台内置)</option>
                  <option value="unknown">Unknown (未知来源)</option>
                </select>
              </div>
              <div>
                <label class="input-label">{{ t('voice.clone.consentStatus') }}</label>
                <select class="select-field" v-model="cloneConsentStatus">
                  <option value="self_owned">Self Owned (本人拥有)</option>
                  <option value="authorized">Authorized (已签署授权书)</option>
                  <option value="unknown">Unknown / Not Required (无明确授权记录)</option>
                </select>
              </div>
            </div>

            <!-- Commercial scope parameters -->
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px;">
              <div>
                <label class="input-label">{{ t('voice.clone.usageScope') }}</label>
                <select class="select-field" v-model="cloneUsageScope">
                  <option value="personal">Personal / Testing</option>
                  <option value="commercial">Commercial / Public release</option>
                </select>
              </div>
              <div>
                <label class="input-label">{{ t('voice.clone.riskLevel') }}</label>
                <select class="select-field" v-model="cloneRiskLevel">
                  <option value="low">Low Risk</option>
                  <option value="medium">Medium Risk</option>
                  <option value="high">High Risk (Requires explicit confirm)</option>
                </select>
              </div>
            </div>

            <!-- Platform limits & Disclosure checks -->
            <div>
              <label class="input-label">{{ t('voice.clone.platforms') }}</label>
              <input type="text" class="input-field" v-model="cloneAllowedPlatforms" placeholder="e.g. YouTube, TikTok, bilibili">
            </div>

            <div style="display: flex; gap: 20px; background: rgba(0,0,0,0.1); padding: 12px; border-radius: 6px;">
              <div style="display: flex; align-items: center; gap: 8px;">
                <input type="checkbox" id="chk-clone-commercial" v-model="cloneCommercialAllowed">
                <label for="chk-clone-commercial" class="input-label" style="margin-bottom: 0; cursor: pointer; font-size: 0.85rem;">
                  {{ t('voice.clone.commercialAllowed') }}
                </label>
              </div>
              <div style="display: flex; align-items: center; gap: 8px;">
                <input type="checkbox" id="chk-clone-disclosure" v-model="cloneAiDisclosureRequired">
                <label for="chk-clone-disclosure" class="input-label" style="margin-bottom: 0; cursor: pointer; font-size: 0.85rem;">
                  {{ t('voice.clone.disclosure') }}
                </label>
              </div>
            </div>

            <button type="submit" class="btn btn-primary" style="margin-top: 8px; font-size: 1rem; padding: 12px 20px;" :disabled="cloning || !cloneModelId">
              <i class="fas" :class="cloning ? 'fa-spinner animate-spin' : 'fa-wand-magic-sparkles'"></i>
              {{ cloning ? t('voice.clone.buttonCloning') : t('voice.clone.buttonClone') }}
            </button>
          </form>
        </div>

        <!-- ==================== TAB 4: VOICE PROFILES ==================== -->
        <div v-if="activeTab === 'voiceProfiles'" class="glass-card" style="padding: 20px; height: 100%; overflow-y: auto; display: flex; flex-direction: column;">
          <h3 style="font-family: var(--font-heading); font-size: 1.25rem; margin-bottom: 20px;">{{ t('voice.profiles.title') }}</h3>

          <div style="flex: 1; display: flex; flex-direction: column; gap: 16px;">
            <div v-if="loadingProfiles" style="text-align: center; padding: 60px 0; color: var(--text-secondary);">
              <i class="fas fa-spinner animate-spin" style="font-size: 2rem; margin-bottom: 12px;"></i>
              <p>{{ t('common.loading') }}</p>
            </div>
            
            <div v-else-if="voiceProfiles.length === 0" style="text-align: center; padding: 60px 0; color: var(--text-secondary);">
              <i class="fas fa-address-book" style="font-size: 3rem; color: var(--text-muted); margin-bottom: 16px;"></i>
              <p>{{ t('voice.profiles.empty') }}</p>
            </div>

            <!-- Profiles Grid -->
            <div v-else style="display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 16px;">
              <div v-for="vp in voiceProfiles" :key="vp.id" class="glass-card" 
                   style="padding: 16px; border: 1px solid var(--border-color); display: flex; flex-direction: column; gap: 12px; position: relative;"
                   :style="{ borderLeft: getProfileLeftBorder(vp) }">
                
                <!-- Profile Header -->
                <div style="display: flex; justify-content: space-between; align-items: start;">
                  <div>
                    <h4 style="font-size: 1rem; font-weight: 600;">{{ vp.display_name }}</h4>
                    <span style="font-size: 0.75rem; color: var(--text-muted); font-family: monospace;">ID: {{ vp.id }}</span>
                  </div>
                  <span class="badge" :class="getProfileStatusBadgeClass(vp.status)">
                    {{ vp.status }}
                  </span>
                </div>

                <!-- Profile Attributes Details -->
                <div style="font-size: 0.8rem; color: var(--text-secondary); display: grid; grid-template-columns: 1fr 1fr; gap: 8px; background: rgba(0,0,0,0.15); padding: 10px; border-radius: 6px;">
                  <div><strong>{{ t('voice.profiles.provider') }}:</strong> {{ vp.provider }}</div>
                  <div><strong>{{ t('voice.profiles.consent') }}:</strong> {{ vp.consent_status }}</div>
                  <div><strong>Commercial:</strong> <i class="fas" :class="vp.commercial_allowed ? 'fa-circle-check text-success' : 'fa-circle-xmark text-danger'"></i></div>
                  <div><strong>Risk Level:</strong> {{ vp.risk_level }}</div>
                  <div style="grid-span: 2; word-break: break-all;"><strong>Voice ID:</strong> {{ vp.voice_id ? vp.voice_id.substring(0,6) + '...' : 'None' }}</div>
                </div>

                <!-- Preview sample audio player if exists -->
                <div v-if="vp.sample_asset_id" style="margin-top: 4px;">
                  <audio-player :src="'/api/assets/' + vp.sample_asset_id + '/download'" :assetId="vp.sample_asset_id" />
                </div>

                <!-- Action Toolbar -->
                <div style="display: flex; gap: 8px; justify-content: flex-end; margin-top: 8px; border-top: 1px solid rgba(255,255,255,0.05); padding-top: 12px;">
                  <button class="btn btn-secondary" style="padding: 4px 8px; font-size: 0.75rem; color: var(--accent-cyan);" 
                          v-if="vp.status === 'active' || vp.status === 'testing'" @click="useProfileInTts(vp)">
                    <i class="fas fa-play"></i> {{ t('voice.profiles.actions.useInTts') }}
                  </button>
                  <button class="btn btn-secondary" style="padding: 4px 8px; font-size: 0.75rem; color: var(--warning);" 
                          v-if="vp.status === 'active' || vp.status === 'testing'" @click="disableProfile(vp.id)">
                    {{ t('voice.profiles.actions.disable') }}
                  </button>
                  <button class="btn btn-secondary" style="padding: 4px 8px; font-size: 0.75rem; color: var(--error);" 
                          v-if="vp.status !== 'revoked'" @click="revokeProfile(vp.id)">
                    {{ t('voice.profiles.actions.revoke') }}
                  </button>
                  <button class="btn btn-secondary" style="padding: 4px 8px; font-size: 0.75rem; color: var(--error);" 
                          v-if="vp.status !== 'expired'" @click="expireProfile(vp.id)">
                    {{ t('voice.profiles.actions.expire') }}
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>

      </div>

      <!-- Convert STT transcript to ScriptVersion Modal -->
      <div v-if="showConvertModal" class="modal-overlay">
        <div class="modal-content glass-card" style="max-width: 450px;">
          <div class="modal-header">
            <h3>{{ t('voice.stt.convertToScript') }}</h3>
            <button class="toast-close" @click="showConvertModal = false"><i class="fas fa-times"></i></button>
          </div>
          <form @submit.prevent="convertTranscriptToScript" style="display: flex; flex-direction: column; gap: 14px;">
            <div>
              <label class="input-label">{{ t('voice.stt.selectProject') }} *</label>
              <select class="select-field" v-model="convertProjectId" required>
                <option value="" disabled>-- Select Target Project --</option>
                <option v-for="proj in projects" :key="proj.id" :value="proj.id">
                  {{ proj.name }}
                </option>
              </select>
            </div>
            <div>
              <label class="input-label">{{ t('voice.stt.scriptTitle') }} *</label>
              <input type="text" class="input-field" v-model="convertScriptTitle" required placeholder="e.g. STT Speech Script version">
            </div>

            <div style="display: flex; justify-content: flex-end; gap: 10px; margin-top: 10px;">
              <button type="button" class="btn btn-secondary" @click="showConvertModal = false">{{ t('common.cancel') }}</button>
              <button type="submit" class="btn btn-primary" :disabled="convertingScript">
                <i class="fas" :class="convertingScript ? 'fa-spinner animate-spin' : 'fa-file-import'"></i>
                {{ convertingScript ? t('common.loading') : t('common.confirm') }}
              </button>
            </div>
          </form>
        </div>
      </div>

      <!-- Mark Failure Reason Modal -->
      <div v-if="failModalExpId" class="modal-overlay">
        <div class="modal-content glass-card" style="max-width: 450px;">
          <div class="modal-header">
            <h3>{{ t('voice.failModal.title') }}</h3>
            <button class="toast-close" @click="closeFailModal"><i class="fas fa-times"></i></button>
          </div>
          <div style="display: flex; flex-direction: column; gap: 14px;">
            <p style="font-size: 0.85rem; color: var(--text-secondary);">
              {{ t('voice.failModal.desc') }}
            </p>
            <div>
              <label class="input-label">{{ t('voice.failModal.labelCategory') }}</label>
              <select class="select-field" v-model="failReasonCategory">
                <option value="pronunciation_error">{{ t('voice.failModal.categories.pronunciation_error') }}</option>
                <option value="robotic_voice">{{ t('voice.failModal.categories.robotic_voice') }}</option>
                <option value="audio_artifact">{{ t('voice.failModal.categories.audio_artifact') }}</option>
                <option value="incorrect_speed">{{ t('voice.failModal.categories.incorrect_speed') }}</option>
                <option value="other">{{ t('voice.failModal.categories.other') }}</option>
              </select>
            </div>
            <div>
              <label class="input-label">{{ t('voice.failModal.labelDetail') }}</label>
              <textarea class="input-field" style="min-height: 80px;" v-model="failReasonDetail" placeholder="Describe the audio issues details..."></textarea>
            </div>
            <div style="display: flex; justify-content: flex-end; gap: 10px; margin-top: 10px;">
              <button class="btn btn-secondary" @click="closeFailModal">{{ t('common.cancel') }}</button>
              <button class="btn btn-primary" @click="submitFailureCase">{{ t('voice.failModal.buttonFlag') }}</button>
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

    // Navigation state
    const activeTab = ref('tts');

    // Translation Tab titles map
    const tabs = computed(() => ({
      tts: t('voice.tabs.tts'),
      stt: t('voice.tabs.stt'),
      voiceClone: t('voice.tabs.voiceClone'),
      voiceProfiles: t('voice.tabs.voiceProfiles')
    }));

    const getTabIcon = (tabId) => {
      switch (tabId) {
        case 'tts': return 'fa-microphone';
        case 'stt': return 'fa-list-check';
        case 'voiceClone': return 'fa-wand-magic-sparkles';
        case 'voiceProfiles': return 'fa-address-book';
        default: return 'fa-circle';
      }
    };

    // Shared / Core Lists
    const models = ref([]);
    const promptTemplates = ref([]);
    const voiceProfiles = ref([]);
    const availableAudioAssets = ref([]);
    const loadingProfiles = ref(false);

    // TTS configurations
    const selectedModelId = ref('');
    const selectedPromptId = ref('');
    const selectedVoiceProfileId = ref('');
    const templateVariables = ref({});
    const rawText = ref('');
    const params = ref({});
    const generating = ref(false);
    const voiceHistory = ref([]);
    const commercialUse = ref(false);
    const explicitConfirm = ref(false);

    // Failure modal helper
    const failModalExpId = ref(null);
    const failReasonCategory = ref('pronunciation_error');
    const failReasonDetail = ref('');

    // STT configuration
    const sttModels = ref([]);
    const sttModelId = ref('');
    const sttSourceType = ref('upload');
    const sttFile = ref(null);
    const sttAssetId = ref('');
    const sttLanguage = ref('');
    const sttFormat = ref('text');
    const sttTranscript = ref('');
    const sttTranscriptAssetId = ref('');
    const transcribing = ref(false);

    // Script Convert Modal
    const showConvertModal = ref(false);
    const convertProjectId = ref('');
    const convertScriptTitle = ref('');
    const projects = ref([]);
    const convertingScript = ref(false);

    // Voice Clone variables
    const cloneModels = ref([]);
    const cloneModelId = ref('');
    const cloneSourceType = ref('upload');
    const cloneFile = ref(null);
    const cloneAssetId = ref('');
    const cloneVoiceName = ref('');
    const cloneDisplayName = ref('');
    const cloneSourceTypeSelection = ref('self_voice');
    const cloneConsentStatus = ref('self_owned');
    const cloneCommercialAllowed = ref(false);
    const cloneUsageScope = ref('personal');
    const cloneAllowedPlatforms = ref('');
    const cloneAiDisclosureRequired = ref(true);
    const cloneRiskLevel = ref('medium');
    const cloning = ref(false);

    // Load base data
    const loadVoiceData = async () => {
      try {
        const modelsData = await apiClient.request('/api/models');
        
        // Filter by capability
        models.value = modelsData.filter(m => m.capability_type === 'tts' && m.enabled);
        sttModels.value = modelsData.filter(m => m.capability_type === 'stt' && m.enabled);
        cloneModels.value = modelsData.filter(m => m.capability_type === 'voice_clone' && m.enabled);

        if (models.value.length > 0) {
          selectedModelId.value = models.value.find(m => m.is_default)?.id || models.value[0].id;
          onModelChange();
        }
        if (sttModels.value.length > 0) {
          sttModelId.value = sttModels.value.find(m => m.is_default)?.id || sttModels.value[0].id;
        }
        if (cloneModels.value.length > 0) {
          cloneModelId.value = cloneModels.value.find(m => m.is_default)?.id || cloneModels.value[0].id;
        }

        // Load prompts
        const promptsData = await apiClient.request('/api/prompts');
        promptTemplates.value = promptsData
          .map(p => ({
            ...p,
            scenario: p.capability_type || p.scenario || '',
            template: p.content ?? p.template ?? '',
            variables_schema: p.variables_schema_json || p.variables_schema || {},
            default_values_json: p.default_values_json || {}
          }))
          .filter(p => p.scenario === 'tts_style' && p.is_latest);

        // Load histories, profiles, and library audio assets
        loadAudioHistory();
        loadVoiceProfiles();
        loadAudioAssets();
      } catch (err) {
        addToast('error', 'Error initializing Voice Lab', err.message);
      }
    };

    const loadAudioHistory = async () => {
      try {
        const experiments = await apiClient.request('/api/experiments');
        const assets = await apiClient.request('/api/assets');

        const voiceExps = experiments.filter(e => e.capability_type === 'tts');
        voiceHistory.value = voiceExps.map(exp => {
          const ref = exp.output_asset_refs_json?.[0];
          const asset = ref ? assets.find(a => a.id === ref.asset_id) : null;
          return { exp, asset };
        });
      } catch (err) {
        console.error('Failed to load history:', err);
      }
    };

    const loadVoiceProfiles = async () => {
      loadingProfiles.value = true;
      try {
        voiceProfiles.value = await apiClient.request('/api/voice-profiles');
      } catch (err) {
        addToast('error', 'Failed to load Voice Profiles', err.message);
      } finally {
        loadingProfiles.value = false;
      }
    };

    const loadAudioAssets = async () => {
      try {
        const data = await apiClient.request('/api/assets');
        availableAudioAssets.value = data.filter(a => a.asset_type === 'audio' && a.status !== 'discarded' && a.status !== 'deleted');
      } catch (err) {
        console.error('Failed to load audio library assets:', err);
      }
    };

    // Helper: File Base64 encoder
    const fileToBase64 = (file) => {
      return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.readAsDataURL(file);
        reader.onload = () => {
          const base64 = reader.result.split(',')[1];
          resolve(base64);
        };
        reader.onerror = error => reject(error);
      });
    };

    // Helper: Upload file to system asset repository
    const uploadAssetFile = async (file, assetType) => {
      const base64 = await fileToBase64(file);
      const payload = {
        asset_type: assetType,
        filename: file.name,
        content_base64: base64,
        mime_type: file.type
      };
      return await apiClient.request('/api/assets/upload', {
        method: 'POST',
        body: JSON.stringify(payload)
      });
    };

    const switchTab = (tabId) => {
      activeTab.value = tabId;
      if (tabId === 'voiceProfiles') {
        loadVoiceProfiles();
      } else if (tabId === 'stt' || tabId === 'voiceClone') {
        loadAudioAssets();
      }
    };

    // Profiles Warning checks
    const selectedModel = computed(() => {
      return models.value.find(m => m.id === selectedModelId.value);
    });

    const selectedVoiceProfile = computed(() => {
      return voiceProfiles.value.find(vp => vp.id === selectedVoiceProfileId.value);
    });

    const providerMismatch = computed(() => {
      if (!selectedModel.value || !selectedVoiceProfile.value) return false;
      return selectedModel.value.provider_id !== selectedVoiceProfile.value.provider_id;
    });

    const isExpired = (expiresAt) => {
      if (!expiresAt) return false;
      return new Date(expiresAt) < new Date();
    };

    const ttsButtonBlocked = computed(() => {
      if (!selectedVoiceProfile.value) return false;
      const vp = selectedVoiceProfile.value;
      if (providerMismatch.value) return true;
      if (vp.status === 'revoked') return true;
      if (vp.status === 'expired' || isExpired(vp.expires_at)) return true;
      if (!vp.commercial_allowed && commercialUse.value && !explicitConfirm.value) return true;
      if (vp.risk_level === 'high' && !explicitConfirm.value) return true;
      return false;
    });

    const onModelChange = () => {
      const model = selectedModel.value;
      if (model) {
        params.value = { ...model.default_params };
      }
    };

    const uiSchema = computed(() => {
      return selectedModel.value?.param_ui_schema || null;
    });

    const selectedPrompt = computed(() => {
      return promptTemplates.value.find(p => p.id === selectedPromptId.value);
    });

    const onPromptTemplateChange = () => {
      const pmt = selectedPrompt.value;
      if (pmt) {
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
        rawText.value = '';
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
      rawText.value = assembled;
    };

    const onVoiceProfileChange = () => {
      commercialUse.value = false;
      explicitConfirm.value = false;
    };

    // Submit Speech generation (TTS with Voice Profile support)
    const generateSpeech = async () => {
      const cleanText = rawText.value.trim();
      if (!cleanText) {
        addToast('error', 'Validation Error', 'Narration script is required.');
        return;
      }
      if (cleanText.length > 500) {
        addToast('error', 'Validation Error', 'TTS character limit is 500 characters.');
        return;
      }

      generating.value = true;
      try {
        const payload = {
          text: cleanText,
          prompt_template_id: selectedPromptId.value || null,
          variables: selectedPromptId.value ? templateVariables.value : null,
          model_id: selectedModelId.value,
          params_json: params.value,
          voice_config: selectedVoiceProfileId.value ? {
            voice_profile_id: selectedVoiceProfileId.value,
            source: 'voice_profile'
          } : null,
          commercial_use: commercialUse.value,
          explicit_confirm: explicitConfirm.value
        };

        const result = await apiClient.request('/api/labs/voice/tts', {
          method: 'POST',
          body: JSON.stringify(payload)
        });

        addToast('success', 'Synthesis Succeeded', 'TTS generated audio successfully!');
        loadCosts();
        loadAudioHistory();
      } catch (err) {
        if (err.error_type === 'VOICE_PROFILE_REVOKED') {
          addToast('error', 'Revoked Tone Error', 'This voice profile has been revoked by the owner and is locked.');
        } else if (err.error_type === 'VOICE_PROFILE_EXPIRED') {
          addToast('error', 'Expired License Error', 'VoiceProfile consent license expired. Action blocked.');
        } else if (err.error_type === 'VOICE_PROFILE_PROVIDER_MISMATCH') {
          addToast('error', 'Provider Conflict', 'Model provider is incompatible with selected voice profile.');
        } else if (err.error_type === 'CONTENT_BLOCKED') {
          addToast('error', 'Safety Violation', 'Safety block triggered by provider filters. Action blocked.');
        } else {
          addToast('error', `Synthesis Failed (${err.error_type || 'Error'})`, err.message || 'Request failed.');
        }
      } finally {
        generating.value = false;
      }
    };

    // STT Handlers
    const onSttFileChange = (e) => {
      const file = e.target.files[0];
      if (file) {
        sttFile.value = file;
      }
    };

    const runTranscription = async () => {
      transcribing.value = true;
      try {
        let audioId = sttAssetId.value;
        if (sttSourceType.value === 'upload') {
          if (!sttFile.value) {
            addToast('error', 'Validation Error', 'Audio file is required for upload transcription.');
            transcribing.value = false;
            return;
          }
          addToast('info', 'Uploading...', 'Uploading local audio file to media repository...');
          const uploadedAsset = await uploadAssetFile(sttFile.value, 'audio');
          audioId = uploadedAsset.id;
          addToast('success', 'Upload Success', `Created asset node: ${audioId}`);
        }

        if (!audioId) {
          addToast('error', 'Validation Error', 'No valid audio asset selected.');
          transcribing.value = false;
          return;
        }

        const payload = {
          audio_asset_id: audioId,
          model_id: sttModelId.value,
          language: sttLanguage.value || null,
          params_json: {
            response_format: sttFormat.value
          }
        };

        const response = await apiClient.request('/api/labs/audio/stt', {
          method: 'POST',
          body: JSON.stringify(payload)
        });

        if (response.status === 'success' || response.output_text) {
          sttTranscript.value = response.output_text || '';
          sttTranscriptAssetId.value = response.output_asset_refs_json?.[0]?.asset_id || '';
          addToast('success', 'Transcription Completed', 'STT speech to text completed successfully.');
          loadCosts();
        } else if (response.status === 'failed') {
          addToast('error', 'Transcription Failed', response.error_json?.message || 'Adapter returned error status.');
        } else {
          addToast('warning', 'Async Queueing', `CELERY Task started asynchronously. Check Task sidebar.`);
        }
      } catch (err) {
        addToast('error', `STT Failed (${err.error_type || 'Error'})`, err.message || 'Request failed.');
      } finally {
        transcribing.value = false;
      }
    };

    const copyTranscript = () => {
      if (!sttTranscript.value) return;
      navigator.clipboard.writeText(sttTranscript.value).then(() => {
        addToast('success', 'Copied', 'Transcript copied to clipboard.');
      }).catch(err => {
        addToast('error', 'Copy failed', err.message);
      });
    };

    const openConvertModal = async () => {
      try {
        projects.value = await apiClient.request('/api/projects');
        convertProjectId.value = projects.value[0]?.id || '';
        convertScriptTitle.value = `Transcript Script - ${new Date().toLocaleDateString()}`;
        showConvertModal.value = true;
      } catch (err) {
        addToast('error', 'Projects loading failed', err.message);
      }
    };

    const convertTranscriptToScript = async () => {
      if (!sttTranscriptAssetId.value) {
        addToast('error', 'Convert Error', 'Transcript asset ID is missing.');
        return;
      }
      convertingScript.value = true;
      try {
        const payload = {
          transcript_asset_id: sttTranscriptAssetId.value,
          title: convertScriptTitle.value
        };
        await apiClient.request(`/api/projects/${convertProjectId.value}/scripts/from-transcript`, {
          method: 'POST',
          body: JSON.stringify(payload)
        });

        addToast('success', 'Script Created', t('voice.stt.successConvert'));
        showConvertModal.value = false;
      } catch (err) {
        addToast('error', 'Conversion failed', err.message);
      } finally {
        convertingScript.value = false;
      }
    };

    // Voice Clone Handlers
    const onCloneFileChange = (e) => {
      const file = e.target.files[0];
      if (file) {
        cloneFile.value = file;
      }
    };

    const runVoiceClone = async () => {
      if (!cloneVoiceName.value.trim()) {
        addToast('error', 'Validation Error', 'Voice name is required.');
        return;
      }

      cloning.value = true;
      try {
        let audioId = cloneAssetId.value;
        if (cloneSourceType.value === 'upload') {
          if (!cloneFile.value) {
            addToast('error', 'Validation Error', 'Voice sample file is required.');
            cloning.value = false;
            return;
          }
          addToast('info', 'Uploading...', 'Uploading reference sound sample...');
          const uploadedAsset = await uploadAssetFile(cloneFile.value, 'audio');
          audioId = uploadedAsset.id;
          addToast('success', 'Upload Success', `Sample saved: ${audioId}`);
        }

        if (!audioId) {
          addToast('error', 'Validation Error', 'No valid audio reference asset.');
          cloning.value = false;
          return;
        }

        const payload = {
          reference_audio_asset_ids: [audioId],
          voice_name: cloneVoiceName.value.trim(),
          display_name: cloneDisplayName.value.trim() || null,
          model_id: cloneModelId.value,
          consent_status: cloneConsentStatus.value === 'unknown' ? 'unknown' : 'granted',
          consent_type: 'self_attested',
          source_person_note: cloneSourceTypeSelection.value,
          usage_scope: cloneUsageScope.value,
          commercial_allowed: cloneCommercialAllowed.value,
          allowed_platforms_json: cloneAllowedPlatforms.value ? cloneAllowedPlatforms.value.split(',').map(s => s.trim()) : [],
          ai_disclosure_required: cloneAiDisclosureRequired.value,
          risk_level: cloneRiskLevel.value
        };

        const response = await apiClient.request('/api/labs/audio/voice-clone', {
          method: 'POST',
          body: JSON.stringify(payload)
        });

        if (response.voice_profile_id) {
          addToast('success', 'Clone Succeeded', t('voice.clone.successClone', { id: response.voice_profile_id }));
          cloneVoiceName.value = '';
          cloneDisplayName.value = '';
          cloneFile.value = null;
          loadCosts();
          
          // Switch to list to see the profile
          switchTab('voiceProfiles');
        } else {
          addToast('error', 'Clone failed', 'Backend failed to create voice profile node.');
        }
      } catch (err) {
        addToast('error', `Voice Clone Failed (${err.error_type || 'Error'})`, err.message || 'Request failed.');
      } finally {
        cloning.value = false;
      }
    };

    // Profiles actions
    const getProfileLeftBorder = (vp) => {
      switch (vp.status) {
        case 'active': return '4px solid var(--success)';
        case 'testing': return '4px solid var(--accent-cyan)';
        case 'disabled': return '4px solid var(--text-muted)';
        case 'revoked':
        case 'expired': return '4px solid var(--error)';
        default: return '1px solid var(--border-color)';
      }
    };

    const getProfileStatusBadgeClass = (status) => {
      switch (status) {
        case 'active': return 'badge-success';
        case 'testing': return 'badge-cyan';
        case 'revoked':
        case 'expired': return 'badge-danger';
        default: return 'badge-warning';
      }
    };

    const useProfileInTts = (vp) => {
      selectedVoiceProfileId.value = vp.id;
      activeTab.value = 'tts';
      addToast('info', 'Voice Profile Loaded', `Selected "${vp.display_name}" as active TTS voice profile.`);
    };

    const disableProfile = async (id) => {
      try {
        await apiClient.request(`/api/voice-profiles/${id}/disable`, { method: 'POST' });
        addToast('warning', 'Profile Disabled', 'Voice profile status set to disabled.');
        loadVoiceProfiles();
      } catch (err) {
        addToast('error', 'Action failed', err.message);
      }
    };

    const revokeProfile = async (id) => {
      try {
        await apiClient.request(`/api/voice-profiles/${id}/mark-revoked`, { method: 'POST' });
        addToast('error', 'Consent Revoked', 'Voice profile consent marked as REVOKED. Locked usage.');
        loadVoiceProfiles();
      } catch (err) {
        addToast('error', 'Action failed', err.message);
      }
    };

    const expireProfile = async (id) => {
      try {
        await apiClient.request(`/api/voice-profiles/${id}/mark-expired`, { method: 'POST' });
        addToast('warning', 'Consent Expired', 'Voice profile marked as EXPIRED.');
        loadVoiceProfiles();
      } catch (err) {
        addToast('error', 'Action failed', err.message);
      }
    };

    // Asset evaluations
    const onAssetRated = async ({ assetId, score }) => {
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
        addToast('success', 'Rating Saved', `Asset quality score rated: ${score}/5`);
        loadAudioHistory();
      } catch (err) {
        addToast('error', 'Failed to save rating', err.message);
      }
    };

    const markAsBest = async (expId) => {
      try {
        await apiClient.request(`/api/experiments/${expId}/mark-best`, { method: 'POST' });
        addToast('success', 'Best Flag Set', 'This experiment was marked as the Best Output.');
        loadAudioHistory();
      } catch (err) {
        addToast('error', 'Request failed', err.message);
      }
    };

    const openFailModal = (expId) => {
      failModalExpId.value = expId;
      failReasonCategory.value = 'pronunciation_error';
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
        loadAudioHistory();
      } catch (err) {
        addToast('error', 'Request failed', err.message);
      }
    };

    const rerunExperiment = (exp) => {
      selectedModelId.value = exp.model_id;
      onModelChange();
      
      if (exp.input_json?.prompt_template_id) {
        selectedPromptId.value = exp.input_json.prompt_template_id;
        templateVariables.value = { ...exp.input_json.template_variables };
        rawText.value = exp.input_text;
      } else {
        selectedPromptId.value = '';
        templateVariables.value = {};
        rawText.value = exp.input_text || (exp.input_json ? exp.input_json.text : '');
      }

      if (exp.metadata_json?.voice_profile_id) {
        selectedVoiceProfileId.value = exp.metadata_json.voice_profile_id;
      } else {
        selectedVoiceProfileId.value = '';
      }
      
      params.value = { ...exp.params_json };
      addToast('info', 'Parameters Restored', 'Copied experiment parameters into configuration panel.');
    };

    const getModelDisplayName = (modelId) => {
      const model = models.value.find(m => m.id === modelId);
      return model ? model.display_name : modelId;
    };

    onMounted(() => {
      loadVoiceData();
    });

    return {
      t,
      activeTab,
      tabs,
      getTabIcon,
      switchTab,
      models,
      promptTemplates,
      voiceProfiles,
      availableAudioAssets,
      selectedModelId,
      selectedPromptId,
      selectedVoiceProfileId,
      templateVariables,
      rawText,
      params,
      generating,
      voiceHistory,
      commercialUse,
      explicitConfirm,
      failModalExpId,
      failReasonCategory,
      failReasonDetail,
      selectedModel,
      selectedVoiceProfile,
      providerMismatch,
      isExpired,
      ttsButtonBlocked,
      uiSchema,
      selectedPrompt,
      onModelChange,
      onPromptTemplateChange,
      getVariableLabel,
      assemblePrompt,
      onVoiceProfileChange,
      generateSpeech,
      onAssetRated,
      markAsBest,
      openFailModal,
      closeFailModal,
      submitFailureCase,
      rerunExperiment,
      getModelDisplayName,
      
      // STT View properties
      sttModels,
      sttModelId,
      sttSourceType,
      sttAssetId,
      sttLanguage,
      sttFormat,
      sttTranscript,
      sttTranscriptAssetId,
      transcribing,
      onSttFileChange,
      runTranscription,
      copyTranscript,
      openConvertModal,
      showConvertModal,
      convertProjectId,
      convertScriptTitle,
      projects,
      convertingScript,
      convertTranscriptToScript,

      // Voice Clone View properties
      cloneModels,
      cloneModelId,
      cloneSourceType,
      cloneAssetId,
      cloneVoiceName,
      cloneDisplayName,
      cloneSourceTypeSelection,
      cloneConsentStatus,
      cloneCommercialAllowed,
      cloneUsageScope,
      cloneAllowedPlatforms,
      cloneAiDisclosureRequired,
      cloneRiskLevel,
      cloning,
      onCloneFileChange,
      runVoiceClone,

      // Voice Profiles properties
      loadingProfiles,
      getProfileLeftBorder,
      getProfileStatusBadgeClass,
      useProfileInTts,
      disableProfile,
      revokeProfile,
      expireProfile
    };
  }
};
