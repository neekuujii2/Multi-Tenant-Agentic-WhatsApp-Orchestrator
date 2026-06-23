import type { ChatSession } from "../types";
import { AlertCircle, CheckCircle2, Clock, MessageCircle } from "lucide-react";

interface SessionListProps {
  sessions: ChatSession[];
  selectedSessionId: string;
  onSelectSession: (session: ChatSession) => void;
  statusFilter: string;
  setStatusFilter: (status: string) => void;
  loading: boolean;
}

export const SessionList: React.FC<SessionListProps> = ({
  sessions,
  selectedSessionId,
  onSelectSession,
  statusFilter,
  setStatusFilter,
  loading,
}) => {
  const totalSessions = sessions.length;
  const handoverSessions = sessions.filter((session) => session.status === "NEEDS_HUMAN").length;
  const resolvedSessions = sessions.filter((session) => session.status === "RESOLVED").length;

  const formatTime = (dateStr?: string) => {
    if (!dateStr) return "";
    const date = new Date(dateStr);
    return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  };

  const getSentimentEmoji = (score?: number) => {
    if (score === undefined || score === null) return "😐";
    if (score < -0.4) return "😡";
    if (score > 0.4) return "😊";
    return "😐";
  };

  const getSentimentColor = (score?: number) => {
    if (score === undefined || score === null) return "var(--text-muted)";
    if (score < -0.4) return "var(--danger)";
    if (score > 0.4) return "var(--success)";
    return "var(--warning)";
  };

  return (
    <div className="session-panel">
      <div className="session-summary">
        <div className="session-stat">
          <strong>{totalSessions}</strong>
          <span>Total chats</span>
        </div>
        <div className="session-stat">
          <strong>{handoverSessions}</strong>
          <span>Need human</span>
        </div>
        <div className="session-stat">
          <strong>{resolvedSessions}</strong>
          <span>Resolved</span>
        </div>
      </div>

      <div className="session-filter-bar">
        {["ALL", "NEEDS_HUMAN", "AGENT_RESPONDING", "RESOLVED"].map((status) => (
          <button
            key={status}
            onClick={() => setStatusFilter(status)}
            className={`btn session-filter ${statusFilter === status ? "is-active" : ""}`}
          >
            {status.replace("_", " ")}
          </button>
        ))}
      </div>

      <div className="session-list-scroll">
        {loading ? (
          <div className="section-banner">
            <span>Refreshing sessions...</span>
          </div>
        ) : sessions.length === 0 ? (
          <div className="session-empty" style={{ padding: "48px 16px", color: "var(--text-muted)" }}>
            <MessageCircle size={28} />
            <span style={{ fontSize: "0.85rem", fontWeight: 500 }}>No sessions found</span>
          </div>
        ) : (
          sessions.map((session) => {
            const isSelected = session.session_id === selectedSessionId;
            const sentiment = session.context_vars?.sentiment_score;

            return (
              <div
                key={session.session_id}
                onClick={() => onSelectSession(session)}
                className={`animate-fade-in session-card ${isSelected ? "is-selected" : ""}`}
              >
                <div className="session-card-top">
                  <span className="session-card-phone">{session.customer_phone}</span>
                  <span className="session-card-time" style={{ display: "flex", alignItems: "center", gap: "4px" }}>
                    <Clock size={10} />
                    {formatTime(session.last_message_at)}
                  </span>
                </div>

                <div className="session-card-meta">
                  <span style={{ maxWidth: "170px", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                    Language: <b style={{ color: "var(--primary)" }}>{session.context_vars?.language?.toUpperCase() || "EN"}</b>
                  </span>
                  <span
                    style={{
                      color: getSentimentColor(sentiment),
                      fontWeight: 600,
                      display: "flex",
                      alignItems: "center",
                      gap: "4px",
                    }}
                  >
                    {getSentimentEmoji(sentiment)} {sentiment !== undefined && sentiment !== null ? sentiment.toFixed(1) : ""}
                  </span>
                </div>

                <div style={{ display: "flex", gap: "6px", marginTop: "10px", flexWrap: "wrap" }}>
                  {session.status === "NEEDS_HUMAN" && (
                    <span className="badge badge-needs-human">
                      <AlertCircle size={10} /> Handover
                    </span>
                  )}
                  {session.status === "AGENT_RESPONDING" && (
                    <span className="badge badge-responding">
                      <MessageCircle size={10} /> Bot active
                    </span>
                  )}
                  {session.status === "RESOLVED" && (
                    <span className="badge badge-resolved">
                      <CheckCircle2 size={10} /> Resolved
                    </span>
                  )}
                  {session.status === "WAITING_FOR_BOT" && (
                    <span className="badge badge-waiting">
                      <Clock size={10} /> Queued
                    </span>
                  )}
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};
