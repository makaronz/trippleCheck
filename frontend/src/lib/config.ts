/**
 * Configuration utilities for the trippleCheck frontend
 */

/**
 * Get the API base URL based on environment and deployment configuration
 * @returns The base URL for API calls
 */
export function getApiBaseUrl(): string {
    // In production, use relative URLs if frontend and backend are on the same domain
    const useRelativeUrls = !import.meta.env.DEV;
    
    if (useRelativeUrls) {
        console.log('Using relative URLs for API calls (production mode)');
        return '';
    }
    
    // Development configuration - check multiple environment variable names for flexibility
    const envVars = {
        VITE_FASTAPI_URL: import.meta.env.VITE_FASTAPI_URL,
        VITE_API_BASE_URL: import.meta.env.VITE_API_BASE_URL,
        VITE_BACKEND_URL: import.meta.env.VITE_BACKEND_URL,
    };
    
    const apiUrl = envVars.VITE_FASTAPI_URL || 
                   envVars.VITE_API_BASE_URL || 
                   envVars.VITE_BACKEND_URL || 
                   'http://127.0.0.1:8000';
    
    // Log configuration for debugging
    if (import.meta.env.DEV) {
        console.log('API Configuration:', {
            selectedUrl: apiUrl,
            availableEnvVars: envVars,
            usingFallback: !Object.values(envVars).some(v => v)
        });
    }
    
    return apiUrl;
}

/**
 * Environment configuration object
 */
export const config = {
    apiBaseUrl: getApiBaseUrl(),
    isDevelopment: import.meta.env.DEV,
    isProduction: !import.meta.env.DEV,
} as const;

/**
 * Build a full API URL
 * @param endpoint - The API endpoint (should start with /)
 * @returns The full URL for the API call
 */
export function buildApiUrl(endpoint: string): string {
    const baseUrl = getApiBaseUrl();
    
    // Ensure endpoint starts with /
    if (!endpoint.startsWith('/')) {
        endpoint = '/' + endpoint;
    }
    
    return baseUrl + endpoint;
}