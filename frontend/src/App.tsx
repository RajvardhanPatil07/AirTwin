import { lazy, Suspense, useState } from "react";
import { GuidedExperience } from "./pages/GuidedExperience";
import "./guided.css";

const AdvancedDashboard = lazy(async () => ({
  default: (await import("./pages/Dashboard")).Dashboard,
}));

export default function App() {
  const [advanced, setAdvanced] = useState(false);
  return advanced ? (
    <>
      <button className="guided-return" onClick={() => setAdvanced(false)}>
        Return to guided view
      </button>
      <Suspense
        fallback={
          <div className="at-app at-loading" role="status">
            Loading the advanced dashboard…
          </div>
        }
      >
        <AdvancedDashboard />
      </Suspense>
    </>
  ) : (
    <GuidedExperience onAdvanced={() => setAdvanced(true)} />
  );
}
