import { ref, onMounted, inject, computed } from 'vue';
import { normalizeCostSummary, sumEstimatedCosts } from '../utils/costs.js';

export default {
  name: 'DashboardView',
  template: `
    <div class="dashboard-page">
      <!-- Quick Stats Row -->
      <div class="grid-cols-12" style="margin-bottom: 32px;">
        <div class="col-span-3 glass-card text-center">
          <i class="fas fa-coins text-warning" style="font-size: 2rem; margin-bottom: 12px; display: inline-block;"></i>
          <h4 style="font-size: 0.85rem; text-transform: uppercase; color: var(--text-secondary);">{{ t('dashboard.stats.cost') }}</h4>
          <p style="font-family: var(--font-heading); font-size: 1.75rem; font-weight: 700; color: var(--accent-cyan); margin-top: 6px;">
            \${{ totalCost.toFixed(4) }} <span style="font-size: 0.8rem; font-weight: normal; color: var(--text-muted);">USD</span>
          </p>
        </div>
        
        <div class="col-span-3 glass-card text-center">
          <i class="fas fa-photo-film text-info" style="font-size: 2rem; margin-bottom: 12px; display: inline-block;"></i>
          <h4 style="font-size: 0.85rem; text-transform: uppercase; color: var(--text-secondary);">{{ t('dashboard.stats.assets') }}</h4>
          <p style="font-family: var(--font-heading); font-size: 1.75rem; font-weight: 700; color: var(--text-primary); margin-top: 6px;">
            {{ stats.assetsCount }}
          </p>
        </div>

        <div class="col-span-3 glass-card text-center">
          <i class="fas fa-flask text-success" style="font-size: 2rem; margin-bottom: 12px; display: inline-block;"></i>
          <h4 style="font-size: 0.85rem; text-transform: uppercase; color: var(--text-secondary);">{{ t('dashboard.stats.experiments') }}</h4>
          <p style="font-family: var(--font-heading); font-size: 1.75rem; font-weight: 700; color: var(--text-primary); margin-top: 6px;">
            {{ stats.experimentsCount }}
          </p>
        </div>

        <div class="col-span-3 glass-card text-center">
          <i class="fas fa-network-wired text-purple" style="font-size: 2rem; margin-bottom: 12px; display: inline-block;"></i>
          <h4 style="font-size: 0.85rem; text-transform: uppercase; color: var(--text-secondary);">{{ t('dashboard.stats.models') }}</h4>
          <p style="font-family: var(--font-heading); font-size: 1.75rem; font-weight: 700; color: var(--text-primary); margin-top: 6px;">
            {{ stats.modelsCount }}
          </p>
        </div>
      </div>

      <!-- Main Section -->
      <div class="grid-cols-12">
        <!-- Recent Invocations -->
        <div class="col-span-8 glass-card">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
            <h3 style="font-family: var(--font-heading); font-size: 1.25rem;">{{ t('dashboard.recent.title') }}</h3>
            <a href="#history" class="btn btn-secondary" style="padding: 6px 12px; font-size: 0.8rem;">{{ t('dashboard.recent.viewAll') }}</a>
          </div>
          
          <div v-if="recentExperiments.length === 0" style="text-align: center; padding: 40px 0; color: var(--text-secondary);">
            <i class="fas fa-flask" style="font-size: 2.5rem; color: var(--text-muted); margin-bottom: 12px;"></i>
            <p>{{ t('dashboard.recent.empty') }}</p>
          </div>
          
          <table v-else class="premium-table">
            <thead>
              <tr>
                <th>{{ t('dashboard.recent.tableId') }}</th>
                <th>{{ t('dashboard.recent.tableType') }}</th>
                <th>{{ t('dashboard.recent.tableModel') }}</th>
                <th>{{ t('dashboard.recent.tableStatus') }}</th>
                <th>{{ t('dashboard.recent.tableTime') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="exp in recentExperiments" :key="exp.id">
                <td style="font-family: monospace; font-size: 0.85rem;">{{ exp.id }}</td>
                <td>
                  <span class="badge" :class="getCapabilityBadgeClass(exp.capability_type)">
                    {{ exp.capability_type }}
                  </span>
                </td>
                <td>{{ getModelName(exp.model_id) }}</td>
                <td>
                  <span class="badge" :class="getStatusBadgeClass(exp.status)">
                    {{ exp.status }}
                  </span>
                </td>
                <td style="font-size: 0.8rem; color: var(--text-secondary);">
                  {{ formatDate(exp.created_at) }}
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Right Panels (Cost Breakdown & Quick Labs) -->
        <div class="col-span-4" style="display: flex; flex-direction: column; gap: 24px;">
          <!-- Cost Breakdown -->
          <div class="glass-card">
            <h3 style="font-family: var(--font-heading); font-size: 1.15rem; margin-bottom: 16px;">{{ t('dashboard.costBreakdown.title') }}</h3>
            <div style="display: flex; flex-direction: column; gap: 14px;">
              <div v-for="cost in costItems" :key="cost.capability_type" style="font-size: 0.85rem;">
                <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
                  <span style="font-weight: 500; text-transform: capitalize;">{{ cost.capability_type.replace('_', ' ') }}</span>
                  <span style="color: var(--accent-cyan); font-weight: 600;">\${{ cost.estimated_total_cost.toFixed(4) }} USD</span>
                </div>
                <div style="width: 100%; height: 6px; background-color: var(--bg-tertiary); border-radius: 3px; overflow: hidden;">
                  <div :style="{ 
                    width: getCostPercent(cost.estimated_total_cost) + '%',
                    backgroundColor: getCostColor(cost.capability_type)
                  }" style="height: 100%; transition: width 0.5s ease;"></div>
                </div>
              </div>
              <div v-if="costItems.length === 0" style="text-align: center; padding: 20px 0; color: var(--text-muted);">
                {{ t('dashboard.costBreakdown.empty') }}
              </div>
            </div>
          </div>

          <!-- Quick Lab Entry -->
          <div class="glass-card">
            <h3 style="font-family: var(--font-heading); font-size: 1.15rem; margin-bottom: 16px;">{{ t('dashboard.quickLauncher.title') }}</h3>
            <div style="display: flex; flex-direction: column; gap: 10px;">
              <a href="#voice" class="btn btn-secondary" style="justify-content: flex-start;">
                <i class="fas fa-microphone text-success"></i> {{ t('dashboard.quickLauncher.voice') }}
              </a>
              <a href="#image" class="btn btn-secondary" style="justify-content: flex-start;">
                <i class="fas fa-image text-info"></i> {{ t('dashboard.quickLauncher.image') }}
              </a>
              <a href="#video" class="btn btn-secondary" style="justify-content: flex-start;">
                <i class="fas fa-video text-warning"></i> {{ t('dashboard.quickLauncher.video') }}
              </a>
            </div>
          </div>
        </div>
      </div>
    </div>
  `,
  setup() {
    const apiClient = inject('apiClient');
    const t = inject('t');
    const stats = ref({
      assetsCount: 0,
      experimentsCount: 0,
      modelsCount: 0,
      providersCount: 0
    });
    const recentExperiments = ref([]);
    const costItems = ref([]);
    const modelsList = ref([]);

    const totalCost = computed(() => {
      return sumEstimatedCosts(costItems.value);
    });

    const loadDashboardData = async () => {
      try {
        // Load counts
        const providers = await apiClient.request('/api/providers');
        const models = await apiClient.request('/api/models');
        const experiments = await apiClient.request('/api/experiments');
        const assets = await apiClient.request('/api/assets');
        const costs = await apiClient.request('/api/costs/summary');

        modelsList.value = models;
        costItems.value = normalizeCostSummary(costs).items;
        recentExperiments.value = experiments.slice(0, 5); // top 5 recent

        stats.value = {
          providersCount: providers.filter(p => p.enabled).length,
          modelsCount: models.filter(m => m.enabled).length,
          experimentsCount: experiments.length,
          assetsCount: assets.filter(a => a.status !== 'discarded' && a.status !== 'deleted').length
        };
      } catch (err) {
        console.error('Failed to load dashboard data:', err);
      }
    };

    const getModelName = (modelId) => {
      const model = modelsList.value.find(m => m.id === modelId);
      return model ? model.display_name : modelId;
    };

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

    const getCostPercent = (cost) => {
      if (totalCost.value === 0) return 0;
      return (cost / totalCost.value) * 100;
    };

    const getCostColor = (cap) => {
      switch (cap) {
        case 'tts': return 'var(--success)';
        case 'image_generation': return 'var(--accent-cyan)';
        case 'video_generation': return 'var(--accent-purple)';
        default: return 'var(--accent-blue)';
      }
    };

    const formatDate = (isoStr) => {
      if (!isoStr) return '';
      const date = new Date(isoStr);
      return date.toLocaleDateString(undefined, { month: 'short', day: 'numeric' }) + ' ' + 
             date.toLocaleTimeString(undefined, { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false });
    };

    onMounted(() => {
      loadDashboardData();
    });

    return {
      t,
      stats,
      recentExperiments,
      costItems,
      totalCost,
      getModelName,
      getCapabilityBadgeClass,
      getStatusBadgeClass,
      getCostPercent,
      getCostColor,
      formatDate
    };
  }
};
