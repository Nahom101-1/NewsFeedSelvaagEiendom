import type { AdminPayload, BriefPayload } from "@/lib/types";

/**
 * Flask owns the data; this app owns presentation. Both calls run on the
 * server, so the Flask origin never has to be reachable from the browser.
 */
export const flaskOrigin =
  process.env.FLASK_ORIGIN ?? "http://127.0.0.1:5000";

async function getJson<T>(path: string): Promise<T | null> {
  try {
    const response = await fetch(`${flaskOrigin}${path}`, {
      cache: "no-store",
    });
    if (!response.ok) return null;
    return (await response.json()) as T;
  } catch {
    // A dead API is a normal state during development; the pages render an
    // explanation rather than crashing.
    return null;
  }
}

export const getBrief = () => getJson<BriefPayload>("/api/brief");
export const getAdmin = () => getJson<AdminPayload>("/api/admin");
