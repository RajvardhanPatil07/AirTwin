import { useEffect, useRef, useState } from "react";
import { MessageCircle, X } from "lucide-react";
import type { Station, ExplainResponse, RegionId, Cuts } from "../types";
import { api } from "../lib/api";
import { DataBadge } from "./DataBadge";

export function AskAirTwin({
  location,
  demo,
  replayAt,
  region,
  cuts,
  hours,
}: {
  location: Station;
  demo: boolean;
  replayAt: string | null;
  region: RegionId;
  cuts: Cuts;
  hours: number;
}) {
  const [open, setOpen] = useState(false);
  const [question, setQuestion] = useState("Why is pollution high here?");
  const [answer, setAnswer] = useState<ExplainResponse | null>(null);
  const [history, setHistory] = useState<{ role: string; content: string }[]>(
    [],
  );
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const requestVersion = useRef(0);
  const trigger = useRef<HTMLButtonElement>(null);
  const input = useRef<HTMLInputElement>(null);
  useEffect(() => {
    requestVersion.current += 1;
    setBusy(false);
    setAnswer(null);
    setHistory([]);
    setError(null);
  }, [location.id, replayAt, region, cuts, hours]);
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
            Gemini reads this location’s forecast, weather, source proxies,
            applied interventions and validation. Each answer cites computed
            evidence.
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
                  region,
                  cuts,
                  hours,
                  history.slice(-8),
                );
                if (version === requestVersion.current) {
                  setAnswer(result);
                  setHistory((previous) =>
                    [
                      ...previous,
                      { role: "user", content: question },
                      { role: "assistant", content: result.answer },
                    ].slice(-8),
                  );
                }
              } catch (failure) {
                if (version === requestVersion.current)
                  setError(
                    failure instanceof Error
                      ? failure.message
                      : "Gemini could not answer. Please retry.",
                  );
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
              {answer.claims.map((claim, index) => (
                <div key={index}>
                  <DataBadge source={claim.source_type} />
                  <p>{claim.text}</p>
                  <small>Evidence: {claim.evidence_ids.join(", ")}</small>
                </div>
              ))}
              <small>Model: {answer.model}</small>
            </div>
          )}
        </section>
      )}
    </>
  );
}
