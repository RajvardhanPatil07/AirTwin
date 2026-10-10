import { afterEach, describe, expect, it, vi } from "vitest";

afterEach(() => {
  vi.unstubAllEnvs();
  vi.unstubAllGlobals();
  vi.resetModules();
});
describe("API availability and provenance", () => {
  it("runs without making API calls when frontend-only demo mode is explicitly configured", async () => {
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
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({ source_type: "modeled", stations: [] }),
      }),
    );
    const { loadDashboard } = await import("./api");
    expect((await loadDashboard()).demo).toBe(true);
  });
});


describe("optimized dashboard bootstrap", () => {
  const bundle = {
    source_type: "modeled",
    assumptions: ["Grid interpolation is modeled"],
    stations: [{
      id: "s1", name: "Monitor", short_name: "Monitor",
      pm25: 23, latitude: 18.6, longitude: 73.8,
      timestamp: "2026-10-10T10:00:00+05:30",
      source_type: "observed", assumptions: ["OpenAQ observation"],
    }],
    cells: [{
      id: "cell-0", latitude: 18.6, longitude: 73.8, pm25: 24,
      bounds: [[18.59, 73.79], [18.61, 73.81]],
      source_type: "modeled", assumptions: ["Interpolation"],
    }],
  };

  it("loads stations and hotspots with one network call, deduplicating simultaneous readers", async () => {
    vi.stubEnv("VITE_API_BASE_URL", "http://test.invalid");
    const fetch = vi.fn().mockResolvedValue({
      ok: true, json: async () => bundle,
    });
    vi.stubGlobal("fetch", fetch);
    const { loadDashboard } = await import("./api");
    const [first, second] = await Promise.all([loadDashboard(), loadDashboard()]);
    expect(fetch).toHaveBeenCalledTimes(1);
    expect(first.demo).toBe(false);
    expect(second.cells[0].source_type).toBe("modeled");
    expect(first.stations[0].source_type).toBe("observed");
    await loadDashboard(null, "pcmc", true);
    expect(fetch).toHaveBeenCalledTimes(2);
  });

  it("falls back to legacy API on a missing bootstrap route", async () => {
    vi.stubEnv("VITE_API_BASE_URL", "http://test.invalid");
    const fetch = vi.fn().mockImplementation(async (uri: string) => {
      if (uri.includes("/v2/bootstrap")) {
        return { ok: false, status: 404, json: async () => ({}) };
      }
      return {
        ok: true,
        json: async () => uri.includes("/stations")
          ? { source_type: "modeled", assumptions: ["Provider"], stations: bundle.stations }
          : { source_type: "modeled", assumptions: ["IDW"], cells: bundle.cells },
      };
    });
    vi.stubGlobal("fetch", fetch);
    const { loadDashboard } = await import("./api");
    const response = await loadDashboard();
    expect(response.demo).toBe(false);
    expect(fetch).toHaveBeenCalledTimes(3);
  });
});
