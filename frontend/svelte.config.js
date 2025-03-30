import adapter from '@sveltejs/adapter-static'; // Zmieniono import na adapter-static
import { vitePreprocess } from '@sveltejs/vite-plugin-svelte';

/** @type {import('@sveltejs/kit').Config} */
const config = {
	// Consult https://svelte.dev/docs/kit/integrations
	// for more information about preprocessors
	preprocess: vitePreprocess(),

	kit: {
		// adapter-auto only supports some environments, see https://kit.svelte.dev/docs/adapter-auto for a list.
		// If your environment is not supported or you settled on a specific environment, switch out the adapter.
		// See https://kit.svelte.dev/docs/adapters for more information about adapters.
		adapter: adapter({
			// Opcje dla adapter-static
			// Domyślnie buduje do katalogu 'build'
			// pages: 'build',
			// assets: 'build',
			fallback: 'index.html', // Ważne dla SPA, aby serwer zwracał index.html dla nieznanych ścieżek
			precompress: false, // Render obsługuje kompresję, więc nie musimy tego robić tutaj
			strict: true
		})
	}
};

export default config;
