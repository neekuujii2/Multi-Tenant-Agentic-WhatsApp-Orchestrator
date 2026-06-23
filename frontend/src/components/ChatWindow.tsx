import { useEffect, useRef, useState } from "react";
import type { ChatSession, Message, SessionStatus } from "../types";
import {
  Send,
  User,
  Bot,
  AlertCircle,
  CheckCircle,
  Lock,
  Cpu,
  Clock,
  FileText,
  ExternalLink,
} from "lucide-react";

interface ChatWindowProps {
  session: ChatSession | null;
  messages: Message[];
  onSendReply: (text: string, status: "RESOLVED" | "NEEDS_HUMAN") => Promise<void>;
  onResolve: () => Promise<void>;
  onTakeover: () => Promise<void>;
  sending: boolean;
  loading: boolean;
}

export const ChatWindow: React.FC<ChatWindowProps> = ({
  session,
  messages,
  onSendReply,
  onResolve,
  onTakeover,
  sending,
  loading,
}) => {
  const [replyText, setReplyText] = useState("");
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  if (!session) {
    return (
      <div className="chat-surface chat-empty-state">
        <div className="chat-empty-icon">
          <Bot size={34} color="var(--primary)" />
        </div>
        <h2 style={{ fontSize: "1.45rem" }}>No conversation selected</h2>
        <p style={{ maxWidth: "460px", color: "var(--text-secondary)", lineHeight: 1.6 }}>
          Select a conversation from the inbox to monitor customer messages, see AI activity, and jump into human takeover when needed.
        </p>
        <span className="badge badge-responding">Inbox monitoring ready</span>
      </div>
    );
  }

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!replyText.trim() || sending) return;
    try {
      await onSendReply(replyText, "NEEDS_HUMAN");
      setReplyText("");
    } catch (error) {
      console.error(error);
    }
  };

  const getStatusBadge = (status: SessionStatus) => {
    switch (status) {
      case "NEEDS_HUMAN":
        return <span className="badge badge-needs-human">Human Takeover</span>;
      case "AGENT_RESPONDING":
        return <span className="badge badge-responding">Bot Active</span>;
      case "RESOLVED":
        return <span className="badge badge-resolved">Resolved</span>;
      default:
        return <span className="badge badge-waiting">Queued</span>;
    }
  };

  const formatMessageTime = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  };

  return (
    <div className="chat-surface" style={{ display: "flex", flexDirection: "column" }}>
      <div className="glass-panel chat-header">
        <div>
          <h2 style={{ fontSize: "1.1rem", display: "flex", alignItems: "center", gap: "10px" }}>
            <User size={18} color="var(--primary)" />
            {session.customer_phone}
          </h2>
          <div style={{ display: "flex", gap: "8px", marginTop: "6px", alignItems: "center", flexWrap: "wrap" }}>
            {getStatusBadge(session.status)}
            <span style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>Messages: {session.message_count}</span>
          </div>
        </div>

        <div className="chat-actions">
          {session.status !== "NEEDS_HUMAN" ? (
            <button onClick={onTakeover} className="btn btn-danger">
              <Lock size={14} />
              Takeover
            </button>
          ) : (
            <button onClick={onResolve} className="btn btn-success">
              <CheckCircle size={14} />
              Resolve
            </button>
          )}
        </div>
      </div>

      <div className="chat-messages">
        {loading && (
          <div className="section-banner">
            <span>Loading conversation history...</span>
          </div>
        )}

        {messages.map((msg, index) => {
          const isOut = msg.direction === "OUTBOUND";
          const hasMeta = msg.agent_meta && (msg.agent_meta.node || msg.agent_meta.detected_language);

          return (
            <div
              key={msg.message_id || index}
              className="animate-fade-in"
              style={{
                display: "flex",
                flexDirection: "column",
                alignItems: isOut ? "flex-end" : "flex-start",
                width: "100%",
              }}
            >
              <div
                style={{
                  display: "flex",
                  alignItems: "flex-end",
                  gap: "8px",
                  maxWidth: "75%",
                  flexDirection: isOut ? "row-reverse" : "row",
                }}
              >
                <div
                  style={{
                    width: "30px",
                    height: "30px",
                    borderRadius: "50%",
                    backgroundColor: isOut ? "var(--primary-glow)" : "var(--bg-tertiary)",
                    border: "1px solid var(--border-color)",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    flexShrink: 0,
                  }}
                >
                  {isOut ? <Bot size={14} color="var(--primary)" /> : <User size={14} color="var(--text-secondary)" />}
                </div>

                <div>
                  <div
                    className="glass-panel"
                    style={{
                      padding: "12px 16px",
                      borderRadius: isOut ? "18px 18px 6px 18px" : "18px 18px 18px 6px",
                      background: isOut
                        ? "linear-gradient(135deg, var(--primary) 0%, var(--primary-hover) 100%)"
                        : "var(--bg-secondary)",
                      border: isOut ? "none" : "1px solid var(--border-color)",
                      color: isOut ? "var(--primary-foreground)" : "var(--text-primary)",
                      boxShadow: isOut ? "0 4px 14px var(--primary-glow)" : "none",
                    }}
                  >
                    {msg.content.media_url && (
                      <div style={{ marginBottom: "8px", borderRadius: "8px", overflow: "hidden" }}>
                        {msg.content.type === "image" ? (
                          <img
                            src={msg.content.media_url}
                            alt="Media content"
                            style={{
                              maxWidth: "100%",
                              maxHeight: "220px",
                              display: "block",
                              borderRadius: "8px",
                              cursor: "pointer",
                            }}
                            onClick={() => window.open(msg.content.media_url, "_blank")}
                          />
                        ) : (
                          <a
                            href={msg.content.media_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            style={{
                              display: "flex",
                              alignItems: "center",
                              gap: "8px",
                              padding: "10px",
                              background: "rgba(0,0,0,0.08)",
                              color: isOut ? "var(--primary-foreground)" : "var(--primary)",
                              textDecoration: "none",
                              borderRadius: "6px",
                              fontSize: "0.8rem",
                            }}
                          >
                            <FileText size={16} />
                            <span style={{ textDecoration: "underline", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                              {msg.content.media_filename || "Download File"}
                            </span>
                            <ExternalLink size={12} />
                          </a>
                        )}
                      </div>
                    )}

                    {msg.content.text && (
                      <p style={{ fontSize: "0.9rem", lineHeight: "1.45", whiteSpace: "pre-wrap" }}>{msg.content.text}</p>
                    )}
                  </div>

                  <div
                    style={{
                      display: "flex",
                      gap: "8px",
                      marginTop: "4px",
                      fontSize: "0.7rem",
                      color: "var(--text-muted)",
                      justifyContent: isOut ? "flex-end" : "flex-start",
                    }}
                  >
                    <span>{formatMessageTime(msg.created_at)}</span>
                    {msg.agent_meta?.detected_language && (
                      <>
                        <span>•</span>
                        <span style={{ textTransform: "uppercase", fontWeight: 600, color: "var(--primary)" }}>
                          {msg.agent_meta.detected_language}
                        </span>
                      </>
                    )}
                  </div>
                </div>
              </div>

              {hasMeta && (
                <div
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: "12px",
                    margin: "4px 36px",
                    fontSize: "0.7rem",
                    color: "var(--text-muted)",
                    background: "color-mix(in srgb, var(--card) 86%, var(--muted) 14%)",
                    padding: "6px 10px",
                    borderRadius: "10px",
                    border: "1px solid var(--border-color)",
                    flexWrap: "wrap",
                  }}
                >
                  <span style={{ display: "flex", alignItems: "center", gap: "4px" }}>
                    <Cpu size={10} color="var(--primary)" />
                    Node: <b>{msg.agent_meta?.node || "workflow"}</b>
                  </span>
                  {msg.agent_meta?.processing_ms !== undefined && (
                    <span style={{ display: "flex", alignItems: "center", gap: "4px" }}>
                      <Clock size={10} />
                      Latency: <b>{msg.agent_meta.processing_ms}ms</b>
                    </span>
                  )}
                  {msg.agent_meta?.sentiment_score !== undefined && (
                    <span
                      style={{
                        color:
                          msg.agent_meta.sentiment_score < -0.4
                            ? "var(--danger)"
                            : msg.agent_meta.sentiment_score > 0.4
                              ? "var(--success)"
                              : "var(--warning)",
                      }}
                    >
                      Sentiment: <b>{msg.agent_meta.sentiment_score.toFixed(2)}</b>
                    </span>
                  )}
                </div>
              )}
            </div>
          );
        })}
        <div ref={messagesEndRef} />
      </div>

      <div className="glass-panel chat-footer">
        {session.status !== "NEEDS_HUMAN" ? (
          <div
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              background: "color-mix(in srgb, var(--secondary) 35%, var(--card) 65%)",
              border: "1px solid var(--primary-glow)",
              borderRadius: "16px",
              padding: "12px 18px",
              gap: "12px",
              flexWrap: "wrap",
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
              <AlertCircle size={16} color="var(--primary)" />
              <span style={{ fontSize: "0.85rem", color: "var(--text-secondary)" }}>
                AI agent is currently managing replies for this customer.
              </span>
            </div>
            <button onClick={onTakeover} className="btn btn-primary" style={{ padding: "8px 12px", fontSize: "0.82rem" }}>
              <Lock size={12} />
              Takeover Chat
            </button>
          </div>
        ) : (
          <form onSubmit={handleSend} style={{ display: "flex", gap: "12px", alignItems: "stretch" }}>
            <input
              type="text"
              value={replyText}
              onChange={(e) => setReplyText(e.target.value)}
              placeholder="Type your response in English, Hindi, or Hinglish..."
              className="input"
              style={{ flex: 1 }}
              disabled={sending}
            />
            <button
              type="submit"
              className="btn btn-primary"
              style={{ width: "52px", minHeight: "46px", padding: 0 }}
              disabled={!replyText.trim() || sending}
            >
              <Send size={16} />
            </button>
          </form>
        )}
      </div>
    </div>
  );
};
