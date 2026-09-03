export type Feedback = "relevant" | "not_relevant" | null;

export type Story = {
  id: number;
  score: number;
  source: string;
  published: string;
  cluster_size: number;
  title: string;
  summary: string;
  why: string;
  url: string;
  category: string;
  feedback: Feedback;
};

export type BriefPayload = {
  week: { number: number; range: string };
  kpis: {
    collected: number;
    unique: number;
    over_threshold: number;
    pending: number;
  };
  list_name: string;
  list_count: number;
  list_blurb: string;
  threshold: number;
  stories: Story[];
  below_count: number;
  generated_at: string;
};

export type AdminPayload = {
  generated_at: string;
  threshold: number;
  totals: {
    collected: number;
    unique: number;
    gated: number;
    blocked: number;
    over_threshold: number;
    multi_source_clusters: number;
    collapse_pct: number;
  };
  distribution: { from: number; to: number; count: number }[];
  sources: { name: string; count: number; latest: string }[];
  feeds: { name: string; type: string; url: string }[];
  runs: {
    started: string;
    finished: string | null;
    feeds_ok: number;
    feeds_failed: number;
    seen: number;
    inserted: number;
  }[];
  labels: { relevant: number; not_relevant: number; with_embedding: number };
  scored_by: Record<string, number>;
};
