import type { AnalyticsData } from "../types";
import {
  MessageSquare,
  Users,
  AlertCircle,
  Inbox,
  Send,
  Smile,
  Frown,
} from "lucide-react";

interface AnalyticsViewProps {
  data: AnalyticsData | null;
  loading: boolean;
}

export const AnalyticsView: React.FC<AnalyticsViewProps> = ({ data, loading }) => {
  if (loading || !data) {
    return (
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          height: "100%",
          color: "var(--text-muted)",
        }}
      >
        <span style={{ fontSize: "0.95rem", fontWeight: 500 }}>Loading analytics data...</span>
      </div>
    );
  }

  // Calculate sentiment position
  const getSentimentPos = (score: number) => {
    // scale from -1..1 to 0..100%
    return ((score + 1) / 2) * 100;
  };

  const getSentimentLabel = (score: number) => {
    if (score < -0.3) return "Frustrated / Negatives";
    if (score > 0.3) return "Happy / Positives";
    return "Neutral / Satisfied";
  };

  return (
    <div
      className="animate-fade-in"
      style={{
        padding: "32px",
        overflowY: "auto",
        height: "100%",
        display: "flex",
        flexDirection: "column",
        gap: "28px",
      }}
    >
      <div>
        <h2 style={{ fontSize: "1.5rem", fontWeight: 800, color: "var(--text-primary)" }}>
          Operational Analytics
        </h2>
        <p style={{ fontSize: "0.85rem", color: "var(--text-secondary)", marginTop: "4px" }}>
          Real-time metrics compiled from agent session operations.
        </p>
      </div>

      {/* Grid of Cards */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
          gap: "20px",
        }}
      >
        {/* Total Sessions */}
        <div className="glass-panel" style={{ padding: "24px", borderRadius: "12px", position: "relative" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", color: "var(--text-secondary)" }}>
            <span style={{ fontSize: "0.8rem", fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.05em" }}>Total Sessions</span>
            <Users size={18} color="var(--primary)" />
          </div>
          <h3 style={{ fontSize: "2.25rem", fontWeight: 800, marginTop: "12px" }}>{data.sessions.total}</h3>
          <p style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginTop: "4px" }}>Active customer threads</p>
        </div>

        {/* Needs Human */}
        <div className="glass-panel" style={{ padding: "24px", borderRadius: "12px", borderLeft: "3px solid var(--danger)" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", color: "var(--text-secondary)" }}>
            <span style={{ fontSize: "0.8rem", fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.05em" }}>Human Handover</span>
            <AlertCircle size={18} color="var(--danger)" />
          </div>
          <h3 style={{ fontSize: "2.25rem", fontWeight: 800, marginTop: "12px", color: "var(--danger)" }}>{data.sessions.needs_human}</h3>
          <p style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginTop: "4px" }}>Pending manual response</p>
        </div>

        {/* Resolved */}
        <div className="glass-panel" style={{ padding: "24px", borderRadius: "12px", borderLeft: "3px solid var(--success)" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", color: "var(--text-secondary)" }}>
            <span style={{ fontSize: "0.8rem", fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.05em" }}>Resolved</span>
            <Smile size={18} color="var(--success)" />
          </div>
          <h3 style={{ fontSize: "2.25rem", fontWeight: 800, marginTop: "12px", color: "var(--success)" }}>{data.sessions.resolved}</h3>
          <p style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginTop: "4px" }}>Completed conversations</p>
        </div>

        {/* Bot active */}
        <div className="glass-panel" style={{ padding: "24px", borderRadius: "12px" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", color: "var(--text-secondary)" }}>
            <span style={{ fontSize: "0.8rem", fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.05em" }}>Bot Active</span>
            <MessageSquare size={18} color="var(--primary)" />
          </div>
          <h3 style={{ fontSize: "2.25rem", fontWeight: 800, marginTop: "12px" }}>{data.sessions.agent_responding}</h3>
          <p style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginTop: "4px" }}>Currently automated</p>
        </div>
      </div>

      {/* Message volume section */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(360px, 1fr))", gap: "24px" }}>
        {/* Messages Statistics */}
        <div className="glass-panel" style={{ padding: "24px", borderRadius: "12px" }}>
          <h4 style={{ fontSize: "1rem", fontWeight: 700, marginBottom: "20px" }}>Message Volume</h4>
          
          <div style={{ display: "flex", gap: "24px", marginBottom: "24px" }}>
            <div style={{ flex: 1, background: "rgba(255, 255, 255, 0.02)", padding: "16px", borderRadius: "8px", border: "1px solid var(--border-color)" }}>
              <div style={{ display: "flex", alignItems: "center", gap: "8px", color: "var(--text-secondary)", fontSize: "0.75rem" }}>
                <Inbox size={14} />
                Inbound Messages
              </div>
              <h5 style={{ fontSize: "1.5rem", fontWeight: 800, marginTop: "8px" }}>{data.messages.inbound}</h5>
            </div>
            
            <div style={{ flex: 1, background: "rgba(255, 255, 255, 0.02)", padding: "16px", borderRadius: "8px", border: "1px solid var(--border-color)" }}>
              <div style={{ display: "flex", alignItems: "center", gap: "8px", color: "var(--text-secondary)", fontSize: "0.75rem" }}>
                <Send size={14} />
                Outbound Responses
              </div>
              <h5 style={{ fontSize: "1.5rem", fontWeight: 800, marginTop: "8px" }}>{data.messages.outbound}</h5>
            </div>
          </div>

          <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
            <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.75rem", color: "var(--text-secondary)" }}>
              <span>Total Messages Processed</span>
              <span>{data.messages.total}</span>
            </div>
            {/* Progress Bar representing ratio */}
            <div style={{ width: "100%", height: "8px", background: "var(--bg-tertiary)", borderRadius: "4px", overflow: "hidden", display: "flex" }}>
              <div style={{ width: `${(data.messages.inbound / (data.messages.total || 1)) * 100}%`, height: "100%", background: "var(--primary)" }} />
              <div style={{ width: `${(data.messages.outbound / (data.messages.total || 1)) * 100}%`, height: "100%", background: "var(--success)" }} />
            </div>
            <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.65rem", color: "var(--text-muted)" }}>
              <span style={{ display: "flex", alignItems: "center", gap: "4px" }}><span style={{ display: "inline-block", width: "6px", height: "6px", background: "var(--primary)", borderRadius: "50%" }} />Inbound</span>
              <span style={{ display: "flex", alignItems: "center", gap: "4px" }}><span style={{ display: "inline-block", width: "6px", height: "6px", background: "var(--success)", borderRadius: "50%" }} />Outbound</span>
            </div>
          </div>
        </div>

        {/* Sentiment Meter */}
        <div className="glass-panel" style={{ padding: "24px", borderRadius: "12px", display: "flex", flexDirection: "column" }}>
          <h4 style={{ fontSize: "1rem", fontWeight: 700, marginBottom: "20px" }}>Customer Sentiment Score</h4>
          
          <div style={{ flex: 1, display: "flex", flexDirection: "column", justifyContent: "center", alignItems: "center", gap: "16px" }}>
            <div style={{ position: "relative", width: "100%", padding: "10px 0" }}>
              {/* Sentiment Slider Visualizer */}
              <div style={{ width: "100%", height: "6px", background: "linear-gradient(to right, var(--danger) 0%, var(--warning) 50%, var(--success) 100%)", borderRadius: "3px" }} />
              
              <div
                style={{
                  position: "absolute",
                  left: `${getSentimentPos(data.average_sentiment)}%`,
                  top: "50%",
                  transform: "translate(-50%, -50%)",
                  width: "16px",
                  height: "16px",
                  borderRadius: "50%",
                  backgroundColor: "#fff",
                  boxShadow: "0 0 10px rgba(0,0,0,0.5)",
                  border: "2px solid var(--primary)",
                  transition: "left 0.5s ease",
                }}
              />
            </div>
            
            <div style={{ display: "flex", justifyContent: "space-between", width: "100%", fontSize: "0.75rem", color: "var(--text-secondary)" }}>
              <span style={{ display: "flex", alignItems: "center", gap: "4px" }}><Frown size={14} color="var(--danger)" /> Frustrated (-1)</span>
              <span>Neutral (0)</span>
              <span style={{ display: "flex", alignItems: "center", gap: "4px" }}><Smile size={14} color="var(--success)" /> Positive (+1)</span>
            </div>

            <div style={{ textAlign: "center", marginTop: "12px" }}>
              <span style={{ fontSize: "0.75rem", textTransform: "uppercase", color: "var(--text-muted)", fontWeight: 700, letterSpacing: "0.03em" }}>Average Customer Sentiment</span>
              <h5 style={{ fontSize: "2rem", fontWeight: 800, marginTop: "4px", color: data.average_sentiment < -0.3 ? "var(--danger)" : data.average_sentiment > 0.3 ? "var(--success)" : "var(--warning)" }}>
                {data.average_sentiment.toFixed(2)}
              </h5>
              <p style={{ fontSize: "0.75rem", color: "var(--text-secondary)", marginTop: "4px" }}>
                {getSentimentLabel(data.average_sentiment)}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Customer languages section */}
      <div className="glass-panel" style={{ padding: "24px", borderRadius: "12px" }}>
        <h4 style={{ fontSize: "1rem", fontWeight: 700, marginBottom: "20px" }}>Customer Language Distribution</h4>
        <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
          {Object.entries(data.languages).length === 0 ? (
            <p style={{ color: "var(--text-muted)", fontSize: "0.85rem" }}>No language data available.</p>
          ) : (
            Object.entries(data.languages).map(([lang, count]) => {
              const total = Object.values(data.languages).reduce((a, b) => a + b, 0);
              const percentage = ((count / total) * 100).toFixed(0);

              const getLanguageName = (code: string) => {
                if (code === "en") return "English";
                if (code === "hi") return "Hindi (हिन्दी)";
                if (code === "hinglish") return "Hinglish (Hindi/English Mix)";
                return code.toUpperCase();
              };

              return (
                <div key={lang} style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
                  <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.8rem" }}>
                    <span style={{ fontWeight: 600, color: "var(--text-primary)" }}>{getLanguageName(lang)}</span>
                    <span style={{ color: "var(--text-secondary)" }}>{count} ({percentage}%)</span>
                  </div>
                  <div style={{ width: "100%", height: "8px", background: "var(--bg-tertiary)", borderRadius: "4px", overflow: "hidden" }}>
                    <div style={{ width: `${percentage}%`, height: "100%", background: "var(--primary)" }} />
                  </div>
                </div>
              );
            })
          )}
        </div>
      </div>
    </div>
  );
};
