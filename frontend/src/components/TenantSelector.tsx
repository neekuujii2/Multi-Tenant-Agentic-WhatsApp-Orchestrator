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
  const selectedTenant = tenants.find((tenant) => tenant.tenant_id === selectedTenantId);

  return (
    <div className="tenant-selector-shell">
      <div className="tenant-selector-card">
        <span className="eyebrow">Tenant Workspace</span>
        <h3 style={{ marginTop: "8px", fontSize: "1rem" }}>
          {selectedTenant?.name || "Select business tenant"}
        </h3>
        <p>Switch inbox context, analytics, and campaign actions from one place.</p>
      </div>

      <div className="tenant-selector-control">
        <select
          value={selectedTenantId}
          onChange={(e) => onSelectTenant(e.target.value)}
          className="input"
          style={{ appearance: "none", cursor: "pointer", fontWeight: 600 }}
        >
          {tenants.map((tenant) => (
            <option key={tenant.tenant_id} value={tenant.tenant_id} style={{ background: "var(--bg-secondary)" }}>
              {tenant.name}
            </option>
          ))}
        </select>
        <ChevronDown size={16} className="tenant-selector-icon" />
      </div>
    </div>
  );
};
