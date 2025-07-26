# System Architecture Diagrams - trippleCheck AI Agent

## 1. High-Level System Architecture

```mermaid
graph TB
    subgraph "Client Layer"
        U[User Browser]
        M[Mobile Device]
    end
    
    subgraph "Frontend Layer"
        FE[SvelteKit Frontend]
        UI[User Interface]
        ST[State Management]
    end
    
    subgraph "API Gateway"
        API[FastAPI Backend]
        RT[Routers]
        MD[Middleware]
    end
    
    subgraph "Application Layer"
        FP[File Processing Service]
        AI[AI Pipeline Service]
        VS[Verification Service]
        PS[Progress Service]
    end
    
    subgraph "Infrastructure Layer"
        FS[File Storage]
        OR[OpenRouter AI API]
        GS[Google Search API]
        LOG[Logging Service]
    end
    
    subgraph "Deployment Layer"
        R[Render.com]
        CDN[CDN]
        MON[Monitoring]
    end
    
    U --> FE
    M --> FE
    FE --> API
    API --> FP
    API --> AI
    API --> VS
    FP --> FS
    AI --> OR
    VS --> GS
    API --> LOG
    API --> R
    R --> CDN
    R --> MON
```

## 2. File Processing Pipeline

```mermaid
flowchart TD
    Start([User Uploads Files]) --> Validate{Validate Files}
    Validate -->|Valid| Process[Process Files]
    Validate -->|Invalid| Error[Return Error]
    
    Process --> Extract[Extract Content]
    Extract --> Format{File Format}
    
    Format -->|PDF| PDFProc[PDF Processor]
    Format -->|DOCX| DOCXProc[DOCX Processor]
    Format -->|Image| ImageProc[Image Processor + OCR]
    Format -->|Archive| ArchiveProc[Archive Processor]
    Format -->|Other| OtherProc[Other Format Processor]
    
    PDFProc --> Store[Store Processed Content]
    DOCXProc --> Store
    ImageProc --> Store
    ArchiveProc --> Store
    OtherProc --> Store
    
    Store --> Success[Return File IDs]
    Error --> End([End])
    Success --> End
```

## 3. AI Processing Pipeline

```mermaid
flowchart TD
    Start([User Submits Query]) --> Validate{Validate Query}
    Validate -->|Valid| Init[Initialize AI Pipeline]
    Validate -->|Invalid| Error[Return Error]
    
    Init --> Analysis[Analysis Stage]
    Analysis --> Context[Build Context]
    Context --> Perspectives[Generate Perspectives]
    
    Perspectives --> Parallel{Parallel Processing}
    Parallel --> Info[Informative Perspective]
    Parallel --> Contr[Contrarian Perspective]
    Parallel --> Comp[Complementary Perspective]
    
    Info --> Verify[Verification Stage]
    Contr --> Verify
    Comp --> Verify
    
    Verify --> Search[Google Search Verification]
    Search --> Compare[Compare Perspectives]
    Compare --> Synthesis[Synthesis Stage]
    Synthesis --> Final[Final Answer]
    
    Final --> Success[Return Results]
    Error --> End([End])
    Success --> End
```

## 4. User Journey Flow

```mermaid
journey
    title User Journey - Document Analysis
    section File Upload
      User visits application: 5: User
      User drags files to upload: 5: User
      System validates files: 4: System
      Files upload successfully: 5: User, System
    section Query Input
      User enters query: 5: User
      System validates query: 4: System
      Query is accepted: 5: User, System
    section Processing
      System starts processing: 4: System
      User sees progress: 5: User
      AI analyzes content: 4: System
      User waits for results: 3: User
    section Results
      System generates perspectives: 5: System
      User receives results: 5: User, System
      User reviews perspectives: 4: User
      User exports results: 4: User
```

## 5. API Interaction Flow

```mermaid
sequenceDiagram
    participant U as User
    participant F as Frontend
    participant B as Backend
    participant FP as File Processor
    participant AI as AI Pipeline
    participant OR as OpenRouter
    participant GS as Google Search
    
    U->>F: Upload files
    F->>B: POST /upload
    B->>FP: Process files
    FP->>B: Return file IDs
    B->>F: Return success
    F->>U: Show uploaded files
    
    U->>F: Submit query
    F->>B: POST /process
    B->>AI: Start AI pipeline
    AI->>OR: Analysis request
    OR->>AI: Analysis result
    AI->>OR: Generate perspectives
    OR->>AI: Perspectives
    AI->>GS: Verify claims
    GS->>AI: Verification results
    AI->>B: Final synthesis
    B->>F: Return results
    F->>U: Display results
```

## 6. Component Architecture

```mermaid
graph LR
    subgraph "Frontend Components"
        P[+page.svelte]
        FU[FileUpload.svelte]
        PQ[QueryInput.svelte]
        PR[Progress.svelte]
        RD[ResultsDisplay.svelte]
    end
    
    subgraph "Backend Services"
        FPS[FileProcessingService]
        AIS[AIPipelineService]
        VFS[VerificationService]
        PSS[ProgressService]
    end
    
    subgraph "External Services"
        ORC[OpenRouterClient]
        GSC[GoogleSearchClient]
        FSC[FileStorageClient]
    end
    
    P --> FU
    P --> PQ
    P --> PR
    P --> RD
    
    FU --> FPS
    PQ --> AIS
    AIS --> VFS
    PR --> PSS
    
    FPS --> FSC
    AIS --> ORC
    VFS --> GSC
```

## 7. Data Flow Architecture

```mermaid
graph TD
    subgraph "Input Layer"
        Files[File Uploads]
        Query[User Query]
    end
    
    subgraph "Processing Layer"
        Validation[Input Validation]
        Extraction[Content Extraction]
        Analysis[AI Analysis]
        Verification[Fact Verification]
    end
    
    subgraph "Output Layer"
        Perspectives[Multi-Perspective Results]
        Synthesis[Final Synthesis]
        Export[Export Options]
    end
    
    subgraph "Storage Layer"
        Temp[Temporary Storage]
        Cache[Response Cache]
        Logs[Processing Logs]
    end
    
    Files --> Validation
    Query --> Validation
    Validation --> Extraction
    Extraction --> Analysis
    Analysis --> Verification
    Verification --> Perspectives
    Perspectives --> Synthesis
    Synthesis --> Export
    
    Extraction --> Temp
    Analysis --> Cache
    Verification --> Logs
```

## 8. Security Architecture

```mermaid
graph TB
    subgraph "Client Security"
        HTTPS[HTTPS/TLS]
        CORS[CORS Policy]
        CSP[Content Security Policy]
    end
    
    subgraph "API Security"
        Validation[Input Validation]
        Sanitization[Content Sanitization]
        RateLimit[Rate Limiting]
        Auth[API Key Validation]
    end
    
    subgraph "File Security"
        MIME[MIME Type Validation]
        Size[Size Limits]
        Scan[Content Scanning]
        Storage[Secure Storage]
    end
    
    subgraph "Infrastructure Security"
        SSL[SSL/TLS Encryption]
        Headers[Security Headers]
        Monitoring[Security Monitoring]
        Backup[Secure Backups]
    end
    
    HTTPS --> Validation
    CORS --> Sanitization
    CSP --> RateLimit
    Validation --> MIME
    Sanitization --> Size
    RateLimit --> Scan
    Auth --> Storage
    MIME --> SSL
    Size --> Headers
    Scan --> Monitoring
    Storage --> Backup
```

## 9. Deployment Architecture

```mermaid
graph TB
    subgraph "Development Environment"
        Local[Local Development]
        DevAPI[Dev API Server]
        DevFE[Dev Frontend]
    end
    
    subgraph "Build Process"
        Build[Build Pipeline]
        Test[Test Suite]
        Deploy[Deploy to Render]
    end
    
    subgraph "Production Environment"
        Render[Render.com]
        Gunicorn[Gunicorn Server]
        Static[Static Files]
        CDN[CDN]
    end
    
    subgraph "External Services"
        OpenRouter[OpenRouter AI]
        GoogleSearch[Google Search]
        Monitoring[Monitoring]
    end
    
    Local --> Build
    DevAPI --> Test
    DevFE --> Test
    Test --> Deploy
    Deploy --> Render
    Render --> Gunicorn
    Render --> Static
    Static --> CDN
    Gunicorn --> OpenRouter
    Gunicorn --> GoogleSearch
    Render --> Monitoring
```

## 10. Error Handling Flow

```mermaid
flowchart TD
    Start([Request Received]) --> Validate{Input Validation}
    Validate -->|Invalid| InputError[Return 400 Bad Request]
    Validate -->|Valid| Process[Process Request]
    
    Process --> FileCheck{File Processing}
    FileCheck -->|Error| FileError[Return 422 Processing Error]
    FileCheck -->|Success| AICheck{AI Processing}
    
    AICheck -->|Error| AIError[Return 503 Service Unavailable]
    AICheck -->|Success| VerifyCheck{Verification}
    
    VerifyCheck -->|Error| VerifyError[Return 503 Verification Error]
    VerifyCheck -->|Success| Success[Return 200 Success]
    
    InputError --> Log[Log Error]
    FileError --> Log
    AIError --> Log
    VerifyError --> Log
    Success --> Log
    
    Log --> End([End])
```

## 11. Performance Monitoring Flow

```mermaid
graph LR
    subgraph "Application Metrics"
        RT[Response Time]
        TP[Throughput]
        ER[Error Rate]
        MU[Memory Usage]
    end
    
    subgraph "External Service Metrics"
        OR[OpenRouter API]
        GS[Google Search API]
        FS[File Storage]
    end
    
    subgraph "User Experience Metrics"
        TTI[Time to Insight]
        TCR[Task Completion Rate]
        US[User Satisfaction]
    end
    
    subgraph "Monitoring System"
        Collect[Data Collection]
        Process[Data Processing]
        Alert[Alerting]
        Dashboard[Dashboard]
    end
    
    RT --> Collect
    TP --> Collect
    ER --> Collect
    MU --> Collect
    OR --> Collect
    GS --> Collect
    FS --> Collect
    TTI --> Collect
    TCR --> Collect
    US --> Collect
    
    Collect --> Process
    Process --> Alert
    Process --> Dashboard
```

## 12. Memory Bank Integration Flow

```mermaid
graph TD
    subgraph "Session Start"
        Start([New Session]) --> Check[Check TASK_log.md]
        Check --> Read[Read Memory Bank Files]
        Read --> Context[Load Project Context]
    end
    
    subgraph "Task Execution"
        Context --> Execute[Execute Task]
        Execute --> Update[Update Active Context]
        Update --> Log[Update TASK_log.md]
    end
    
    subgraph "Session End"
        Log --> Review[Review Changes]
        Review --> Save[Save to Memory Bank]
        Save --> Intelligence[Update Project Intelligence]
    end
    
    subgraph "Memory Bank Files"
        PB[projectbrief.md]
        PC[productContext.md]
        SP[systemPatterns.md]
        TC[techContext.md]
        AC[activeContext.md]
        PR[progress.md]
        MB[memory-bank.mdc]
    end
    
    Read --> PB
    Read --> PC
    Read --> SP
    Read --> TC
    Read --> AC
    Read --> PR
    Update --> AC
    Save --> PR
    Intelligence --> MB
```

---

**Diagram Version**: 1.0.0  
**Last Updated**: 2024-12-19  
**Total Diagrams**: 12 comprehensive system diagrams  
**Coverage**: Architecture, flows, security, deployment, monitoring, and Memory Bank integration 