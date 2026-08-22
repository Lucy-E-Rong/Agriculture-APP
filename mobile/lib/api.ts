import { AiProvider } from "@/store/appStore";
import { Language } from "@/lib/i18n";

export const API_BASE_URL =
  process.env.EXPO_PUBLIC_API_BASE_URL ?? "https://agriculture-app-green.vercel.app";

export async function verifyAccessCode(accessCode: string): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/access/verify`, {
    headers: { "X-Demo-Access-Code": accessCode }
  });

  if (!response.ok) {
    throw new Error(response.status === 401 ? "Invalid access code" : `Access check failed with status ${response.status}`);
  }
}

export type ScanLocationSnapshot = {
  display?: string;
  greenhouse?: string;
  section?: string;
  table?: string;
  row?: string;
  plant_id?: string;
  sample_id?: string;
  variety?: string;
  growth_stage?: string;
};

export type HumanReviewReason =
  | "high_or_critical_water_stress"
  | "non_water_factor_to_rule_out"
  | "ambiguous_visual_evidence";

export type AnalyzeScanInput = {
  accessCode: string;
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
  locationSnapshot?: ScanLocationSnapshot;
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
  human_review_reasons?: HumanReviewReason[];
};

export type PersistedAnalyzeScanResult = AnalyzeScanResult & {
  scan_id: string;
  created_at: string;
};

export type RecentScan = {
  id: string;
  created_at: string;
  stress_level: AnalyzeScanResult["stress_level"];
  severity_score: number;
  confidence: number;
  diagnosis: string;
  location_snapshot: ScanLocationSnapshot;
};

export type ScanDetail = RecentScan & {
  analysis_result: AnalyzeScanResult;
  image_url: string;
};

type FetchResponse = Awaited<ReturnType<typeof fetch>>;

async function responseError(response: FetchResponse, fallback: string) {
  try {
    const payload = await response.json();
    return new Error(typeof payload.detail === "string" ? payload.detail : fallback);
  } catch {
    return new Error(fallback);
  }
}

export async function analyzeScan(input: AnalyzeScanInput): Promise<PersistedAnalyzeScanResult> {
  const { accessCode, ...payload } = input;
  const response = await fetch(`${API_BASE_URL}/api/scans/analyze`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-Demo-Access-Code": accessCode
    },
    body: JSON.stringify(payload)
  });

  if (!response.ok) {
    throw await responseError(response, `Analyze scan failed with status ${response.status}`);
  }

  return response.json();
}

export async function getRecentScans(accessCode: string): Promise<RecentScan[]> {
  const response = await fetch(`${API_BASE_URL}/api/scans/recent`, {
    headers: { "X-Demo-Access-Code": accessCode }
  });
  if (!response.ok) {
    throw await responseError(response, `Recent scans failed with status ${response.status}`);
  }
  return response.json();
}

export async function getScanDetail(accessCode: string, scanId: string): Promise<ScanDetail> {
  const response = await fetch(`${API_BASE_URL}/api/scans/${encodeURIComponent(scanId)}`, {
    headers: { "X-Demo-Access-Code": accessCode }
  });
  if (!response.ok) {
    throw await responseError(response, `Scan detail failed with status ${response.status}`);
  }
  return response.json();
}
