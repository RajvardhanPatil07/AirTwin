export type WorkspaceView = "overview" | "forecast" | "sources" | "scenarios" | "validation";
export const workspacePaths: Record<WorkspaceView, string> = {
  overview: "/map",
  forecast: "/forecast",
  sources: "/sources",
  scenarios: "/interventions",
  validation: "/validation",
};
