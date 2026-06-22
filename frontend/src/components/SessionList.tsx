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
  // Format dates nicely
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
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        height: "100%",
        borderRight: "1px solid var(--border-color)",
        background: "var(--bg-secondary)",
      }}
    >
      {/* Status Filters */}
      <div
        style={{
          display: "flex",
          gap: "4px",
          padding: "12px",
          background: "var(--bg-primary)",
          borderBottom: "1px solid var(--border-color)",
          overflowX: "auto",
        }}
      >
        {["ALL", "NEEDS_HUMAN", "AGENT_RESPONDING", "RESOLVED"].map((status) => (
          <button
            key={status}
            onClick={() => setStatusFilter(status)}
            className="btn"
            style={{
              padding: "6px 10px",
              fontSize: "0.7rem",
              fontWeight: 700,
              borderRadius: "6px",
              background: statusFilter === status ? "var(--primary)" : "var(--bg-tertiary)",
              color: statusFilter === status ? "#fff" : "var(--text-secondary)",
              border: "1px solid var(--border-color)",
              whiteSpace: "nowrap",
            }}
          >
            {status.replace("_", " ")}
          </button>
        ))}
      </div>

      {/* List Container */}
      <div style={{ flex: 1, overflowY: "auto", padding: "8px" }}>
        {loading ? (
          <div className="section-banner">
            <span>Refreshing sessions...</span>
          </div>
        ) : sessions.length === 0 ? (
          <div
            style={{
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              justifyContent: "center",
              padding: "40px 16px",
              color: "var(--text-muted)",
              textAlign: "center",
              gap: "8px",
            }}
          >
            <MessageCircle size={28} />
            <span style={{ fontSize: "0.85rem", fontWeight: 500 }}>No sessions found</span>
          </div>
        ) : (
          sessions.map((session) => {
            const isSelected = session.session_id === selectedSessionId;
            const status = session.status;
            const sentiment = session.context_vars?.sentiment_score;

            return (
              <div
                key={session.session_id}
                onClick={() => onSelectSession(session)}
                className={`animate-fade-in`}
                style={{
                  background: isSelected ? "rgba(139, 92, 246, 0.08)" : "transparent",
                  border: isSelected ? "1px solid var(--border-active)" : "1px solid transparent",
                  borderRadius: "10px",
                  padding: "14px",
                  marginBottom: "8px",
                  cursor: "pointer",
                  transition: "all 0.2s ease",
                  display: "flex",
                  flexDirection: "column",
                  gap: "6px",
                  position: "relative",
                }}
                onMouseEnter={(e) => {
                  if (!isSelected) {
                    e.currentTarget.style.background = "rgba(255, 255, 255, 0.02)";
                    e.currentTarget.style.borderColor = "var(--border-color)";
                  }
                }}
                onMouseLeave={(e) => {
                  if (!isSelected) {
                    e.currentTarget.style.background = "transparent";
                    e.currentTarget.style.borderColor = "transparent";
                  }
                }}
              >
                {/* Phone & Time Row */}
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                  <span style={{ fontSize: "0.85rem", fontWeight: 600, color: "var(--text-primary)" }}>
                    {session.customer_phone}
                  </span>
                  <span
                    style={{
                      fontSize: "0.7rem",
                      color: "var(--text-muted)",
                      display: "flex",
                      alignItems: "center",
                      gap: "4px",
                    }}
                  >
                    <Clock size={10} />
                    {formatTime(session.last_message_at)}
                  </span>
                </div>

                {/* Subtitle / Context Row */}
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                  <span style={{ fontSize: "0.75rem", color: "var(--text-secondary)", maxWidth: "160px", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                    Language: <b style={{ color: "var(--primary)" }}>{session.context_vars?.language?.toUpperCase() || "EN"}</b>
                  </span>
                  <span
                    style={{
                      fontSize: "0.75rem",
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

                {/* Status Badges Row */}
                <div style={{ display: "flex", gap: "6px", marginTop: "4px", flexWrap: "wrap" }}>
                  {status === "NEEDS_HUMAN" && (
                    <span className="badge badge-needs-human">
                      <AlertCircle size={10} /> Handover
                    </span>
                  )}
                  {status === "AGENT_RESPONDING" && (
                    <span className="badge badge-responding">
                      <MessageCircle size={10} /> Bot active
                    </span>
                  )}
                  {status === "RESOLVED" && (
                    <span className="badge badge-resolved">
                      <CheckCircle2 size={10} /> Resolved
                    </span>
                  )}
                  {status === "WAITING_FOR_BOT" && (
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
