import { Opportunity, SourceDescriptor } from "@/lib/types";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";
const DEFAULT_USER_KEY = "local-user";

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error(`API request failed: ${response.status}`);
  }

  return (await response.json()) as T;
}

export async function getOpportunities(params?: {
  applied?: boolean;
  status?: string;
}): Promise<Opportunity[]> {
  const query = new URLSearchParams({
    user_key: DEFAULT_USER_KEY,
    status: params?.status ?? "active",
  });

  if (typeof params?.applied === "boolean") {
    query.set("applied", String(params.applied));
  }

  return apiFetch<Opportunity[]>(`/opportunities?${query.toString()}`);
}

export async function getOpportunity(id: number): Promise<Opportunity> {
  return apiFetch<Opportunity>(
    `/opportunities/${id}?user_key=${encodeURIComponent(DEFAULT_USER_KEY)}`,
  );
}

export async function getSources(): Promise<SourceDescriptor[]> {
  return apiFetch<SourceDescriptor[]>("/ingest/sources");
}

export async function setAppliedState(
  id: number,
  isApplied: boolean,
): Promise<Opportunity> {
  return apiFetch<Opportunity>(`/opportunities/${id}/apply`, {
    method: "PATCH",
    body: JSON.stringify({
      user_key: DEFAULT_USER_KEY,
      is_applied: isApplied,
      documents_ready: [],
      notes: null,
    }),
  });
}
