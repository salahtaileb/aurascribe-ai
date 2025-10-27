// frontend/BillingConfirmationModal.tsx
import React, { useState } from "react";

type Code = { icd10ca: string; ccp?: string; label: string; confidence?: number };

type Props = {
  visible: boolean;
  language?: "fr" | "en";
  suggestions: Code[];
  sessionId: string;
  oauthToken: string;
  onClose: (result?: any) => void;
};

export default function BillingConfirmationModal({ visible, language = "fr", suggestions, sessionId, oauthToken, onClose }: Props) {
  const [selected, setSelected] = useState<Code[]>(suggestions);

  if (!visible) return null;

  const title = language === "fr" ? "Codes de facturation proposés" : "Proposed billing codes";
  const instructions = language === "fr"
    ? "Vérifiez et modifiez les codes si nécessaire. Confirmez pour soumettre à la RAMQ."
    : "Review and edit codes if necessary. Confirm to submit to RAMQ.";

  async function submit() {
    const res = await fetch("/billing/submit", {
      method: "POST",
      headers: { "Content-Type": "application/json", "Authorization": `Bearer ${oauthToken}` },
      body: JSON.stringify({
        session_id: sessionId,
        selected_codes: selected,
        confirm: true,
        language
      })
    });
    const data = await res.json();
    onClose(data);
  }

  return (
    <div className="modal" role="dialog" aria-modal="true">
      <h2>{title}</h2>
      <p>{instructions}</p>
      <div className="codes-list">
        {selected.map((c, i) => (
          <div key={i} className="code-row">
            <input type="text" value={c.icd10ca} onChange={(e) => {
              const copy = [...selected]; copy[i].icd10ca = e.target.value; setSelected(copy);
            }} />
            <input type="text" value={c.ccp || ""} onChange={(e) => {
              const copy = [...selected]; copy[i].ccp = e.target.value; setSelected(copy);
            }} />
            <input type="text" value={c.label} onChange={(e) => {
              const copy = [...selected]; copy[i].label = e.target.value; setSelected(copy);
            }} />
            <button onClick={() => { setSelected(selected.filter((_, idx) => idx !== i)); }}>
              {language === "fr" ? "Retirer" : "Remove"}
            </button>
          </div>
        ))}
      </div>
      <div className="modal-actions">
        <button onClick={() => onClose()}>{language === "fr" ? "Annuler" : "Cancel"}</button>
        <button onClick={submit} className="primary">{language === "fr" ? "Soumettre à la RAMQ" : "Submit to RAMQ"}</button>
      </div>
    </div>
  );
}