"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { ApplyToggle } from "@/components/apply-toggle";
import { getOpportunity } from "@/lib/api";
import { isClosingSoon } from "@/lib/format";
import { getBestOpportunityUrl, isDisplayableExternalUrl, isVerifiedStatus } from "@/lib/links";
import type { Opportunity } from "@/lib/types";

function renderValue(value: string | null | undefined, fallback = "Not extracted yet") {
  return value && value.trim() ? value : fallback;
}

export default function OpportunityDetailPage() {
  const [opportunity, setOpportunity] = useState<Opportunity | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const id = Number(new URLSearchParams(window.location.search).get("id"));
    if (!Number.isInteger(id) || id <= 0) {
      setError("This opportunity link is invalid.");
      setLoading(false);
      return;
    }

    getOpportunity(id)
      .then(setOpportunity)
      .catch(() => {
        setError("This opportunity could not be loaded from the live API.");
      })
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return <main className="shell"><div className="panel empty-state">Loading opportunity...</div></main>;
  }

  if (error || opportunity === null) {
    return (
      <main className="shell">
        <div className="panel empty-state">
          {error ?? "Opportunity not found."} <Link href="/">Back to all opportunities</Link>
        </div>
      </main>
    );
  }

  const isApplied = Boolean(opportunity.tracking?.is_applied);
  const closingSoon = isClosingSoon(opportunity.deadline_text);
  const sourceUrl = isDisplayableExternalUrl(opportunity.source_url)
    ? opportunity.source_url
    : null;
  const officialUrl = isDisplayableExternalUrl(opportunity.official_url)
    ? opportunity.official_url
    : null;
  const supervisorProfileUrl = isDisplayableExternalUrl(opportunity.supervisor_profile_url)
    ? opportunity.supervisor_profile_url
    : null;
  const externalLink = getBestOpportunityUrl(opportunity);

  return (
    <main className="shell">
      <div className="detail-shell">
        <section className="detail-panel">
          <div className="card-topline">
            <span className="meta">{opportunity.source_name}</span>
            {isVerifiedStatus(opportunity.verification_status) ? (
              <span className="badge badge-verified">Verified source</span>
            ) : null}
            {closingSoon ? <span className="badge badge-closing">Closing soon</span> : null}
            {isApplied ? <span className="badge badge-applied">Applied</span> : null}
          </div>

          <h1 className="detail-title">{opportunity.title}</h1>

          <div className="detail-grid">
            <div className="detail-item">
              <div className="detail-label">Institution</div>
              <div className="detail-value">{renderValue(opportunity.institution)}</div>
            </div>
            <div className="detail-item">
              <div className="detail-label">Country</div>
              <div className="detail-value">{renderValue(opportunity.country)}</div>
            </div>
            <div className="detail-item">
              <div className="detail-label">City</div>
              <div className="detail-value">{renderValue(opportunity.city)}</div>
            </div>
            <div className="detail-item">
              <div className="detail-label">Domain</div>
              <div className="detail-value">{renderValue(opportunity.domain_primary)}</div>
            </div>
            <div className="detail-item">
              <div className="detail-label">Funding</div>
              <div className="detail-value">{renderValue(opportunity.funding)}</div>
            </div>
            <div className="detail-item">
              <div className="detail-label">Salary / stipend</div>
              <div className="detail-value">{renderValue(opportunity.salary_stipend)}</div>
            </div>
            <div className="detail-item">
              <div className="detail-label">Duration</div>
              <div className="detail-value">{renderValue(opportunity.duration_text)}</div>
            </div>
            <div className="detail-item">
              <div className="detail-label">Start date</div>
              <div className="detail-value">{renderValue(opportunity.start_date_text)}</div>
            </div>
            <div className="detail-item">
              <div className="detail-label">Deadline</div>
              <div className="detail-value">{renderValue(opportunity.deadline_text)}</div>
            </div>
            <div className="detail-item">
              <div className="detail-label">Supervisor</div>
              <div className="detail-value">{renderValue(opportunity.supervisor_name)}</div>
            </div>
          </div>

          <div style={{ marginTop: 22 }}>
            <h2 className="detail-section-title">Domain tags</h2>
            <div className="tag-row">
              {opportunity.domain_tags.map((tag) => (
                <span className="tag" key={`${opportunity.id}-${tag}`}>
                  {tag}
                </span>
              ))}
            </div>
          </div>

          <div style={{ marginTop: 26 }}>
            <h2 className="detail-section-title">Opportunity description</h2>
            <div className="detail-text">
              {renderValue(opportunity.description)}
            </div>
          </div>

          <div style={{ marginTop: 26 }}>
            <h2 className="detail-section-title">Qualification requirements</h2>
            <div className="detail-text">
              {renderValue(opportunity.qualification_requirements)}
            </div>
          </div>

          <div style={{ marginTop: 26 }}>
            <h2 className="detail-section-title">Application process</h2>
            <div className="detail-text">
              {renderValue(opportunity.application_process)}
            </div>
          </div>
        </section>

        <aside className="detail-panel">
          <div className="eyebrow">Applicant actions</div>
          <div className="detail-actions" style={{ marginTop: 16 }}>
            {externalLink ? (
              <a
                className="button-link button-primary"
                href={externalLink.href}
                rel="noreferrer"
                target="_blank"
              >
                {externalLink.label}
              </a>
            ) : null}
            <ApplyToggle
              opportunityId={opportunity.id}
              isApplied={isApplied}
              onOpportunityUpdated={setOpportunity}
            />
            <Link className="button-link button-secondary" href="/">
              Back to all
            </Link>
          </div>

          <div style={{ marginTop: 24 }}>
            <h2 className="detail-section-title">Required documents</h2>
            <div className="doc-list">
              {(opportunity.required_documents ?? []).length > 0 ? (
                opportunity.required_documents?.map((doc) => (
                  <span className="tag" key={`${opportunity.id}-${doc}`}>
                    {doc}
                  </span>
                ))
              ) : (
                <span className="helper-line">No structured document list extracted yet.</span>
              )}
            </div>
          </div>

          <div style={{ marginTop: 24 }}>
            <h2 className="detail-section-title">Links</h2>
            <div className="detail-links">
              {sourceUrl ? (
                <a
                  className="button-link button-secondary"
                  href={sourceUrl}
                  rel="noreferrer"
                  target="_blank"
                >
                  Source page
                </a>
              ) : null}
              {officialUrl ? (
                <a
                  className="button-link button-primary"
                  href={officialUrl}
                  rel="noreferrer"
                  target="_blank"
                >
                  Application page
                </a>
              ) : null}
              {supervisorProfileUrl ? (
                <a
                  className="button-link button-muted"
                  href={supervisorProfileUrl}
                  rel="noreferrer"
                  target="_blank"
                >
                  Supervisor profile
                </a>
              ) : null}
              {!sourceUrl && !officialUrl && !supervisorProfileUrl ? (
                <span className="helper-line">No validated external links extracted yet.</span>
              ) : null}
            </div>
          </div>

          <div style={{ marginTop: 24 }}>
            <h2 className="detail-section-title">Contact</h2>
            <div className="detail-text">{renderValue(opportunity.contact_info)}</div>
          </div>
        </aside>
      </div>
    </main>
  );
}
