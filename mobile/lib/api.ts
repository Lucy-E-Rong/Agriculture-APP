import { AiProvider } from "@/store/appStore";
import { Language } from "@/lib/i18n";

const API_BASE_URL = process.env.EXPO_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export type AnalyzeScanInput = {
  imageBase64?: string;
  imageUri?: string;
  imageMimeType?: string;
  provider: AiProvider;
  language: Language;
  cropId?: string;
  greenhouseId?: string;
  sectionId?: string;
  tableId?: string;
  rowId?: string;
};

export type AnalyzeScanResult = {
  crop_is_lettuce: boolean;
  crop_confidence: number;
  image_quality: {
    usable: boolean;
    issues: string[];
    retake_guidance: string[];
  };
  plant_stress_detected: boolean;
  stress_level: "none" | "low" | "medium" | "high" | "critical";
  severity_score: number;
  confidence: number;
  diagnosis: string;
  observed_symptoms: {
    type: string;
    location: string;
    description: string;
  }[];
  possible_causes: {
    category: string;
    likelihood: "uncertain" | "possible" | "likely";
    reason: string;
  }[];
  detected_issues: string[];
  recommendations: string[];
  needs_human_review: boolean;
};

export async function analyzeScan(input: AnalyzeScanInput): Promise<AnalyzeScanResult> {
  const response = await fetch(`${API_BASE_URL}/api/scans/analyze`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(input)
  });

  if (!response.ok) {
    throw new Error(`Analyze scan failed with status ${response.status}`);
  }

  return response.json();
}
