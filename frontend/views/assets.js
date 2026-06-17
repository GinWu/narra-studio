import { ref, onMounted, inject, computed } from 'vue';
import AudioPlayer from '../components/player.js';

export default {
  name: 'AssetsView',
  components: {
    AudioPlayer
  },
  template: `
    <div class="assets-page">
      <!-- Controls Panel -->
      <div class="glass-card" style="margin-bottom: 24px; display: flex; justify-content: space-between; align-items: center; gap: 16px; flex-wrap: wrap; padding: 16px 24px;">
        <div style="display: flex; gap: 12px; align-items: center; flex-grow: 1;">
          <!-- Filter by Type -->
          <div style="width: 150px;">
            <select class="select-field" v-model="filterType" style="padding: 8px 12px; font-size: 0.85rem;">
              <option value="">{{ t('assets.filters.allTypes') }}</option>
              <option value="image">{{ t('assets.filters.image') }}</option>
              <option value="audio">{{ t('assets.filters.audio') }}</option>
              <option value="video">{{ t('assets.filters.video') }}</option>
            </select>
          </div>
          
          <!-- Search input -->
          <div style="flex-grow: 1; max-width: 300px;">
            <input type="text" class="input-field" v-model="searchQuery" :placeholder="t('assets.filters.search')" style="padding: 8px 12px; font-size: 0.85rem;">
          </div>

          <!-- Show Discarded Toggle -->
          <div style="display: flex; align-items: center; gap: 8px; font-size: 0.85rem; color: var(--text-secondary);">
            <input type="checkbox" id="show-discarded" v-model="showDiscarded">
            <label for="show-discarded" style="cursor: pointer;">{{ t('assets.filters.showDiscarded') }}</label>
          </div>
        </div>

        <div style="font-size: 0.85rem; color: var(--text-muted);">
          {{ t('assets.filters.stats', { count: filteredAssets.length }) }}
        </div>
      </div>

      <!-- Assets Gallery Grid -->
      <div v-if="filteredAssets.length === 0" class="glass-card text-center" style="padding: 80px 0;">
        <i class="fas fa-cubes" style="font-size: 3.5rem; color: var(--text-muted); margin-bottom: 16px;"></i>
        <p style="color: var(--text-secondary);">{{ t('assets.filters.empty') }}</p>
      </div>

      <div class="grid-cols-12" style="gap: 20px;">
        <div v-for="ast in filteredAssets" :key="ast.id" class="col-span-4 glass-card" 
             style="display: flex; flex-direction: column; justify-content: space-between; padding: 14px;"
             :style="{ opacity: ast.status === 'discarded' ? 0.6 : 1 }">
          
          <div>
            <!-- Media Preview Area -->
            <div style="aspect-ratio: 16/9; background-color: var(--bg-primary); border-radius: 6px; overflow: hidden; display: flex; align-items: center; justify-content: center; border: 1px solid var(--border-color); position: relative;">
              <!-- Image Preview -->
              <img v-if="ast.asset_type === 'image'" :src="ast.download_path" alt="Asset" 
                   style="width: 100%; height: 100%; object-fit: cover; cursor: pointer;"
                   @click="openLightbox(ast.download_path)">
              
              <!-- Video Preview -->
              <video v-else-if="ast.asset_type === 'video'" controls style="width: 100%; height: 100%; object-fit: contain;">
                <source :src="ast.download_path" type="video/mp4">
              </video>
              
              <!-- Audio Icon -->
              <div v-else style="display: flex; flex-direction: column; align-items: center; gap: 8px;">
                <i class="fas fa-file-audio text-success" style="font-size: 2.5rem;"></i>
                <span style="font-size: 0.75rem; color: var(--text-muted);">{{ t('voice.config.speechText') }}</span>
              </div>

              <!-- Discarded Overlay Badge -->
              <span v-if="ast.status === 'discarded'" class="badge badge-warning" style="position: absolute; top: 8px; left: 8px; font-size: 0.6rem;">
                {{ t('assets.card.discarded') }}
              </span>
            </div>

            <!-- Metadata Info -->
            <div style="margin-top: 12px;">
              <div style="display: flex; justify-content: space-between; align-items: start;">
                <h4 style="font-size: 0.9rem; font-weight: 600; text-overflow: ellipsis; overflow: hidden; white-space: nowrap; max-width: 180px;" :title="ast.file_name">
                  {{ ast.file_name }}
                </h4>
                <span class="badge" :class="getTypeBadgeClass(ast.asset_type)" style="font-size: 0.6rem;">
                  {{ t('assets.card.type') }}: {{ ast.asset_type }}
                </span>
              </div>
              
              <div style="font-size: 0.75rem; color: var(--text-secondary); display: flex; flex-direction: column; gap: 4px; margin-top: 6px;">
                <div>ID: <span style="font-family: monospace;">{{ ast.id }}</span></div>
                <div>{{ t('assets.card.size') }}: {{ formatBytes(ast.size_bytes) }} | {{ t('assets.card.mime') }}: {{ ast.mime_type }}</div>
                <div v-if="ast.width && ast.height">{{ t('assets.card.dimension') }}: {{ ast.width }}x{{ ast.height }} px</div>
              </div>
            </div>
          </div>

          <!-- Rating & Action Bar -->
          <div style="margin-top: 14px; border-top: 1px solid rgba(255,255,255,0.05); padding-top: 10px;">
            <!-- Audio player specific inline for audio assets -->
            <div v-if="ast.asset_type === 'audio'" style="margin-bottom: 12px;">
              <audio-player :src="ast.download_path" :assetId="ast.id" :initialRating="ast.rating || 0" @rated="onAssetRated" />
            </div>

            <!-- Standard stars rating inline for non-audio -->
            <div v-else style="display: flex; justify-content: space-between; align-items: center; font-size: 0.8rem; margin-bottom: 10px;">
              <span style="color: var(--text-secondary);">{{ t('assets.card.score') }}</span>
              <div class="rating-stars" style="cursor: pointer;">
                <i v-for="i in 5" :key="i" class="fas fa-star" 
                   :class="i <= (ast.rating || 0) ? 'rating-star-active' : ''" 
                   @click="rateAsset(ast.id, i)"></i>
              </div>
            </div>

            <div style="display: flex; justify-content: space-between; gap: 8px;">
              <a :href="ast.download_path" target="_blank" class="btn btn-secondary" style="padding: 6px; font-size: 0.75rem; flex: 1;" title="Download Asset file">
                <i class="fas fa-download"></i> {{ t('assets.card.actionDownload') }}
              </a>
              <button class="btn btn-secondary" style="padding: 6px; font-size: 0.75rem; flex: 1;" 
                      :style="{ color: ast.status === 'discarded' ? 'var(--text-muted)' : 'var(--warning)' }"
                      @click="toggleDiscard(ast)" :disabled="ast.status === 'discarded'">
                <i class="fas" :class="ast.status === 'discarded' ? 'fa-folder-open' : 'fa-trash-can-arrow-up'"></i>
                {{ ast.status === 'discarded' ? t('assets.card.discarded') : t('assets.card.actionDiscard') }}
              </button>
              <button class="btn btn-danger" style="padding: 6px; font-size: 0.75rem; min-width: 36px;" 
                      :title="t('assets.card.actionDelete')" @click="deleteAsset(ast.id)">
                <i class="fas fa-trash"></i>
              </button>
            </div>
          </div>

        </div>
      </div>

      <!-- Lightbox preview -->
      <div v-if="lightboxSrc" class="modal-overlay" @click="closeLightbox" style="background-color: rgba(0,0,0,0.95);">
        <img :src="lightboxSrc" style="max-width: 90vw; max-height: 90vh; border-radius: 8px; border: 1px solid var(--border-color);" @click.stop>
      </div>
    </div>
  `,
  setup() {
    const apiClient = inject('apiClient');
    const addToast = inject('addToast');
    const t = inject('t');
    const assets = ref([]);

    const filterType = ref('');
    const searchQuery = ref('');
    const showDiscarded = ref(false);
    const lightboxSrc = ref(null);

    const loadAssets = async () => {
      try {
        const data = await apiClient.request('/api/assets');
        assets.value = data;
      } catch (err) {
        addToast('error', 'Error loading assets', err.message);
      }
    };

    const filteredAssets = computed(() => {
      return assets.value.filter(ast => {
        // Filter out soft-deleted files (they should not return from backend but if they do)
        if (ast.status === 'deleted' || ast.deleted_at) return false;

        // Discard logic
        if (ast.status === 'discarded' && !showDiscarded.value) return false;

        const matchType = !filterType.value || ast.asset_type === filterType.value;
        const q = searchQuery.value.toLowerCase().trim();
        const matchQuery = !q || 
          ast.file_name.toLowerCase().includes(q) ||
          (ast.tags && ast.tags.some(t => t.toLowerCase().includes(q)));

        return matchType && matchQuery;
      });
    });

    const getTypeBadgeClass = (type) => {
      switch (type) {
        case 'image': return 'badge-cyan';
        case 'audio': return 'badge-success';
        case 'video': return 'badge-purple';
        default: return 'badge-cyan';
      }
    };

    const formatBytes = (bytes) => {
      if (!bytes) return '0 B';
      const k = 1024;
      const sizes = ['B', 'KB', 'MB', 'GB'];
      const i = Math.floor(Math.log(bytes) / Math.log(k));
      return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
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
        addToast('success', 'Rating Saved', `Asset rated: ${score}/5`);
        loadAssets();
      } catch (err) {
        addToast('error', 'Failed to save rating', err.message);
      }
    };

    const onAssetRated = (payload) => {
      if (payload && payload.assetId) {
        rateAsset(payload.assetId, payload.score);
      } else {
        loadAssets();
      }
    };

    const toggleDiscard = async (ast) => {
      if (ast.status === 'discarded') return;
      try {
        await apiClient.request(`/api/assets/${ast.id}/discard`, { method: 'POST' });
        addToast('success', 'Status Changed', 'Asset has been successfully discarded.');
        loadAssets();
      } catch (err) {
        addToast('error', 'Action failed', err.message);
      }
    };

    const deleteAsset = async (id) => {
      if (!confirm('Are you sure you want to soft delete this asset? It will be hidden and become undownloadable.')) return;
      try {
        await apiClient.request(`/api/assets/${id}/delete`, { method: 'POST' });
        addToast('success', 'Asset Deleted', 'Asset successfully soft-deleted.');
        loadAssets();
      } catch (err) {
        addToast('error', 'Deletion failed', err.message);
      }
    };

    const openLightbox = (src) => {
      lightboxSrc.value = src;
    };

    const closeLightbox = () => {
      lightboxSrc.value = null;
    };

    onMounted(() => {
      loadAssets();
    });

    return {
      t,
      filterType,
      searchQuery,
      showDiscarded,
      lightboxSrc,
      filteredAssets,
      getTypeBadgeClass,
      formatBytes,
      rateAsset,
      onAssetRated,
      toggleDiscard,
      deleteAsset,
      openLightbox,
      closeLightbox
    };
  }
};
