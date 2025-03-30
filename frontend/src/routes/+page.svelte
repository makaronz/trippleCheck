<script lang="ts">
  import { onMount } from 'svelte';
  import { browser } from '$app/environment'; // Importuj 'browser' do sprawdzania środowiska

  // Usunięto zmienną apiKey
  let query = ''; // Zapytanie użytkownika
  let selectedFiles: FileList | null = null; // Wybrane pliki przez użytkownika
  let processedDocuments: { name: string; content: string; size: number }[] = []; // Przetworzone dokumenty
  let fileProcessingStatus: { [key: string]: string } = {}; // Status przetwarzania plików
  let isLoading = false; // Czy trwa przetwarzanie zapytania AI
  let isProcessingFiles = false; // Czy trwa przetwarzanie plików
  let responseData: any = null; // Odpowiedź z backendu
  let errorMessage = ''; // Komunikat błędu

  // W wersji produkcyjnej używamy względnych ścieżek, ponieważ backend i frontend są na tej samej domenie
  // Dla lokalnego rozwoju można użyć pełnego URL, jeśli frontend i backend działają na różnych portach
  const useRelativeUrls = !import.meta.env.DEV; // W trybie produkcyjnym używaj względnych URL
  const apiBaseUrl = useRelativeUrls ? '' : (import.meta.env.VITE_FASTAPI_URL || 'http://127.0.0.1:8000');
  console.log(`API base URL: ${apiBaseUrl || '(using relative URLs)'}`);

  // Funkcja do odczytu pliku jako base64
  function readFileAsBase64(file: File): Promise<string> {
      return new Promise((resolve, reject) => {
          const reader = new FileReader();
          reader.onload = () => {
              const base64String = (reader.result as string).split(',')[1];
              resolve(base64String);
          };
          reader.onerror = (error) => reject(error);
          reader.readAsDataURL(file);
      });
  }

  // Funkcja do obsługi zmiany plików w inpucie
  function handleFileSelection(event: Event) {
      const input = event.target as HTMLInputElement;
      if (input.files) {
          selectedFiles = input.files;
          processedDocuments = []; // Resetuj przetworzone pliki przy nowym wyborze
          fileProcessingStatus = {}; // Resetuj statusy
          processSelectedFiles(); // Rozpocznij przetwarzanie od razu
      }
  }

  // Funkcja przetwarzająca wybrane pliki
  async function processSelectedFiles() {
      if (!selectedFiles || selectedFiles.length === 0) return;

      isProcessingFiles = true;
      errorMessage = '';
      const filesToProcess = Array.from(selectedFiles); // Konwertuj FileList na Array
      selectedFiles = null; // Wyczyść wybór, aby uniknąć ponownego przetwarzania tych samych plików

      const processingPromises = filesToProcess.map(async (file) => {
          const fileName = file.name;
          fileProcessingStatus = { ...fileProcessingStatus, [fileName]: 'Przetwarzanie...' };
          try {
              const base64Data = await readFileAsBase64(file);
              const response = await fetch(`${apiBaseUrl}/api/v1/process_file`, {
                  method: 'POST',
                  headers: { 'Content-Type': 'application/json' },
                  credentials: 'same-origin', // Pozwól przesyłać ciasteczka przy tym samym pochodzeniu
                  body: JSON.stringify({
                      filename: fileName,
                      file_data_base64: base64Data,
                  }),
              });

              if (!response.ok) {
                  let errorDetail = `Błąd ${response.status}`;
                  try {
                      const errorJson = await response.json();
                      errorDetail = errorJson.detail || errorDetail;
                  } catch (e) { /* ignore */ }
                  throw new Error(errorDetail);
              }

              const result = await response.json();
              fileProcessingStatus = { ...fileProcessingStatus, [fileName]: 'Gotowy ✔' };
              return { name: fileName, content: result.content, size: file.size };

          } catch (error: any) {
              console.error(`Błąd przetwarzania pliku ${fileName}:`, error);
              fileProcessingStatus = { ...fileProcessingStatus, [fileName]: `Błąd: ${error.message}` };
              return null; // Zwróć null w przypadku błędu
          }
      });

      const results = await Promise.all(processingPromises);
      processedDocuments = results.filter(doc => doc !== null) as { name: string; content: string; size: number }[];
      isProcessingFiles = false;
      console.log('Przetworzone dokumenty:', processedDocuments);
  }
  // Usunięto zbędny nawias klamrowy

  // Funkcja wysyłająca zapytanie do backendu
  async function submitQuery() {
    // Usunięto sprawdzanie apiKey
    if (!query.trim()) {
      errorMessage = 'Proszę wprowadzić zapytanie.';
      return;
    }

    isLoading = true;
    errorMessage = '';
    responseData = null;

    // Przygotowanie danych żądania, użyj przetworzonych dokumentów
    // Usunięto api_key z ciała żądania
    const requestBody = {
      query: query,
      documents: processedDocuments, // Przekaż przetworzone dokumenty
    };

    try {
      const response = await fetch(`${apiBaseUrl}/api/v1/process_query`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'same-origin', // Pozwól przesyłać ciasteczka przy tym samym pochodzeniu
        body: JSON.stringify(requestBody),
      });

      if (!response.ok) {
        let errorDetail = `Błąd serwera: ${response.status}`;
        try {
            const errorJson = await response.json();
            errorDetail = errorJson.detail || errorDetail;
        } catch (e) {
            // Ignoruj błąd parsowania JSON błędu
        }
        throw new Error(errorDetail);
      }

      responseData = await response.json();
      console.log('Odpowiedź z backendu:', responseData);

    } catch (error: any) {
      console.error('Błąd podczas wysyłania zapytania:', error);
      errorMessage = `Wystąpił błąd: ${error.message}`;
    } finally {
      isLoading = false;
    }
  }

  // Funkcja do bezpiecznego renderowania Markdown (prosta implementacja)
  // W rzeczywistej aplikacji lepiej użyć biblioteki jak 'marked' lub 'markdown-it'
  // Ta wersja jest bardzo podstawowa i może niepoprawnie renderować złożony Markdown.
  // Poprawiono obsługę tagów HTML - nie escapujemy '<' i '>'.
  function renderMarkdown(markdown: string | undefined | null): string {
      if (!markdown) return '';
      // Proste zastępowanie dla podstawowego formatowania, ale pozwala na HTML
      // UWAGA: To nie jest bezpieczne, jeśli Markdown pochodzi z niezaufanego źródła!
      // W produkcyjnej aplikacji należałoby użyć biblioteki z sanitizacją.
      let html = markdown;
      // Podstawowe formatowanie Markdown na HTML
      html = html.replace(/^## (.*$)/gim, '<h2>$1</h2>'); // Nagłówki H2
      html = html.replace(/^\* \*\*(.*)\*\*:/gim, '<br><strong>$1:</strong>'); // Pogrubione etykiety w listach
      html = html.replace(/^\* (.*$)/gim, '<li>$1</li>'); // Elementy listy
      // Zamień bloki list na <ul> - bardzo uproszczone
      html = html.replace(/(<li>.*<\/li>)/gs, '<ul>$1</ul>');
      html = html.replace(/\n/g, '<br>'); // Nowe linie

      // UWAGA: Bezpieczeństwo! W realnej aplikacji potrzebna sanitizacja!
      return html;
  }

  // Funkcja do pobierania danych jako JSON
  function downloadJson(data: any, filename: string) {
      const jsonStr = JSON.stringify(data, null, 2); // Formatowanie z wcięciami
      const blob = new Blob([jsonStr], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
  }

  function handleExport() {
      if (responseData) {
          const timestamp = new Date().toISOString().replace(/:/g, '-');
          downloadJson(responseData, `ai_agent_results_${timestamp}.json`);
      } else {
          alert('Brak danych do wyeksportowania.');
      }
  }

</script>

<svelte:head>
  <title>Pixel Pasta AI Agent</title>
  <!-- Czcionka Pixel -->
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin=""> <!-- Poprawiono: dodano puste cudzysłowy -->
  <link href="https://fonts.googleapis.com/css2?family=Press+Start+2P&display=swap" rel="stylesheet">
</svelte:head>

<div class="pixel-background">
  <header class="header-banner">
      <h1 class="pixel-title">PIXEL PASTA AI AGENT</h1>
  </header>

  <main class="container">
    <!-- Można tu dodać obrazek robota, jeśli jest dostępny -->
    <!-- <img src="/path/to/robot.png" alt="Pixel Pasta Mascot" class="mascot-image"> -->
    <p class="description">Asystent AI do złożonych zadań. Wprowadź zapytanie i opcjonalnie dodaj pliki jako kontekst.</p>

    <section class="card input-section">
      <h2 class="card-title">Wejście Użytkownika</h2>
    <!-- Usunięto pole na klucz API -->

    <div class="form-group">
        <label for="documents">Załącz dokumenty (opcjonalnie):</label> <!-- Usunięto limit z etykiety -->
        <input type="file" id="documents" on:change={handleFileSelection} multiple accept=".txt,.pdf,.md,.jpg,.jpeg,.png,.gif,.bmp,.tiff" />
         {#if isProcessingFiles}
             <small>Trwa przetwarzanie plików...</small>
         {/if}
         {#if Object.keys(fileProcessingStatus).length > 0}
            <div class="file-status-list">
                <small>Status przetwarzania plików:</small>
                <ul>
                    {#each Object.entries(fileProcessingStatus) as [name, status]}
                        <li>{name}: {status}</li>
                    {/each}
                </ul>
            </div>
         {/if}
    </div>

    <div class="form-group">
      <label for="query">Twoje Zapytanie:</label>
      <textarea id="query" bind:value={query} rows="5" placeholder="Wprowadź swoje pytanie lub polecenie..." required></textarea>
    </div>

    <button on:click={submitQuery} disabled={isLoading}>
      {isLoading ? 'Przetwarzanie...' : 'Wyślij Zapytanie'}
    </button>
  </section>

  {#if errorMessage}
    <div class="error-message">
      <p>Błąd: {errorMessage}</p>
    </div>
  {/if}

  {#if isLoading}
    <div class="loading-indicator">
      <p>⏳ Przetwarzanie zapytania przez potok AI... To może chwilę potrwać.</p>
      <!-- Tutaj można dodać bardziej szczegółowe wskaźniki postępu -->
    </div>
  {/if}

  {#if responseData}
    <section class="card results-section">
      <h2 class="card-title">Wyniki Przetwarzania</h2>

      <!-- Krok 1: Analiza -->
      <div class="result-step">
        <h3>Krok 1: Analiza Zapytania</h3>
        <p><strong>Model:</strong> {responseData.analysis.model}</p>
        {#if responseData.analysis.result_json}
          <pre>{JSON.stringify(responseData.analysis.result_json, null, 2)}</pre>
        {:else}
          <p><strong>Surowa odpowiedź:</strong></p>
          <pre>{responseData.analysis.raw_response}</pre>
        {/if}
        {#if responseData.analysis.error}
          <p class="error-text">Błąd analizy: {responseData.analysis.error}</p>
        {/if}
      </div>

      <!-- Krok 2: Perspektywy -->
      <div class="result-step">
        <h3>Krok 2: Wygenerowane Perspektywy</h3>
        {#each responseData.perspectives as p, i}
          <div class="perspective">
            <h4>Perspektywa {i + 1}: {p.type} ({p.model})</h4>
            {#if p.error}
              <p class="error-text">Błąd generowania: {p.error}</p>
              <p><strong>Odpowiedź (błąd):</strong> {p.response}</p>
            {:else}
               <!-- Używamy @html do renderowania prostego Markdown -->
               <div class="markdown-content">{@html renderMarkdown(p.response)}</div>
            {/if}
          </div>
        {/each}
      </div>

      <!-- Krok 3: Weryfikacja i Synteza -->
       <div class="result-step">
        <h3>Krok 3: Weryfikacja i Synteza</h3>
        <p><strong>Model:</strong> {responseData.verification_synthesis.model}</p>
         {#if responseData.verification_synthesis.error}
            <p class="error-text">Błąd weryfikacji/syntezy: {responseData.verification_synthesis.error}</p>
            <p><strong>Surowa odpowiedź (błąd):</strong></p>
            <pre>{responseData.verification_synthesis.raw_response}</pre>
         {:else if responseData.verification_synthesis.verification_comparison_report || responseData.verification_synthesis.final_synthesized_answer}
             <!-- Renderuj całą odpowiedź jako Markdown, bo zawiera już nagłówki -->
             <div class="markdown-content">{@html renderMarkdown(responseData.verification_synthesis.raw_response)}</div>
         {:else}
             <p><strong>Surowa odpowiedź (brak podziału?):</strong></p>
             <pre>{responseData.verification_synthesis.raw_response}</pre>
         {/if}
      </div>

       <!-- Przycisk Eksportu JSON -->
       <button on:click={handleExport} disabled={!responseData}>Eksportuj wyniki jako JSON</button>
    </section>
  {/if}

</main>

<style>
  /* Importuj style globalne lub zdefiniuj tutaj */
  :global(body) {
      margin: 0;
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
      background-color: #1a1a2e; /* Ciemne tło */
      color: #e0e0e0; /* Jasny tekst */
  }

  .pixel-background {
      /* Można dodać tło w stylu pixel art */
      background-color: #161625;
      min-height: 100vh;
      padding-bottom: 2rem;
  }

  .header-banner {
      background-color: #0f0f1a;
      padding: 1.5rem 0;
      text-align: center;
      border-bottom: 3px solid #e040fb; /* Neonowy różowy */
      margin-bottom: 2rem;
  }

  .pixel-title {
      font-family: 'Press Start 2P', cursive;
      color: #e040fb; /* Neonowy różowy */
      font-size: clamp(1.8rem, 5vw, 2.5rem); /* Responsywny rozmiar czcionki */
      text-shadow: 2px 2px #00ffff, -2px -2px #ff80ff; /* Neonowy cyjan i jaśniejszy różowy */
      margin: 0;
      letter-spacing: 2px;
  }

   .mascot-image { /* Styl dla potencjalnego obrazka */
       display: block;
       margin: 1rem auto 2rem auto;
       max-width: 200px; /* Dostosuj rozmiar */
       height: auto;
   }

  .container {
    max-width: 900px;
    margin: 0 auto;
    padding: 0 1rem;
  }

  .description {
      text-align: center;
      font-size: 1.1rem;
      color: #a0a0c0;
      margin-bottom: 2rem;
  }

  .card {
    margin-top: 2rem;
    padding: 1.5rem;
    border: 2px solid #4a4a6a; /* Ciemniejszy border */
    border-radius: 8px;
    background-color: #1e1e3f; /* Ciemniejszy fiolet/niebieski */
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.5); /* Mocniejszy cień */
    position: relative; /* Dla potencjalnych pseudo-elementów */
  }
   .card-title {
       font-family: 'Press Start 2P', cursive;
       color: #e040fb;
       margin-top: 0;
       margin-bottom: 1.5rem;
       text-align: center;
       font-size: 1.4rem;
       border-bottom: 2px solid #4a4a6a;
       padding-bottom: 0.5rem;
   }
  .form-group {
    margin-bottom: 1.5rem; /* Zwiększony margines */
  }
  label {
    display: block;
    margin-bottom: 0.5rem;
    font-weight: bold;
    color: #00ffff; /* Neonowy cyjan */
    font-family: 'Press Start 2P', cursive;
    font-size: 0.9rem;
  }
  input[type="text"],
  input[type="password"],
  textarea,
  input[type="file"] {
    width: 100%;
    padding: 0.75rem;
    border: 1px solid #4a4a6a;
    border-radius: 4px;
    box-sizing: border-box;
    background-color: #2a2a4a; /* Ciemniejsze tło pola */
    color: #e0e0e0; /* Jasny tekst w polu */
    font-size: 1rem;
    margin-bottom: 0.5rem; /* Dodano margines dolny */
  }
   input[type="file"] {
      padding: 0.5rem;
      cursor: pointer;
   }
   /* Styl dla przycisku pliku */
   input[type="file"]::file-selector-button {
       font-family: 'Press Start 2P', cursive;
       padding: 0.5rem 1rem;
       border: none;
       background-color: #e040fb;
       color: #161625;
       border-radius: 4px;
       cursor: pointer;
       transition: background-color 0.2s;
   }
   input[type="file"]::file-selector-button:hover {
       background-color: #ff80ff;
   }

  textarea {
    min-height: 100px;
    resize: vertical;
    font-family: monospace; /* Lepsze dla kodu/promptów */
  }
  button {
    padding: 0.8rem 1.5rem;
    background: linear-gradient(45deg, #e040fb, #00ffff); /* Gradient neonowy */
    color: #161625; /* Ciemny tekst na przycisku */
    border: none;
    border-radius: 4px;
    cursor: pointer;
    font-size: 1rem;
    font-family: 'Press Start 2P', cursive;
    transition: transform 0.2s, box-shadow 0.2s;
    text-transform: uppercase;
    margin-top: 1rem; /* Dodano margines górny */
  }
  button:disabled {
    background: #4a4a6a;
    color: #888;
    cursor: not-allowed;
    transform: none;
    box-shadow: none;
  }
  button:hover:not(:disabled) {
    transform: translateY(-2px);
    box-shadow: 0 4px 8px rgba(224, 64, 251, 0.4), 0 4px 8px rgba(0, 255, 255, 0.4);
  }
  small, .file-status-list small {
    display: block;
    margin-top: 0.3rem;
    font-size: 0.85rem;
    color: #a0a0c0; /* Jaśniejszy szary */
  }
  .error-message {
    margin-top: 1rem;
    padding: 1rem;
    background-color: #4d1f24; /* Ciemniejsza czerwień */
    color: #ff8080; /* Jaśniejsza czerwień tekstu */
    border: 1px solid #ff4d4d;
    border-radius: 4px;
    font-weight: bold;
  }
   .error-text {
      color: #ff8080; /* Jaśniejsza czerwień */
      font-weight: bold;
   }
   .file-status-list {
       margin-top: 0.5rem;
       font-size: 0.9rem;
       background-color: #2a2a4a; /* Ciemniejsze tło */
       padding: 0.5rem 1rem;
       border-radius: 4px;
       border: 1px solid #4a4a6a;
   }
   .file-status-list ul {
       list-style: none;
       padding: 0;
       margin: 0.3rem 0 0 0;
   }
    .file-status-list li {
       margin-bottom: 0.2rem;
       color: #c0c0e0;
   }
  .loading-indicator {
    margin-top: 1rem;
    text-align: center;
    font-style: italic;
    color: #00ffff; /* Neonowy cyjan */
    font-family: 'Press Start 2P', cursive;
    font-size: 1.1rem;
  }
  .results-section {
      /* Usunięto powtórzone style - dziedziczone z .card */
  }
  .result-step {
      margin-bottom: 2.5rem; /* Zwiększony margines */
      padding-bottom: 1.5rem;
      border-bottom: 1px dashed #4a4a6a;
  }
  .result-step:last-child {
      border-bottom: none;
  }
   .result-step h3 {
      margin-bottom: 1rem;
      color: #00ffff; /* Neonowy cyjan */
      font-family: 'Press Start 2P', cursive;
      font-size: 1.2rem;
   }
   .perspective {
      margin-top: 1.5rem; /* Zwiększony margines */
      padding: 1.5rem; /* Zwiększony padding */
      border: 1px solid #4a4a6a;
      border-radius: 6px; /* Lekko zaokrąglone rogi */
      background-color: #2a2a4a;
      box-shadow: inset 0 0 5px rgba(0, 0, 0, 0.4); /* Wewnętrzny cień */
   }
   .perspective h4 {
      margin-top: 0;
      margin-bottom: 0.5rem;
      font-size: 1.1rem;
      color: #e0e0e0;
      font-family: 'Press Start 2P', cursive;
      font-size: 1rem;
      border-bottom: 1px solid #4a4a6a;
      padding-bottom: 0.3rem;
   }
   pre {
      background-color: #161625; /* Bardzo ciemne tło dla pre */
      color: #c0c0e0; /* Jaśniejszy tekst w pre */
      padding: 1rem;
      border-radius: 4px;
      overflow-x: auto;
      white-space: pre-wrap;
      word-wrap: break-word;
      border: 1px solid #4a4a6a;
   }
   .markdown-content {
       line-height: 1.7; /* Zwiększona interlinia */
       color: #d0d0f0; /* Lekko jaśniejszy tekst */
   }
   .markdown-content h2 {
       margin-top: 1.5em;
       margin-bottom: 0.5em;
       padding-bottom: 0.3em;
       border-bottom: 1px solid #4a4a6a;
       color: #e040fb;
       font-family: 'Press Start 2P', cursive;
       font-size: 1.1rem; /* Dopasowanie rozmiaru */
   }
    .markdown-content strong {
        color: #00ffff;
    }
   .markdown-content li {
       margin-bottom: 0.7em; /* Zwiększony odstęp */
       margin-left: 1.5em;
   }
   .markdown-content a {
       color: #00ffff;
       text-decoration: none; /* Usunięcie podkreślenia */
       border-bottom: 1px dotted #00ffff; /* Kropkowane podkreślenie */
       transition: color 0.2s, border-bottom-color 0.2s;
   }
   .markdown-content a:hover {
       color: #80ffff;
       border-bottom-color: #80ffff;
   }
   /* Dodatkowe style dla lepszego wyglądu */
   ::selection {
       background: #e040fb;
       color: #161625;
   }
</style>
</div>
