import { createApp, ref, reactive, onMounted, computed, provide } from 'vue';
import { APIClient } from './api.js';
import { t, currentLocale, setLocale } from './i18n.js';
import { normalizeCostSummary, sumEstimatedCosts } from './utils/costs.js';

// Instantiate API Client
const apiClient = new APIClient();

// Create the app
const app = createApp({
  template: `
    <div id="app-layout">
      <!-- Sidebar Navigation -->
      <aside id="sidebar">
        <div id="sidebar-brand" style="flex-direction: column; align-items: flex-start; justify-content: center; gap: 4px;">
          <div style="display: flex; align-items: center; gap: 8px;">
            <i class="fas fa-cubes-gradient" style="font-size: 1.15rem; color: var(--accent-cyan);"></i>
            <h1 style="margin: 0; font-size: 1.2rem; font-weight: 700; line-height: 1.2;">Narra Studio</h1>
          </div>
          <span style="font-size: 0.62rem; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.05em; font-weight: 500; white-space: nowrap; line-height: 1;">
            {{ t('sidebar.subLabel') }}
          </span>
        </div>

        <nav id="sidebar-nav">
          <a v-for="link in navLinks" 
             :key="link.route" 
             :href="'#' + link.route"
             class="nav-item"
             :class="{ active: activeRoute === link.route }">
            <i :class="link.icon"></i>
            {{ t('sidebar.' + link.route) }}
          </a>
        </nav>
        
        <!-- Sidebar Settings Panel -->
        <div id="sidebar-settings">
          <div class="settings-group">
            <div class="settings-row">
              <span>{{ t('sidebar.mockMode') }}</span>
              <label class="toggle-switch">
                <input type="checkbox" v-model="mockMode" @change="toggleMockMode">
                <span class="slider-toggle"></span>
              </label>
            </div>
            <div style="margin-bottom: 8px;">
              <span class="input-label" style="margin-bottom: 4px; font-size: 0.75rem;">{{ t('sidebar.apiBaseUrl') }}</span>
              <input type="text" class="input-field" 
                     style="padding: 6px 10px; font-size: 0.8rem;" 
                     v-model="apiBaseUrl" 
                     @change="updateBaseUrl"
                     :disabled="mockMode">
            </div>
            <div>
              <span class="input-label" style="margin-bottom: 4px; font-size: 0.75rem;">{{ t('sidebar.language') }}</span>
              <select class="input-field" 
                      style="padding: 6px 10px; font-size: 0.8rem; cursor: pointer; background: var(--bg-secondary); color: var(--text-primary); border: 1px solid var(--border-color); border-radius: 4px;" 
                      v-model="currentLocale" 
                      @change="onLanguageChange">
                <option value="en">English</option>
                <option value="zh">中文</option>
              </select>
            </div>
          </div>
        </div>
      </aside>

      <!-- Main Workspace -->
      <div id="main-container">
        <!-- Top Header -->
        <header id="main-header">
          <div class="header-title">
            <h2>{{ activePageName }}</h2>
          </div>
          <div class="header-actions">
            <!-- Cost summary tray -->
            <div class="cost-tray" title="Estimated cost summary across Labs">
              <i class="fas fa-coins text-warning"></i>
              <span>Total Estimated Cost: <strong>\${{ formattedTotalCost }} USD</strong></span>
            </div>
            
            <!-- Tasks indicator -->
            <div class="cost-tray" style="cursor: pointer;" @click="toggleTaskDrawer">
              <i class="fas" :class="runningTasksCount > 0 ? 'fa-spinner animate-spin' : 'fa-tasks'"></i>
              <span>Tasks: <strong>{{ runningTasksCount }} / {{ Object.keys(activeTasks).length }}</strong></span>
            </div>
          </div>
        </header>

        <!-- Viewport -->
        <main id="main-content">
          <keep-alive>
            <component :is="activeRoute + '-view'" />
          </keep-alive>
        </main>
      </div>

      <!-- Toast Alerts Container -->
      <div id="alert-container">
        <div v-for="toast in toasts" :key="toast.id" class="toast" :class="'toast-' + toast.type">
          <i class="fas" :class="getToastIcon(toast.type)" style="margin-top: 3px;"></i>
          <div class="toast-content">
            <div class="toast-title">{{ toast.title }}</div>
            <div class="toast-message">{{ toast.message }}</div>
          </div>
          <button class="toast-close" @click="removeToast(toast.id)">
            <i class="fas fa-times"></i>
          </button>
        </div>
      </div>

      <!-- Task Drawer Widget -->
      <div v-if="taskDrawerOpen" id="task-drawer" class="glass-card" style="padding: 16px;">
        <div class="task-drawer-header">
          <h4 style="font-family: var(--font-heading); font-size: 0.95rem;">Asynchronous Tasks</h4>
          <button class="toast-close" @click="taskDrawerOpen = false"><i class="fas fa-times"></i></button>
        </div>
        <div class="task-drawer-content">
          <div v-if="Object.keys(activeTasks).length === 0" style="text-align: center; color: var(--text-muted); font-size: 0.8rem; padding: 16px 0;">
            No tasks in queue.
          </div>
          <div v-for="task in activeTasks" :key="task.id" class="task-mini-card">
            <div style="display: flex; justify-content: space-between; margin-bottom: 4px; font-weight: 600;">
              <span>{{ getTaskLabel(task.capability_type) }}</span>
              <span class="badge" :class="getTaskBadgeClass(task.status)">{{ task.status }}</span>
            </div>
            <div style="color: var(--text-secondary); font-size: 0.75rem;">
              Task ID: {{ task.id }}
            </div>
            <div v-if="task.progress !== undefined" style="margin-top: 4px;">
              <div style="display: flex; justify-content: space-between; font-size: 0.75rem; color: var(--text-muted);">
                <span>Progress</span>
                <span>{{ task.progress }}%</span>
              </div>
              <div class="task-progress-bar">
                <div class="task-progress-fill" :style="{ width: task.progress + '%' }"></div>
              </div>
            </div>
            <div style="margin-top: 8px; display: flex; justify-content: flex-end; gap: 8px;" v-if="['pending', 'queued', 'running', 'provider_pending', 'provider_running'].includes(task.status)">
              <button class="btn btn-secondary" style="padding: 3px 8px; font-size: 0.7rem;" @click="cancelTask(task.id)">Cancel</button>
            </div>
          </div>
        </div>
      </div>
    </div>
  `,
  setup() {
    const activeRoute = ref('dashboard');
    const mockMode = ref(apiClient.isMockMode());
    const apiBaseUrl = ref(apiClient.getBaseUrl());
    const toasts = ref([]);
    const activeTasks = reactive({});
    const taskDrawerOpen = ref(false);
    
    // Cost breakdown state
    const costSummary = ref(normalizeCostSummary());

    const navLinks = [
      { name: 'Dashboard', route: 'dashboard', icon: 'fas fa-chart-line' },
      { name: 'Providers', route: 'providers', icon: 'fas fa-key' },
      { name: 'Model Registry', route: 'models', icon: 'fas fa-sliders' },
      { name: 'Prompt Library', route: 'prompts', icon: 'fas fa-terminal' },
      { name: 'Voice Lab', route: 'voice', icon: 'fas fa-microphone' },
      { name: 'Image Lab', route: 'image', icon: 'fas fa-image' },
      { name: 'Video Lab', route: 'video', icon: 'fas fa-video' },
      { name: 'Asset Library', route: 'assets', icon: 'fas fa-photo-film' },
      { name: 'Compare & Eval', route: 'compare', icon: 'fas fa-balance-scale' },
      { name: 'Projects', route: 'projects', icon: 'fas fa-folder' },
      { name: 'Run History', route: 'history', icon: 'fas fa-history' }
    ];

    const activePageName = computed(() => {
      return t('sidebar.' + activeRoute.value);
    });

    const formattedTotalCost = computed(() => {
      return sumEstimatedCosts(costSummary.value?.items).toFixed(4);
    });


    const runningTasksCount = computed(() => {
      return Object.values(activeTasks).filter(t => 
        ['pending', 'queued', 'running', 'provider_pending', 'provider_running'].includes(t.status)
      ).length;
    });

    // Hash Router
    const updateRoute = () => {
      const hash = window.location.hash.replace(/^#\/?/, '');
      if (hash && navLinks.some(l => l.route === hash)) {
        activeRoute.value = hash;
      } else {
        activeRoute.value = 'dashboard';
        window.location.hash = '#dashboard';
      }
    };

    // Toasts helpers
    const addToast = (type, title, message) => {
      const id = Date.now() + Math.random().toString(36).substring(2, 6);
      toasts.value.push({ id, type, title, message });
      // Auto close after 5 seconds
      setTimeout(() => {
        removeToast(id);
      }, 5000);
    };

    const removeToast = (id) => {
      toasts.value = toasts.value.filter(t => t.id !== id);
    };

    const getToastIcon = (type) => {
      switch (type) {
        case 'success': return 'fa-check-circle text-success';
        case 'error': return 'fa-exclamation-circle text-danger';
        case 'warning': return 'fa-exclamation-triangle text-warning';
        default: return 'fa-info-circle text-info';
      }
    };

    // Cost loader
    const loadCosts = async () => {
      try {
        const data = await apiClient.request('/api/costs/summary');
        costSummary.value = normalizeCostSummary(data);
      } catch (err) {
        console.error('Failed to load cost summary:', err);
      }
    };

    // Settings updating
    const toggleMockMode = () => {
      apiClient.setMockMode(mockMode.value);
      addToast('info', 'Mode Switched', `System switched to ${mockMode.value ? 'MOCK MODE' : 'REAL API MODE'}.`);
      // Reload costs / lists on mode change
      loadCosts();
    };

    const updateBaseUrl = () => {
      apiClient.setBaseUrl(apiBaseUrl.value);
      addToast('success', 'API URL Updated', `API base url set to: ${apiBaseUrl.value}`);
    };

    const toggleTaskDrawer = () => {
      taskDrawerOpen.value = !taskDrawerOpen.value;
    };

    const getTaskLabel = (type) => {
      switch (type) {
        case 'video_generation': return 'Video Generation';
        case 'image_generation': return 'Image Generation';
        case 'tts': return 'Text to Speech';
        default: return 'Async Work';
      }
    };

    const getTaskBadgeClass = (status) => {
      switch (status) {
        case 'succeeded': return 'badge-success';
        case 'failed': return 'badge-danger';
        case 'cancelled': return 'badge-purple';
        case 'running':
        case 'provider_running': return 'badge-cyan';
        default: return 'badge-warning';
      }
    };

    // Task Polling Loop
    const registerTaskPolling = (taskId) => {
      // Create initial local entry
      activeTasks[taskId] = {
        id: taskId,
        status: 'pending',
        progress: 0,
        capability_type: 'video_generation' // Default, will update
      };
      
      const poll = async () => {
        // Stop polling if task is no longer in activeTasks or finished
        if (!activeTasks[taskId]) return;
        
        try {
          const task = await apiClient.request(`/api/tasks/${taskId}`);
          activeTasks[taskId] = task;
          
          if (['succeeded', 'failed', 'cancelled', 'timeout'].includes(task.status)) {
            if (task.status === 'succeeded') {
              addToast('success', 'Task Completed', `Task ${taskId} completed successfully!`);
              loadCosts(); // Refresh cost
            } else if (task.status === 'failed') {
              addToast('error', 'Task Failed', `Task ${taskId} failed: ${task.error?.message || 'Unknown error'}`);
            }
            // Remove from active tracking after a delay so user can see it completed in drawer
            setTimeout(() => {
              delete activeTasks[taskId];
            }, 10000);
            return;
          }
          // Continue polling
          setTimeout(poll, 3000);
        } catch (err) {
          console.error(`Error polling task ${taskId}:`, err);
          activeTasks[taskId].status = 'failed';
          activeTasks[taskId].error = { message: err.message || 'Connection lost' };
          addToast('error', 'Task Error', `Failed to poll status for task ${taskId}`);
        }
      };
      
      setTimeout(poll, 1000);
    };

    const cancelTask = async (taskId) => {
      try {
        await apiClient.request(`/api/tasks/${taskId}/cancel`, { method: 'POST' });
        addToast('warning', 'Task Cancel Requested', `Sent cancellation request for task ${taskId}`);
        if (activeTasks[taskId]) {
          activeTasks[taskId].status = 'cancelled';
        }
      } catch (err) {
        addToast('error', 'Cancellation Failed', err.message || 'Could not cancel task');
      }
    };

    // Global handles provided to all views
    provide('apiClient', apiClient);
    provide('addToast', addToast);
    provide('loadCosts', loadCosts);
    provide('registerTaskPolling', registerTaskPolling);
    provide('t', t);
    provide('currentLocale', currentLocale);
    provide('setLocale', setLocale);

    onMounted(() => {
      window.addEventListener('hashchange', updateRoute);
      updateRoute();
      loadCosts();
      
      // Periodically refresh cost summary
      setInterval(loadCosts, 15000);
    });

    return {
      t,
      currentLocale,
      setLocale,
      onLanguageChange: () => {
        setLocale(currentLocale.value);
      },
      activeRoute,
      mockMode,
      apiBaseUrl,
      toasts,
      activeTasks,
      taskDrawerOpen,
      costSummary,
      navLinks,
      activePageName,
      formattedTotalCost,
      runningTasksCount,
      toggleMockMode,
      updateBaseUrl,
      toggleTaskDrawer,
      getTaskLabel,
      getTaskBadgeClass,
      removeToast,
      getToastIcon,
      cancelTask
    };
  }
});

// Keep translation available to Options API templates even if a view forgets
// to return the injected function from setup().
app.mixin({
  methods: {
    t
  }
});

app.config.errorHandler = (err, instance, info) => {
  console.error('Unhandled Vue error:', { err, info, instance });
};

// Lazy register components by mapping views to global components
// To prevent ES import errors, we define them below.
// We will register each view on the app so it is usable via <component :is="..." />
import DashboardView from './views/dashboard.js';
import ProvidersView from './views/providers.js';
import ModelsView from './views/models.js';
import PromptsView from './views/prompts.js';
import VoiceView from './views/voice.js';
import ImageView from './views/image.js';
import VideoView from './views/video.js';
import AssetsView from './views/assets.js';
import CompareView from './views/compare.js';
import ProjectsView from './views/projects.js';
import HistoryView from './views/history.js';

app.component('dashboard-view', DashboardView);
app.component('providers-view', ProvidersView);
app.component('models-view', ModelsView);
app.component('prompts-view', PromptsView);
app.component('voice-view', VoiceView);
app.component('image-view', ImageView);
app.component('video-view', VideoView);
app.component('assets-view', AssetsView);
app.component('compare-view', CompareView);
app.component('projects-view', ProjectsView);
app.component('history-view', HistoryView);

app.mount('#app');
