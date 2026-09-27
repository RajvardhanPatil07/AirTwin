import { afterEach, describe, expect, it, vi } from "vitest";

afterEach(() => {
  vi.unstubAllEnvs();
  vi.unstubAllGlobals();
  vi.resetModules();
});
describe("API availability and provenance", () => {
  it("runs without making API calls when no backend is configured", async () => {
    vi.stubEnv("VITE_API_BASE_URL", "");
    const fetch = vi.fn();
    vi.stubGlobal("fetch", fetch);
    const { loadDashboard } = await import("./api");
    const data = await loadDashboard();
    expect(fetch).not.toHaveBeenCalled();
    expect(data.demo).toBe(true);
    expect(data.stations.every((s) => s.source_type === "synthetic")).toBe(
      true,
    );
  });
  it("falls back as a whole dashboard when the backend is unavailable", async () => {
    vi.stubEnv("VITE_API_BASE_URL", "http://test.invalid");
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new Error("offline")));
    const { loadDashboard } = await import("./api");
    const data = await loadDashboard();
    expect(data.demo).toBe(true);
    expect(data.warning).toContain("Backend unavailable");
    expect(
      data.cells.every((c) => c.population_source_type === "synthetic"),
    ).toBe(true);
  });
  it("rejects responses without provenance rather than assuming observed", async () => {
    vi.stubEnv("VITE_API_BASE_URL", "http://test.invalid");
    vi.stubGlobal(
      "fetch",
      vi
        .fn()
        .mockResolvedValue({ ok: true, json: async () => ({ stations: [] }) }),
    );
    const { loadDashboard } = await import("./api");
    expect((await loadDashboard()).demo).toBe(true);
  });
  it("rejects modeled responses without assumptions", async () => {
    vi.stubEnv("VITE_API_BASE_URL", "http://test.invalid");
    vi.stubGlobal(
      "fetch",
      vi
        .fn()
        .mockResolvedValue({
          ok: true,
          json: async () => ({ source_type: "modeled", stations: [] }),
        }),
    );
    const { loadDashboard } = await import("./api");
    expect((await loadDashboard()).demo).toBe(true);
  });
});
