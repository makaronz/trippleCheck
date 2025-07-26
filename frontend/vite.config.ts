import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';

export default defineConfig({
	plugins: [sveltekit()],
	
	// Build configuration
	build: {
		target: 'es2020',
		outDir: 'build',
		assetsDir: 'assets',
		sourcemap: true,
		minify: 'esbuild',  // Use esbuild instead of terser for faster builds
		rollupOptions: {
			output: {
				// Chunking strategy for better caching
				manualChunks: {
					vendor: ['svelte']
				}
			}
		}
	},
	
	// Development server configuration
	server: {
		port: 5173,
		host: true,
		proxy: {
			'/api': {
				target: 'http://127.0.0.1:8000',
				changeOrigin: true,
				secure: false
			}
		}
	},
	
	// Preview server configuration
	preview: {
		port: 4173,
		host: true
	},
	
	// Optimization
	optimizeDeps: {
		include: ['svelte']
	}
});
