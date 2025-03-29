# -*- coding: utf-8 -*-
from app import create_app

# Tworzymy instancję aplikacji za pomocą fabryki
app = create_app()

if __name__ == '__main__':
    # Uruchomienie serwera Flask
    # Użyj host='0.0.0.0' jeśli chcesz udostępnić w sieci lokalnej
    # debug=True jest przydatne podczas rozwoju, ale powinno być False w produkcji
    print("\nUruchamianie serwera Flask na http://127.0.0.1:5000")
    print("Naciśnij CTRL+C aby zatrzymać serwer.")
    app.run(debug=True, host='0.0.0.0', port=5000)
