import { useEffect, useRef, useState } from "react";
import { MessageCircle, X } from "lucide-react";
import type { Station, ExplainResponse } from "../types";
import { api } from "../lib/api";
import { DataBadge } from "./DataBadge";

export function AskAirTwin({
  location,
  demo,
  replayAt,
}: {
  location: Station;
  demo: boolean;
  replayAt: string | null;
}) {
  const [open, setOpen] = useState(false);
  const [question, setQuestion] = useState("Why is pollution high here?");
  const [answer, setAnswer] = useState<ExplainResponse | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const requestVersion = useRef(0);
  const trigger = useRef<HTMLButtonElement>(null);
  const input = useRef<HTMLInputElement>(null);
  useEffect(() => {
    requestVersion.current += 1;
    setBusy(false);
    setAnswer(null);
    setError(null);
  }, [location.id, replayAt]);
  useEffect(() => {
    if (open) input.current?.focus();
  }, [open]);
  if (demo) return null;
  const close = () => {
    setOpen(false);
    trigger.current?.focus();
  };
  return (
    <>
      <button
        ref={trigger}
        className="ask-trigger"
        onClick={() => setOpen(true)}
        aria-expanded={open}
      >
        <MessageCircle size={15} /> Ask AirTwin
      </button>
      {open && (
        <section
          className="ask-drawer"
          role="dialog"
          aria-label="Ask AirTwin"
          onKeyDown={(event) => {
            if (event.key === "Escape") close();
          }}
        >
          <header>
            <div>
              <h2>Ask AirTwin</h2>
              <p>{location.name} · grounded in actual outputs</p>
            </div>
            <button aria-label="Close Ask AirTwin" onClick={close}>
              <X size={18} />
            </button>
          </header>
          <DataBadge source="modeled" detail="EXPLANATION" />
          <p className="helper">
            No LLM key is required. A grounded template is used when no provider
            is configured or its response fails checks.
          </p>
          <form
            onSubmit={async (event) => {
              event.preventDefault();
              const version = ++requestVersion.current;
              setBusy(true);
              setError(null);
              try {
                const result = await api.explain(
                  location.id,
                  question,
                  replayAt,
                );
                if (version === requestVersion.current) setAnswer(result);
              } catch {
                if (version === requestVersion.current)
                  setError("Could not generate an explanation. Please retry.");
              } finally {
                if (version === requestVersion.current) setBusy(false);
              }
            }}
          >
            <label htmlFor="air-question">Your question</label>
            <input
              ref={input}
              id="air-question"
              value={question}
              maxLength={1000}
              onChange={(event) => setQuestion(event.target.value)}
              required
            />
            <button className="run-button" disabled={busy}>
              {busy ? "Reading model outputs…" : "Explain this location"}
            </button>
          </form>
          {error && <p role="alert">{error}</p>}
          {answer && (
            <div className="ask-answer" aria-live="polite">
              <p>{answer.answer}</p>
              <small>Method: {answer.method.replaceAll("_", " ")}</small>
            </div>
          )}
        </section>
      )}
    </>
  );
}
