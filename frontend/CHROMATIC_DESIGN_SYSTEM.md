# AirTwin / Chromatic Design System

This is the frontend-specific visual specification for the \`dev/parth-overhaul\` branch. The design keeps the previous API, data model, map interactions and provenance logic.

## Direction
A clear, vibrant, high-trust decision-support workspace rather than a dense generic admin dashboard. Electric indigo and cobalt are navigation and action colors, aqua/mint is the benefit accent, warm coral distinguishes forecasts, and air-quality heatmap colors retain their **established concentration meanings**. Never recolor severity bands to match branding.

| Token | Hex | Role |
|---|---|---|
| Ink | \`#111936\` | High contrast foreground |
| Sidebar | \`#0b1432\` | Persistent navigation surface |
| Ultraviolet | \`#6958f7\` | Active, selected, focused |
| Cobalt | \`#4062f5\` | Actions and modeled analytic accents |
| Aqua | \`#00b7da\` | Forecast and exploratory accents |
| Mint | \`#04b89e\` | Benefits, change and verified status |
| Coral | \`#fb775f\` | Forecast differentiation only |
| Canvas | \`#f5f7ff\` | Workspace background |

## Type
Inter (bundled with \`@fontsource/inter\`) is the UI font. Primary title 31–48px with strong weight 800 and negative tracking; panel titles 18–22px; running text at least 13px where space permits; provenance badges at least 10px. The primary CTA must be visibly dominant.

## Interaction
- Visible focus rings and keyboard-operable buttons and Leaflet station points.
- Mobile navigation has a dismissible backdrop; in compact view, selecting a section scrolls to the analysis panel.
- Section tabs expose \`tablist\`, \`tab\`, \`tabpanel\` with linked IDs for assistive technology.
- A keyboard-accessible skip link bypasses persistent navigation.
- Reduced-motion settings disable nonessential transitions.
- The app still labels observed, modeled and synthetic data separately; never imply modeled forecasts are observed sensor measurements.

## QA and limitations
The React/Vite build, ESLint and existing Vitest suites run in GitHub Actions. Browser-based pixel review is pending a deployed or locally accessible build. The generated earlier static design previews are **not** verified running-app screenshots.
