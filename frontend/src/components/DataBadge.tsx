import type { SourceType } from "../types";

export function DataBadge({
  source,
  detail,
}: {
  source: SourceType;
  detail?: string;
}) {
  return (
    <span className={`data-badge ${source}`}>
      {source.toUpperCase()}
      {detail && ` · ${detail}`}
    </span>
  );
}
