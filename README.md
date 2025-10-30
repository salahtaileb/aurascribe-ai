# AuraScribe — Phase 1 (MVP) — Français par défaut / French by default

> **✅ CONFIRMATION**: This is the demo project created on **October 27, 2025 (afternoon at 18:14 EDT)**
> 
> For detailed project information, see [PROJECT_INFO.md](./PROJECT_INFO.md)

But: Ce dépôt contient un scaffold MVP pour AuraScribe — un scribe médical AI bilingue (FR/EN) pour la santé sexuelle au Québec.
Le français est la langue par défaut de l'interface et des prompts.

Principaux composants inclus :
- FastAPI backend (app/)
- Agents modularisés (STT, Chief Complaint, HPI, A&P, Medical Scribe, MADO Policy, Orchestrator)
- Ephemeral Redis store pour transcripts (TTL)
- Postgres audit (ne stocke pas de PHI)
- FHIR R4 client pour intégration EMR (DocumentReference/Composition)
- OAuth2/OIDC skeleton (remplacer par IdP prod)
- Frontend composants: Consent modal + Audio recorder (React TSX)
- Dockerfile + docker-compose pour dev (Postgres + Redis + FastAPI)

Pré-requis locaux :
- Docker & Docker Compose (recommandé pour dev)
- Variables d'environnement (voir .env.example)

Commandes dev (docker compose) :
  cp .env.example .env
  docker compose up --build

Notes de conformité :
- Ne pas stocker audio/transcript en clair. Redis TTL utilisé pour sessions éphémères.
- Redaction locale (policy_redaction.py) appliquée avant tout envoi à LLM externe.
- En prod : activer KMS, TLS, IdP (Keycloak/Azure AD), hébergement Canada.

FRENCH UI default: all UI strings default to French; frontend props allow language="fr" | "en".

Voir les fichiers d'exemple dans /app et /frontend.
