let processedFiles = []; // Przechowuje przetworzone dane plików { name: string, content: string, size: number }

// --- Obsługa Plików ---
async function handleFileUpload() {
    const fileInput = document.getElementById('documentUpload');
    const files = fileInput.files;
    const filesListDiv = document.getElementById('filesList');
    const uploadButton = fileInput.nextElementSibling; // Przycisk 'Przetwórz'

    if (files.length === 0) {
        displayError('Nie wybrano żadnych plików.');
        return;
    }
    if (files.length > 4) {
        displayError('Można załadować maksymalnie 4 pliki.');
        return;
    }

    processedFiles = []; // Resetuj listę przy nowym ładowaniu
    filesListDiv.innerHTML = ''; // Wyczyść poprzednie wpisy
    uploadButton.disabled = true;
    clearError();

    let processingPromises = [];
    // Stwórz wpisy w UI od razu, aby pokazać postęp
    for (let i = 0; i < files.length; i++) {
        const file = files[i];
        const fileEntry = document.createElement('div');
        fileEntry.id = `file-entry-${i}`;
        fileEntry.className = 'file-entry';
        fileEntry.innerHTML = `<span>${i + 1}. ${file.name} (${formatFileSize(file.size)})</span> <span class="status">⏳ Przetwarzanie...</span>`;
        filesListDiv.appendChild(fileEntry);
        processingPromises.push(processSingleFile(file, i));
    }

    try {
        // Czekaj na przetworzenie wszystkich plików
        const results = await Promise.all(processingPromises);
        processedFiles = results.filter(r => r !== null); // Odfiltruj błędy

        // Aktualizuj statusy w UI po zakończeniu wszystkich
        results.forEach((result, index) => {
            const fileEntry = document.getElementById(`file-entry-${index}`);
            if (fileEntry) {
                const statusSpan = fileEntry.querySelector('.status');
                if (result) {
                    statusSpan.innerHTML = '<span style="color: green;">✔ Gotowy</span>';
                } else {
                    // Błąd został już obsłużony w processSingleFile
                    if (statusSpan && !statusSpan.innerHTML.includes('Błąd')) {
                        statusSpan.innerHTML = '<span style="color: red;">✖ Błąd</span>';
                    }
                }
            }
        });

        if (processedFiles.length === 0 && files.length > 0) {
            // Opcjonalnie: Pokaż ogólny błąd, jeśli żaden plik się nie powiódł
            // displayError('Wystąpiły błędy podczas przetwarzania wszystkich plików.');
        }

    } catch (error) {
        // Ogólny błąd jeśli Promise.all zawiedzie (mało prawdopodobne)
        console.error("Błąd podczas grupowego przetwarzania plików:", error);
        displayError("Wystąpił nieoczekiwany błąd podczas przetwarzania plików.");
        filesListDiv.innerHTML = '<em style="color:red;">Nie udało się przetworzyć plików.</em>';
    } finally {
        uploadButton.disabled = false;
        // Wyczyść input, aby można było wybrać te same pliki ponownie
        // fileInput.value = null; // Może być irytujące, jeśli użytkownik chce dodać więcej
    }
}

// Przetwarza JEDEN plik i wysyła go na serwer
async function processSingleFile(file, index) {
    const fileEntry = document.getElementById(`file-entry-${index}`);
    const statusSpan = fileEntry ? fileEntry.querySelector('.status') : null;

    return new Promise((resolve) => {
        const reader = new FileReader();
        reader.onload = async (event) => {
            try {
                const base64Data = event.target.result.split(',')[1]; // Pobierz dane base64
                const response = await fetch('/process_file', { // Używamy względnej ścieżki
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        filename: file.name,
                        file_data_base64: base64Data
                    })
                });

                if (!response.ok) {
                    let errorMsg = `Błąd serwera ${response.status}`;
                    try {
                        const errorData = await response.json();
                        errorMsg = errorData.error || errorMsg;
                    } catch (e) { /* Ignoruj błąd parsowania JSON błędu */ }
                    throw new Error(errorMsg);
                }

                const result = await response.json();
                resolve({
                    name: file.name,
                    content: result.content, // Przetworzony tekst z serwera
                    size: file.size
                });

            } catch (error) {
                console.error(`Błąd przetwarzania pliku ${file.name}:`, error);
                if (statusSpan) {
                    statusSpan.innerHTML = `<span style="color: red;">✖ Błąd: ${error.message}</span>`;
                }
                resolve(null); // Zwróć null w przypadku błędu
            }
        };
        reader.onerror = () => {
            const errorMsg = `Nie udało się odczytać pliku ${file.name}`;
            console.error(errorMsg);
            if (statusSpan) {
                statusSpan.innerHTML = `<span style="color: red;">✖ Błąd: ${errorMsg}</span>`;
            }
            resolve(null); // Zwróć null
        };
        reader.readAsDataURL(file); // Odczytaj plik jako Data URL (zawiera base64)
    });
}


// --- Wysyłanie Zapytania ---
async function sendQuery() {
    const queryInput = document.getElementById('queryInput');
    const query = queryInput.value.trim();
    const loadingIndicator = document.getElementById('loadingIndicator');
    const loadingStatus = document.getElementById('loadingStatus');
    const responseContainer = document.getElementById('responseContainer');
    const pipelineStepsDiv = document.getElementById('pipelineSteps');
    const finalResponseDiv = document.getElementById('finalResponse');
    const finalResponseCard = document.getElementById('finalResponseCard');
    const sendButton = queryInput.nextElementSibling; // Przycisk 'Wyślij'

    if (!query) {
        displayError('Wprowadź zapytanie lub polecenie!');
        return;
    }

    // Pokaż ładowanie, ukryj stare wyniki i błędy
    loadingIndicator.style.display = 'block';
    loadingStatus.textContent = 'Inicjalizacja agenta...';
    responseContainer.style.display = 'none';
    pipelineStepsDiv.innerHTML = ''; // Wyczyść poprzednie kroki
    finalResponseDiv.innerHTML = '';
    clearError();
    sendButton.disabled = true; // Wyłącz przycisk podczas przetwarzania

    try {
        loadingStatus.textContent = 'Wysyłanie zapytania do serwera...';
        const response = await fetch('/process_query', { // Używamy względnej ścieżki
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                query: query,
                documents: processedFiles // Wyślij pełne przetworzone dane na serwer
            })
        });

        loadingStatus.textContent = 'Oczekiwanie na odpowiedź serwera...';

        if (!response.ok) {
            let errorMsg = `Błąd serwera: ${response.status}`;
             try {
                 const errorData = await response.json();
                 errorMsg = errorData.error || errorMsg;
             } catch(e) { /* Ignoruj błąd parsowania JSON błędu */ }
             throw new Error(errorMsg);
        }

        loadingStatus.textContent = 'Przetwarzanie odpowiedzi...';
        const result = await response.json();

         // Dynamiczne renderowanie kroków pipeline
         pipelineStepsDiv.innerHTML = ''; // Wyczyść na wszelki wypadek

         if (result.analysis) {
             addPipelineStep('Analiza Zapytania', result.analysis, true); // True dla formatowania JSON
         }
          if (result.perspectives && Array.isArray(result.perspectives)) {
             result.perspectives.forEach((p, index) => {
                const isErrorResponse = p.response && p.response.startsWith("BŁĄD:");
                addPipelineStep(`Perspektywa ${index + 1} (${p.model})`, p.response, false, isErrorResponse);
             });
         }
         if (result.verification) {
             addPipelineStep('Weryfikacja Odpowiedzi', result.verification);
         }

         // Renderowanie odpowiedzi końcowej z użyciem Marked.js
         if (result.final_response) {
            finalResponseDiv.innerHTML = marked.parse(result.final_response);
            finalResponseCard.style.display = 'block';
         } else {
             finalResponseCard.style.display = 'none';
         }

         responseContainer.style.display = 'block';

    } catch (error) {
        console.error('Błąd podczas przetwarzania zapytania:', error);
        displayError(`Wystąpił błąd: ${error.message}`);
    } finally {
        loadingIndicator.style.display = 'none'; // Ukryj ładowanie
        sendButton.disabled = false; // Włącz przycisk z powrotem
    }
}

// --- Funkcje Pom
