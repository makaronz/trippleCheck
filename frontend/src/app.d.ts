// See https://svelte.dev/docs/kit/types#app.d.ts
// for information about these interfaces
declare global {
	namespace App {
		// interface Error {}
		// interface Locals {}
		// interface PageData {}
		// interface PageState {}
		// interface Platform {}
	}

	// Environment variables interface for better type safety
	interface ImportMetaEnv {
		readonly VITE_FASTAPI_URL?: string;
		readonly VITE_API_BASE_URL?: string;
		readonly VITE_BACKEND_URL?: string;
		readonly DEV: boolean;
		readonly PROD: boolean;
	}

	interface ImportMeta {
		readonly env: ImportMetaEnv;
	}
}

export {};
