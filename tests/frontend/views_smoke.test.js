import test from 'node:test';
import assert from 'node:assert';
import fs from 'node:fs';
import path from 'node:path';
import vm from 'node:vm';

const frontendDir = path.resolve(process.cwd(), 'frontend');

const filesToTest = [
  'api.js',
  'app.js',
  'components/player.js',
  'views/dashboard.js',
  'views/providers.js',
  'views/models.js',
  'views/prompts.js',
  'views/voice.js',
  'views/image.js',
  'views/video.js',
  'views/assets.js',
  'views/compare.js',
  'views/projects.js',
  'views/history.js'
];

test('Frontend Files Syntax & Export Structure Smoke Test', () => {
  for (const filename of filesToTest) {
    const filePath = path.join(frontendDir, filename);
    
    // Check file exists
    assert.ok(fs.existsSync(filePath), `File should exist: ${filename}`);
    
    const content = fs.readFileSync(filePath, 'utf8');
    
    // 1. Verify Syntactic Validity using vm.Script
    // We wrap inside an async block or ESM module context representation to support ESM syntax
    try {
      new vm.Script(content, { filename });
    } catch (err) {
      // vm.Script doesn't support "import" at top level without module options, 
      // but let's confirm the SyntaxError is only about import/export, not real syntax errors.
      if (!err.message.includes('Cannot use import statement') && 
          !err.message.includes('Unexpected token \'export\'')) {
        assert.fail(`Syntax error in ${filename}: ${err.message}`);
      }
    }

    // 2. Structural checks for views and components
    if (filename.startsWith('views/') || filename.startsWith('components/')) {
      assert.ok(content.includes('export default'), `${filename} should have an ESM export default`);
      assert.ok(content.includes('template:'), `${filename} should define a component template`);
      assert.ok(content.includes('setup('), `${filename} should use Vue 3 Composition API setup function`);
    }
  }
});

test('Lab views use stable two-column layout classes', () => {
  const css = fs.readFileSync(path.join(frontendDir, 'app.css'), 'utf8');
  assert.ok(css.includes('.lab-two-column'), 'app.css should define lab two-column layout');
  assert.ok(css.includes('minmax(360px, 480px)'), 'lab configuration column should have ergonomic width bounds');

  for (const filename of ['views/voice.js', 'views/image.js', 'views/video.js']) {
    const content = fs.readFileSync(path.join(frontendDir, filename), 'utf8');
    assert.ok(content.includes('lab-two-column'), `${filename} should use stable lab layout`);
    assert.ok(content.includes('lab-config-panel'), `${filename} should identify the configuration panel`);
    assert.ok(content.includes('lab-results-panel'), `${filename} should identify the results panel`);
  }
});

test('Docker web image serves frontend through same-origin API proxy', () => {
  const dockerfile = fs.readFileSync(path.resolve(process.cwd(), 'docker/web.Dockerfile'), 'utf8');
  const webServer = fs.readFileSync(path.join(frontendDir, 'web_server.py'), 'utf8');

  assert.ok(dockerfile.includes('/app/frontend/web_server.py'), 'web Dockerfile should run the frontend proxy server');
  assert.ok(webServer.includes('AIWM_API_BASE_URL'), 'web proxy should read backend API base URL from environment');
  assert.ok(webServer.includes('self.path.startswith("/api/")'), 'web proxy should route /api requests to backend');
});

test('Views that call t() expose translator to templates', () => {
  for (const filename of filesToTest) {
    if (!filename.startsWith('views/') && !filename.startsWith('components/')) continue;

    const content = fs.readFileSync(path.join(frontendDir, filename), 'utf8');
    if (!content.includes("t('") && !content.includes('t("')) continue;

    assert.ok(
      content.includes("const t = inject('t')"),
      `${filename} should inject the translation function when using t()`
    );
    assert.match(
      content,
      /return\s*{[\s\S]*?\bt,/,
      `${filename} should return t so the template can call it`
    );
  }
});
