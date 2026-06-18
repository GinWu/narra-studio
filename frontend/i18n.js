import { ref } from 'vue';

export const currentLocale = ref(localStorage.getItem('aiwm_locale') || 'en');

export const translations = {
  en: {
    common: {
      save: 'Save',
      cancel: 'Cancel',
      delete: 'Delete',
      edit: 'Edit',
      actions: 'Actions',
      status: 'Status',
      loading: 'Loading...',
      success: 'Success',
      error: 'Error',
      confirm: 'Confirm',
      close: 'Close',
      warning: 'Warning',
      select: 'Select',
      add: 'Add',
      duplicate: 'Duplicate',
      test: 'Test Connection',
      rerun: 'Rerun',
      copy: 'Copy',
      info: 'Info',
      default: 'Default',
      none: 'None',
      ok: 'OK',
      added: 'Added',
      qualityRating: 'Quality Rating:',
      failed: 'Failed',
      cancelled: 'Cancelled',
      running: 'Running'
    },
    sidebar: {
      subLabel: 'AI Media Production Workbench',
      dashboard: 'Dashboard',
      providers: 'Providers',
      models: 'Model Registry',
      prompts: 'Prompt Library',
      voice: 'Audio Lab',
      image: 'Image Lab',
      video: 'Video Lab',
      assets: 'Asset Library',
      compare: 'Compare & Eval',
      projects: 'Projects',
      history: 'Run History',
      mockMode: 'Mock Mode',
      apiBaseUrl: 'API Base URL',
      language: 'Language'
    },
    dashboard: {
      title: 'Dashboard',
      stats: {
        cost: 'Estimated Cost',
        assets: 'Media Assets',
        experiments: 'Experiments',
        models: 'Active Models'
      },
      recent: {
        title: 'Recent Experiments',
        tableId: 'Experiment ID',
        tableType: 'Type',
        tableModel: 'Model',
        tableStatus: 'Status',
        tableTime: 'Created At',
        viewAll: 'View All',
        empty: 'No experiments run yet. Start one in the labs!'
      },
      costBreakdown: {
        title: 'Cost Breakdown',
        empty: 'No costs logged yet.'
      },
      quickLauncher: {
        title: 'Quick Launcher',
        voice: 'Launch Audio Lab',
        image: 'Launch Image Lab',
        video: 'Launch Video Lab'
      }
    },
    providers: {
      title: 'Providers',
      policy: {
        title: 'Security & Credential Isolation Policy',
        desc: 'The frontend never directly stores, transmits, or exposes API secret keys to the browser. Keys must be injected into the backend container through Docker Compose environment variables, Docker Secrets, or secret files. You only reference the key by its credential name/variable reference here.'
      },
      table: {
        name: 'Provider Name',
        type: 'Type',
        status: 'Status',
        credentials: 'Credentials Reference',
        actions: 'Actions'
      },
      buttons: {
        add: 'Register Provider',
        test: 'Test Connection'
      },
      status: {
        enabled: 'Enabled',
        disabled: 'Disabled'
      },
      actions: {
        enable: 'Enable',
        disable: 'Disable',
        saveChanges: 'Save Changes'
      },
      help: {
        codeLocked: 'Provider code is a stable registry identifier and cannot be changed after creation.'
      },
      credentialHelp: {
        env: {
          title: 'Environment Variable',
          desc: 'Read from the backend API/worker container environment, not from the browser or your desktop. Add the variable to Docker Compose env_file/environment, then enter its variable name here.'
        },
        docker_secret: {
          title: 'Docker Secret',
          desc: 'Read from a file mounted inside the backend container, normally /run/secrets/<secret_name>. Create or mount the secret in Docker Compose, then enter the secret name here. The real key is never saved in the database.'
        },
        file: {
          title: 'Backend Container File Path',
          desc: 'Read from a text file path visible inside the backend container. Use this only for local/dev deployments where you can mount a secret file into the container.'
        },
        none: {
          title: 'No Credential',
          desc: 'Use this for mock providers or providers that do not require authentication. No secret reference is needed.'
        }
      },
      modal: {
        titleAdd: 'Register New Provider',
        titleEdit: 'Edit Provider Configuration',
        labelName: 'Provider Code',
        labelDisplay: 'Display Name',
        labelType: 'Provider Type',
        labelBase: 'API Base URL (Optional)',
        labelAuth: 'Auth Type',
        labelSource: 'Credential Source',
        labelRef: 'Credential Reference Name',
        labelFile: 'Secret File Path (Optional)',
        labelFileOptional: 'Secret File Path Override (Optional)',
        labelTimeout: 'Timeout (Seconds)'
      }
    },
    models: {
      title: 'Model Registry',
      filters: {
        allCaps: 'All Capabilities',
        allPrvs: 'All Providers',
        register: 'Register Model',
        empty: 'No models matching the selected filters found.'
      },
      card: {
        default: 'Default',
        recommended: 'Recommended',
        verification: 'Needs Verification',
        provider: 'Provider',
        capability: 'Capability',
        pricing: 'Cost Pricing',
        actionEnable: 'Enable',
        actionDisable: 'Disable'
      },
      modal: {
        titleAdd: 'Register New Model',
        titleEdit: 'Edit Model Registry',
        labelCode: 'Model Code (ID)',
        labelDisplay: 'Display Name',
        labelCapability: 'Capability Type',
        labelProvider: 'Provider',
        labelDefaultParams: 'Default Parameters (JSON)',
        labelUiSchema: 'Parameter UI Schema (JSON)',
        labelCostUnit: 'Cost Unit',
        labelPricingHint: 'Pricing Hint / Description'
      }
    },
    prompts: {
      title: 'Prompt Library',
      sidebar: {
        templates: 'Templates',
        search: 'Search prompts...',
        new: 'New',
        empty: 'No templates found.',
        scenario: 'Scenario',
        usedCount: 'Used {count} times'
      },
      editor: {
        duplicate: 'Duplicate',
        delete: 'Delete',
        labelName: 'Template Name',
        labelScenario: 'Scenario (Capability Scenario)',
        labelTemplate: 'Template Text (Use {{variable_name}} for placeholding)',
        labelVariablesSchema: 'Variables Schema (JSON Object Definition)',
        labelDefaultValues: 'Default Values (JSON Object)',
        labelRating: 'Rating',
        actionSave: 'Save Changes',
        actionReset: 'Reset',
        selectPlaceholder: 'Select a prompt template or click \'New\' to create one.'
      },
      revisions: {
        title: 'Version Revisions',
        empty: 'Single version initial template. Updates to template content or variable schemas automatically trigger version tracking.',
        current: 'Current Latest',
        actionSwitch: 'Switch'
      }
    },
    voice: {
      title: 'Audio Lab',
      config: {
        title: 'TTS Configuration',
        model: 'TTS Model *',
        template: 'Use Prompt Template (Optional)',
        variables: 'Template Variables',
        speechText: 'Speech Narrative *',
        chars: '{count} / 500 chars',
        settings: 'Voice Settings',
        buttonSpeech: 'Generate Speech',
        buttonGenerating: 'Generating Audio...',
        directTextMode: '-- Direct Text Mode (No Template) --'
      },
      history: {
        title: 'Generated Audio History',
        empty: 'No audio files generated yet. Configure options and click Generate.',
        labelModel: 'Model',
        labelLatency: 'Latency',
        badgeBest: 'Best Output',
        badgeFailed: 'Fail Node',
        actionRerun: 'Rerun / Tune',
        actionMarkBest: 'Mark Best',
        actionMarkFailure: 'Mark Failure'
      },
      failModal: {
        title: 'Mark Experiment Failure',
        desc: 'Please select or enter the specific reason why this synthesis is considered a failure node.',
        labelCategory: 'Failure Reason Category',
        labelDetail: 'Detailed Explanation',
        buttonFlag: 'Flag Failure',
        categories: {
          pronunciation_error: 'Pronunciation / Reading Error',
          robotic_voice: 'Robotic / Unnatural Tone',
          audio_artifact: 'Background Noise / Artifacts',
          incorrect_speed: 'Speed / Rhythm Issues',
          other: 'Other / Custom'
        }
      },
      tabs: {
        tts: 'TTS Synthesis',
        stt: 'STT Transcription',
        voiceClone: 'Voice Clone',
        voiceProfiles: 'Voice Profiles'
      },
      stt: {
        title: 'STT Configuration',
        audioSource: 'Audio Source',
        uploadFile: 'Upload Audio File',
        selectAsset: 'Select from Asset Library',
        model: 'STT Model *',
        language: 'Language (Optional)',
        format: 'Response Format',
        buttonTranscribe: 'Run Transcription',
        buttonTranscribing: 'Transcribing...',
        transcriptTitle: 'Transcript Result',
        emptyTranscript: 'Transcript is empty.',
        copyBtn: 'Copy Transcript',
        convertToScript: 'Convert to Script Version',
        scriptTitle: 'Script Version Title',
        selectProject: 'Select Project',
        successConvert: 'Transcript successfully converted to ScriptVersion!'
      },
      clone: {
        title: 'Voice Clone Configuration',
        sampleSource: 'Voice Sample Source',
        uploadSample: 'Upload Voice Samples',
        selectAsset: 'Select from Asset Library',
        voiceName: 'Voice Name *',
        displayName: 'Display Name',
        sourceType: 'Source Type',
        consentStatus: 'Consent Status',
        commercialAllowed: 'Allow Commercial Use',
        usageScope: 'Usage Scope',
        platforms: 'Allowed Platforms (comma separated)',
        riskLevel: 'Risk Level',
        disclosure: 'Require AI Generated Disclosure',
        legalDisclaimer: 'Legal Notice: By performing Voice Clone, you confirm you have all necessary legal authorization and consents for this voice sample. Cloning unauthorized voices is strictly prohibited.',
        buttonClone: 'Start Voice Clone',
        buttonCloning: 'Cloning Voice...',
        successClone: 'Voice cloned successfully! Created VoiceProfile: {id}'
      },
      profiles: {
        title: 'Voice Profiles Management',
        empty: 'No voice profiles registered yet. Clone a new voice or seed model profiles.',
        provider: 'Provider',
        voiceId: 'Voice ID (Masked)',
        status: 'Status',
        consent: 'Consent Status',
        commercial: 'Commercial Allowed',
        platforms: 'Platforms',
        risk: 'Risk Level',
        actions: {
          disable: 'Disable',
          revoke: 'Revoke',
          expire: 'Mark Expired',
          useInTts: 'Use in TTS',
          setDefault: 'Set as Project Default'
        },
        warnings: {
          revoked: 'This voice profile has been REVOKED. It cannot be used.',
          expired: 'This voice profile has EXPIRED.',
          testing: 'This voice profile is in testing mode.',
          highRisk: 'This is a HIGH RISK voice profile. Confirm usage explicitly.',
          commercialWarning: 'This voice profile is not allowed for commercial use.',
          providerMismatch: 'The selected Voice Profile provider does not match the active model provider!'
        }
      }
    },
    image: {
      title: 'Image Lab',
      config: {
        title: 'Image Configuration',
        model: 'Image Model *',
        template: 'Use Prompt Template (Optional)',
        prompt: 'Image Prompt *',
        negative: 'Negative Prompt (Optional)',
        settings: 'Model Settings',
        count: 'Image Count (N) *',
        buttonGenerate: 'Generate Image',
        buttonGenerating: 'Generating Image...',
        directPromptMode: '-- Direct Prompt Mode (No Template) --'
      },
      history: {
        title: 'Generated Images History',
        empty: 'No images generated yet. Configure options and click Generate.',
        rateQuality: 'Rate Quality:'
      },
      failModal: {
        title: 'Mark Experiment Failure',
        desc: 'Please select or enter the specific reason why this image generation is considered a failure node.',
        labelCategory: 'Failure Reason Category',
        labelDetail: 'Detailed Explanation',
        buttonFlag: 'Flag Failure',
        categories: {
          deformed_anatomy: 'Deformed Anatomy / Limbs',
          poor_details: 'Poor Quality / Artifacts',
          blurry_image: 'Blurry / Low Resolution',
          prompt_mismatch: 'Prompt Mismatch / Hallucination',
          other: 'Other / Custom'
        }
      }
    },
    video: {
      title: 'Video Lab',
      config: {
        title: 'Video Configuration',
        model: 'Video Model *',
        prompt: 'Video Prompt *',
        startFrame: 'Start Frame Image (Optional)',
        selectFrame: 'Select Start Frame Image',
        changeFrame: 'Change Start Frame',
        settings: 'Model Settings',
        duration: 'Duration (Seconds) *',
        buttonGenerate: 'Generate Video',
        buttonGenerating: 'Generating Video...',
        buttonSubmitting: 'Submitting Async Task...'
      },
      history: {
        title: 'Async Video Productions',
        empty: 'No video generation jobs submitted yet.',
        progress: 'Progress',
        rateUsability: 'Asset Usability:',
        actionCancel: 'Cancel Job'
      },
      frameModal: {
        title: 'Select Start Frame Image',
        empty: 'No generated images found in library. Launch Image Lab to generate a starting frame.'
      },
      failModal: {
        title: 'Mark Experiment Failure',
        desc: 'Please select or enter the specific reason why this video generation is considered a failure node.',
        labelCategory: 'Failure Reason Category',
        labelDetail: 'Detailed Explanation',
        buttonFlag: 'Flag Failure',
        categories: {
          flickering_artifacts: 'Flickering / Glitches',
          deformed_motion: 'Deformed / Unnatural Motion',
          bad_morphing: 'Drastic Morphs / Hallucinations',
          poor_resolution: 'Low Res / Blurry Frames',
          other: 'Other / Custom'
        }
      }
    },
    assets: {
      title: 'Asset Library',
      filters: {
        allTypes: 'All Asset Types',
        image: 'Images',
        audio: 'Audio',
        video: 'Videos',
        search: 'Search assets by name or tags...',
        stats: 'Total: {count} assets',
        empty: 'No assets found in storage.',
        showDiscarded: 'Show Discarded Assets'
      },
      card: {
        type: 'Type',
        mime: 'MIME',
        size: 'Size',
        dimension: 'Dimensions',
        duration: 'Duration',
        actionDownload: 'Download',
        actionDiscard: 'Discard',
        actionDelete: 'Delete Permanent',
        score: 'Score:',
        discarded: 'Discarded'
      }
    },
    compare: {
      title: 'Compare & Eval',
      workspace: {
        title: 'Comparative Evaluation Workspace',
        desc: 'Select two or more generated assets to compare side-by-side. You can rate them on multiple dimensions and mark the best candidate in this comparison group.',
        select: 'Select Assets to Compare',
        clear: 'Clear Selection',
        comparing: 'Comparing {count} assets',
        empty: 'Select assets to open comparison panels.'
      },
      card: {
        best: 'Group Best',
        markBest: 'Mark Best',
        usability: 'Usability',
        fidelity: 'Prompt Fidelity',
        quality: 'Technical Quality',
        conclusion: 'Evaluation Summary / Conclusion',
        commentPlaceholder: 'Write the evaluation notes or model comparison results summary...',
        buttonSave: 'Save Evaluation Conclusion',
        buttonSaving: 'Saving...'
      },
      selector: {
        title: 'Select Assets to Compare',
        empty: 'No generated assets found.'
      }
    },
    projects: {
      title: 'Projects',
      workspace: {
        title: 'Projects Workspace',
        create: 'Create Project',
        empty: 'No content projects created yet. Create one to organize shots, scripts, and exports.',
        enter: 'Enter Workspace',
        deleteConfirm: 'Are you sure you want to delete this project?',
        created: 'Created'
      },
      modalCreate: {
        title: 'Create New Project',
        name: 'Project Name *',
        namePlaceholder: 'e.g. Sci-Fi Intro Draft',
        desc: 'Description',
        descPlaceholder: 'Brief outline of project scope...',
        buttonCreate: 'Create Project'
      },
      active: {
        back: 'Back to Projects List',
        export: 'Export Manifest',
        scriptTitle: 'Script Board Narrative',
        scriptPlaceholder: 'Type or paste the narration draft / screenplay outline here...',
        saveScript: 'Save Script Version',
        addShot: 'Add Shot Card',
        shotLabel: 'Shot label (e.g. Shot 1, Close Up Face)',
        shotCue: 'Narrative text cue / Prompt hint...',
        buttonAddTimeline: 'Add to Timeline',
        timelineTitle: 'Timeline Shots Ordering',
        timelineEmpty: 'No shots defined for this project. Create one on the left.',
        shotActions: {
          linkAsset: 'Link Asset',
          clearAsset: 'Unlink',
          saveShot: 'Save',
          deleteShot: 'Delete'
        },
        assetSelectorTitle: 'Link Media Asset to Shot',
        projectPrefix: 'Project',
        noAssetLinked: 'No asset linked.',
        generate: 'Generate',
        runQuickGenerateTitle: 'Run generation using shot cue text',
        noAssetsAvailable: 'No generated assets available.',
        linkButton: 'Link',
        linkedPrefix: 'Linked',
        defaultVoiceProfile: 'Default Voice Profile',
        selectVoiceProfile: 'Select Voice Profile',
        overrideVoiceProfile: 'Override Voice Profile',
        generateVoiceover: 'Generate Voiceover',
        buttonGeneratingVoiceover: 'Generating...',
        projectVoiceoverSettings: 'Project Voiceover Settings'
      },
      exportModal: {
        title: 'Project Production Manifest',
        titlePreview: 'Project Export Manifest Preview',
        warning: 'Security License Notice',
        warningText: 'Exported assets comply with safety guidelines. Keep records of cost estimates and model references.',
        downloadBtn: 'Download Manifest JSON',
        warningsTitle: 'Security / Verification Warnings',
        successTitle: 'Security & License Sanity Passed',
        successDesc: 'Credential leakage sanitizer completed. No sensitive local volume paths or Authorization tokens detected in exported references.',
        payloadLabel: 'JSON Manifest Payload (relative paths & safe hashes)'
      }
    },
    history: {
      title: 'Run History',
      filters: {
        allStatuses: 'All Statuses',
        searchPlaceholder: 'Search inputs...',
        showOnlyBest: 'Show Only Best Cases',
        allLabs: 'All Labs',
        voice: 'Audio Lab',
        image: 'Image Lab',
        video: 'Video Lab'
      },
      table: {
        expId: 'Experiment ID',
        type: 'Type',
        model: 'Model',
        status: 'Status',
        latency: 'Latency',
        time: 'Created At',
        detail: 'Details',
        empty: 'No history found.',
        titleInput: 'Title / Input',
        tags: 'Tags / Flags',
        best: 'Best',
        failCase: 'Fail Case',
        btnDetails: 'Details'
      },
      modal: {
        title: 'Experiment Execution Log',
        tabDetails: 'Details',
        tabParams: 'Parameters',
        tabLogs: 'System Logs',
        tabOutput: 'Output Preview',
        labelProvider: 'Provider',
        labelModel: 'Model Registry ID',
        labelAdapter: 'Adapter Node',
        labelLatency: 'Latency',
        labelCost: 'Estimated Cost',
        labelInput: 'Raw Input Content',
        labelOutput: 'Output Asset Refs',
        inputTitle: 'Input JSON Payload',
        paramsTitle: 'Effective Parameters',
        logsTitle: 'Celery / Invocation Trace Logs',
        synthesisScriptLabel: 'Synthesis Narrative Script / Prompt:',
        modelConfigLabel: 'Model Configuration:',
        inputParamsLabel: 'Input Parameters (Params JSON):',
        linkedAssetRef: 'Linked Media Asset Reference',
        fileLabel: 'File:',
        mimeLabel: 'MIME:',
        sizeLabel: 'Size:',
        downloadAsset: 'Download Asset',
        noOutputAsset: 'No output asset generated or linked. This experiment might have failed or is in progress.',
        loadingLogs: 'Loading trace events...',
        noLogs: 'No execution logs found for this experiment run.',
        stepLabel: 'Step:'
      }
    }
  },
  zh: {
    common: {
      save: '保存',
      cancel: '取消',
      delete: '删除',
      edit: '编辑',
      actions: '操作',
      status: '状态',
      loading: '加载中...',
      success: '成功',
      error: '错误',
      confirm: '确认',
      close: '关闭',
      warning: '警告',
      select: '选择',
      add: '添加',
      duplicate: '克隆',
      test: '测试连接',
      rerun: '重新运行',
      copy: '复制',
      info: '信息',
      default: '默认',
      none: '无',
      ok: '确定',
      added: '已添加',
      qualityRating: '评估质量:',
      failed: '失败',
      cancelled: '已取消',
      running: '进行中'
    },
    sidebar: {
      subLabel: 'AI 媒体内容创作工作台',
      dashboard: '控制台',
      providers: '服务商配置',
      models: '模型仓库',
      prompts: '提示词模板',
      voice: '音频实验台',
      image: '图片实验台',
      video: '视频实验台',
      assets: '媒体资源库',
      compare: '对比与评估',
      projects: '内容项目',
      history: '运行日志',
      mockMode: '模拟模式',
      apiBaseUrl: 'API 基地址',
      language: '语言选择'
    },
    dashboard: {
      title: '控制台',
      stats: {
        cost: '预估成本',
        assets: '媒体资源',
        experiments: '实验记录',
        models: '已启用模型'
      },
      recent: {
        title: '最近实验',
        tableId: '实验 ID',
        tableType: '类型',
        tableModel: '模型',
        tableStatus: '状态',
        tableTime: '创建时间',
        viewAll: '查看全部',
        empty: '暂无实验记录。去实验台运行一个吧！'
      },
      costBreakdown: {
        title: '成本分摊',
        empty: '暂无成本记录。'
      },
      quickLauncher: {
        title: '快速启动',
        voice: '进入音频实验台',
        image: '进入图片实验台',
        video: '进入视频实验台'
      }
    },
    providers: {
      title: '服务商配置',
      policy: {
        title: '安全与凭据隔离策略',
        desc: '前端永远不会直接将 API 密钥存储、传输或暴露给浏览器。密钥必须通过 Docker Compose 环境变量、Docker Secrets 或密钥文件注入到后端容器中。您只需在此处引用其凭据名称/变量别名。'
      },
      table: {
        name: '服务商名称',
        type: '类型',
        status: '状态',
        credentials: '凭据引用',
        actions: '操作'
      },
      buttons: {
        add: '注册服务商',
        test: '测试连接'
      },
      status: {
        enabled: '已启用',
        disabled: '已禁用'
      },
      actions: {
        enable: '启用',
        disable: '停用',
        saveChanges: '保存修改'
      },
      help: {
        codeLocked: '服务商代码是稳定的注册标识，创建后不可修改。'
      },
      credentialHelp: {
        env: {
          title: 'Environment Variable：后端容器环境变量',
          desc: '这里读取的是 API/worker 后端容器内的环境变量，不是浏览器或当前桌面设备的环境变量。请在 Docker Compose 的 env_file 或 environment 中配置真实 Key，然后这里只填写变量名。'
        },
        docker_secret: {
          title: 'Docker Secret：容器内密钥文件',
          desc: '这里读取的是后端容器内挂载的密钥文件，默认路径为 /run/secrets/<secret_name>。请在 Docker Compose 中创建或挂载 secret，然后这里只填写 secret 名称；真实 Key 不会保存到数据库。'
        },
        file: {
          title: 'Local System File Path：后端容器可见文件路径',
          desc: '这里的“本地文件”指后端容器内部可访问的文件路径，不是浏览器所在电脑的路径。通常用于开发部署：把宿主机密钥文件挂载进容器，再填写容器内路径。'
        },
        none: {
          title: 'None：无需凭据',
          desc: '适用于 Mock 服务商或无需认证的服务商，不需要填写凭据引用。'
        }
      },
      modal: {
        titleAdd: '注册新服务商',
        titleEdit: '编辑服务商配置',
        labelName: '服务商代码',
        labelDisplay: '显示名称',
        labelType: '服务商类型',
        labelBase: 'API 基地址 (可选)',
        labelAuth: '认证类型',
        labelSource: '凭据来源',
        labelRef: '凭据引用变量名',
        labelFile: '密钥文件路径 (可选)',
        labelFileOptional: '密钥文件路径覆盖 (可选)',
        labelTimeout: '超时时间 (秒)'
      }
    },
    models: {
      title: '模型仓库',
      filters: {
        allCaps: '所有能力类型',
        allPrvs: '所有服务商',
        register: '注册新模型',
        empty: '未找到符合筛选条件的注册模型。'
      },
      card: {
        default: '默认',
        recommended: '推荐',
        verification: '待生产验证',
        provider: '服务商',
        capability: '支持能力',
        pricing: '资费标准',
        actionEnable: '启用',
        actionDisable: '禁用'
      },
      modal: {
        titleAdd: '注册新模型',
        titleEdit: '编辑模型配置',
        labelCode: '模型代码 (ID)',
        labelDisplay: '显示名称',
        labelCapability: '能力类型',
        labelProvider: '所属服务商',
        labelDefaultParams: '默认参数 (JSON)',
        labelUiSchema: '参数 UI 架构 (JSON)',
        labelCostUnit: '计费单位',
        labelPricingHint: '计费说明 / 资费说明'
      }
    },
    prompts: {
      title: '提示词仓库',
      sidebar: {
        templates: '模板列表',
        search: '搜索提示词...',
        new: '新建模板',
        empty: '未找到模板。',
        scenario: '场景',
        usedCount: '已使用 {count} 次'
      },
      editor: {
        duplicate: '克隆',
        delete: '删除',
        labelName: '模板名称',
        labelScenario: '场景类型 (Scenario)',
        labelTemplate: '模板文本 (使用 {{variable_name}} 进行占位替换)',
        labelVariablesSchema: '变量 Schema (JSON 对象定义)',
        labelDefaultValues: '默认变量值 (JSON 对象)',
        labelRating: '模板评分',
        actionSave: '保存修改',
        actionReset: '重置',
        selectPlaceholder: '请选择一个提示词模板，或点击“新建模板”进行创建。'
      },
      revisions: {
        title: '版本演进记录',
        empty: '当前模板为初始版本。修改模板内容或变量定义后保存会自动生成新版本节点进行追踪。',
        current: '最新版本',
        actionSwitch: '切换到此版本'
      }
    },
    voice: {
      title: '音频实验台',
      config: {
        title: 'TTS 配置面板',
        model: '选择 TTS 模型 *',
        template: '使用提示词模板 (可选)',
        variables: '模板填充变量',
        speechText: '语音文本内容 *',
        chars: '{count} / 500 字符',
        settings: '声音高级参数',
        buttonSpeech: '合成音频',
        buttonGenerating: '正在合成音频...',
        directTextMode: '-- 直接文本输入 (不使用提示词模板) --'
      },
      history: {
        title: '音频历史生成记录',
        empty: '暂无已生成音频。请配置左侧选项并点击“合成音频”。',
        labelModel: '使用模型',
        labelLatency: '合成耗时',
        badgeBest: '最佳输出',
        badgeFailed: '失败节点',
        actionRerun: '载入配置 / 微调',
        actionMarkBest: '标为最佳',
        actionMarkFailure: '标记失败'
      },
      failModal: {
        title: '标记实验音频失败',
        desc: '请选择或输入该音频合成效果被判定为失败节点（Fail Node）的具体原因（用于后续模型调试与对比）。',
        labelCategory: '问题类型分类',
        labelDetail: '详细原因描述',
        buttonFlag: '标记失败',
        categories: {
          pronunciation_error: '发音/朗读错误',
          robotic_voice: '机械音/语气不自然',
          audio_artifact: '背景噪音/音频杂音',
          incorrect_speed: '语速/节奏不当',
          other: '其他原因/自定义'
        }
      },
      tabs: {
        tts: 'TTS 旁白合成',
        stt: 'STT 语音转写',
        voiceClone: '声音克隆',
        voiceProfiles: '音色库管理'
      },
      stt: {
        title: 'STT 语音转写配置',
        audioSource: '音频来源',
        uploadFile: '上传音频文件',
        selectAsset: '从媒体库选择',
        model: '选择 STT 模型 *',
        language: '识别语言 (可选)',
        format: '响应格式',
        buttonTranscribe: '执行转写',
        buttonTranscribing: '正在转写...',
        transcriptTitle: '转写文本结果',
        emptyTranscript: '转写文本为空。',
        copyBtn: '复制文本',
        convertToScript: '转为项目剧本版本',
        scriptTitle: '脚本版本标题',
        selectProject: '选择所属内容项目',
        successConvert: '转写文本已成功生成新的项目剧本版本！'
      },
      clone: {
        title: '声音克隆参数配置',
        sampleSource: '声音样本来源',
        uploadSample: '上传样本音频',
        selectAsset: '从媒体库选择',
        voiceName: '音色名称 *',
        displayName: '显示名称',
        sourceType: '音色来源类型',
        consentStatus: '授权状态',
        commercialAllowed: '允许商用',
        usageScope: '使用范围',
        platforms: '允许发布平台 (英文逗号分隔)',
        riskLevel: '风险等级',
        disclosure: '要求 AI 生成披露声明',
        legalDisclaimer: '合规声明：在进行声音克隆前，您必须确认已获得被克隆人声音的所有法律授权和同意。严禁克隆未授权的声音。',
        buttonClone: '开始声音克隆',
        buttonCloning: '正在克隆声音...',
        successClone: '声音克隆成功！已创建音色配置文件 ID: {id}'
      },
      profiles: {
        title: '音色库列表管理',
        empty: '暂无音色配置文件。您可以通过声音克隆创建，或注册支持音色选择的模型。',
        provider: '能力供应商',
        voiceId: 'Provider 内部音色 ID',
        status: '配置状态',
        consent: '授权确认状态',
        commercial: '商用属性',
        platforms: '使用平台',
        risk: '风险属性',
        actions: {
          disable: '禁用音色',
          revoke: '标记已撤销',
          expire: '标记已过期',
          useInTts: '在 TTS 中使用',
          setDefault: '设为项目默认音色'
        },
        warnings: {
          revoked: '该音色已被“撤销（REVOKED）”，系统已锁定使用。',
          expired: '该音色授权已“过期（EXPIRED）”，请重新导入。',
          testing: '该音色处于测试（Testing）阶段，请在确认授权前谨慎使用。',
          highRisk: '该音色属于高风险（HIGH RISK）属性，使用时需要显式授权确认。',
          commercialWarning: '该音色不支持商用（Commercial Not Allowed）。',
          providerMismatch: '选择的音色供应商与当前 TTS 模型所属供应商不匹配！'
        }
      }
    },
    image: {
      title: '图片实验台',
      config: {
        title: '图片配置面板',
        model: '选择图片模型 *',
        template: '使用提示词模板 (可选)',
        prompt: '图片提示词 *',
        negative: '反向提示词 (可避开元素)',
        settings: '模型参数配置',
        count: '单次生成数量 (N) *',
        buttonGenerate: '生成图片',
        buttonGenerating: '正在生成图片...',
        directPromptMode: '-- 直接提示词输入 (不使用提示词模板) --'
      },
      history: {
        title: '图片历史生成记录',
        empty: '暂无已生成图片。请配置左侧选项并点击“生成图片”。',
        rateQuality: '评估质量:'
      },
      failModal: {
        title: '标记实验图片失败',
        desc: '请选择或输入该图片生成效果被判定为失败节点（Fail Node）的具体原因（用于后续模型调试与对比）。',
        labelCategory: '问题类型分类',
        labelDetail: '详细原因描述',
        buttonFlag: '标记失败',
        categories: {
          deformed_anatomy: '肢体畸形/画面扭曲',
          poor_details: '画面粗糙/细节损坏',
          blurry_image: '模糊不清/分辨率低',
          prompt_mismatch: '图文不符/模型幻觉',
          other: '其他原因/自定义'
        }
      }
    },
    video: {
      title: '视频实验台',
      config: {
        title: '视频配置面板',
        model: '选择视频模型 *',
        prompt: '视频描述词 *',
        startFrame: '首帧起始图 (可选)',
        selectFrame: '选择起始图片',
        changeFrame: '修改起始帧',
        settings: '模型参数配置',
        duration: '视频时长 (秒) *',
        buttonGenerate: '生成视频',
        buttonGenerating: '正在排队/生成中...',
        buttonSubmitting: '正在提交异步任务...'
      },
      history: {
        title: '异步视频生产清单',
        empty: '暂无已提交的视频生成任务。',
        progress: '生产进度',
        rateUsability: '可用性评分:',
        actionCancel: '取消任务'
      },
      frameModal: {
        title: '选择起始帧图片',
        empty: '媒体库中暂未找到已生成图片。请先在图片实验台中生成一张可用首帧。'
      },
      failModal: {
        title: '标记实验视频失败',
        desc: '请选择或输入该视频生成效果被判定为失败节点（Fail Node）的具体原因（用于后续模型调试与对比）。',
        labelCategory: '问题类型分类',
        labelDetail: '详细原因描述',
        buttonFlag: '标记失败',
        categories: {
          flickering_artifacts: '闪烁与伪影',
          deformed_motion: '动作畸形/不自然',
          bad_morphing: '画面突变/模型幻觉',
          poor_resolution: '低分辨率/画面模糊',
          other: '其他原因/自定义'
        }
      }
    },
    assets: {
      title: '媒体资源库',
      filters: {
        allTypes: '所有文件类型',
        image: '图片 (Image)',
        audio: '音频 (Audio)',
        video: '视频 (Video)',
        search: '搜索文件名或关联标签...',
        stats: '共 {count} 个资源文件',
        empty: '媒体库存储中暂无可用资源文件。',
        showDiscarded: '显示已回收资源'
      },
      card: {
        type: '文件类型',
        mime: 'MIME 类型',
        size: '文件大小',
        dimension: '画面分辨率',
        duration: '音频/视频时长',
        actionDownload: '下载文件',
        actionDiscard: '移入回收',
        actionDelete: '永久删除',
        score: '可用性评分:',
        discarded: '已回收'
      }
    },
    compare: {
      title: '对比与评估',
      workspace: {
        title: '多模型对比评估工作台',
        desc: '选择两个或多个已生成文件进行横向侧面对比。您可以在多个维度上进行打分评价，并标记本组内表现最优秀的最佳输出。',
        select: '选择对比资源',
        clear: '清空本组',
        comparing: '正在对比 {count} 个文件',
        empty: '请先选择要对比的媒体文件以开启横向评估面板。'
      },
      card: {
        best: '本组最佳',
        markBest: '设为最佳',
        usability: '可用性评分',
        fidelity: '提示词契合度',
        quality: '技术指标质量',
        conclusion: '该组多模型评估总结结论',
        commentPlaceholder: '在此编写关于这几款模型输出对比的详细评测日志或定性分析结论...',
        buttonSave: '保存评估对比结论',
        buttonSaving: '正在保存评估结论...'
      },
      selector: {
        title: '选择资源加入对比',
        empty: '暂无已生成的可用媒体文件。'
      }
    },
    projects: {
      title: '内容项目管理',
      workspace: {
        title: '项目工作区',
        create: '创建新项目',
        empty: '暂无项目。创建一个内容项目来组织和排版您的剧本旁白、镜头与导出的多媒体生产清单吧。',
        enter: '进入项目空间',
        deleteConfirm: '确定要删除此项目吗？该操作仅删除项目关系，不影响媒体库底层资源。',
        created: '创建时间'
      },
      modalCreate: {
        title: '创建内容生产项目',
        name: '项目名称 *',
        namePlaceholder: '例如：科幻短片片头草稿',
        desc: '项目说明/备注',
        descPlaceholder: '项目范围简要概述...',
        buttonCreate: '确认创建项目'
      },
      active: {
        back: '返回内容项目列表',
        export: '导出生产清单',
        scriptTitle: '项目剧本/旁白叙事',
        scriptPlaceholder: '在此输入或粘贴剧本旁白草稿 / 剧本大纲...',
        saveScript: '保存当前脚本版本',
        addShot: '添加分镜卡片',
        shotLabel: '分镜画面标识 (例如：Shot 1，人物特写)',
        shotCue: '该镜头的画外音或画面 Prompt 提示词...',
        buttonAddTimeline: '添加到分镜时间轴',
        timelineTitle: '时间轴分镜排序',
        timelineEmpty: '当前项目尚未添加分镜卡片。请在左侧配置并添加到时间轴。',
        shotActions: {
          linkAsset: '关联媒体',
          clearAsset: '解绑',
          saveShot: '保存',
          deleteShot: '移除分镜'
        },
        assetSelectorTitle: '将媒体库资源关联至分镜',
        projectPrefix: '项目',
        noAssetLinked: '未关联媒体。',
        generate: '生成',
        runQuickGenerateTitle: '根据分镜提示词文本快速生成媒体',
        noAssetsAvailable: '没有可用的生成媒体文件。',
        linkButton: '关联',
        linkedPrefix: '已关联',
        defaultVoiceProfile: '默认旁白音色',
        selectVoiceProfile: '选择旁白音色',
        overrideVoiceProfile: '覆盖旁白音色',
        generateVoiceover: '生成旁白',
        buttonGeneratingVoiceover: '生成中...',
        projectVoiceoverSettings: '项目旁白设置'
      },
      exportModal: {
        title: '内容项目生产清单 (Manifest)',
        titlePreview: '内容项目生产清单预览',
        warning: '安全、许可与合规须知',
        warningText: '导出的清单媒体资源及估算资费均来自系统记录。请在生产发布时留意安全过滤与模型许可合规要求。',
        downloadBtn: '下载生产清单 JSON',
        warningsTitle: '安全与验证警告',
        successTitle: '安全与许可合规验证通过',
        successDesc: '凭据泄漏清洗器执行完毕。未在导出的引用中检测到敏感的本地挂载路径或授权 Token。',
        payloadLabel: 'JSON 清单载荷 (仅包含相对路径和安全哈希)'
      }
    },
    history: {
      title: '运行日志',
      filters: {
        allStatuses: '所有状态',
        searchPlaceholder: '搜索输入内容...',
        showOnlyBest: '仅显示最佳案例',
        allLabs: '所有实验台',
        voice: '音频实验台',
        image: '图片实验台',
        video: '视频实验台'
      },
      table: {
        expId: '实验记录 ID',
        type: '调用类型',
        model: '调测模型',
        status: '调用状态',
        latency: '网关延迟',
        time: '创建时间',
        detail: '日志详情',
        empty: '未检索到运行日志记录。',
        titleInput: '标题 / 输入文本',
        tags: '标签 / 标记',
        best: '最佳',
        failCase: '失败案例',
        btnDetails: '详情'
      },
      modal: {
        title: '模型接口调用及评估实验详情',
        tabDetails: '调用信息',
        tabParams: '模型参数',
        tabLogs: '生命周期日志',
        tabOutput: '输出预览',
        labelProvider: '所属服务商',
        labelModel: '模型注册编码',
        labelAdapter: '调用能力适配器',
        labelLatency: '实际网关耗时',
        labelCost: '折算预估资费',
        labelInput: '输入请求内容',
        labelOutput: '输出关联媒体',
        inputTitle: '完整输入 JSON 载荷',
        paramsTitle: '实际生效接口调用参数',
        logsTitle: '异步任务及网关调用链路追踪日志 (Celery Trace Logs)',
        synthesisScriptLabel: '合成文本/提示词:',
        modelConfigLabel: '模型配置:',
        inputParamsLabel: '输入参数 (Params JSON):',
        linkedAssetRef: '关联媒体资源引用',
        fileLabel: '文件名:',
        mimeLabel: 'MIME类型:',
        sizeLabel: '大小:',
        downloadAsset: '下载资源',
        noOutputAsset: '未生成或关联输出资源。该实验可能失败或仍在进行中。',
        loadingLogs: '正在加载调用链日志...',
        noLogs: '未找到该实验运行的执行日志。',
        stepLabel: '步骤:'
      }
    }
  }
};

export const setLocale = (locale) => {
  if (translations[locale]) {
    currentLocale.value = locale;
    localStorage.setItem('aiwm_locale', locale);
  }
};

export const t = (key, variables = {}) => {
  const keys = key.split('.');
  let value = translations[currentLocale.value];
  
  for (const k of keys) {
    if (value && value[k] !== undefined) {
      value = value[k];
    } else {
      // Fallback to English
      value = translations['en'];
      for (const kFallback of keys) {
        if (value && value[kFallback] !== undefined) {
          value = value[kFallback];
        } else {
          return key;
        }
      }
      break;
    }
  }
  
  if (typeof value === 'string') {
    let result = value;
    Object.keys(variables).forEach(v => {
      result = result.replace(new RegExp(`{\\s*${v}\\s*}`, 'g'), variables[v]);
    });
    return result;
  }
  return key;
};
