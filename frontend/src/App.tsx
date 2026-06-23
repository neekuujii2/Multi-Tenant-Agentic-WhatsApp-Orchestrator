import { useEffect, useState } from "react";
import { Header } from "./components/Header";
import { TenantSelector } from "./components/TenantSelector";
import { SessionList } from "./components/SessionList";
import { ChatWindow } from "./components/ChatWindow";
import { AnalyticsView } from "./components/AnalyticsView";
import { BroadcastModal } from "./components/BroadcastModal";
import type { AnalyticsData, ChatSession, Message, Tenant } from "./types";
import {
  fetchTenants,
  fetchSessions,
  fetchMessages,
  resolveSession,
  takeoverSession,
  sendReply,
  fetchAnalytics,
  sendBroadcast,
  subscribeToTenantEvents,
} from "./api";

function App() {
  const [theme, setTheme] = useState<"light" | "dark">(() => {
    if (typeof window === "undefined") return "light";
    const storedTheme = window.localStorage.getItem("wa-orchestrator-theme");
    if (storedTheme === "light" || storedTheme === "dark") return storedTheme;
    return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
  });

  const [currentTab, setCurrentTab] = useState<"inbox" | "analytics" | "campaigns">("inbox");
  const [tenants, setTenants] = useState<Tenant[]>([]);
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [messages, setMessages] = useState<Message[]>([]);
  const [analytics, setAnalytics] = useState<AnalyticsData | null>(null);
  const [selectedTenantId, setSelectedTenantId] = useState<string>("");
  const [selectedSession, setSelectedSession] = useState<ChatSession | null>(null);
  const [statusFilter, setStatusFilter] = useState<string>("ALL");
  const [loadingTenants, setLoadingTenants] = useState(true);
  const [loadingSessions, setLoadingSessions] = useState(false);
  const [loadingMessages, setLoadingMessages] = useState(false);
  const [loadingAnalytics, setLoadingAnalytics] = useState(false);
  const [sendingReply, setSendingReply] = useState(false);
  const [sendingBroadcast, setSendingBroadcast] = useState(false);
  const [appError, setAppError] = useState<string>("");
  const selectedSessionId = selectedSession?.session_id ?? "";
  const isSseLive = Boolean(selectedTenantId);

  useEffect(() => {
    document.documentElement.classList.toggle("dark", theme === "dark");
    window.localStorage.setItem("wa-orchestrator-theme", theme);
  }, [theme]);

  useEffect(() => {
    async function loadInitialData() {
      try {
        const tenantList = await fetchTenants();
        setTenants(tenantList);
        if (tenantList.length > 0) {
          setSelectedTenantId(tenantList[0].tenant_id);
        }
        setAppError("");
      } catch (err) {
        console.error("Failed to load tenants", err);
        setAppError("Unable to load tenants. Check whether the backend API is running.");
      } finally {
        setLoadingTenants(false);
      }
    }

    loadInitialData();
  }, []);

  useEffect(() => {
    if (!selectedTenantId) return;

    async function loadSessions() {
      setLoadingSessions(true);
      try {
        const filter = statusFilter === "ALL" ? undefined : statusFilter;
        const sessionList = await fetchSessions(selectedTenantId, filter);
        setSessions(sessionList);
        setAppError("");

        if (selectedSessionId) {
          const match = sessionList.find((session) => session.session_id === selectedSessionId);
          setSelectedSession(match ?? null);
        }
      } catch (err) {
        console.error("Failed to load sessions", err);
        setAppError("Unable to load sessions for the selected tenant.");
      } finally {
        setLoadingSessions(false);
      }
    }

    loadSessions();
  }, [selectedTenantId, selectedSessionId, statusFilter]);

  useEffect(() => {
    if (!selectedSessionId) return;

    async function loadMessages() {
      setLoadingMessages(true);
      try {
        const msgList = await fetchMessages(selectedSessionId);
        setMessages(msgList);
        setAppError("");
      } catch (err) {
        console.error("Failed to load messages", err);
        setAppError("Unable to load the conversation thread right now.");
      } finally {
        setLoadingMessages(false);
      }
    }

    loadMessages();
  }, [selectedSessionId]);

  useEffect(() => {
    if (currentTab !== "analytics" || !selectedTenantId) return;

    async function loadAnalytics() {
      setLoadingAnalytics(true);
      try {
        const data = await fetchAnalytics(selectedTenantId);
        setAnalytics(data);
        setAppError("");
      } catch (err) {
        console.error("Failed to load analytics", err);
        setAppError("Unable to load analytics for this tenant.");
      } finally {
        setLoadingAnalytics(false);
      }
    }

    loadAnalytics();
  }, [currentTab, selectedTenantId]);

  useEffect(() => {
    if (!selectedTenantId) return;

    const unsubscribe = subscribeToTenantEvents(selectedTenantId, (eventData) => {
      const { event, session_id, status, message } = eventData;

      if ((event === "inbound_message" || event === "outbound_message") && message) {
        if (selectedSession?.session_id === session_id) {
          setMessages((prev) => {
            if (prev.some((item) => item.message_id === message.message_id)) return prev;
            return [...prev, message];
          });
        }

        setSessions((prevSessions) => {
          const exists = prevSessions.some((session) => session.session_id === session_id);

          if (exists) {
            return prevSessions
              .map((session) => {
                if (session.session_id === session_id) {
                  return {
                    ...session,
                    status,
                    message_count: session.message_count + 1,
                    last_message_at: new Date().toISOString(),
                    context_vars: {
                      ...session.context_vars,
                      sentiment_score: message.agent_meta?.sentiment_score ?? session.context_vars?.sentiment_score,
                      language: message.agent_meta?.detected_language ?? session.context_vars?.language,
                    },
                  };
                }

                return session;
              })
              .sort((a, b) => {
                const dateA = a.last_message_at ? new Date(a.last_message_at).getTime() : 0;
                const dateB = b.last_message_at ? new Date(b.last_message_at).getTime() : 0;
                return dateB - dateA;
              });
          }

          const newSession: ChatSession = {
            session_id,
            tenant_id: selectedTenantId,
            customer_phone: message.sender === "BOT" ? "Customer" : message.sender,
            status,
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
            last_message_at: new Date().toISOString(),
            message_count: 1,
            context_vars: {
              language: message.agent_meta?.detected_language ?? "en",
              sentiment_score: message.agent_meta?.sentiment_score ?? 0,
            },
            flags: {
              needs_human: status === "NEEDS_HUMAN",
              is_frustrated: status === "NEEDS_HUMAN",
              broadcast_eligible: true,
            },
          };

          return [newSession, ...prevSessions];
        });
      }

      if (event === "session_status_changed") {
        setSessions((prev) => prev.map((session) => (session.session_id === session_id ? { ...session, status } : session)));
        if (selectedSession?.session_id === session_id) {
          setSelectedSession((prev) => (prev ? { ...prev, status } : null));
        }
      }
    });

    return unsubscribe;
  }, [selectedSession, selectedTenantId]);

  const handleResolve = async () => {
    if (!selectedSession) return;
    try {
      await resolveSession(selectedSession.session_id);
      setSelectedSession((prev) => (prev ? { ...prev, status: "RESOLVED" } : null));
      setAppError("");
    } catch {
      setAppError("Failed to resolve the session.");
    }
  };

  const handleTakeover = async () => {
    if (!selectedSession) return;
    try {
      await takeoverSession(selectedSession.session_id);
      setSelectedSession((prev) => (prev ? { ...prev, status: "NEEDS_HUMAN" } : null));
      setAppError("");
    } catch {
      setAppError("Failed to take over the session.");
    }
  };

  const handleSendReply = async (text: string, status: "RESOLVED" | "NEEDS_HUMAN") => {
    if (!selectedSession) return;
    setSendingReply(true);
    try {
      await sendReply(selectedSession.session_id, text, status);
      setAppError("");
    } catch {
      setAppError("Failed to send the manual reply.");
    } finally {
      setSendingReply(false);
    }
  };

  const handleSendBroadcast = async (templateId: string, cohort: string) => {
    if (!selectedTenantId) return;
    setSendingBroadcast(true);
    try {
      const res = await sendBroadcast(selectedTenantId, templateId, cohort);
      setAppError("");
      alert(`Broadcast sent successfully to ${res.sent_count} subscribers.`);
      setCurrentTab("inbox");
    } catch {
      setAppError("Failed to launch the campaign broadcast.");
    } finally {
      setSendingBroadcast(false);
    }
  };

  const currentTenant = tenants.find((tenant) => tenant.tenant_id === selectedTenantId) || null;

  if (loadingTenants) {
    return (
      <div className="app-loader-screen">
        <div className="app-loader-card glass-panel">
          <p className="eyebrow">Connecting Dashboard</p>
          <h1>Loading tenant workspace...</h1>
          <span className="loader-line" />
        </div>
      </div>
    );
  }

  return (
    <div className="app-container">
      <Header
        currentTab={currentTab}
        setCurrentTab={setCurrentTab}
        tenantName={currentTenant?.name || ""}
        isLive={isSseLive}
        theme={theme}
        onToggleTheme={() => setTheme((prev) => (prev === "light" ? "dark" : "light"))}
      />

      <div className="app-shell">
        {appError && (
          <div className="section-banner section-banner-error">
            <span>{appError}</span>
            <button className="btn btn-secondary" onClick={() => setAppError("")}>
              Dismiss
            </button>
          </div>
        )}

        {currentTab === "inbox" && (
          <div className="main-content inbox-layout">
            <div className="sidebar-column">
              <TenantSelector
                tenants={tenants}
                selectedTenantId={selectedTenantId}
                onSelectTenant={(id) => {
                  setMessages([]);
                  setSelectedTenantId(id);
                  setSelectedSession(null);
                }}
              />
              <div className="sidebar-scroll-region">
                <SessionList
                  sessions={sessions}
                  selectedSessionId={selectedSession?.session_id || ""}
                  onSelectSession={(session) => {
                    setMessages([]);
                    setSelectedSession(session);
                  }}
                  statusFilter={statusFilter}
                  setStatusFilter={setStatusFilter}
                  loading={loadingSessions}
                />
              </div>
            </div>

            <div className="view-panel">
              <ChatWindow
                session={selectedSession}
                messages={messages}
                onSendReply={handleSendReply}
                onResolve={handleResolve}
                onTakeover={handleTakeover}
                sending={sendingReply}
                loading={loadingMessages}
              />
            </div>
          </div>
        )}

        {currentTab === "analytics" && (
          <div className="tab-panel tab-shell">
            <AnalyticsView data={analytics} loading={loadingAnalytics} />
          </div>
        )}

        {currentTab === "campaigns" && (
          <div className="tab-panel tab-shell">
            <BroadcastModal
              tenant={currentTenant}
              onSendBroadcast={handleSendBroadcast}
              sending={sendingBroadcast}
            />
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
