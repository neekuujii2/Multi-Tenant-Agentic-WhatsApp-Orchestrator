import type { Tenant } from "../types";
import { ChevronDown } from "lucide-react";

interface TenantSelectorProps {
  tenants: Tenant[];
  selectedTenantId: string;
  onSelectTenant: (tenantId: string) => void;
}

export const TenantSelector: React.FC<TenantSelectorProps> = ({
  tenants,
  selectedTenantId,
  onSelectTenant,
}) => {
  return (
    <div
      style={{
        padding: "16px",
        borderBottom: "1px solid var(--border-color)",
        position: "relative",
      }}
    >
      <label
        style={{
          display: "block",
          fontSize: "0.7rem",
          fontWeight: 700,
          color: "var(--text-muted)",
          textTransform: "uppercase",
          letterSpacing: "0.05em",
          marginBottom: "8px",
        }}
      >
        Select Business Tenant
      </label>
      <div style={{ position: "relative" }}>
        <select
          value={selectedTenantId}
          onChange={(e) => onSelectTenant(e.target.value)}
          className="input"
          style={{
            width: "100%",
            paddingRight: "36px",
            appearance: "none",
            cursor: "pointer",
            fontWeight: 600,
            fontSize: "0.85rem",
            display: "flex",
            alignItems: "center",
            background: "var(--bg-tertiary)",
            color: "var(--text-primary)",
            height: "42px",
          }}
        >
          {tenants.map((t) => (
            <option key={t.tenant_id} value={t.tenant_id} style={{ background: "var(--bg-secondary)" }}>
              💼 {t.name}
            </option>
          ))}
        </select>
        <ChevronDown
          size={16}
          style={{
            position: "absolute",
            right: "12px",
            top: "50%",
            transform: "translateY(-50%)",
            color: "var(--text-secondary)",
            pointerEvents: "none",
          }}
        />
      </div>
    </div>
  );
};
