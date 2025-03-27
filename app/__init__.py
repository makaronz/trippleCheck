# -*- coding: utf-8 -*-
import os
from flask import Flask
from dotenv import load_dotenv
import pytesseract

# Wczytaj zmienne środowiskowe z pliku .env
load_dotenv()

def create_app():
    """Tworzy i konfiguruje instancję aplikacji Flask."""
    app = Flask(__name__, instance_relative_config=True)

    # --- Konfiguracja Aplikacji ---
    app.config.from_mapping(
        SECRET_KEY=os.getenv('SECRET_KEY', 'dev'), # Klucz sekretny dla sesji itp.
        OPENROUTER_API_KEY=os.getenv('OPENROUTER_API_KEY'),
        MAX_DOCUMENT_CHARS=4000,
        # Opcjonalnie: ścieżka do Tesseract
        TESSERACT_CMD=os.getenv('TESSERACT_CMD', None)
    )

    # Sprawdzenie klucza API przy starcie
    if not app.config['OPENROUTER_API_KEY']:
        raise ValueError("BŁĄD KRYTYCZNY: Brak klucza OPENROUTER_API_KEY w pliku .env lub zmiennych środowiskowych!")

    # Konfiguracja Tesseracta, jeśli podano ścieżkę
    if app.config['TESSERACT_CMD']:
        pytesseract.pytesseract.tesseract_cmd = app.config['TESSERACT_CMD']
        print(f"Ustawiono ścieżkę Tesseracta na: {app.config['TESSERACT_CMD']}")

    # Sprawdzenie dostępności Tesseracta (opcjonalne, ale pomocne)
    try:
        tesseract_version = pytesseract.get_tesseract_version()
        print(f"Tesseract OCR znaleziony (wersja: {tesseract_version}). Przetwarzanie obrazów włączone.")
    except pytesseract.TesseractNotFoundError:
        print("\n" + "="*60)
        print(" OSTRZEŻENIE: Tesseract OCR nie został znaleziony.")
        print(" Funkcjonalność przetwarzania obrazów (JPG, PNG) nie będzie działać.")
        print(" Zainstaluj Tesseract OCR (https://github.com/tesseract-ocr/tesseract)")
        print(" i upewnij się, że jest w PATH systemowym, lub ustaw zmienną")
        print(" TESSERACT_CMD w pliku .env lub zmiennych środowiskowych.")
        print("="*60 + "\n")
    except Exception as e:
         print(f"\nOSTRZEŻENIE: Wystąpił problem przy sprawdzaniu Tesseracta: {e}\n")


    # Rejestracja tras (blueprintów)
    with app.app_context():
        from . import routes
        # Jeśli używasz blueprintów: app.register_blueprint(routes.bp)
        # W tym przypadku, ponieważ routes.py importuje 'app', wystarczy import

    print("Aplikacja Flask utworzona i skonfigurowana.")
    return app
