import React, { useState, useRef, useEffect } from "react";

type Props = {
  oauthToken: string;
  language?: "fr" | "en";
  sessionId: string;
  onResult?: (result: any) => void;
};

export default function AudioRecorder({ oauthToken, language = "fr", sessionId, onResult }: Props) {
  const [recording, setRecording] = useState(false);
  const [consented, setConsented] = useState(false);
  const [anonymous, setAnonymous] = useState(false);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const [chunks, setChunks] = useState<Blob[]>([]);

  useEffect(() => {
    return () => {
      if (mediaRecorderRef.current && mediaRecorderRef.current.state !== "inactive") {
        mediaRecorderRef.current.stop();
      }
    };
  }, []);

  async function startRecording() {
    if (!consented) {
      alert(language === "fr" ? "Veuillez consentir avant l'enregistrement." : "Please consent before recording.");
      return;
    }
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    const mr = new MediaRecorder(stream);
    mediaRecorderRef.current = mr;
    mr.ondataavailable = (e) => setChunks((prev) => [...prev, e.data]);
    mr.onstop = upload;
    mr.start();
    setRecording(true);
  }

  function stopRecording() {
    const mr = mediaRecorderRef.current;
    if (mr && mr.state !== "inactive") mr.stop();
    setRecording(false);
  }

  async function upload() {
    const blob = new Blob(chunks, { type: "audio/webm" });
    setChunks([]);
    const form = new FormData();
    form.append("audio", blob, "recording.webm");
    form.append("session", sessionId);
    form.append("language", language);
    form.append("anonymous", String(anonymous));

    const res = await fetch("/transcribe", {
      method: "POST",
      body: form,
      headers: {
        Authorization: `Bearer ${oauthToken}`
      }
    });
    if (!res.ok) {
      const text = await res.text();
      alert("Upload failed: " + text);
      return;
    }
    const data = await res.json();
    onResult?.(data);
  }

  return (
    <div className="recorder">
      <label>
        <input type="checkbox" checked={consented} onChange={(e) => setConsented(e.target.checked)} />
        {language === "fr" ? "Consentement donné" : "Consent given"}
      </label>
      <label>
        <input type="checkbox" checked={anonymous} onChange={(e) => setAnonymous(e.target.checked)} />
        {language === "fr" ? "Saisie anonyme" : "Anonymous intake"}
      </label>

      {!recording ? (
        <button onClick={startRecording}>{language === "fr" ? "Démarrer" : "Start"}</button>
      ) : (
        <button onClick={stopRecording}>{language === "fr" ? "Arrêter" : "Stop"}</button>
      )}
    </div>
  );
}