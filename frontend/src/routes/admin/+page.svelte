<script lang="ts">
	import { onMount } from 'svelte';
	import { getApiBaseUrl, buildApiUrl } from '$lib/config';

	// Admin settings interface
	interface AdminSettings {
		api_key: string;
		models: {
			analysis: string;
			perspective_informative: string;
			perspective_contrarian: string;
			perspective_complementary: string;
			verification: string;
			synthesis: string;
		};
	}

	// OpenRouter model options (Updated January 2025)
	const openRouterModels = [
		// Latest & Most Powerful Models
		'anthropic/claude-opus-4',
		'anthropic/claude-sonnet-4',
		'openai/o3-pro',
		'qwen/qwen3-235b-a22b-thinking-2507',
		'x-ai/grok-4',
		'x-ai/grok-3',
		
		// Google Models
		'google/gemini-2.5-pro',
		'google/gemini-2.5-flash',
		'google/gemini-2.5-flash-lite',
		
		// Mistral Models
		'mistralai/magistral-medium-2506',
		'mistralai/magistral-small-2506',
		'mistralai/devstral-medium',
		'mistralai/devstral-small',
		'mistralai/mistral-small-3.2-24b-instruct',
		
		// DeepSeek R1 Models (Latest Reasoning Models)
		'deepseek/deepseek-r1-0528',
		'deepseek/deepseek-r1-0528-qwen3-8b',
		'deepseek/deepseek-r1-distill-qwen-7b',
		
		// Qwen Models
		'qwen/qwen3-235b-a22b-2507',
		'qwen/qwen3-coder',
		
		// Free Models (Great for testing)
		'qwen/qwen3-235b-a22b-2507:free',
		'qwen/qwen3-coder:free',
		'mistralai/mistral-small-3.2-24b-instruct:free',
		'deepseek/deepseek-r1-0528:free',
		'deepseek/deepseek-r1-0528-qwen3-8b:free',
		'google/gemma-3n-e2b-it:free',
		'tencent/hunyuan-a13b-instruct:free',
		'moonshotai/kimi-k2:free',
		'moonshotai/kimi-dev-72b:free',
		
		// Specialized Models
		'morph/morph-v3-large',
		'morph/morph-v3-fast',
		'minimax/minimax-m1',
		'baidu/ernie-4.5-300b-a47b',
		
		// Legacy Popular Models (Still Available)
		'openchat/openchat-3.5-0106',
		'meta-llama/llama-3-70b-instruct',
		'teknium/openhermes-2.5-mistral-7b'
	];

	let settings: AdminSettings = {
		api_key: '',
		models: {
			analysis: 'qwen/qwen3-coder:free',
			perspective_informative: 'google/gemini-2.5-flash',
			perspective_contrarian: 'deepseek/deepseek-r1-0528:free',
			perspective_complementary: 'mistralai/mistral-small-3.2-24b-instruct:free',
			verification: 'anthropic/claude-sonnet-4',
			synthesis: 'qwen/qwen3-235b-a22b-thinking-2507'
		}
	};

	let loading = false;
	let saveMessage = '';
	
	// Use shared configuration for API URL
	const apiBaseUrl = getApiBaseUrl();

	// Load current settings on component mount
	onMount(async () => {
		await loadSettings();
	});

	async function loadSettings() {
		try {
			const response = await fetch(`${apiBaseUrl}/api/v1/admin/settings`);
			if (response.ok) {
				const data = await response.json();
				settings = { ...settings, ...data };
			}
		} catch (error) {
			console.error('Error loading settings:', error);
		}
	}

	async function saveSettings() {
		loading = true;
		saveMessage = '';
		
		try {
			const response = await fetch(`${apiBaseUrl}/api/v1/admin/settings`, {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json'
				},
				body: JSON.stringify(settings)
			});

			if (response.ok) {
				saveMessage = '✅ Settings saved successfully!';
			} else {
				const error = await response.json();
				saveMessage = `❌ Error: ${error.detail || 'Failed to save settings'}`;
			}
		} catch (error) {
			saveMessage = `❌ Network error: ${error}`;
		} finally {
			loading = false;
			setTimeout(() => saveMessage = '', 3000);
		}
	}

	async function testApiKey() {
		if (!settings.api_key.trim()) {
			saveMessage = '❌ Please enter an API key first';
			return;
		}

		loading = true;
		try {
			const response = await fetch(`${apiBaseUrl}/api/v1/admin/test-api-key`, {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json'
				},
				body: JSON.stringify({ api_key: settings.api_key })
			});

			if (response.ok) {
				if (settings.api_key === '${API_KEY_FROM_ENV}') {
					saveMessage = '✅ Environment API key is valid!';
				} else {
					saveMessage = '✅ API key is valid!';
				}
			} else {
				const error = await response.json();
				saveMessage = `❌ API key test failed: ${error.detail}`;
			}
		} catch (error) {
			saveMessage = `❌ Error testing API key: ${error}`;
		} finally {
			loading = false;
			setTimeout(() => saveMessage = '', 3000);
		}
	}

	function setRecommendedModels() {
		settings.models = {
			analysis: 'qwen/qwen3-coder:free',
			perspective_informative: 'google/gemini-2.5-flash',
			perspective_contrarian: 'deepseek/deepseek-r1-0528:free',
			perspective_complementary: 'mistralai/mistral-small-3.2-24b-instruct:free',
			verification: 'anthropic/claude-sonnet-4',
			synthesis: 'qwen/qwen3-235b-a22b-thinking-2507'
		};
		saveMessage = '✨ Recommended models applied! Don\'t forget to save.';
		setTimeout(() => saveMessage = '', 3000);
	}

	function setEnvApiKey() {
		settings.api_key = '${API_KEY_FROM_ENV}';
		saveMessage = '🔒 Set to use environment variable. Don\'t forget to save.';
		setTimeout(() => saveMessage = '', 3000);
	}
</script>

<main class="admin-panel">
	<nav class="breadcrumb">
		<a href="/" class="back-link">← Back to trippleCheck</a>
	</nav>
	<h1>🔧 Admin Panel</h1>
	<p class="subtitle">Configure LLM models and API settings for trippleCheck</p>

	<div class="update-banner">
		<h3>🚀 Latest Updates (January 2025)</h3>
		<ul>
			<li><strong>New Models:</strong> Claude Opus 4, OpenAI O3 Pro, Qwen3-235B, DeepSeek R1, X.AI Grok 4</li>
			<li><strong>Free Models:</strong> Many high-quality free options now available</li>
			<li><strong>Recommendations:</strong> Optimized default selections for best performance/cost ratio</li>
		</ul>
	</div>

	<div class="settings-container">
		<!-- API Key Section -->
		<section class="setting-section">
			<h2>🔑 OpenRouter API Configuration</h2>
			<div class="form-group">
				<label for="api-key">API Key:</label>
				<div class="api-key-input">
					<input
						id="api-key"
						type="password"
						bind:value={settings.api_key}
						placeholder="Enter your OpenRouter API key or ${'${API_KEY_FROM_ENV}'}"
						class="api-key-field"
					/>
					<button 
						on:click={testApiKey} 
						disabled={loading || !settings.api_key.trim()}
						class="test-btn"
					>
						Test Key
					</button>
				</div>
				<div class="api-key-options">
					<button 
						on:click={setEnvApiKey} 
						class="env-btn"
						type="button"
					>
						🔒 Use Environment Variable
					</button>
					<small class="help-text">
						Get your API key from <a href="https://openrouter.ai/keys" target="_blank">OpenRouter</a> • 
						Or use <code>${'${API_KEY_FROM_ENV}'}</code> to read from environment variables (OPENROUTER_API_KEY or API_KEY)
					</small>
				</div>
			</div>
		</section>

		<!-- Model Configuration Section -->
		<section class="setting-section">
			<h2>🤖 Model Configuration</h2>
			<p class="section-description">
				Configure which OpenRouter models to use for each phase of the AI pipeline. 
				<strong>🆓 = Free models</strong> • <strong>⭐ = Recommended</strong>
			</p>

			<div class="model-grid">
				<div class="model-config">
					<label for="analysis-model">📊 Analysis Phase:</label>
					<select id="analysis-model" bind:value={settings.models.analysis}>
						{#each openRouterModels as model}
							<option value={model}>
								{model}{model.includes(':free') ? ' 🆓' : ''}
								{#if model === 'qwen/qwen3-coder:free'} ⭐ Recommended{/if}
							</option>
						{/each}
					</select>
					<small>Initial query analysis and understanding • Recommended: qwen/qwen3-coder:free</small>
				</div>

				<div class="model-config">
					<label for="informative-model">📚 Informative Perspective:</label>
					<select id="informative-model" bind:value={settings.models.perspective_informative}>
						{#each openRouterModels as model}
							<option value={model}>
								{model}{model.includes(':free') ? ' 🆓' : ''}
								{#if model === 'google/gemini-2.5-flash'} ⭐ Recommended{/if}
							</option>
						{/each}
					</select>
					<small>Factual, educational response • Recommended: google/gemini-2.5-flash</small>
				</div>

				<div class="model-config">
					<label for="contrarian-model">🔍 Contrarian Perspective:</label>
					<select id="contrarian-model" bind:value={settings.models.perspective_contrarian}>
						{#each openRouterModels as model}
							<option value={model}>
								{model}{model.includes(':free') ? ' 🆓' : ''}
								{#if model === 'deepseek/deepseek-r1-0528:free'} ⭐ Recommended{/if}
							</option>
						{/each}
					</select>
					<small>Alternative viewpoints and challenges • Recommended: deepseek/deepseek-r1-0528:free</small>
				</div>

				<div class="model-config">
					<label for="complementary-model">🧩 Complementary Perspective:</label>
					<select id="complementary-model" bind:value={settings.models.perspective_complementary}>
						{#each openRouterModels as model}
							<option value={model}>
								{model}{model.includes(':free') ? ' 🆓' : ''}
								{#if model === 'mistralai/mistral-small-3.2-24b-instruct:free'} ⭐ Recommended{/if}
							</option>
						{/each}
					</select>
					<small>Additional context and connections • Recommended: mistralai/mistral-small-3.2-24b-instruct:free</small>
				</div>

				<div class="model-config">
					<label for="verification-model">✅ Verification Phase:</label>
					<select id="verification-model" bind:value={settings.models.verification}>
						{#each openRouterModels as model}
							<option value={model}>
								{model}{model.includes(':free') ? ' 🆓' : ''}
								{#if model === 'anthropic/claude-sonnet-4'} ⭐ Recommended{/if}
							</option>
						{/each}
					</select>
					<small>Quality check and validation • Recommended: anthropic/claude-sonnet-4</small>
				</div>

				<div class="model-config">
					<label for="synthesis-model">🎯 Synthesis Phase:</label>
					<select id="synthesis-model" bind:value={settings.models.synthesis}>
						{#each openRouterModels as model}
							<option value={model}>
								{model}{model.includes(':free') ? ' 🆓' : ''}
								{#if model === 'qwen/qwen3-235b-a22b-thinking-2507'} ⭐ Recommended{/if}
							</option>
						{/each}
					</select>
					<small>Final answer compilation • Recommended: qwen/qwen3-235b-a22b-thinking-2507</small>
				</div>
			</div>
		</section>

		<!-- Save Section -->
		<section class="save-section">
			<div class="button-group">
				<button 
					on:click={setRecommendedModels} 
					disabled={loading}
					class="recommend-btn"
				>
					⭐ Set Recommended Models
				</button>
				
				<button 
					on:click={saveSettings} 
					disabled={loading}
					class="save-btn"
				>
					{#if loading}
						💾 Saving...
					{:else}
						💾 Save Configuration
					{/if}
				</button>
			</div>
			
			{#if saveMessage}
				<div class="save-message">{saveMessage}</div>
			{/if}
		</section>
	</div>
</main>

<style>
	.admin-panel {
		max-width: 1000px;
		margin: 0 auto;
		padding: 2rem;
		background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
		min-height: 100vh;
		color: white;
	}

	.breadcrumb {
		margin-bottom: 1.5rem;
	}

	.back-link {
		color: #87CEEB;
		text-decoration: none;
		font-size: 1rem;
		display: inline-flex;
		align-items: center;
		gap: 0.5rem;
		padding: 0.5rem 1rem;
		background: rgba(255, 255, 255, 0.1);
		border-radius: 10px;
		transition: all 0.3s ease;
		border: 1px solid rgba(255, 255, 255, 0.2);
	}

	.back-link:hover {
		background: rgba(255, 255, 255, 0.2);
		transform: translateY(-2px);
		box-shadow: 0 4px 15px rgba(0,0,0,0.2);
	}

	h1 {
		font-size: 3rem;
		margin-bottom: 0.5rem;
		text-align: center;
		text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
	}

	.subtitle {
		text-align: center;
		font-size: 1.2rem;
		margin-bottom: 1.5rem;
		opacity: 0.9;
	}

	.update-banner {
		background: linear-gradient(45deg, #FF6B6B, #4ECDC4);
		border-radius: 15px;
		padding: 1.5rem;
		margin-bottom: 2rem;
		color: white;
		box-shadow: 0 4px 15px rgba(0,0,0,0.2);
	}

	.update-banner h3 {
		margin: 0 0 1rem 0;
		font-size: 1.3rem;
		font-weight: bold;
	}

	.update-banner ul {
		margin: 0;
		padding-left: 1.5rem;
		list-style-type: disc;
	}

	.update-banner li {
		margin-bottom: 0.5rem;
		line-height: 1.4;
	}

	.update-banner strong {
		font-weight: bold;
	}

	.settings-container {
		background: rgba(255, 255, 255, 0.1);
		border-radius: 20px;
		padding: 2rem;
		backdrop-filter: blur(10px);
		border: 1px solid rgba(255, 255, 255, 0.2);
		box-shadow: 0 8px 32px rgba(0,0,0,0.1);
	}

	.setting-section {
		margin-bottom: 2.5rem;
		padding-bottom: 2rem;
		border-bottom: 1px solid rgba(255, 255, 255, 0.1);
	}

	.setting-section:last-child {
		border-bottom: none;
		margin-bottom: 0;
	}

	h2 {
		font-size: 1.5rem;
		margin-bottom: 1rem;
		color: #fff;
	}

	.section-description {
		margin-bottom: 1.5rem;
		opacity: 0.8;
		font-size: 1rem;
	}

	.form-group {
		margin-bottom: 1rem;
	}

	.api-key-input {
		display: flex;
		gap: 0.5rem;
		align-items: center;
		margin-bottom: 1rem;
	}

	.api-key-field {
		flex: 1;
		padding: 0.75rem;
		border: none;
		border-radius: 10px;
		background: rgba(255, 255, 255, 0.9);
		color: #333;
		font-size: 1rem;
	}

	.api-key-options {
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
	}

	.env-btn {
		align-self: flex-start;
		padding: 0.5rem 1rem;
		background: #6B73FF;
		color: white;
		border: none;
		border-radius: 8px;
		cursor: pointer;
		font-size: 0.9rem;
		font-weight: bold;
		transition: background-color 0.3s;
	}

	.env-btn:hover {
		background: #5A62E6;
	}

	.test-btn {
		padding: 0.75rem 1.5rem;
		background: #4CAF50;
		color: white;
		border: none;
		border-radius: 10px;
		cursor: pointer;
		font-weight: bold;
		transition: background-color 0.3s;
	}

	.test-btn:hover:not(:disabled) {
		background: #45a049;
	}

	.test-btn:disabled {
		background: #cccccc;
		cursor: not-allowed;
	}

	.help-text {
		display: block;
		margin-top: 0.5rem;
		opacity: 0.7;
		font-size: 0.9rem;
	}

	.help-text a {
		color: #87CEEB;
		text-decoration: none;
	}

	.help-text a:hover {
		text-decoration: underline;
	}

	.help-text code {
		background: rgba(255, 255, 255, 0.2);
		padding: 0.2rem 0.4rem;
		border-radius: 4px;
		font-family: 'Courier New', monospace;
		font-size: 0.85rem;
		color: #FFD700;
	}

	.model-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
		gap: 1.5rem;
	}

	.model-config {
		background: rgba(255, 255, 255, 0.05);
		padding: 1.5rem;
		border-radius: 15px;
		border: 1px solid rgba(255, 255, 255, 0.1);
	}

	.model-config label {
		display: block;
		font-weight: bold;
		margin-bottom: 0.5rem;
		font-size: 1.1rem;
	}

	.model-config select {
		width: 100%;
		padding: 0.75rem;
		border: none;
		border-radius: 10px;
		background: rgba(255, 255, 255, 0.9);
		color: #333;
		font-size: 1rem;
		margin-bottom: 0.5rem;
	}

	.model-config small {
		display: block;
		opacity: 0.7;
		font-size: 0.9rem;
		font-style: italic;
	}

	.save-section {
		text-align: center;
		padding-top: 1rem;
	}

	.button-group {
		display: flex;
		gap: 1rem;
		justify-content: center;
		flex-wrap: wrap;
	}

	.save-btn {
		padding: 1rem 2rem;
		background: linear-gradient(45deg, #FF6B6B, #4ECDC4);
		color: white;
		border: none;
		border-radius: 15px;
		font-size: 1.1rem;
		font-weight: bold;
		cursor: pointer;
		transition: transform 0.3s, box-shadow 0.3s;
		box-shadow: 0 4px 15px rgba(0,0,0,0.2);
	}

	.recommend-btn {
		padding: 1rem 2rem;
		background: linear-gradient(45deg, #FFD700, #FFA500);
		color: #333;
		border: none;
		border-radius: 15px;
		font-size: 1.1rem;
		font-weight: bold;
		cursor: pointer;
		transition: transform 0.3s, box-shadow 0.3s;
		box-shadow: 0 4px 15px rgba(255, 215, 0, 0.3);
	}

	.save-btn:hover:not(:disabled) {
		transform: translateY(-2px);
		box-shadow: 0 6px 20px rgba(0,0,0,0.3);
	}

	.recommend-btn:hover:not(:disabled) {
		transform: translateY(-2px);
		box-shadow: 0 6px 20px rgba(255, 215, 0, 0.5);
	}

	.save-btn:disabled,
	.recommend-btn:disabled {
		opacity: 0.6;
		cursor: not-allowed;
		transform: none;
	}

	.save-message {
		margin-top: 1rem;
		padding: 0.75rem;
		border-radius: 10px;
		background: rgba(255, 255, 255, 0.1);
		font-weight: bold;
		animation: fadeIn 0.3s ease-in;
	}

	@keyframes fadeIn {
		from { opacity: 0; transform: translateY(-10px); }
		to { opacity: 1; transform: translateY(0); }
	}

	@media (max-width: 768px) {
		.admin-panel {
			padding: 1rem;
		}

		h1 {
			font-size: 2rem;
		}

		.model-grid {
			grid-template-columns: 1fr;
		}

		.api-key-input {
			flex-direction: column;
		}

		.test-btn {
			width: 100%;
		}
	}
</style>