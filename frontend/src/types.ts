export type Region = "canada" | "usa" | "uk" | "china" | "global";
export type Topic = "tech" | "finance" | "health" | "daily" | "learning";
export type TimeRange = "24h" | "3d" | "7d";

export type QAStatus = "pass" | "fail" | "fallback";
export type ConfidenceTag = "multi_source" | "single_source";

export interface DigestRequest {
  topics: Topic[];
  range: TimeRange;
  regions: Region[];
  publishers?: string[] | null;
  max_cards?: number;
  max_cards_per_topic?: number;
}

export interface Citation {
  publisher: string;
  url: string;
  published_at?: string | null;
}

export interface Bullet {
  text: string;
  citations: Citation[];
}

export interface DigestCard {
  id: string;
  topic: Topic;
  headline: string;
  publisher: string;
  published_at: string;
  confidence: ConfidenceTag;
  bullets: Bullet[];
  sources?: Citation[] | null;
}

export interface DigestResponse {
  schema_version: string;
  generated_at: string;
  qa_status: QAStatus;
  request: DigestRequest;
  cards: DigestCard[];
  qa_notes?: string[] | null;
}
