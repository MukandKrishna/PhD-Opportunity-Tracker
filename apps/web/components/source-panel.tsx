import type { SourceDescriptor } from "@/lib/types";

type SourcePanelProps = {
  sources: SourceDescriptor[];
};

export function SourcePanel({ sources }: SourcePanelProps) {
  return (
    <section className="panel">
      <div className="section-head">
        <div>
          <h2 className="section-title">Source coverage</h2>
          <p className="section-copy">
            Live-ready sources are the ones we can target first for genuine, current
            PhD opportunities.
          </p>
        </div>
      </div>

      <div className="grid">
        {sources.map((source) => (
          <article className="opportunity-card" key={source.source_name}>
            <div className="card-topline">
              <span className="meta">{source.category}</span>
              {source.live_ready ? (
                <span className="badge badge-verified">Live ready</span>
              ) : (
                <span className="badge badge-closing">Planned next</span>
              )}
            </div>

            <div>
              <h3 className="card-title" style={{ fontSize: "1.35rem" }}>
                {source.display_name}
              </h3>
              <div className="meta-row" style={{ marginTop: 12 }}>
                <span className="meta">{source.trust_level}</span>
                <span className="meta">{source.source_type}</span>
              </div>
            </div>

            <p className="card-description">
              {source.notes ?? "No notes yet."}
            </p>
          </article>
        ))}
      </div>
    </section>
  );
}
