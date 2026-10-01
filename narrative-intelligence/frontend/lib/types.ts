export interface EvidenceSpan {
  text: string;
  start: number;
  end: number;
  reason: string;
}

export interface FeatureValue {
  feature_id: string;
  value: string | number | boolean | string[] | null;
  confidence: number;
  evidence?: EvidenceSpan[];
}

export interface FeatureVector {
  document_id: string;
  features: FeatureValue[];
  metadata?: Record<string, any>;
}

export interface ClassifierResult {
  human_probability: number;
  ai_probability: number;
  predicted_class: string;
  model_version: string;
  feature_set: string;
}

export interface NarrativeProfile {
  document_id: string;
  core30_features: FeatureVector;
  full304_features?: FeatureVector;
  classification?: ClassifierResult;
  diagnostics?: Record<string, any>;
  metadata: Record<string, any>;
}

export interface ErrorDetail {
  code: string;
  message: string;
}

export interface AnalyzeResponse {
  status: string;
  error?: ErrorDetail;
  narrative_profile?: NarrativeProfile;
  executive_summary?: string;
  message?: string;
}
