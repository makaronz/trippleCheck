from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os
from pathlib import Path

# Załaduj zmienne środowiskowe z pliku .env
load_dotenv()

# Import routerów (po załadowaniu .env)
from .routers import process, files # Dodano import files

app = FastAPI(
    title="Pixel Pasta AI Agent",
    description="Przeprojektowana aplikacja AI z asynchronicznym potokiem i wieloma perspektywami.",
    version="1.0.0"
)

# Określ ścieżkę do katalogu ze statycznymi plikami (frontend assets)
static_files_dir = Path(__file__).parent / "static" / "dist"
api_app = FastAPI(title="API")

# Dołączanie routerów do pod-aplikacji API
api_app.include_router(process.router)
api_app.include_router(files.router)

# Dołącz pod-aplikację API pod prefiksem /api/v1
app.mount("/api/v1", api_app)

# Dodaj obsługę plików statycznych, jeśli katalog istnieje
if static_files_dir.exists():
    app.mount("/", StaticFiles(directory=str(static_files_dir), html=True), name="static")

    @app.get("/", include_in_schema=False)
    async def serve_spa():
        """Serwuj główny plik HTML aplikacji SvelteKit (Single Page Application)"""
        index_path = static_files_dir / "index.html"
        if index_path.exists():
            return FileResponse(index_path)
        raise HTTPException(status_code=404, detail="Frontend nie jest dostępny")
else:
    # Fallback, gdy katalog statycznych plików nie istnieje
    @app.get("/", tags=["General"])
    async def read_root():
        """Podstawowy endpoint sprawdzający działanie aplikacji."""
        return {"message": "API działa poprawnie. Frontend nie jest dostępny."}

# Konfiguracja CORS

# Parametry z origins konwertowane są na regex
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://pixel-pasta-ai-app.onrender.com",
    # Dodać inne produkcyjne domeny, jeśli potrzeba
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins, # Pozwól na żądania z tych źródeł
    allow_credentials=True,
    allow_methods=["*"], # Pozwól na wszystkie metody (GET, POST, etc.)
    allow_headers=["*"], # Pozwól na wszystkie nagłówki
)

if __name__ == "__main__":
    # Ten blok zazwyczaj nie jest używany bezpośrednio,
    # aplikację uruchamia się przez Uvicorn z linii komend:
    # uvicorn fastapi_app.app.main:app --reload --host 0.0.0.0 --port 8000
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")
    uvicorn.run(app, host=host, port=port)
