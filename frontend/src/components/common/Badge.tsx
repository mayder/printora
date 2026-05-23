import type { LucideIcon } from "lucide-react";

export function Badge({ icon: Icon, label, value }: { icon?: LucideIcon; label: string; value: number | string }) {
  return (
    <div className="badge">
      {Icon ? (
        <span className="badge-icon">
          <Icon size={17} strokeWidth={2.1} />
        </span>
      ) : null}
      <span className="badge-text">
        <span>{label}</span>
        <strong>{value}</strong>
      </span>
    </div>
  );
}
