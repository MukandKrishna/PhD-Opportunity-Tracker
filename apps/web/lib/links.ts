const EXAMPLE_HOSTS = new Set([
  "example.com",
  "example.net",
  "example.org",
  "university.example",
]);

export function isDisplayableExternalUrl(value: string | null | undefined): value is string {
  if (!value) {
    return false;
  }

  try {
    const url = new URL(value);
    if (url.protocol !== "http:" && url.protocol !== "https:") {
      return false;
    }

    const host = url.hostname.replace(/^www\./, "").toLowerCase();
    if (EXAMPLE_HOSTS.has(host) || host.endsWith(".example")) {
      return false;
    }

    const path = url.pathname.toLowerCase();
    return !["/demo-", "/demo_", "/test-", "/placeholder"].some((marker) =>
      path.includes(marker),
    );
  } catch {
    return false;
  }
}

export function isVerifiedStatus(status: string): boolean {
  return status === "official" || status === "aggregator_verified";
}

export function getBestOpportunityUrl(opportunity: {
  official_url?: string | null;
  source_url?: string | null;
}): { href: string; label: string } | null {
  if (isDisplayableExternalUrl(opportunity.official_url)) {
    return {
      href: opportunity.official_url,
      label: "Application page",
    };
  }

  if (isDisplayableExternalUrl(opportunity.source_url)) {
    return {
      href: opportunity.source_url,
      label: "Source page",
    };
  }

  return null;
}
