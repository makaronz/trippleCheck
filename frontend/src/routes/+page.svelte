<script lang="ts">
  import { onMount } from 'svelte';
  import { browser } from '$app/environment'; // Import 'browser' for environment checks

  // Removed apiKey variable
  let query = ''; // User query
  let selectedFiles: FileList | null = null; // Files selected by the user
  let processedDocuments: { name: string; content: string; size: number }[] = []; // Processed documents
  let fileProcessingStatus: { [key: string]: string } = {}; // File processing status
  let isLoading = false; // Is AI query processing in progress?
  let isProcessingFiles = false; // Is file processing in progress?
  let responseData: any = null; // Response from the backend
  let errorMessage = ''; // Error message

  // In production, use relative paths because backend and frontend are on the same domain
  // For local development, use the full URL if frontend and backend run on different ports
  const useRelativeUrls = !import.meta.env.DEV; // Use relative URLs in production mode
  const apiBaseUrl = useRelativeUrls ? '' : (import.meta.env.VITE_FASTAPI_URL || 'http://127.0.0.1:8000');
  console.log(`API base URL: ${apiBaseUrl || '(using relative URLs)'}`);

  // Function to read file as base64
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

  // Function to handle file selection change in input
  function handleFileSelection(event: Event) {
      const input = event.target as HTMLInputElement;
      if (input.files) {
          selectedFiles = input.files;
          processedDocuments = []; // Reset processed files on new selection
          fileProcessingStatus = {}; // Reset statuses
          processSelectedFiles(); // Start processing immediately
      }
  }

  // Function to process selected files
  async function processSelectedFiles() {
      if (!selectedFiles || selectedFiles.length === 0) return;

      isProcessingFiles = true;
      errorMessage = '';
      const filesToProcess = Array.from(selectedFiles); // Convert FileList to Array
      selectedFiles = null; // Clear selection to avoid reprocessing the same files

      const processingPromises = filesToProcess.map(async (file) => {
          const fileName = file.name;
          fileProcessingStatus = { ...fileProcessingStatus, [fileName]: 'Processing...' };
          try {
              const base64Data = await readFileAsBase64(file);
              const response = await fetch(`${apiBaseUrl}/api/v1/process_file`, {
                  method: 'POST',
                  headers: { 'Content-Type': 'application/json' },
                  credentials: 'same-origin', // Allow sending cookies for same-origin requests
                  body: JSON.stringify({
                      filename: fileName,
                      file_data_base64: base64Data,
                  }),
              });

              if (!response.ok) {
                  let errorDetail = `Error ${response.status}`;
                  try {
                      const errorJson = await response.json();
                      errorDetail = errorJson.detail || errorDetail;
                  } catch (e) { /* ignore */ }
                  throw new Error(errorDetail);
              }

              const result = await response.json();
              fileProcessingStatus = { ...fileProcessingStatus, [fileName]: 'Ready ✔' };
              return { name: fileName, content: result.content, size: file.size };

          } catch (error: any) {
              console.error(`Error processing file ${fileName}:`, error);
              fileProcessingStatus = { ...fileProcessingStatus, [fileName]: `Error: ${error.message}` };
              return null; // Return null in case of error
          }
      });

      const results = await Promise.all(processingPromises);
      processedDocuments = results.filter(doc => doc !== null) as { name: string; content: string; size: number }[];
      isProcessingFiles = false;
      console.log('Processed documents:', processedDocuments);
  }
  // Removed redundant curly brace

  // Function to send query to the backend
  async function submitQuery() {
    // Removed apiKey check
    if (!query.trim()) {
      errorMessage = 'Please enter a query.';
      return;
    }

    isLoading = true;
    errorMessage = '';
    responseData = null;

    // Prepare request data, use processed documents
    // Removed api_key from request body
    const requestBody = {
      query: query,
      documents: processedDocuments, // Pass processed documents
    };

    try {
      const response = await fetch(`${apiBaseUrl}/api/v1/process_query`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'same-origin', // Allow sending cookies for same-origin requests
        body: JSON.stringify(requestBody),
      });

      if (!response.ok) {
        let errorDetail = `Server Error: ${response.status}`;
        try {
            const errorJson = await response.json();
            errorDetail = errorJson.detail || errorDetail;
        } catch (e) {
            // Ignore error parsing error JSON
        }
        throw new Error(errorDetail);
      }

      responseData = await response.json();
      console.log('Response from backend:', responseData);

    } catch (error: any) {
      console.error('Error submitting query:', error);
      errorMessage = `An error occurred: ${error.message}`;
    } finally {
      isLoading = false;
    }
  }

  // Function for safe Markdown rendering (simple implementation)
  // In a real application, it's better to use a library like 'marked' or 'markdown-it'
  // This version is very basic and might not render complex Markdown correctly.
  // Improved handling of HTML tags - do not escape '<' and '>'.
  function renderMarkdown(markdown: string | undefined | null): string {
      if (!markdown) return '';
      // Simple replacement for basic formatting, but allows HTML
      // WARNING: This is not safe if Markdown comes from an untrusted source!
      // A production application should use a library with sanitization.
      let html = markdown;
      // Basic Markdown to HTML formatting
      html = html.replace(/^## (.*$)/gim, '<h2>$1</h2>'); // H2 headers
      html = html.replace(/^\* \*\*(.*)\*\*:/gim, '<br><strong>$1:</strong>'); // Bold labels in lists
      html = html.replace(/^\* (.*$)/gim, '<li>$1</li>'); // List items
      // Replace list blocks with <ul> - very simplified
      html = html.replace(/(<li>.*<\/li>)/gs, '<ul>$1</ul>');
      html = html.replace(/\n/g, '<br>'); // New lines

      // WARNING: Security! Sanitization needed in a real application!
      return html;
  }

  // Function to download data as JSON
  function downloadJson(data: any, filename: string) {
      const jsonStr = JSON.stringify(data, null, 2); // Formatting with indentation
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
          alert('No data to export.');
      }
  }

</script>

<svelte:head>
  <title>trippleCheck</title>
  <!-- Pixel Font -->
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin=""> <!-- Fixed: added empty quotes -->
  <link href="https://fonts.googleapis.com/css2?family=Press+Start+2P&display=swap" rel="stylesheet">
</svelte:head>

<div class="pixel-background">
  <header class="header-banner">
      <h1 class="pixel-title">trippleCheck</h1>
  </header>

  <main class="container">
    <!-- A robot image could be added here if available -->
    <!-- <img src="/path/to/robot.png" alt="Pixel Pasta Mascot" class="mascot-image"> -->
    <p class="description">AI assistant for complex tasks. Enter your query and optionally add files for context.</p>

    <section class="card input-section">
      <h2 class="card-title">User Input</h2>
    <!-- Removed API key field -->

    <div class="form-group">
        <label for="documents">Attach documents (optional):</label> <!-- Removed limit from label -->
        <input type="file" id="documents" on:change={handleFileSelection} multiple accept=".txt,.pdf,.md,.jpg,.jpeg,.png,.gif,.bmp,.tiff" />
         {#if isProcessingFiles}
             <small>Processing files...</small>
         {/if}
         {#if Object.keys(fileProcessingStatus).length > 0}
            <div class="file-status-list">
                <small>File processing status:</small>
                <ul>
                    {#each Object.entries(fileProcessingStatus) as [name, status]}
                        <li>{name}: {status}</li>
                    {/each}
                </ul>
            </div>
         {/if}
    </div>

    <div class="form-group">
      <label for="query">Your Query:</label>
      <textarea id="query" bind:value={query} rows="5" placeholder="Enter your question or command..." required></textarea>
    </div>

    <button on:click={submitQuery} disabled={isLoading}>
      {isLoading ? 'Processing...' : 'Submit Query'}
    </button>
  </section>

  {#if errorMessage}
    <div class="error-message">
      <p>Error: {errorMessage}</p>
    </div>
  {/if}

  {#if isLoading}
    <div class="loading-indicator">
      <p>⏳ Processing query through the AI pipeline... This might take a moment.</p>
      <!-- More detailed progress indicators could be added here -->
    </div>
  {/if}

  {#if responseData}
    <section class="card results-section">
      <h2 class="card-title">Processing Results</h2>

      <!-- Step 1: Analysis -->
      <div class="result-step">
        <h3>Step 1: Query Analysis</h3>
        <p><strong>Model:</strong> {responseData.analysis.model}</p>
        {#if responseData.analysis.result_json}
          <pre>{JSON.stringify(responseData.analysis.result_json, null, 2)}</pre>
        {:else}
          <p><strong>Raw Response:</strong></p>
          <pre>{responseData.analysis.raw_response}</pre>
        {/if}
        {#if responseData.analysis.error}
          <p class="error-text">Analysis Error: {responseData.analysis.error}</p>
        {/if}
      </div>

      <!-- Step 2: Perspectives -->
      <div class="result-step">
        <h3>Step 2: Generated Perspectives</h3>
        {#each responseData.perspectives as p, i}
          <div class="perspective">
            <h4>Perspective {i + 1}: {p.type} ({p.model})</h4>
            {#if p.error}
              <p class="error-text">Generation Error: {p.error}</p>
              <p><strong>Response (error):</strong> {p.response}</p>
            {:else}
               <!-- Use @html to render simple Markdown -->
               <div class="markdown-content">{@html renderMarkdown(p.response)}</div>
            {/if}
          </div>
        {/each}
      </div>

      <!-- Step 3: Verification and Synthesis -->
       <div class="result-step">
        <h3>Step 3: Verification and Synthesis</h3>
        <p><strong>Model:</strong> {responseData.verification_synthesis.model}</p>
         {#if responseData.verification_synthesis.error}
            <p class="error-text">Verification/Synthesis Error: {responseData.verification_synthesis.error}</p>
            <p><strong>Raw Response (error):</strong></p>
            <pre>{responseData.verification_synthesis.raw_response}</pre>
         {:else if responseData.verification_synthesis.verification_comparison_report || responseData.verification_synthesis.final_synthesized_answer}
             <!-- Render the entire response as Markdown, as it already contains headers -->
             <div class="markdown-content">{@html renderMarkdown(responseData.verification_synthesis.raw_response)}</div>
         {:else}
             <p><strong>Raw Response (no split?):</strong></p>
             <pre>{responseData.verification_synthesis.raw_response}</pre>
         {/if}
      </div>

       <!-- JSON Export Button -->
       <button on:click={handleExport} disabled={!responseData}>Export Results as JSON</button>
    </section>
  {/if}

</main>

<style>
  /* Import global styles or define here */
  :global(body) {
      margin: 0;
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
      background-color: #1a1a2e; /* Dark background */
      color: #e0e0e0; /* Light text */
  }

  .pixel-background {
      /* A pixel art style background could be added */
      background-color: #161625;
      min-height: 100vh;
      padding-bottom: 2rem;
  }

  .header-banner {
      background-color: #0f0f1a;
      padding: 1.5rem 0;
      text-align: center;
      border-bottom: 3px solid #e040fb; /* Neon pink */
      margin-bottom: 2rem;
  }

  .pixel-title {
      font-family: 'Press Start 2P', cursive;
      color: #e040fb; /* Neon pink */
      font-size: clamp(1.8rem, 5vw, 2.5rem); /* Responsive font size */
      text-shadow: 2px 2px #00ffff, -2px -2px #ff80ff; /* Neon cyan and lighter pink */
      margin: 0;
      letter-spacing: 2px;
  }

   .mascot-image { /* Style for potential mascot image */
       display: block;
       margin: 1rem auto 2rem auto;
       max-width: 200px; /* Adjust size */
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
    border: 2px solid #4a4a6a; /* Darker border */
    border-radius: 8px;
    background-color: #1e1e3f; /* Darker purple/blue */
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.5); /* Stronger shadow */
    position: relative; /* For potential pseudo-elements */
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
    margin-bottom: 1.5rem; /* Increased margin */
  }
  label {
    display: block;
    margin-bottom: 0.5rem;
    font-weight: bold;
    color: #00ffff; /* Neon cyan */
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
    background-color: #2a2a4a; /* Darker field background */
    color: #e0e0e0; /* Light text in field */
    font-size: 1rem;
    margin-bottom: 0.5rem; /* Added bottom margin */
  }
   input[type="file"] {
      padding: 0.5rem;
      cursor: pointer;
   }
   /* Style for file input button */
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
    font-family: monospace; /* Better for code/prompts */
  }
  button {
    padding: 0.8rem 1.5rem;
    background: linear-gradient(45deg, #e040fb, #00ffff); /* Neon gradient */
    color: #161625; /* Dark text on button */
    border: none;
    border-radius: 4px;
    cursor: pointer;
    font-size: 1rem;
    font-family: 'Press Start 2P', cursive;
    transition: transform 0.2s, box-shadow 0.2s;
    text-transform: uppercase;
    margin-top: 1rem; /* Added top margin */
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
    color: #a0a0c0; /* Lighter gray */
  }
  .error-message {
    margin-top: 1rem;
    padding: 1rem;
    background-color: #4d1f24; /* Darker red */
    color: #ff8080; /* Lighter red text */
    border: 1px solid #ff4d4d;
    border-radius: 4px;
    font-weight: bold;
  }
   .error-text {
      color: #ff8080; /* Lighter red */
      font-weight: bold;
   }
   .file-status-list {
       margin-top: 0.5rem;
       font-size: 0.9rem;
       background-color: #2a2a4a; /* Darker background */
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
    color: #00ffff; /* Neon cyan */
    font-family: 'Press Start 2P', cursive;
    font-size: 1.1rem;
  }
  .results-section {
      /* Removed repeated styles - inherited from .card */
  }
  .result-step {
      margin-bottom: 2.5rem; /* Increased margin */
      padding-bottom: 1.5rem;
      border-bottom: 1px dashed #4a4a6a;
  }
  .result-step:last-child {
      border-bottom: none;
  }
   .result-step h3 {
      margin-bottom: 1rem;
      color: #00ffff; /* Neon cyan */
      font-family: 'Press Start 2P', cursive;
      font-size: 1.2rem;
   }
   .perspective {
      margin-top: 1.5rem; /* Increased margin */
      padding: 1.5rem; /* Increased padding */
      border: 1px solid #4a4a6a;
      border-radius: 6px; /* Slightly rounded corners */
      background-color: #2a2a4a;
      box-shadow: inset 0 0 5px rgba(0, 0, 0, 0.4); /* Inner shadow */
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
      background-color: #161625; /* Very dark background for pre */
      color: #c0c0e0; /* Lighter text in pre */
      padding: 1rem;
      border-radius: 4px;
      overflow-x: auto;
      white-space: pre-wrap;
      word-wrap: break-word;
      border: 1px solid #4a4a6a;
   }
   .markdown-content {
       line-height: 1.7; /* Increased line spacing */
       color: #d0d0f0; /* Slightly lighter text */
   }
   .markdown-content h2 {
       margin-top: 1.5em;
       margin-bottom: 0.5em;
       padding-bottom: 0.3em;
       border-bottom: 1px solid #4a4a6a;
       color: #e040fb;
       font-family: 'Press Start 2P', cursive;
       font-size: 1.1rem; /* Adjusted size */
   }
    .markdown-content strong {
        color: #00ffff;
    }
   .markdown-content li {
       margin-bottom: 0.7em; /* Increased spacing */
       margin-left: 1.5em;
   }
   .markdown-content a {
       color: #00ffff;
       text-decoration: none; /* Removed underline */
       border-bottom: 1px dotted #00ffff; /* Dotted underline */
       transition: color 0.2s, border-bottom-color 0.2s;
   }
   .markdown-content a:hover {
       color: #80ffff;
       border-bottom-color: #80ffff;
   }
   /* Additional styles for better appearance */
   ::selection {
       background: #e040fb;
       color: #161625;
   }
</style>
</div>
