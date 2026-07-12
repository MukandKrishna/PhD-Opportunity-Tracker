import { OpportunityFilterBoard } from "@/components/opportunity-filter-board";
import { getOpportunities, getSources } from "@/lib/api";
import { isVerifiedStatus } from "@/lib/links";

export default async function HomePage() {
  const [opportunities, sources] = await Promise.all([
    getOpportunities({ applied: undefined }),
    getSources(),
  ]);

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

        <OpportunityFilterBoard opportunities={opportunities} sources={sources} />
      </section>
    </main>
  );
}
