import Link from "next/link";

import { OpportunityCard } from "@/components/opportunity-card";
import { getOpportunities } from "@/lib/api";

export default async function AppliedPage() {
  const opportunities = await getOpportunities({ applied: true });

  return (
    <main className="shell" style={{ paddingBottom: 40 }}>
      <section className="hero" style={{ paddingBottom: 14 }}>
        <div className="hero-card">
          <div className="eyebrow">Applied workflow</div>
          <h1 className="hero-title">Everything you have already moved forward on.</h1>
          <p className="hero-copy">
            This view keeps your active application pipeline separate while the main
            dashboard still shows those same opportunities with a green applied state.
          </p>
        </div>
        <aside className="stats-card">
          <div className="eyebrow">Applied count</div>
          <div className="stat">
            <div className="stat-value">{opportunities.length}</div>
            <div className="stat-label">Marked as applied</div>
          </div>
          <Link className="button-link button-secondary" href="/">
            Back to all opportunities
          </Link>
        </aside>
      </section>

      <section>
        <div className="section-head">
          <div>
            <h2 className="section-title">Applied opportunities</h2>
            <p className="section-copy">
              Keep using this as your working shortlist while we add notes, reminders,
              and document readiness later.
            </p>
          </div>
        </div>

        <div className="grid">
          {opportunities.length > 0 ? (
            opportunities.map((opportunity) => (
              <OpportunityCard key={opportunity.id} opportunity={opportunity} />
            ))
          ) : (
            <div className="panel empty-state">
              Nothing is marked as applied yet.
            </div>
          )}
        </div>
      </section>
    </main>
  );
}
