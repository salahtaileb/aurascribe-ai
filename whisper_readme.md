```markdown
# Whisper (local) — guide d'intégration pour AuraScribe (FR par défaut)

Pourquoi utiliser Whisper local ?
- Évite coûts d'API externes et réduit exposition PHI à des fournisseurs.
- Permet exécution on‑premise ou dans VPC privé (conformité Loi 25).
- Inconvénients : nécessite CPU ou idéalement GPU; latence sur CPU.

Installation rapide
- GPU recommandée: installer PyTorch compatible CUDA, puis:
  pip install git+https://github.com/m-bain/whisperx.git
- CPU: pip install -U openai-whisper

Configuration
- .env:
  STT_BACKEND=whisper
  WHISPER_MODEL=small  # tiny | small | medium | large (large require GPU)
- Prétraitez audio en mono 16kHz WAV pour meilleure qualité.

Exécution
- Whisper s'exécute dans le même conteneur API ou sur un service dédié (si GPU).
- Pour latence plus faible, utilisez modèle small/tiny sur CPU, medium+ sur GPU.

Sécurité
- Garder le service dans VPC / réseau privé.
- Ne pas envoyer audio à l'extérieur sans redaction/consentement.