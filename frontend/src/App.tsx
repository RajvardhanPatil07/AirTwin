import { lazy, Suspense, useEffect, useState } from "react";
import { LandingPage } from "./pages/LandingPage";
import type { WorkspaceView } from "./pages/routes";

const DecisionStudio = lazy(() => import("./pages/DecisionStudio").then((module) => ({ default: module.DecisionStudio })));

type Route = "home" | WorkspaceView;
const routes: Record<Route, string> = {
  home: "/",
  overview: "/map",
  forecast: "/forecast",
  sources: "/sources",
  scenarios: "/interventions",
  validation: "/validation",
};

function currentRoute(): Route {
  const path = window.location.pathname.replace(/\/+$/, "") || "/";
  if (path === "/dashboard" || path === "/overview") return "overview";
  return (Object.entries(routes).find(([, url]) => url === path)?.[0] as Route | undefined) ?? "home";
}

export default function App() {
  const [route, setRoute] = useState<Route>(currentRoute);

  useEffect(() => {
    const sync = () => setRoute(currentRoute());
    window.addEventListener("popstate", sync);
    return () => window.removeEventListener("popstate", sync);
  }, []);

  function navigate(next: Route) {
    if (next !== route) {
      window.history.pushState({}, "", routes[next]);
      setRoute(next);
      window.scrollTo({ top: 0, left: 0, behavior: "instant" });
    }
  }

  useEffect(() => {
    document.title = route === "home" ? "AirTwin — Read the air" :
      `${route === "overview" ? "Pollution map" : route === "scenarios" ? "Interventions" : route[0].toUpperCase() + route.slice(1)} | AirTwin`;
  }, [route]);

  if (route === "home") return <LandingPage onNavigate={navigate} />;
  return <Suspense fallback={<main className="at-route-loading" role="status">Opening AirTwin workspace…</main>}>
    <DecisionStudio view={route} onNavigate={navigate} />
  </Suspense>;
}
