import { StyleSheet, View } from "react-native";
import { AnalyzeScanResult } from "@/lib/api";
import { Language, t } from "@/lib/i18n";
import { AppText } from "@/components/AppText";
import { Card } from "@/components/Card";
import { StressBadge } from "@/components/StressBadge";
import { colors } from "@/constants/colors";

export function ScanAnalysisResult({ result, language }: { result: AnalyzeScanResult; language: Language }) {
  return (
    <Card style={styles.card}>
      <View style={styles.header}>
        <AppText variant="subtitle">{t(language, "diagnosis")}</AppText>
        <StressBadge level={result.stress_level} language={language} />
      </View>
      {!result.image_quality.usable ? (
        <View style={styles.section}>
          <AppText variant="label">{t(language, "imageQuality")}</AppText>
          {result.image_quality.issues.map((item) => <AppText key={item}>• {item}</AppText>)}
          {result.image_quality.retake_guidance.map((item) => <AppText key={item}>• {item}</AppText>)}
        </View>
      ) : null}
      <Field label={t(language, "severity")} value={`${result.severity_score}/5`} />
      <Field label={t(language, "confidence")} value={`${Math.round(result.confidence * 100)}%`} />
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
      {result.needs_human_review ? <AppText style={styles.review}>{t(language, "humanReview")}</AppText> : null}
    </Card>
  );
}

function Field({ label, value }: { label: string; value: string }) {
  return (
    <View style={styles.field}>
      <AppText variant="label">{label}</AppText>
      <AppText>{value}</AppText>
    </View>
  );
}

const styles = StyleSheet.create({
  card: { gap: 12 },
  header: { flexDirection: "row", alignItems: "center", justifyContent: "space-between" },
  section: { gap: 7 },
  field: { gap: 3 },
  review: { color: colors.amberDark, fontWeight: "800" }
});
