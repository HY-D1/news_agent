import { useMemo, useState } from "react";
import "./App.css";
import { generateDigest } from "./api";
import type { DigestResponse, Topic, TimeRange, Region } from "./types";

const TOPICS: { key: Topic; label: string }[] = [
  { key: "tech", label: "Tech" },
  { key: "finance", label: "Finance" },
  { key: "health", label: "Health" },
  { key: "daily", label: "Daily" },
  { key: "learning", label: "Learning" },
];

export default function App() {
  const [topics, setTopics] = useState<Topic[]>(["tech"]);
  const [range, setRange] = useState<TimeRange>("24h");
  const [regions] = useState<Region[]>(["canada"]);

  const [data, setData] = useState<DigestResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  const canGenerate = topics.length > 0 && regions.length > 0;

  const topicSet = useMemo(() => new Set(topics), [topics]);

  function toggleTopic(t: Topic) {
    setTopics((prev) =>
      prev.includes(t) ? prev.filter((x) => x !== t) : [...prev, t]
    );
  }

  async function onGenerate() {
    setLoading(true);
    setErr(null);
    try {
      const res = await generateDigest({ topics, range, regions });
      setData(res);
    } catch (e: any) {
      setErr(e?.message ?? "Unknown error");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={{ maxWidth: 980, margin: "0 auto", padding: 24 }}>
      <h1 style={{ marginBottom: 8 }}>News Digest</h1>
      <p style={{ marginTop: 0, opacity: 0.75 }}>
        Demo output is mocked today. Each bullet includes citations.
      </p>

      <div style={{ display: "flex", gap: 16, flexWrap: "wrap", alignItems: "center" }}>
        <div>
          <div style={{ fontSize: 12, opacity: 0.7 }}>Topics</div>
          <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginTop: 6 }}>
            {TOPICS.map((t) => (
              <button
                key={t.key}
                onClick={() => toggleTopic(t.key)}
                style={{
                  padding: "8px 10px",
                  borderRadius: 999,
                  border: "1px solid #ddd",
                  background: topicSet.has(t.key) ? "#111" : "#fff",
                  color: topicSet.has(t.key) ? "#fff" : "#111",
                  cursor: "pointer",
                }}
              >
                {t.label}
              </button>
            ))}
          </div>
        </div>

        <div>
          <div style={{ fontSize: 12, opacity: 0.7 }}>Time range</div>
          <select
            value={range}
            onChange={(e) => setRange(e.target.value as TimeRange)}
            style={{ marginTop: 6, padding: 8, borderRadius: 8 }}
          >
            <option value="24h">Last 24h</option>
            <option value="3d">Last 3 days</option>
            <option value="7d">Last 7 days</option>
          </select>
        </div>

        <div style={{ marginLeft: "auto" }}>
          <button
            disabled={!canGenerate || loading}
            onClick={onGenerate}
            style={{
              padding: "10px 14px",
              borderRadius: 10,
              border: "1px solid #ddd",
              background: loading ? "#f3f3f3" : "#111",
              color: loading ? "#111" : "#fff",
              cursor: loading ? "not-allowed" : "pointer",
              minWidth: 140,
            }}
          >
            {loading ? "Generating..." : "Generate Digest"}
          </button>
        </div>
      </div>

      {err && (
        <div style={{ marginTop: 16, padding: 12, border: "1px solid #f3c", borderRadius: 10 }}>
          <b>Error:</b> {err}
        </div>
      )}

      {data && (
        <div style={{ marginTop: 20 }}>
          <div style={{ display: "flex", justifyContent: "space-between", gap: 12, flexWrap: "wrap" }}>
            <div>
              <b>QA status:</b> {data.qa_status}
              {data.qa_notes?.length ? (
                <span style={{ opacity: 0.7 }}> — {data.qa_notes[0]}</span>
              ) : null}
            </div>
            <div style={{ opacity: 0.7 }}>
              Generated: {new Date(data.generated_at).toLocaleString()}
            </div>
          </div>

          <div style={{ marginTop: 16, display: "grid", gap: 14 }}>
            {data.cards.map((card) => (
              <div key={card.id} style={{ border: "1px solid #e6e6e6", borderRadius: 14, padding: 14 }}>
                <div style={{ display: "flex", gap: 10, alignItems: "baseline", flexWrap: "wrap" }}>
                  <h3 style={{ margin: 0 }}>{card.headline}</h3>
                  <span style={{ fontSize: 12, opacity: 0.75 }}>
                    {card.publisher} • {new Date(card.published_at).toLocaleString()}
                  </span>
                  <span style={{ fontSize: 12, padding: "2px 8px", border: "1px solid #ddd", borderRadius: 999 }}>
                    {card.confidence === "multi_source" ? "Multi-source" : "Single-source"}
                  </span>
                  <span style={{ fontSize: 12, opacity: 0.7 }}>
                    Topic: {card.topic}
                  </span>
                </div>

                <ul style={{ marginTop: 10 }}>
                  {card.bullets.map((b, idx) => (
                    <li key={idx} style={{ marginBottom: 8 }}>
                      {b.text}{" "}
                      <span style={{ fontSize: 12, opacity: 0.8 }}>
                        {b.citations.map((c, i) => (
                          <a
                            key={i}
                            href={c.url}
                            target="_blank"
                            rel="noreferrer"
                            style={{ marginLeft: 6 }}
                          >
                            [{i + 1}]
                          </a>
                        ))}
                      </span>
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
