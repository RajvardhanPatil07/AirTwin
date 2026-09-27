export const number = (value: number, digits = 1) =>
  value.toLocaleString("en-IN", {
    maximumFractionDigits: digits,
    minimumFractionDigits: digits,
  });
export const compact = (value: number) =>
  Intl.NumberFormat("en", {
    notation: "compact",
    maximumFractionDigits: 2,
  }).format(value);
export const timeLabel = (value: string) =>
  new Date(value).toLocaleTimeString("en-IN", {
    timeZone: "Asia/Kolkata",
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  });
export const dateLabel = (value: string) =>
  new Date(value).toLocaleDateString("en-IN", {
    timeZone: "Asia/Kolkata",
    day: "numeric",
    month: "short",
    year: "numeric",
  });
