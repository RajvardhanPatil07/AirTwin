import { lazy, Suspense, useEffect, useState } from "react";
import { LandingPage } from "./pages/LandingPage";

const DecisionStudio = lazy(() =>
  import("./pages/DecisionStudio").then((module) => ({ default: module.DecisionStudio })),
);

type Page = "home" | "map" | "forecast" | "sources" | "scenarios" | "validation";
const pages: Page[] = ["home", "map", "forecast", "sources", "scenarios", "validation"];

function readRoute(): Page {
  const path = window.location.hash.replace(/^#\/?/, "").split(/[/?]/)[0];
  if (path === "overview" || path === "dashboard") return "map";
  return pages.includes(path as Page) ? (path as Page) : "home";
}

export default function App() {
  const [page, setPage] = useState<Page>(readRoute);

  useEffect(() => {
    const onRoute = () => {
      setPage(readRoute());
      window.scrollTo({ top: 0, behavior: "instant" });
    };
    window.addEventListener("hashchange", onRoute);
    return () => window.removeEventListener("hashchange", onRoute);
  }, []);

  const navigate = (next: Exclude<Page, "home">) => {
    const target = "#/" + next;
    if (window.location.hash !== target) window.location.hash = target;
    else window.scrollTo({ top: 0, behavior: "smooth" });
  };

  if (page === "home") return <LandingPage />;
  return (
    <Suspense fallback={
      <main className="air-route-loading" role="status">
        <span>AirTwin / ENR–01</span>
        <p>Opening the {page} workspace…</p>
      </main>
    }>
      <DecisionStudio
        view={page === "map" ? "overview" : page}
        onNavigate={(next) => navigate(next === "overview" ? "map" : next)}
      />
    </Suspense>
  );
}
