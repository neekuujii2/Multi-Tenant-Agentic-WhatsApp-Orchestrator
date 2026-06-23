import { useState } from "react";
import type { Tenant } from "../types";
import { AlertTriangle, Send } from "lucide-react";

interface BroadcastModalProps {
  tenant: Tenant | null;
  onSendBroadcast: (templateId: string, cohort: string) => Promise<void>;
  sending: boolean;
}

export const BroadcastModal: React.FC<BroadcastModalProps> = ({
  tenant,
  onSendBroadcast,
  sending,
}) => {
  const [selectedTemplateId, setSelectedTemplateId] = useState("");
  const [selectedCohort, setSelectedCohort] = useState("all_sessions");

  if (!tenant) return null;

  const templates = tenant.campaign_templates || [];
  const selectedTemplate = templates.find((template) => template.template_id === selectedTemplateId);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedTemplateId || sending) return;
    try {
      await onSendBroadcast(selectedTemplateId, selectedCohort);
    } catch (error) {
      console.error(error);
    }
  };

  return (
    <div
      className="animate-fade-in"
      style={{
        display: "flex",
        flexDirection: "column",
        gap: "28px",
        maxWidth: "1080px",
        margin: "0 auto",
      }}
    >
      <div>
        <h2 style={{ fontSize: "1.5rem", color: "var(--text-primary)" }}>Campaign Broadcasts</h2>
        <p style={{ fontSize: "0.85rem", color: "var(--text-secondary)", marginTop: "4px" }}>
          Deliver WhatsApp template campaigns to customer cohorts.
        </p>
      </div>

      <div className="campaign-grid">
        <form onSubmit={handleSubmit} className="panel-card" style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
          <div>
            <label style={{ display: "block", fontSize: "0.8rem", fontWeight: 700, color: "var(--text-secondary)", marginBottom: "8px" }}>
              1. Select Campaign Template
            </label>
            <select
              value={selectedTemplateId}
              onChange={(e) => setSelectedTemplateId(e.target.value)}
              className="input"
              required
            >
              <option value="">Select template</option>
              {templates.map((template) => (
                <option key={template.template_id} value={template.template_id}>
                  {template.name}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label style={{ display: "block", fontSize: "0.8rem", fontWeight: 700, color: "var(--text-secondary)", marginBottom: "8px" }}>
              2. Target Cohort Subscriber Segment
            </label>
            <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
              {[
                { id: "all_sessions", label: "All Sessions", desc: "Send to all historical customer threads." },
                { id: "active_7days", label: "Active Last 7 Days", desc: "Send to customers active in the last week." },
                { id: "resolved_only", label: "Resolved Sessions Only", desc: "Send only to successfully closed threads." },
              ].map((cohort) => (
                <label
                  key={cohort.id}
                  style={{
                    display: "flex",
                    alignItems: "flex-start",
                    gap: "12px",
                    padding: "14px",
                    background: selectedCohort === cohort.id ? "color-mix(in srgb, var(--secondary) 42%, var(--card) 58%)" : "var(--bg-tertiary)",
                    border: selectedCohort === cohort.id ? "1px solid var(--border-active)" : "1px solid var(--border-color)",
                    borderRadius: "16px",
                    cursor: "pointer",
                    transition: "all 0.2s ease",
                  }}
                >
                  <input
                    type="radio"
                    name="cohort"
                    value={cohort.id}
                    checked={selectedCohort === cohort.id}
                    onChange={() => setSelectedCohort(cohort.id)}
                    style={{ marginTop: "3px" }}
                  />
                  <div>
                    <span style={{ fontSize: "0.85rem", fontWeight: 600, color: "var(--text-primary)" }}>{cohort.label}</span>
                    <p style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginTop: "2px" }}>{cohort.desc}</p>
                  </div>
                </label>
              ))}
            </div>
          </div>

          <div
            style={{
              padding: "12px",
              background: "color-mix(in srgb, var(--warning) 10%, var(--card) 90%)",
              border: "1px solid color-mix(in srgb, var(--warning) 22%, transparent)",
              borderRadius: "16px",
              display: "flex",
              gap: "10px",
              alignItems: "flex-start",
            }}
          >
            <AlertTriangle size={16} color="var(--warning)" style={{ flexShrink: 0, marginTop: "2px" }} />
            <p style={{ fontSize: "0.75rem", color: "var(--text-secondary)", lineHeight: "1.4" }}>
              <b>Rate limits apply:</b> Broadcasts are paced at 20 messages per second. Ensure template contents comply with Meta business policies.
            </p>
          </div>

          <button type="submit" className="btn btn-primary" style={{ width: "100%", minHeight: "46px" }} disabled={!selectedTemplateId || sending}>
            <Send size={16} />
            {sending ? "Sending Broadcast Campaign..." : "Launch Broadcast Campaign"}
          </button>
        </form>

        <div className="panel-card" style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
          <h4 style={{ fontSize: "0.9rem", fontWeight: 700, color: "var(--text-secondary)" }}>Template Preview</h4>

          {selectedTemplate ? (
            <div style={{ flex: 1, display: "flex", flexDirection: "column", gap: "16px" }}>
              <div
                style={{
                  background: "var(--bg-secondary)",
                  border: "1px solid var(--border-color)",
                  borderRadius: "16px",
                  padding: "16px",
                  display: "flex",
                  flexDirection: "column",
                  gap: "12px",
                }}
              >
                <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", fontWeight: 600 }}>
                  TEMPLATE ID: {selectedTemplate.template_id}
                </div>
                <div style={{ fontSize: "0.9rem", color: "var(--text-primary)", whiteSpace: "pre-wrap", borderTop: "1px solid var(--border-color)", paddingTop: "12px" }}>
                  {selectedTemplate.body}
                </div>
              </div>

              {selectedTemplate.media_url && (
                <div>
                  <span style={{ fontSize: "0.75rem", color: "var(--text-secondary)", fontWeight: 600 }}>Attached Media Asset</span>
                  <div style={{ marginTop: "6px", borderRadius: "16px", overflow: "hidden", border: "1px solid var(--border-color)", background: "var(--bg-tertiary)", padding: "8px" }}>
                    <img src={selectedTemplate.media_url} alt="Template visual preview" style={{ maxWidth: "100%", maxHeight: "180px", display: "block", margin: "0 auto", borderRadius: "12px" }} />
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div style={{ flex: 1, display: "flex", alignItems: "center", justifyContent: "center", border: "1px dashed var(--border-color)", borderRadius: "16px", color: "var(--text-muted)", fontSize: "0.85rem", minHeight: "280px" }}>
              Select a template to view preview
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
