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
        // Sprawdź rozszerzenie pliku PRZED dodaniem do przetwarzania
        if (file.name.toLowerCase().endsWith('.pdf')) {
            // Sprawdź rozmiar pliku PDF
            if (file.size > 10 * 1024 * 1024) { // 10MB w bajtach
                fileEntry.innerHTML = `<span>${i + 1}. ${file.name} (${formatFileSize(file.size)})</span> <span class="status" style="color: red;">✖ PDF zbyt duży (maks. 10MB)</span>`;
                filesListDiv.appendChild(fileEntry);
                // Nie dodawaj do processingPromises, ale dodaj null, aby zachować indeksowanie
                processingPromises.push(Promise.resolve(null));
            } else {
                fileEntry.innerHTML = `<span>${i + 1}. ${file.name} (${formatFileSize(file.size)})</span> <span class="status">⏳ Przetwarzanie...</span>`;
                filesListDiv.appendChild(fileEntry);
                processingPromises.push(processSingleFile(file, i));
            }
        } else {
            fileEntry.innerHTML = `<span>${i + 1}. ${file.name} (${formatFileSize(file.size)})</span> <span class="status">⏳ Przetwarzanie...</span>`;
            filesListDiv.appendChild(fileEntry);
            processingPromises.push(processSingleFile(file, i));
        }
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
    const apiKeyInput = document.getElementById('apiKeyInput'); // Pobierz pole klucza API
    const apiKey = apiKeyInput.value.trim(); // Pobierz wartość klucza API
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
    // Sprawdź, czy klucz API został wprowadzony
    if (!apiKey) {
        displayError('Wprowadź klucz API OpenRouter!');
        apiKeyInput.focus(); // Ustaw fokus na polu klucza
        return;
    }

    // Pokaż ładowanie, ukryj stare wyniki i błędy
    loadingIndicator.style.display = 'block';
    responseContainer.style.display = 'block'; // Pokaż kontener odpowiedzi od razu
    pipelineStepsDiv.innerHTML = ''; // Wyczyść poprzednie kroki
    finalResponseDiv.innerHTML = '';
    finalResponseCard.style.display = 'none'; // Ukryj kartę odpowiedzi końcowej
    clearError();
    sendButton.disabled = true; // Wyłącz przycisk podczas przetwarzania

    // Dodaj sekcję postępu całkowitego
    const progressSection = document.createElement('div');
    progressSection.className = 'progress-section';
    progressSection.innerHTML = `
        <div class="progress-header pixel-text">Postęp całkowity</div>
        <div class="progress-bar-container">
            <div class="progress-bar" id="totalProgressBar" style="width: 0%"></div>
        </div>
        <div class="progress-percentage pixel-text" id="totalProgressPercentage">0%</div>
    `;
    pipelineStepsDiv.appendChild(progressSection);

    // Dodaj sekcje dla każdego kroku
    const analysisSection = createStepSection('Krok 1: Analiza zapytania', 'analysisStep');
    const perspectivesSection = createStepSection('Krok 2: Generowanie perspektyw', 'perspectivesStep');
    const verificationSection = createStepSection('Krok 3: Weryfikacja odpowiedzi', 'verificationStep');
    const synthesisSection = createStepSection('Krok 4: Synteza końcowa', 'synthesisStep');
    
    pipelineStepsDiv.appendChild(analysisSection);
    pipelineStepsDiv.appendChild(perspectivesSection);
    pipelineStepsDiv.appendChild(verificationSection);
    pipelineStepsDiv.appendChild(synthesisSection);

    // Aktualizuj postęp całkowity
    updateTotalProgress(0);
    
    try {
        // Krok 1: Analiza zapytania (25% całości)
        updateStepStatus('analysisStep', 'W trakcie...', 0);
        loadingStatus.textContent = 'Krok 1/4: Analiza zapytania...';
        
        const response = await fetch('/process_query', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                query: query,
                documents: processedFiles,
                api_key: apiKey,
                stream_updates: true // Dodatkowy parametr informujący serwer o chęci otrzymywania aktualizacji
            })
        });

        if (!response.ok) {
            let errorMsg = `Błąd serwera: ${response.status}`;
            try {
                const errorData = await response.json();
                errorMsg = errorData.error || errorMsg;
            } catch(e) { /* Ignoruj błąd parsowania JSON błędu */ }
            throw new Error(errorMsg);
        }

        const result = await response.json();

        // Aktualizuj sekcję analizy
        if (result.analysis) {
            updateStepStatus('analysisStep', 'Zakończono', 100);
            
            // Dodaj szczegóły analizy
            const analysisDetails = document.createElement('div');
            analysisDetails.className = 'step-details';
            
            // Dodaj informacje o modelu
            const modelInfo = document.createElement('div');
            modelInfo.className = 'model-info pixel-text';
            modelInfo.innerHTML = `Model: ${result.analysis_model || 'mistralai/mistral-7b-instruct'}`;
            analysisDetails.appendChild(modelInfo);
            
            // Dodaj prompt
            const promptInfo = document.createElement('div');
            promptInfo.className = 'prompt-info';
            promptInfo.innerHTML = `<div class="prompt-header pixel-text">Prompt:</div>
                                   <pre class="prompt-content">${escapeHtml(result.analysis_prompt || 'Prompt niedostępny')}</pre>`;
            analysisDetails.appendChild(promptInfo);
            
            // Dodaj wynik analizy
            try {
                const jsonObj = JSON.parse(result.analysis);
                analysisDetails.innerHTML += `<div class="result-header pixel-text">Wynik analizy:</div>
                                            <pre class="json-content">${JSON.stringify(jsonObj, null, 2)}</pre>`;
            } catch (e) {
                analysisDetails.innerHTML += `<div class="result-header pixel-text">Wynik analizy:</div>
                                            <pre class="result-content">${escapeHtml(result.analysis)}</pre>`;
            }
            
            document.getElementById('analysisStep').appendChild(analysisDetails);
            updateTotalProgress(25);
        }

        // Krok 2: Generowanie perspektyw (25% całości)
        updateStepStatus('perspectivesStep', 'W trakcie...', 0);
        loadingStatus.textContent = 'Krok 2/4: Generowanie perspektyw...';
        
        if (result.perspectives && Array.isArray(result.perspectives)) {
            const totalPerspectives = result.perspectives.length;
            let completedPerspectives = 0;
            
            // Dodaj kontener na perspektywy
            const perspectivesContainer = document.createElement('div');
            perspectivesContainer.className = 'perspectives-container';
            document.getElementById('perspectivesStep').appendChild(perspectivesContainer);
            
            // Dodaj każdą perspektywę
            result.perspectives.forEach((p, index) => {
                const isErrorResponse = p.response && p.response.startsWith("BŁĄD:");
                const perspectiveDiv = document.createElement('div');
                perspectiveDiv.className = 'perspective-item';
                perspectiveDiv.innerHTML = `
                    <div class="perspective-header pixel-text">Perspektywa ${index + 1}: ${p.model}</div>
                    <div class="model-info">Specjalizacja: ${p.specialization || 'Brak'}</div>
                    <div class="prompt-info">
                        <div class="prompt-header pixel-text">Prompt:</div>
                        <pre class="prompt-content">${escapeHtml(p.prompt || 'Prompt niedostępny')}</pre>
                    </div>
                    <div class="result-header pixel-text">Odpowiedź:</div>
                    <div class="perspective-content ${isErrorResponse ? 'error-content' : ''}">
                        ${isErrorResponse ? escapeHtml(p.response) : marked.parse(p.response)}
                    </div>
                `;
                perspectivesContainer.appendChild(perspectiveDiv);
                
                // Aktualizuj postęp perspektyw
                completedPerspectives++;
                const perspectiveProgress = Math.round((completedPerspectives / totalPerspectives) * 100);
                updateStepStatus('perspectivesStep', `Generowanie ${completedPerspectives}/${totalPerspectives}`, perspectiveProgress);
            });
            
            updateStepStatus('perspectivesStep', 'Zakończono', 100);
            updateTotalProgress(50);
        }

        // Krok 3: Weryfikacja (25% całości)
        updateStepStatus('verificationStep', 'W trakcie...', 0);
        loadingStatus.textContent = 'Krok 3/4: Weryfikacja odpowiedzi...';
        
        if (result.verification) {
            // Dodaj szczegóły weryfikacji
            const verificationDetails = document.createElement('div');
            verificationDetails.className = 'step-details';
            
            // Dodaj informacje o modelu
            const modelInfo = document.createElement('div');
            modelInfo.className = 'model-info pixel-text';
            modelInfo.innerHTML = `Model: ${result.verification_model || 'nousresearch/nous-hermes-2-mixtral-8x7b-dpo'}`;
            verificationDetails.appendChild(modelInfo);
            
            // Dodaj prompt
            const promptInfo = document.createElement('div');
            promptInfo.className = 'prompt-info';
            promptInfo.innerHTML = `<div class="prompt-header pixel-text">Prompt:</div>
                                   <pre class="prompt-content">${escapeHtml(result.verification_prompt || 'Prompt niedostępny')}</pre>`;
            verificationDetails.appendChild(promptInfo);
            
            // Dodaj wynik weryfikacji
            const verificationContent = document.createElement('div');
            verificationContent.className = 'verification-content';
            verificationContent.innerHTML = `<div class="result-header pixel-text">Raport weryfikacji:</div>
                                           <div class="markdown-content">${marked.parse(result.verification)}</div>`;
            verificationDetails.appendChild(verificationContent);
            
            document.getElementById('verificationStep').appendChild(verificationDetails);
            updateStepStatus('verificationStep', 'Zakończono', 100);
            updateTotalProgress(75);
        }

        // Krok 4: Synteza (25% całości)
        updateStepStatus('synthesisStep', 'W trakcie...', 0);
        loadingStatus.textContent = 'Krok 4/4: Synteza końcowa...';
        
        if (result.final_response) {
            // Dodaj szczegóły syntezy
            const synthesisDetails = document.createElement('div');
            synthesisDetails.className = 'step-details';
            
            // Dodaj informacje o modelu
            const modelInfo = document.createElement('div');
            modelInfo.className = 'model-info pixel-text';
            modelInfo.innerHTML = `Model: ${result.synthesis_model || 'nousresearch/nous-hermes-2-mixtral-8x7b-dpo'}`;
            synthesisDetails.appendChild(modelInfo);
            
            // Dodaj prompt
            const promptInfo = document.createElement('div');
            promptInfo.className = 'prompt-info';
            promptInfo.innerHTML = `<div class="prompt-header pixel-text">Prompt:</div>
                                   <pre class="prompt-content">${escapeHtml(result.synthesis_prompt || 'Prompt niedostępny')}</pre>`;
            synthesisDetails.appendChild(promptInfo);
            
            document.getElementById('synthesisStep').appendChild(synthesisDetails);
            
            // Renderowanie odpowiedzi końcowej
            finalResponseDiv.innerHTML = marked.parse(result.final_response);
            finalResponseCard.style.display = 'block';
            
            updateStepStatus('synthesisStep', 'Zakończono', 100);
            updateTotalProgress(100);
        }

        loadingStatus.textContent = 'Przetwarzanie zakończone!';

    } catch (error) {
        console.error('Błąd podczas przetwarzania zapytania:', error);
        displayError(`Wystąpił błąd: ${error.message}`);
    } finally {
        loadingIndicator.style.display = 'none'; // Ukryj ładowanie
        sendButton.disabled = false; // Włącz przycisk z powrotem
    }
}

// --- Funkcje pomocnicze dla nowego interfejsu ---

// Tworzy sekcję dla kroku przetwarzania
function createStepSection(title, id) {
    const section = document.createElement('div');
    section.className = 'processing-step';
    section.id = id;
    
    const header = document.createElement('div');
    header.className = 'step-header';
    
    const titleDiv = document.createElement('div');
    titleDiv.className = 'step-title pixel-text';
    titleDiv.textContent = title;
    
    const statusDiv = document.createElement('div');
    statusDiv.className = 'step-status';
    statusDiv.id = `${id}-status`;
    statusDiv.textContent = 'Oczekiwanie...';
    
    const progressContainer = document.createElement('div');
    progressContainer.className = 'progress-bar-container';
    
    const progressBar = document.createElement('div');
    progressBar.className = 'progress-bar';
    progressBar.id = `${id}-progress`;
    progressBar.style.width = '0%';
    
    const progressPercentage = document.createElement('div');
    progressPercentage.className = 'progress-percentage pixel-text';
    progressPercentage.id = `${id}-percentage`;
    progressPercentage.textContent = '0%';
    
    progressContainer.appendChild(progressBar);
    header.appendChild(titleDiv);
    header.appendChild(statusDiv);
    
    section.appendChild(header);
    section.appendChild(progressContainer);
    section.appendChild(progressPercentage);
    
    return section;
}

// Aktualizuje status i postęp kroku
function updateStepStatus(stepId, status, progressPercentage) {
    const statusElement = document.getElementById(`${stepId}-status`);
    const progressBar = document.getElementById(`${stepId}-progress`);
    const percentageElement = document.getElementById(`${stepId}-percentage`);
    
    if (statusElement) statusElement.textContent = status;
    if (progressBar) progressBar.style.width = `${progressPercentage}%`;
    if (percentageElement) percentageElement.textContent = `${progressPercentage}%`;
}

// Aktualizuje całkowity postęp
function updateTotalProgress(percentage) {
    const totalProgressBar = document.getElementById('totalProgressBar');
    const totalProgressPercentage = document.getElementById('totalProgressPercentage');
    
    if (totalProgressBar) totalProgressBar.style.width = `${percentage}%`;
    if (totalProgressPercentage) totalProgressPercentage.textContent = `${percentage}%`;
}

// --- Funkcje pomocnicze UI ---

// Dodaje krok pipeline do UI (stara metoda, zachowana dla kompatybilności)
function addPipelineStep(title, content, isJson = false, isError = false) {
     const pipelineStepsDiv = document.getElementById('pipelineSteps');
     const stepDiv = document.createElement('div');
     stepDiv.className = 'module-response';
     if (isError) {
         stepDiv.style.borderColor = '#dc3545';
     }

     const header = document.createElement('div');
     header.className = 'response-header';
     header.textContent = title;
     if (isError) {
         header.style.color = '#dc3545';
     }

     const contentDiv = document.createElement('div');
     contentDiv.className = 'response-content';
     if (isJson) {
         try {
             const jsonObj = JSON.parse(content);
             contentDiv.innerHTML = `<pre><code>${JSON.stringify(jsonObj, null, 2)}</code></pre>`;
         } catch (e) {
              // Jeśli to nie JSON, wyświetl jako tekst w pre
              contentDiv.innerHTML = `<pre><code>${escapeHtml(content)}</code></pre>`;
         }
     } else if (isError) {
         contentDiv.textContent = content;
         contentDiv.style.color = '#dc3545';
     } else {
         try {
            // Użyj marked do parsowania Markdown
            contentDiv.innerHTML = marked.parse(content);
          } catch (e) {
             console.warn("Failed to parse Markdown for step:", title, e);
             contentDiv.textContent = content; // Fallback to plain text
          }
     }

     stepDiv.appendChild(header);
     stepDiv.appendChild(contentDiv);
     pipelineStepsDiv.appendChild(stepDiv);
 }

// Formatowanie rozmiaru pliku
function formatFileSize(bytes) {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
}

// Wyświetlanie błędów
function displayError(message) {
    const errorContainer = document.getElementById('errorContainer');
    const errorMessageDiv = document.getElementById('errorMessage');
    errorMessageDiv.textContent = message;
    errorContainer.style.display = 'block';
}

// Czyszczenie błędów
function clearError() {
    const errorContainer = document.getElementById('errorContainer');
    errorContainer.style.display = 'none';
}

// Prosta funkcja do escape'owania HTML
function escapeHtml(unsafe) {
    if (typeof unsafe !== 'string') {
        return '';
    }
    return unsafe
         .replace(/&/g, "&amp;")
         .replace(/</g, "&lt;")
         .replace(/>/g, "&gt;")
         .replace(/"/g, "&quot;")
         .replace(/'/g, "&#039;");
}

// Inicjalizacja przy ładowaniu strony
document.addEventListener('DOMContentLoaded', () => {
   console.log("Agent AI (JS) gotowy.");
   // Ustaw opcje dla marked
   marked.setOptions({
       gfm: true, // Enable GitHub Flavored Markdown
       breaks: true, // Convert single line breaks to <br>
   });
});
