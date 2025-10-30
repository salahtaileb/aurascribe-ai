# AuraScribe AI - Project Information

## Demo Project Confirmation

**Yes, this is the demo project created on October 27, 2025 (afternoon).**

## Project Details

- **Project Name**: AuraScribe AI
- **Creation Date**: October 27, 2025 at 18:14 (afternoon)
- **Type**: Demo/MVP - AI Medical Scribe System
- **Primary Language**: French (with English support)
- **Target Region**: Québec, Canada

## Purpose

This is a demonstration/proof-of-concept implementation of an AI-powered medical scribe system designed specifically for Québec healthcare professionals. The system:

- Listens to patient-clinician conversations
- Automatically generates structured clinical notes
- Integrates with EMR systems via FHIR R4
- Complies with Québec healthcare regulations (MADO reporting)
- Uses ephemeral storage to protect patient privacy (PHI)

## Key Components

### Backend Agents
- **STT Agent**: Speech-to-text using Whisper/Deepgram
- **Chief Complaint Agent**: Extracts primary patient complaint
- **HPI Agent**: Generates History of Present Illness
- **A&P Agent**: Creates Assessment & Plan
- **Medical Scribe Agent**: Overall clinical note generation
- **MADO Policy Agent**: Handles mandatory disease reporting for Québec
- **Billing Agent**: Generates RAMQ billing codes
- **Orchestrator**: Coordinates all agents (Medical Director)

### Infrastructure
- **FastAPI**: Backend REST API
- **Redis**: Ephemeral storage with TTL (no persistent PHI)
- **PostgreSQL**: Audit logs (no PHI stored)
- **Docker Compose**: Local development environment
- **FHIR R4 Client**: EMR integration

### Frontend Components
- **AudioRecorder.tsx**: Voice recording interface
- **ConsentModal.tsx**: Patient consent management
- **BillingConfirmationModal.tsx**: Billing review interface

## Development Status

This is a **Phase 1 MVP** scaffold/demo. It demonstrates the architecture and key components but is not production-ready. For production deployment, the following would be required:

- Production OAuth2/OIDC identity provider (Keycloak, Azure AD)
- KMS for encryption at rest and in transit
- Canada-based hosting (compliance requirement)
- Full security audit and penetration testing
- Production-grade monitoring and logging
- Load testing and performance optimization

## Compliance Notes

- **French First**: All UI defaults to French per Québec regulations
- **PHI Protection**: No persistent storage of audio or transcripts
- **MADO Integration**: Automated reporting of notifiable diseases
- **Audit Trail**: All access logged (without storing PHI)
- **RAMQ Billing**: Québec medical billing code generation

## Original Upload

The initial codebase was uploaded on October 27, 2025 at 18:14 EDT, creating this demo project structure with all the components listed above.

---

**Confirmation**: This repository contains the AuraScribe AI demo created in the afternoon of October 27, 2025.
