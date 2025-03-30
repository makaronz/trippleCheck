from fastapi import FastAPI
from dotenv import load_dotenv
import os

# Załaduj zmienne środowiskowe z pliku .env
load_dotenv()

# Import routerów (po załadowaniu .env)
from .routers import process, files # Dodano import files

app = FastAPI(
    title="AI Agent - FastAPI Edition",
    description="Przeprojektowana aplikacja AI z asynchronicznym potokiem i wieloma perspektywami.",
    version="1.0.0"
)

# Dołączanie routerów
app.include_router(process.router)
app.include_router(files.router) # Dodano router plików

@app.get("/", tags=["General"])
async def read_root():
    """Podstawowy endpoint sprawdzający działanie aplikacji."""
    return {"message": "Witaj w AI Agent - FastAPI Edition!"}

# Konfiguracja CORS dla frontendu SvelteKit (domyślnie port 5173)
from fastapi.middleware.cors import CORSMiddleware

origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    # Można dodać inne dozwolone źródła, np. adres produkcyjny
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
