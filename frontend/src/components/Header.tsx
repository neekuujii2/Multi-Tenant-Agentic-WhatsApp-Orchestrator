import { BarChart3, Megaphone, MessageSquare, Radio } from "lucide-react";

interface HeaderProps {
  currentTab: "inbox" | "analytics" | "campaigns";
  setCurrentTab: (tab: "inbox" | "analytics" | "campaigns") => void;
  tenantName: string;
  isLive: boolean;
}

export const Header: React.FC<HeaderProps> = ({
  currentTab,
  setCurrentTab,
  tenantName,
  isLive,
}) => {
  return (
    <header
      className="glass-panel header-shell"
    >
      <div className="header-brand">
        <div
          style={{
            background: "linear-gradient(135deg, var(--primary) 0%, #ec4899 100%)",
            width: "36px",
            height: "36px",
            borderRadius: "10px",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            boxShadow: "0 0 15px rgba(139, 92, 246, 0.4)",
          }}
        >
          <Radio size={20} color="#fff" />
        </div>
        <div>
          <h1 style={{ fontSize: "1.15rem", fontWeight: 700, display: "flex", alignItems: "center", gap: "8px" }}>
            WhatsApp Agentic Orchestrator
          </h1>
          <p style={{ fontSize: "0.75rem", color: "var(--text-secondary)" }}>
            Multi-Tenant Agent Console
          </p>
        </div>
      </div>

      <nav className="header-nav">
        <button
          onClick={() => setCurrentTab("inbox")}
          className={`btn ${currentTab === "inbox" ? "btn-primary" : "btn-secondary"}`}
          style={{ padding: "8px 16px", borderRadius: "8px" }}
        >
          <MessageSquare size={16} />
          Inbox
        </button>
        <button
          onClick={() => setCurrentTab("analytics")}
          className={`btn ${currentTab === "analytics" ? "btn-primary" : "btn-secondary"}`}
          style={{ padding: "8px 16px", borderRadius: "8px" }}
        >
          <BarChart3 size={16} />
          Analytics
        </button>
        <button
          onClick={() => setCurrentTab("campaigns")}
          className={`btn ${currentTab === "campaigns" ? "btn-primary" : "btn-secondary"}`}
          style={{ padding: "8px 16px", borderRadius: "8px" }}
        >
          <Megaphone size={16} />
          Campaigns
        </button>
      </nav>

      <div className="header-actions">
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: "8px",
            background: "rgba(255, 255, 255, 0.03)",
            padding: "6px 12px",
            borderRadius: "8px",
            border: "1px solid var(--border-color)",
          }}
        >
          <div
            className={isLive ? "pulse-primary" : ""}
            style={{
              width: "8px",
              height: "8px",
              borderRadius: "50%",
              backgroundColor: isLive ? "var(--success)" : "var(--text-muted)",
              boxShadow: isLive ? "0 0 10px var(--success)" : "none",
            }}
          />
          <span style={{ fontSize: "0.75rem", fontWeight: 600, color: "var(--text-secondary)" }}>
            {isLive ? "SSE LIVE" : "DISCONNECTED"}
          </span>
        </div>

        <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-end" }}>
          <span style={{ fontSize: "0.85rem", fontWeight: 600, color: "var(--text-primary)" }}>
            {tenantName || "Loading..."}
          </span>
          <span style={{ fontSize: "0.7rem", color: "var(--text-muted)", letterSpacing: "0.03em" }}>
            ACTIVE TENANT
          </span>
        </div>
      </div>
    </header>
  );
};
