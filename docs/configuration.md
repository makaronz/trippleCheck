# trippleCheck Configuration Guide

## API URL Configuration

The frontend automatically configures the API URL based on the environment:

### Development Mode
In development, the frontend uses environment variables to connect to the backend:

```bash
# Primary environment variable (recommended)
VITE_FASTAPI_URL=http://127.0.0.1:8000

# Alternative names (for compatibility)
VITE_API_BASE_URL=http://127.0.0.1:8000
VITE_BACKEND_URL=http://127.0.0.1:8000
```

### Production Mode
In production, the frontend automatically uses relative URLs, assuming the frontend and backend are served from the same domain.

## Environment Variable Priority

The system checks environment variables in the following order:
1. `VITE_FASTAPI_URL` (primary)
2. `VITE_API_BASE_URL` (alternative)
3. `VITE_BACKEND_URL` (alternative)
4. Fallback: `http://127.0.0.1:8000`

## Configuration Examples

### Local Development
```bash
# .env.local
VITE_FASTAPI_URL=http://localhost:8000
```

### Docker Development
```bash
# .env.local
VITE_FASTAPI_URL=http://backend:8000
```

### Production (Same Domain)
```bash
# No configuration needed - uses relative URLs automatically
```

### Production (Different Domain)
```bash
# .env.production
VITE_FASTAPI_URL=https://api.yourdomain.com
```

### Production (Subdomain)
```bash
# .env.production
VITE_FASTAPI_URL=https://api.yourdomain.com/v1
```

## Debugging Configuration

In development mode, the API configuration is logged to the browser console:

```javascript
API Configuration: {
  selectedUrl: "http://127.0.0.1:8000",
  availableEnvVars: {
    VITE_FASTAPI_URL: "http://127.0.0.1:8000",
    VITE_API_BASE_URL: undefined,
    VITE_BACKEND_URL: undefined
  },
  usingFallback: false
}
```

## Shared Configuration

The configuration is centralized in `src/lib/config.ts` and used consistently across:
- Main application (`src/routes/+page.svelte`)
- Admin panel (`src/routes/admin/+page.svelte`)
- Any future components that need API access

## Benefits

✅ **Environment Aware**: Automatically adapts to development vs production  
✅ **Flexible**: Supports multiple environment variable names  
✅ **Centralized**: Single source of truth for API configuration  
✅ **Debuggable**: Clear logging in development mode  
✅ **Production Ready**: Optimized for various deployment scenarios  

## Troubleshooting

### API calls failing in development
1. Check if backend is running on the configured port
2. Verify environment variable is set correctly
3. Check browser console for configuration logs

### API calls failing in production
1. Ensure frontend and backend are on the same domain for relative URLs
2. If using different domains, set appropriate CORS headers
3. Use absolute URLs via environment variables if needed