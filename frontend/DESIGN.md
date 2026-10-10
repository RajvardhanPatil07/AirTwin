# Light glass dashboard

The user-selected light glass AirTwin image (27 September 2026) supersedes the earlier civic dashboard reference.

- Pale ice blue canvas, atmospheric landscape backdrop, translucent pearl glass, navy text, teal actions.
- A 62/38 map and scenario workspace, stacking below 850px.
- Slim header, honest snapshot notices, workspace title, scenario comparison shown once.
- Locally bundled Inter and existing Lucide icons.
- Leaflet retains real OpenStreetMap geography and interactive selection. Raised grid faces encode concentration visually, not terrain elevation.
- Observed, modeled, synthetic and stale labels remain truthful. Values come from existing APIs and demo engine.
- Ranking and assumptions use progressive disclosure; all analysis tabs remain available.
- Light theme defaults; dark theme and reduced-motion preference remain supported.

## Guided experience, 10 October 2026

The selected eight-step board at `../../output/ui-concepts/airtwin-guided-workflow.png` is the visual authority for the default frontend. The original glass dashboard remains behind Advanced view with its previous design and APIs.

- Operate mode: choose a Pune + PCMC area, see example air levels, forecast, source assumptions, action comparison, plan constraints, evidence and review.
- White panels on `#f5f8f6`, dark blue-green text `#102b32`, green actions `#086440`, thin `#dce7e1` borders. Preserve locally bundled Inter and Lucide icons.
- A 1,230px maximum shell, 16px workspace corners, restrained 10px panel corners, one shared horizontal eight-step navigation. On mobile, navigation scrolls within its own container while content stacks without document overflow.
- Vengeance UI Spotlight Navbar and Animated Button are adapted for controlled state, Vite, native button semantics and reduced motion. Preserve their MIT attribution under `src/components/ui/`.
- Leaflet displays OpenStreetMap geography. Guide values and heatmap overlays are illustrative. Compact before/after maps omit zoom controls to keep popups readable.
- Date-aware forecast labels, stable Recharts rendering, explicit offline assistant fallback, amber infeasible-plan warnings carried into Review, and a downloadable JSON example review.
- Dark theme remains an optional local guide state. No live-health or measured-improvement claim is made by the guide.

The guided experience now uses backend location values and grid cells. Forecast, source, scenario, planning and validation panels share the existing API contracts. Keep the white/green guide shell and Vengeance navigation/buttons. Planning amounts use backend INR costs; modeled action responses remain assumption based. Offline illustration is used only when the initial dashboard connection fails or demo mode is explicitly configured.
