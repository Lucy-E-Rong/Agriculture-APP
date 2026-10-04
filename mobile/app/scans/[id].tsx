import { useEffect, useState } from "react";
import { ActivityIndicator, Image, Pressable, StyleSheet, View } from "react-native";
import { Link, useLocalSearchParams } from "expo-router";
import { ChevronLeft } from "lucide-react-native";
import { AppText } from "@/components/AppText";
import { Card } from "@/components/Card";
import { ScanAnalysisResult } from "@/components/ScanAnalysisResult";
import { Screen } from "@/components/Screen";
import { colors } from "@/constants/colors";
import { getScanDetail, ScanDetail } from "@/lib/api";
import { t } from "@/lib/i18n";
import { useAppStore } from "@/store/appStore";

export default function ScanDetailScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const language = useAppStore((state) => state.language);
  const accessCode = useAppStore((state) => state.accessCode);
  const [detail, setDetail] = useState<ScanDetail>();
  const [error, setError] = useState(false);

  useEffect(() => {
    let active = true;
    setDetail(undefined);
    setError(false);
    if (!id) {
      setError(true);
      return () => {
        active = false;
      };
    }
    getScanDetail(accessCode, id)
      .then((value) => {
        if (active) setDetail(value);
      })
      .catch(() => {
        if (active) setError(true);
      });
    return () => {
      active = false;
    };
  }, [accessCode, id]);

  return (
    <Screen>
      <View style={styles.header}>
        <Link href="/(tabs)" asChild>
          <Pressable style={styles.backButton}>
            <ChevronLeft color={colors.primary} size={22} />
          </Pressable>
        </Link>
        <View style={styles.headerText}>
          <AppText variant="title">{t(language, "scanDetails")}</AppText>
          {detail?.location_snapshot.display ? <AppText variant="caption">{detail.location_snapshot.display}</AppText> : null}
        </View>
      </View>

      {!detail && !error ? <ActivityIndicator color={colors.primary} /> : null}
      {error ? <AppText>{t(language, "scanDetailError")}</AppText> : null}
      {detail ? (
        <>
          <Image source={{ uri: detail.image_url }} style={styles.image} resizeMode="cover" />
          <ScanContextDetail snapshot={detail.location_snapshot} language={language} />
          <ScanAnalysisResult result={detail.analysis_result} language={language} />
        </>
      ) : null}
    </Screen>
  );
}

function ScanContextDetail({ snapshot, language }: { snapshot: ScanDetail["location_snapshot"]; language: "en" | "zh" }) {
  const fields = [
    ["greenhouse", t(language, "greenhouse")],
    ["section", t(language, "section")],
    ["table", t(language, "table")],
    ["row", t(language, "row")],
    ["plant_id", t(language, "plantId")],
    ["sample_id", t(language, "sampleId")],
    ["variety", t(language, "variety")],
    ["period", t(language, "period")],
    ["growth_stage", t(language, "growthStage")]
  ] as const;
  const present = fields.filter(([key]) => snapshot[key]);
  if (!snapshot.display && !present.length) return null;

  return (
    <Card style={styles.contextCard}>
      <AppText variant="subtitle">{t(language, "scanContext")}</AppText>
      {snapshot.display ? <AppText>{snapshot.display}</AppText> : null}
      {present.map(([key, label]) => (
        <View key={key} style={styles.contextField}>
          <AppText variant="label">{label}</AppText>
          <AppText>{snapshot[key]}</AppText>
        </View>
      ))}
    </Card>
  );
}

const styles = StyleSheet.create({
  header: { flexDirection: "row", alignItems: "center", gap: 12 },
  headerText: { flex: 1, gap: 2 },
  contextCard: { gap: 10 },
  contextField: { gap: 3 },
  backButton: {
    width: 42,
    height: 42,
    borderRadius: 8,
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: colors.primaryTint
  },
  image: { width: "100%", height: 300, borderRadius: 12, backgroundColor: colors.primaryTint }
});
