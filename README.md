# AI Agent - Pixel Pasta (trippleCheck) - FastAPI & SvelteKit Edition

A web application featuring a FastAPI backend and a SvelteKit frontend. It utilizes an AI pipeline (analysis, perspective generation, verification, synthesis) to answer user queries, with the option to add text or image files as context.

## Features

*   Processes natural language queries.
*   Supports uploading `.txt`, `.pdf`, `.md`, `.jpg`, `.jpeg`, `.png`, `.gif`, `.bmp`, `.tiff` files as additional context (OCR for images).
*   Utilizes AI models from OpenRouter.
*   Features a 3-step AI processing pipeline:
    1.  **Analysis:** Understands the query and context.
    2.  **Perspective Generation:** Creates three distinct perspectives (Informative, Contrarian, Complementary) in parallel.
    3.  **Verification & Synthesis:** Evaluates the perspectives using Google Search, compares them, and synthesizes a final, verified answer.
*   Pixel art styled user interface built with SvelteKit.

## Local Setup

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/makaronz/trippleCheck.git
    cd trippleCheck
    ```
2.  **Create and activate a virtual environment (recommended):**
    ```bash
    # Create environment for backend
    python -m venv venv
    # Windows
    .\venv\Scripts\activate
    # macOS/Linux
    source venv/bin/activate
    ```
3.  **Install backend dependencies:**
    ```bash
    pip install -r fastapi_app/requirements.txt
    ```
4.  **Install frontend dependencies:**
    ```bash
    cd frontend
    npm install
    cd ..
    ```
5.  **Configure environment variables:**
    *   Create a file named `.env` in the **root** directory of the project (where `render.yaml` is).
    *   Add your OpenRouter API key:
        ```dotenv
        # Used by the FastAPI backend
        OPENROUTER_API_KEY=your_openrouter_api_key

        # Optional: Define if frontend runs on a different port during local dev
        # VITE_FASTAPI_URL=http://127.0.0.1:8000
        ```
    *   Replace `your_openrouter_api_key` with your actual key.
6.  **(Optional) Install Tesseract OCR:**
    *   If you want to process image files (`.jpg`, `.png`, etc.), you need to install Tesseract OCR: [Tesseract Installation Instructions](https://github.com/tesseract-ocr/tesseract#installing-tesseract).
    *   Ensure Tesseract is added to your system's `PATH` environment variable. The application uses `ocrmypdf` and `pytesseract` which rely on the system's Tesseract installation.
7.  **Run the application (Development Mode):**
    *   **Terminal 1 (Backend):**
        ```bash
        # Make sure your virtual environment is activated
        cd fastapi_app
        uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
        ```
    *   **Terminal 2 (Frontend):**
        ```bash
        cd frontend
        npm run dev
        ```
    *   The application frontend will be available at `http://localhost:5173` (or another port if 5173 is busy), and the backend API at `http://127.0.0.1:8000`.

## Deployment (Render.com)

The application is configured for deployment on [Render](https://render.com/) using a single web service.

*   **Configuration File:** `render.yaml` defines the build and start commands.
*   **Build Process:**
    1.  Installs Python dependencies (`fastapi_app/requirements.txt`).
    2.  Installs Node.js dependencies and builds the SvelteKit frontend (`cd frontend && npm install && npm run build`).
    3.  Copies the built frontend static files into the FastAPI static directory (`fastapi_app/app/static/dist/`).
*   **Start Command:** Uses Gunicorn to run the FastAPI application (`cd fastapi_app && gunicorn ... app.main:app ...`).
*   **Environment Variables on Render:** You **must** set the `OPENROUTER_API_KEY` secret environment variable in the Render service settings. The `PYTHON_VERSION` is set in `render.yaml`.

Render automatically detects `render.yaml` when creating a "Blueprint" service connected to your GitHub repository. Pushing changes to the connected branch will trigger a new deployment.

**Note on OCR:** Tesseract OCR is **not** installed by default in the Render Python environment defined in `render.yaml`. Image OCR functionality will **not** work in the deployed version unless you modify the deployment (e.g., by using a Dockerfile that includes Tesseract).
