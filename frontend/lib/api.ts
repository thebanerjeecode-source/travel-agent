import type { PlanRequest, PlanResponse } from "./types";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function parseError(response: Response): Promise<string> {
  try {
    const data = await response.json();
    if (typeof data.detail === "string") return data.detail;
    if (Array.isArray(data.detail)) return data.detail.map((d: { msg?: string }) => d.msg).join(", ");
    return JSON.stringify(data);
  } catch {
    return response.statusText || "Request failed";
  }
}

export async function createPlan(body: PlanRequest): Promise<PlanResponse> {
  const response = await fetch(`${API_URL}/api/v1/plans`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!response.ok) {
    throw new Error(await parseError(response));
  }
  return response.json();
}

export async function fetchPlan(sessionId: string): Promise<PlanResponse> {
  const response = await fetch(`${API_URL}/api/v1/plans/${sessionId}`);
  if (!response.ok) {
    throw new Error(await parseError(response));
  }
  return response.json();
}

export function markdownUrl(sessionId: string): string {
  return `${API_URL}/api/v1/plans/${sessionId}/markdown`;
}

export function healthUrl(): string {
  return `${API_URL}/health`;
}

export { API_URL };
