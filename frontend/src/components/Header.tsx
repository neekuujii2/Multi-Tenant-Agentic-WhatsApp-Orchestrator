import { BarChart3, Megaphone, MessageSquare, Moon, Radio, Sun } from "lucide-react";

interface HeaderProps {
  currentTab: "inbox" | "analytics" | "campaigns";
  setCurrentTab: (tab: "inbox" | "analytics" | "campaigns") => void;
  tenantName: string;
  isLive: boolean;
  theme: "light" | "dark";
  onToggleTheme: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  currentTab,
  setCurrentTab,
  tenantName,
  isLive,
  theme,
  onToggleTheme,
}) => {
  return (
    <header className="glass-panel header-shell">
      <div className="header-brand">
        <div className="brand-mark">
          <Radio size={20} />
        </div>
        <div className="brand-copy">
          <h1 style={{ fontSize: "1.12rem" }}>WhatsApp Agentic Orchestrator</h1>
          <p>Multi-tenant inbox, analytics, and campaign control</p>
        </div>
      </div>

      <nav className="header-nav">
        <button
          onClick={() => setCurrentTab("inbox")}
          className={`btn tab-trigger ${currentTab === "inbox" ? "is-active" : "btn-secondary"}`}
        >
          <MessageSquare size={16} />
          Inbox
        </button>
        <button
          onClick={() => setCurrentTab("analytics")}
          className={`btn tab-trigger ${currentTab === "analytics" ? "is-active" : "btn-secondary"}`}
        >
          <BarChart3 size={16} />
          Analytics
        </button>
        <button
          onClick={() => setCurrentTab("campaigns")}
          className={`btn tab-trigger ${currentTab === "campaigns" ? "is-active" : "btn-secondary"}`}
        >
          <Megaphone size={16} />
          Campaigns
        </button>
      </nav>

      <div className="header-actions">
        <div className="status-pill">
          <div className={`status-dot ${isLive ? "is-live pulse-primary" : ""}`} />
          <span style={{ fontSize: "0.78rem", fontWeight: 700, color: "var(--text-secondary)" }}>
            {isLive ? "Live Sync Active" : "Disconnected"}
          </span>
        </div>

        <button
          type="button"
          className="btn btn-secondary theme-toggle"
          onClick={onToggleTheme}
          aria-label="Toggle theme"
        >
          {theme === "dark" ? <Sun size={18} /> : <Moon size={18} />}
        </button>

        <div className="tenant-chip">
          <strong>{tenantName || "Loading tenant"}</strong>
          <span>ACTIVE WORKSPACE</span>
        </div>
      </div>
    </header>
  );
};
