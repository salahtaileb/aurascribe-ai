import React from "react";

type Props = {
  visible: boolean;
  language?: "fr" | "en";
  onAccept: (anonymous: boolean) => void;
  onDecline: () => void;
};

export default function ConsentModal({ visible, language = "fr", onAccept, onDecline }: Props) {
  if (!visible) return null;
  const text = language === "fr" ? {
    title: "Consentement à l'enregistrement",
    description: "En activant l'enregistrement, vous consentez au traitement audio pour la documentation clinique. L'audio et les transcriptions sont traités temporairement puis supprimés. Vous pouvez choisir une saisie anonyme.",
    accept: "J'accepte et j'enregistre",
    acceptAnon: "J'accepte — Saisie anonyme",
    decline: "Refuser"
  } : {
    title: "Recording Consent",
    description: "By enabling recording you consent to audio processing for clinical documentation. Audio and transcripts are processed temporarily and deleted after processing. You may choose anonymous intake.",
    accept: "I Agree and Record",
    acceptAnon: "I Agree — Anonymous Intake",
    decline: "Decline"
  };

  return (
    <div role="dialog" aria-modal="true" className="consent-modal">
      <h2>{text.title}</h2>
      <p>{text.description}</p>
      <div className="consent-actions">
        <button onClick={() => onAccept(false)} className="primary">{text.accept}</button>
        <button onClick={() => onAccept(true)} className="secondary">{text.acceptAnon}</button>
        <button onClick={onDecline} className="tertiary">{text.decline}</button>
      </div>
    </div>
  );
}