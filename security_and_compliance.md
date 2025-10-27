```markdown
# AuraScribe — Security, Privacy & Compliance Summary

This document summarizes required measures to comply with:
- Loi 25 (Québec)
- PIPEDA (Canada)
- HIPAA (U.S. healthcare privacy guidance, useful controls)

Key principles
- Minimize data collected (data minimization).
- Explicit informed bilingual consent for audio recording and data use.
- Keep PHI/PII out of logs and avoid storing it persistently.
- Use ephemeral storage for transcripts (Redis with TTL, or in-memory), purge immediately.
- Encrypt in transit (TLS 1.3) and at rest (AES-256); use KMS/HSM for key management.
- Use strong authentication (OIDC/OAuth2) and RBAC for EMR write permission.
- Maintain audit logs that record metadata (who, when, action) — audit logs must NOT contain PHI.
- Data residency: host production services and backups in Canada (required under Loi 25 preferences).
- Breach notification: implement detection, notifications to CNIL-equivalent, and users per Loi 25/PIPEDA timelines.
- Contracts: BAAs or equivalent with third parties (LLM providers, STT providers). Require contractual assurances re: model training, data retention, deletion on request.

Minimum technical controls (implementation recommendations)
- TLS 1.3 termination at load balancer. Enforce HSTS and secure cookies.
- Use OIDC provider with short-lived access tokens and refresh tokens (rotate).
- Enforce RBAC: only clinicians with "emr.write" scope may trigger FHIR writes.
- Ephemeral store: Redis with TLS, with strict ACLs and key TTL (e.g., 5 minutes).
- Secrets: store in Managed KMS (AWS KMS / Azure KeyVault / GCP KMS).
- LLM calls: redact PHI prior to external calls; if possible, use on-prem or BAA-capable providers and use training opt-out.
- Logging: structured logs (JSON) with redaction middleware. Mask transcripts and audio names.
- Monitoring: SIEM alerts for unusual accesses; retention policies for logs (no PHI).
- Data Subject Rights: endpoints to handle deletion / access requests; maintain minimal metadata to verify the request without PHI.

Privacy-by-design features
- Consent capture prior to any audio recording.
- Anonymous intake option (no name) for sensitive visits.
- Local policy agent validates content against MADO rules before persistence or LLM use.
- Client-to-EMR flows: prefer sending FHIR references (Patient/Encounter reference) rather than raw identifier strings.

Operational & legal
- Perform Privacy Impact Assessment (PIA) for Loi 25.
- Draft SOPs for breach response and data subject requests.
- Maintain documentation of third-party processors and data flows.

```