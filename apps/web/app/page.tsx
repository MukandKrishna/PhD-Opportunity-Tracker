"use client";

import { useCallback, useEffect, useState } from "react";

import { OpportunityFilterBoard } from "@/components/opportunity-filter-board";
import { getOpportunities, getSources } from "@/lib/api";
import { isVerifiedStatus } from "@/lib/links";
import type { Opportunity, SourceDescriptor } from "@/lib/types";

export default function HomePage() {
  const [opportunities, setOpportunities] = useState<Opportunity[]>([]);
  const [sources, setSources] = useState<SourceDescriptor[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadDashboard = useCallback(async () => {
    try {
      setError(null);
      const [nextOpportunities, nextSources] = await Promise.all([
        getOpportunities({ applied: undefined }),
        getSources(),
      ]);
      setOpportunities(nextOpportunities);
      setSources(nextSources);
    } catch {
      setError("The live API is unavailable. A free backend may need a minute to wake up.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadDashboard();
  }, [loadDashboard]);

  const handleOpportunityUpdated = (updated: Opportunity) => {
    setOpportunities((current) =>
      current.map((item) => (item.id === updated.id ? updated : item)),
    );
  };

  const appliedCount = opportunities.filter((item) => item.tracking?.is_applied).length;
  const verifiedCount = opportunities.filter((item) =>
    isVerifiedStatus(item.verification_status),
  ).length;
  const liveReadyCount = sources.filter((item) => item.live_ready).length;

  return (
    <main className="shell">
      <section className="hero">
        <div className="hero-card">
          <div className="eyebrow">Focused on real applications</div>
          <h1 className="hero-title">Active PhD openings you can actually work through.</h1>
          <p className="hero-copy">
            This dashboard shortlists PhD openings by reading titles, descriptions,
            requirements, and application text for your target AI research areas.
            We start from structured, credible sources first, then widen coverage
            carefully instead of scraping random noise.
          </p>
          <div className="hero-pills">
            <span className="pill">RAG</span>
            <span className="pill">Agents</span>
            <span className="pill">Multi-Agent</span>
            <span className="pill">Knowledge Graphs</span>
            <span className="pill">AI</span>
            <span className="pill">ML</span>
            <span className="pill">DL</span>
            <span className="pill">Computer Vision</span>
            <span className="pill">Data Science</span>
          </div>
        </div>

        <aside className="stats-card">
          <div className="eyebrow">Snapshot</div>
          <div className="stats-grid">
            <div className="stat">
              <div className="stat-value">{opportunities.length}</div>
              <div className="stat-label">Active records loaded</div>
            </div>
            <div className="stat">
              <div className="stat-value">{verifiedCount}</div>
              <div className="stat-label">Verified or official</div>
            </div>
            <div className="stat">
              <div className="stat-value">{appliedCount}</div>
              <div className="stat-label">Already applied</div>
            </div>
            <div className="stat">
              <div className="stat-value">{liveReadyCount}</div>
              <div className="stat-label">Live-ready sources</div>
            </div>
          </div>
        </aside>
      </section>

      <section>
        <div className="section-head">
          <div>
            <h2 className="section-title">All active opportunities</h2>
            <p className="section-copy">
              Filter by your target intake windows and the websites you trust most.
            </p>
          </div>
        </div>

        {loading ? (
          <div className="panel empty-state">Loading live opportunities...</div>
        ) : error ? (
          <div className="panel empty-state">
            {error} <button onClick={() => void loadDashboard()}>Try again</button>
          </div>
        ) : (
          <OpportunityFilterBoard
            opportunities={opportunities}
            sources={sources}
            onOpportunityUpdated={handleOpportunityUpdated}
          />
        )}
      </section>
    </main>
  );
}
