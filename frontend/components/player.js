import { ref, onMounted, watch, inject } from 'vue';

export default {
  name: 'AudioPlayer',
  props: {
    src: { type: String, required: true },
    assetId: { type: String, required: true },
    initialRating: { type: Number, default: 0 }
  },
  emits: ['rated'],
  template: `
    <div class="audio-player-card">
      <div class="audio-controls">
        <button class="btn btn-secondary" style="padding: 8px 12px; border-radius: 50%; width: 40px; height: 40px;" @click="togglePlay">
          <i class="fas" :class="isPlaying ? 'fa-pause' : 'fa-play'"></i>
        </button>
        
        <div style="font-size: 0.75rem; font-family: monospace; color: var(--text-secondary); min-width: 35px;">
          {{ formatTime(currentTime) }}
        </div>

        <div class="audio-progress" ref="progressBar" @click="seek">
          <div class="audio-progress-bar" :style="{ width: progressPercent + '%' }"></div>
        </div>

        <div style="font-size: 0.75rem; font-family: monospace; color: var(--text-secondary); min-width: 35px;">
          {{ formatTime(duration) }}
        </div>

        <div style="display: flex; align-items: center; gap: 6px;">
          <i class="fas fa-volume-up" style="color: var(--text-muted); font-size: 0.8rem;"></i>
          <input type="range" min="0" max="1" step="0.1" v-model="volume" @input="updateVolume" 
                 style="width: 60px; height: 4px; accent-color: var(--accent-cyan);">
        </div>

        <a :href="downloadUrl" target="_blank" class="btn btn-secondary" style="padding: 8px 12px; font-size: 0.8rem;" title="Download File">
          <i class="fas fa-download"></i>
        </a>
      </div>

      <!-- Rating row -->
      <div style="display: flex; justify-content: space-between; align-items: center; border-top: 1px solid rgba(255,255,255,0.05); padding-top: 8px; font-size: 0.8rem;">
        <span style="color: var(--text-secondary);">{{ t('common.qualityRating') }}</span>
        <div class="rating-stars" style="cursor: pointer;">
          <i v-for="i in 5" :key="i" class="fas fa-star" 
             :class="i <= currentRating ? 'rating-star-active' : ''" 
             @click="rateAsset(i)"></i>
        </div>
      </div>

      <!-- Hidden Audio element -->
      <audio ref="audioElement" :src="resolvedSrc" @timeupdate="onTimeUpdate" @loadedmetadata="onLoadedMetadata" @ended="onEnded"></audio>
    </div>
  `,
  setup(props, { emit }) {
    const t = inject('t');
    const isPlaying = ref(false);
    const currentTime = ref(0);
    const duration = ref(0);
    const volume = ref(0.8);
    const currentRating = ref(props.initialRating);
    const audioElement = ref(null);
    const progressBar = ref(null);

    // Watch for initial rating changes
    watch(() => props.initialRating, (newVal) => {
      currentRating.value = newVal;
    });

    const resolvedSrc = computed(() => {
      // If it starts with /api or is fully qualified, return as is. Otherwise resolve relative.
      if (props.src.startsWith('http') || props.src.startsWith('/api')) {
        return props.src;
      }
      return `/api/assets/${props.assetId}/download`;
    });

    const downloadUrl = computed(() => {
      return resolvedSrc.value;
    });

    const togglePlay = () => {
      if (!audioElement.value) return;
      if (isPlaying.value) {
        audioElement.value.pause();
        isPlaying.value = false;
      } else {
        // Pause all other players in document first
        document.querySelectorAll('audio').forEach(el => {
          if (el !== audioElement.value) {
            el.pause();
          }
        });
        audioElement.value.play();
        isPlaying.value = true;
      }
    };

    const seek = (e) => {
      if (!audioElement.value || !progressBar.value || duration.value === 0) return;
      const rect = progressBar.value.getBoundingClientRect();
      const clickX = e.clientX - rect.left;
      const width = rect.width;
      const clickPercent = clickX / width;
      audioElement.value.currentTime = clickPercent * duration.value;
    };

    const updateVolume = () => {
      if (audioElement.value) {
        audioElement.value.volume = volume.value;
      }
    };

    const onTimeUpdate = () => {
      if (audioElement.value) {
        currentTime.value = audioElement.value.currentTime;
      }
    };

    const onLoadedMetadata = () => {
      if (audioElement.value) {
        duration.value = audioElement.value.duration;
      }
    };

    const onEnded = () => {
      isPlaying.value = false;
      currentTime.value = 0;
    };

    const formatTime = (secs) => {
      if (isNaN(secs)) return '00:00';
      const m = Math.floor(secs / 60).toString().padStart(2, '0');
      const s = Math.floor(secs % 60).toString().padStart(2, '0');
      return `${m}:${s}`;
    };

    const progressPercent = computed(() => {
      if (duration.value === 0) return 0;
      return (currentTime.value / duration.value) * 100;
    });

    const rateAsset = (score) => {
      currentRating.value = score;
      emit('rated', { assetId: props.assetId, score });
    };

    onMounted(() => {
      if (audioElement.value) {
        audioElement.value.volume = volume.value;
      }
    });

    return {
      t,
      isPlaying,
      currentTime,
      duration,
      volume,
      currentRating,
      audioElement,
      progressBar,
      resolvedSrc,
      downloadUrl,
      togglePlay,
      seek,
      updateVolume,
      onTimeUpdate,
      onLoadedMetadata,
      onEnded,
      formatTime,
      progressPercent,
      rateAsset
    };
  }
};
