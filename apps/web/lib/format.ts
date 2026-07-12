export function summarizeText(text: string | null | undefined, max = 240): string {
  if (!text) {
    return "No detailed summary has been extracted yet.";
  }

  const normalized = text.replace(/\s+/g, " ").trim();
  if (normalized.length <= max) {
    return normalized;
  }
  return `${normalized.slice(0, max).trim()}...`;
}

export function isClosingSoon(deadlineText: string | null | undefined): boolean {
  if (!deadlineText) {
    return false;
  }

  const parsed = new Date(deadlineText);
  if (Number.isNaN(parsed.getTime())) {
    return false;
  }

  const now = new Date();
  const diffMs = parsed.getTime() - now.getTime();
  const diffDays = diffMs / (1000 * 60 * 60 * 24);
  return diffDays >= 0 && diffDays <= 14;
}

export function formatSourceName(sourceName: string): string {
  const displayNames: Record<string, string> = {
    academictransfer: "AcademicTransfer",
    euraxess: "EURAXESS",
    findaphd: "FindAPhD",
    inria: "Inria",
    jobs_ac_uk: "jobs.ac.uk",
  };

  if (displayNames[sourceName]) {
    return displayNames[sourceName];
  }

  return sourceName
    .split("_")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}
