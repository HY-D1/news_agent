import { useState, useMemo } from "react";
import "./App.css";
import { generateDigest } from "./api";
import type { DigestResponse, Topic, TimeRange, Region, DigestCard } from "./types";

const TOPICS: { key: Topic; label: string; icon: string }[] = [
  { key: "tech", label: "Technology", icon: "💻" },
  { key: "finance", label: "Finance", icon: "💰" },
  { key: "health", label: "Health", icon: "🏥" },
  { key: "daily", label: "Daily News", icon: "📰" },
  { key: "learning", label: "Learning", icon: "📚" },
];

const TIME_RANGES: { key: TimeRange; label: string }[] = [
  { key: "24h", label: "Last 24 hours" },
  { key: "3d", label: "Last 3 days" },
  { key: "7d", label: "Last 7 days" },
];

const REGIONS: { key: Region; label: string; flag: string }[] = [
  { key: "canada", label: "Canada", flag: "🇨🇦" },
  { key: "usa", label: "USA", flag: "🇺🇸" },
  { key: "uk", label: "UK", flag: "🇬🇧" },
  { key: "china", label: "China", flag: "🇨🇳" },
  { key: "global", label: "Global", flag: "🌍" },
];

// Confidence badge component
function ConfidenceBadge({ confidence }: { confidence: string }) {
  const isMulti = confidence === "multi_source";
  return (
    <span className={`confidence-badge ${isMulti ? "multi" : "single"}`}>
      {isMulti ? "✓ Multi-source" : "○ Single-source"}
    </span>
  );
}

// Topic badge component
function TopicBadge({ topic }: { topic: Topic }) {
  const topicInfo = TOPICS.find((t) => t.key === topic);
  return (
    <span className="topic-badge">
      {topicInfo?.icon} {topicInfo?.label || topic}
    </span>
  );
}

// Card component
function NewsCard({ card }: { card: DigestCard }) {
  const publishedDate = new Date(card.published_at);
  const timeAgo = getTimeAgo(publishedDate);

  return (
    <article className="news-card">
      <div className="card-header">
        <div className="card-meta">
          <TopicBadge topic={card.topic} />
          <ConfidenceBadge confidence={card.confidence} />
        </div>
        <h3 className="card-title">{card.headline}</h3>
        <div className="card-source">
          <span className="publisher">{card.publisher}</span>
          <span className="separator">•</span>
          <span className="time" title={publishedDate.toLocaleString()}>
            {timeAgo}
          </span>
        </div>
      </div>

      <div className="card-content">
        <ul className="bullet-list">
          {card.bullets.map((bullet, idx) => (
            <li key={idx} className="bullet-item">
              <span className="bullet-text">{bullet.text}</span>
              <span className="citations">
                {bullet.citations.map((citation, i) => (
                  <a
                    key={i}
                    href={citation.url}
                    target="_blank"
                    rel="noreferrer"
                    className="citation-link"
                    title={`${citation.publisher} - ${new Date(
                      citation.published_at || ""
                    ).toLocaleDateString()}`}
                  >
                    [{i + 1}]
                  </a>
                ))}
              </span>
            </li>
          ))}
        </ul>
      </div>

      {card.sources && card.sources.length > 0 && (
        <div className="card-footer">
          <span className="sources-label">Sources:</span>
          <div className="sources-list">
            {card.sources.map((source, i) => (
              <a
                key={i}
                href={source.url}
                target="_blank"
                rel="noreferrer"
                className="source-link"
              >
                {source.publisher}
              </a>
            ))}
          </div>
        </div>
      )}
    </article>
  );
}

// Helper function for time ago
function getTimeAgo(date: Date): string {
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);

  if (diffMins < 1) return "Just now";
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  if (diffDays === 1) return "Yesterday";
  return `${diffDays} days ago`;
}

// Main App Component
export default function App() {
  // State
  const [topics, setTopics] = useState<Topic[]>(["tech"]);
  const [range, setRange] = useState<TimeRange>("24h");
  const [regions, setRegions] = useState<Region[]>(["canada"]);
  const [data, setData] = useState<DigestResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  // Computed
  const canGenerate = topics.length > 0 && regions.length > 0;
  const topicSet = useMemo(() => new Set(topics), [topics]);
  const regionSet = useMemo(() => new Set(regions), [regions]);

  // Handlers
  function toggleTopic(t: Topic) {
    setTopics((prev) =>
      prev.includes(t) ? prev.filter((x) => x !== t) : [...prev, t]
    );
  }

  function toggleRegion(r: Region) {
    setRegions((prev) =>
      prev.includes(r) ? prev.filter((x) => x !== r) : [...prev, r]
    );
  }

  async function onGenerate() {
    setLoading(true);
    setErr(null);
    setData(null);
    try {
      const res = await generateDigest({ topics, range, regions });
      setData(res);
    } catch (e: unknown) {
      const message = e instanceof Error ? e.message : "Unknown error";
      setErr(message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="app">
      {/* Header */}
      <header className="header">
        <div className="header-content">
          <div className="logo">
            <span className="logo-icon">📰</span>
            <h1>News Agent</h1>
          </div>
          <p className="subtitle">
            AI-powered news digest from trusted sources
          </p>
        </div>
      </header>

      {/* Main Content */}
      <main className="main">
        {/* Control Panel */}
        <section className="control-panel">
          {/* Topics */}
          <div className="control-section">
            <label className="control-label">
              Topics <span className="required">*</span>
            </label>
            <div className="topic-grid">
              {TOPICS.map((t) => (
                <button
                  key={t.key}
                  onClick={() => toggleTopic(t.key)}
                  className={`topic-btn ${topicSet.has(t.key) ? "active" : ""}`}
                  type="button"
                >
                  <span className="topic-icon">{t.icon}</span>
                  <span className="topic-name">{t.label}</span>
                </button>
              ))}
            </div>
          </div>

          {/* Time Range */}
          <div className="control-section">
            <label className="control-label">Time Range</label>
            <div className="range-options">
              {TIME_RANGES.map((r) => (
                <button
                  key={r.key}
                  onClick={() => setRange(r.key)}
                  className={`range-btn ${range === r.key ? "active" : ""}`}
                  type="button"
                >
                  {r.label}
                </button>
              ))}
            </div>
          </div>

          {/* Regions */}
          <div className="control-section">
            <label className="control-label">
              Regions <span className="required">*</span>
            </label>
            <div className="region-grid">
              {REGIONS.map((r) => (
                <button
                  key={r.key}
                  onClick={() => toggleRegion(r.key)}
                  className={`region-btn ${regionSet.has(r.key) ? "active" : ""}`}
                  type="button"
                >
                  <span className="region-flag">{r.flag}</span>
                  <span className="region-name">{r.label}</span>
                </button>
              ))}
            </div>
          </div>

          {/* Generate Button */}
          <button
            onClick={onGenerate}
            disabled={!canGenerate || loading}
            className="generate-btn"
            type="button"
          >
            {loading ? (
              <>
                <span className="spinner"></span>
                Generating...
              </>
            ) : (
              <>
                <span>✨</span> Generate Digest
              </>
            )}
          </button>

          {!canGenerate && (
            <p className="hint">
              Select at least one topic and one region to continue
            </p>
          )}
        </section>

        {/* Error Message */}
        {err && (
          <div className="error-message">
            <span className="error-icon">⚠️</span>
            <div>
              <strong>Error</strong>
              <p>{err}</p>
            </div>
          </div>
        )}

        {/* Results */}
        {data && (
          <section className="results">
            {/* Results Header */}
            <div className="results-header">
              <div className="results-stats">
                <h2>Your Digest</h2>
                <div className="stats">
                  <span className={`status-badge ${data.qa_status}`}>
                    {data.qa_status === "pass"
                      ? "✓ Verified"
                      : data.qa_status === "fallback"
                      ? "⚡ Fallback"
                      : "✗ Failed"}
                  </span>
                  <span className="card-count">{data.cards.length} stories</span>
                  <span className="generated-time">
                    Generated {new Date(data.generated_at).toLocaleTimeString()}
                  </span>
                </div>
              </div>
              {data.qa_notes && data.qa_notes[0] && (
                <p className="qa-note">{data.qa_notes[0]}</p>
              )}
            </div>

            {/* Cards Grid */}
            {data.cards.length > 0 ? (
              <div className="cards-grid">
                {data.cards.map((card) => (
                  <NewsCard key={card.id} card={card} />
                ))}
              </div>
            ) : (
              <div className="empty-state">
                <span className="empty-icon">📭</span>
                <p>No stories found for your criteria.</p>
                <p className="empty-hint">
                  Try selecting different topics or a longer time range.
                </p>
              </div>
            )}
          </section>
        )}

        {/* Initial State */}
        {!data && !loading && !err && (
          <div className="welcome-state">
            <div className="welcome-icon">📰</div>
            <h2>Welcome to News Agent</h2>
            <p>
              Select your topics and regions above, then click "Generate Digest"
              to get a personalized news summary from trusted sources.
            </p>
            <div className="features">
              <div className="feature">
                <span>🔍</span>
                <p>Multi-source verification</p>
              </div>
              <div className="feature">
                <span>🔗</span>
                <p>Citation-backed stories</p>
              </div>
              <div className="feature">
                <span>⚡</span>
                <p>AI-powered clustering</p>
              </div>
            </div>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="footer">
        <p>News Agent Digest • Local Demo</p>
      </footer>
    </div>
  );
}
