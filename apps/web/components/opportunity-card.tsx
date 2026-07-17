import Link from "next/link";

import { ApplyToggle } from "@/components/apply-toggle";
import { formatSourceName, isClosingSoon, summarizeText } from "@/lib/format";
import { getBestOpportunityUrl, isVerifiedStatus } from "@/lib/links";
import type { Opportunity } from "@/lib/types";

type OpportunityCardProps = {
  opportunity: Opportunity;
  onOpportunityUpdated?: (opportunity: Opportunity) => void;
};

export function OpportunityCard({
  opportunity,
  onOpportunityUpdated,
}: OpportunityCardProps) {
  const closingSoon = isClosingSoon(opportunity.deadline_text);
  const isApplied = Boolean(opportunity.tracking?.is_applied);
  const externalLink = getBestOpportunityUrl(opportunity);

  return (
    <article className="opportunity-card">
      <div className="card-topline">
        <span className="meta">{formatSourceName(opportunity.source_name)}</span>
        {isVerifiedStatus(opportunity.verification_status) ? (
          <span className="badge badge-verified">Verified source</span>
        ) : null}
        {closingSoon ? <span className="badge badge-closing">Closing soon</span> : null}
        {isApplied ? <span className="badge badge-applied">Applied</span> : null}
      </div>

      <div>
        <h2 className="card-title">{opportunity.title}</h2>
        <div className="meta-row" style={{ marginTop: 12 }}>
          {opportunity.institution ? <span className="meta">{opportunity.institution}</span> : null}
          {opportunity.country ? <span className="meta">{opportunity.country}</span> : null}
          {opportunity.city ? <span className="meta">{opportunity.city}</span> : null}
          {opportunity.deadline_text ? (
            <span className="meta">Deadline {opportunity.deadline_text}</span>
          ) : null}
        </div>
      </div>

      <div className="tag-row">
        {opportunity.domain_tags.map((tag) => (
          <span className="tag" key={`${opportunity.id}-${tag}`}>
            {tag}
          </span>
        ))}
      </div>

      <p className="card-description">
        {summarizeText(opportunity.description ?? opportunity.qualification_requirements)}
      </p>

      <div className="cta-row">
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
        <Link
          className="button-link button-secondary"
          href={{ pathname: "/opportunity", query: { id: opportunity.id } }}
        >
          Open details
        </Link>
        <ApplyToggle
          opportunityId={opportunity.id}
          isApplied={isApplied}
          onOpportunityUpdated={onOpportunityUpdated}
        />
      </div>
    </article>
  );
}
