import { StyleSheet, View } from "react-native";
import { AnalyzeScanResult } from "@/lib/api";
import { Language, t } from "@/lib/i18n";
import { AppText } from "@/components/AppText";
import { Card } from "@/components/Card";
import { StressBadge } from "@/components/StressBadge";
import { colors } from "@/constants/colors";

export function ScanAnalysisResult({ result, language }: { result: AnalyzeScanResult; language: Language }) {
  const healthy =
    result.severity_score === 0 &&
    result.image_quality.usable &&
    result.crop_is_lettuce &&
    result.observed_symptoms.length === 0 &&
    result.detected_issues.length === 0;
  const levelKey = {
    none: "stressNone",
    low: "stressLow",
    medium: "stressMedium",
    high: "stressHigh",
    critical: "stressCritical"
  }[result.stress_level] as "stressNone" | "stressLow" | "stressMedium" | "stressHigh" | "stressCritical";
  const explanationKey = {
    none: "severityNoneExplanation",
    low: "severityLowExplanation",
    medium: "severityMediumExplanation",
    high: "severityHighExplanation",
    critical: "severityCriticalExplanation"
  }[result.stress_level] as
    | "severityNoneExplanation"
    | "severityLowExplanation"
    | "severityMediumExplanation"
    | "severityHighExplanation"
    | "severityCriticalExplanation";
  const reviewReasons = result.human_review_reasons ?? [];

  return (
    <Card style={styles.card}>
      <View style={styles.header}>
        <AppText variant="subtitle">{t(language, "waterStressAssessment")}</AppText>
        <StressBadge level={result.stress_level} language={language} />
      </View>
      {!result.image_quality.usable ? (
        <View style={styles.section}>
          <AppText variant="label">{t(language, "imageQuality")}</AppText>
          {result.image_quality.issues.map((item) => <AppText key={item}>• {item}</AppText>)}
          {result.image_quality.retake_guidance.map((item) => <AppText key={item}>• {item}</AppText>)}
        </View>
      ) : null}
      <View style={styles.field}>
        <AppText variant="label">{t(language, "severity")}</AppText>
        <AppText>{result.severity_score}/5 · {t(language, levelKey)}</AppText>
        <AppText variant="caption">{t(language, explanationKey)}</AppText>
      </View>
      {healthy ? (
        <AppText style={styles.healthy}>{t(language, "healthy")}</AppText>
      ) : result.severity_score === 0 ? (
        <AppText>{t(language, "noClearWaterStress")}</AppText>
      ) : null}
      <AppText>{result.diagnosis}</AppText>
      {result.observed_symptoms.length ? (
        <View style={styles.section}>
          <AppText variant="label">{t(language, "visibleSigns")}</AppText>
          {result.observed_symptoms.map((item, index) => (
            <AppText key={`${item.type}-${index}`}>• {item.description} ({item.location})</AppText>
          ))}
        </View>
      ) : null}
      {result.possible_causes.length ? (
        <View style={styles.section}>
          <AppText variant="label">{t(language, "possibleCauses")}</AppText>
          {result.possible_causes.map((item, index) => (
            <AppText key={`${item.category}-${index}`}>• {item.category}: {item.reason}</AppText>
          ))}
        </View>
      ) : null}
      <AppText variant="label">{t(language, "recommendations")}</AppText>
      {result.recommendations.map((item) => <AppText key={item}>• {item}</AppText>)}
      {result.needs_human_review ? (
        <View style={styles.reviewSection}>
          <AppText style={styles.review}>{t(language, "humanReview")}</AppText>
          {reviewReasons.map((reason) => (
            <AppText key={reason}>• {t(language, humanReviewReasonKey(reason))}</AppText>
          ))}
        </View>
      ) : null}
    </Card>
  );
}

function humanReviewReasonKey(reason: NonNullable<AnalyzeScanResult["human_review_reasons"]>[number]) {
  return {
    high_or_critical_water_stress: "reviewHighStress",
    non_water_factor_to_rule_out: "reviewNonWaterFactor",
    ambiguous_visual_evidence: "reviewAmbiguousEvidence"
  }[reason] as "reviewHighStress" | "reviewNonWaterFactor" | "reviewAmbiguousEvidence";
}

const styles = StyleSheet.create({
  card: { gap: 12 },
  header: { flexDirection: "row", alignItems: "center", justifyContent: "space-between" },
  section: { gap: 7 },
  field: { gap: 3 },
  healthy: { color: colors.primary, fontWeight: "800" },
  reviewSection: { gap: 7, paddingTop: 4 },
  review: { color: colors.amberDark, fontWeight: "800" }
});
