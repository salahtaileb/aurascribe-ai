```mermaid
flowchart TD
  subgraph Client
    A[Clinician Web/Mobile (FR default)] -->|Audio + meta (session_id, lang=fr/en)| API[FastAPI Gateway]
  end

  subgraph Backend
    API --> Auth[OIDC/OAuth2 + RBAC]
    API --> Orchestrator[Medical Director Agent]
    Orchestrator --> STT[STT Agent (Deepgram / Whisper)]
    Orchestrator --> Policy[MADO Policy Agent (local redaction)]
    Orchestrator --> CC[Chief Complaint Agent (LLM)]
    Orchestrator --> HPI[HPI Agent (LLM)]
    Orchestrator --> AP[A&P Agent (LLM)]
    Orchestrator --> Scribe[Medical Scribe Agent (LLM)]
    Orchestrator --> FHIR[FHIR R4 Client]
    Orchestrator --> Redis[Redis Ephemeral Store (TTL)]
    Orchestrator --> Audit[Audit DB (Postgres) - no PHI]
  end

  subgraph EMR
    FHIR --> EMR[(EMR / FHIR Server)]
  end