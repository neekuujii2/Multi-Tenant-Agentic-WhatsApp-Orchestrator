import type { AnalyticsData, ChatSession, DashboardEvent, Message, Tenant } from "./types";

const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

export async function fetchTenants(): Promise<Tenant[]> {
  const resp = await fetch(`${API_BASE}/dashboard/tenants`);
  if (!resp.ok) throw new Error("Failed to fetch tenants");
  return resp.json();
}

export async function fetchTenant(tenantId: string): Promise<Tenant> {
  const resp = await fetch(`${API_BASE}/dashboard/tenants/${tenantId}`);
  if (!resp.ok) throw new Error("Failed to fetch tenant");
  return resp.json();
}

export async function fetchSessions(
  tenantId: string,
  status?: string
): Promise<ChatSession[]> {
  const url = new URL(`${API_BASE}/dashboard/tenants/${tenantId}/sessions`);
  if (status) url.searchParams.append("status", status);
  const resp = await fetch(url.toString());
  if (!resp.ok) throw new Error("Failed to fetch sessions");
  return resp.json();
}

export async function fetchMessages(sessionId: string): Promise<Message[]> {
  const resp = await fetch(`${API_BASE}/dashboard/sessions/${sessionId}/messages`);
  if (!resp.ok) throw new Error("Failed to fetch messages");
  return resp.json();
}

export async function resolveSession(sessionId: string): Promise<void> {
  const resp = await fetch(`${API_BASE}/dashboard/sessions/${sessionId}/resolve`, {
    method: "POST",
  });
  if (!resp.ok) throw new Error("Failed to resolve session");
}

export async function takeoverSession(sessionId: string): Promise<void> {
  const resp = await fetch(`${API_BASE}/dashboard/sessions/${sessionId}/takeover`, {
    method: "POST",
  });
  if (!resp.ok) throw new Error("Failed to takeover session");
}

export async function sendReply(
  sessionId: string,
  text: string,
  status: "RESOLVED" | "NEEDS_HUMAN" = "RESOLVED"
): Promise<void> {
  const resp = await fetch(`${API_BASE}/dashboard/sessions/${sessionId}/reply`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text, status }),
  });
  if (!resp.ok) throw new Error("Failed to send reply");
}

export async function fetchAnalytics(tenantId: string): Promise<AnalyticsData> {
  const resp = await fetch(`${API_BASE}/dashboard/tenants/${tenantId}/analytics`);
  if (!resp.ok) throw new Error("Failed to fetch analytics");
  return resp.json();
}

export async function sendBroadcast(
  tenantId: string,
  templateId: string,
  cohort: string
): Promise<{ sent_count: number }> {
  const resp = await fetch(`${API_BASE}/dashboard/tenants/${tenantId}/broadcast`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ template_id: templateId, cohort }),
  });
  if (!resp.ok) throw new Error("Failed to send broadcast");
  return resp.json();
}

export function subscribeToTenantEvents(
  tenantId: string,
  onEvent: (data: DashboardEvent) => void
): () => void {
  const url = `${API_BASE}/dashboard/tenants/${tenantId}/events`;
  const eventSource = new EventSource(url);

  eventSource.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      onEvent(data);
    } catch (e) {
      console.error("Failed to parse SSE payload", e);
    }
  };

  eventSource.onerror = (e) => {
    console.error("SSE connection error", e);
  };

  // Return unsubscribe cleanup function
  return () => {
    eventSource.close();
  };
}
