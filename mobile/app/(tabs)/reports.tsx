import { StyleSheet, View } from "react-native";
import { AppText } from "@/components/AppText";
import { Card } from "@/components/Card";
import { Screen } from "@/components/Screen";
import { StressBadge } from "@/components/StressBadge";
import { colors } from "@/constants/colors";
import { recentScans } from "@/lib/mockData";
import { t } from "@/lib/i18n";
import { useAppStore } from "@/store/appStore";

const trend = [2, 4, 3, 6, 5, 8, 4];

export default function ReportsScreen() {
  const language = useAppStore((state) => state.language);

  return (
    <Screen>
      <View>
        <AppText variant="title">{t(language, "reports")}</AppText>
      </View>

      <Card style={styles.trendCard}>
        <AppText variant="subtitle">{t(language, "reportSummary")}</AppText>
        <View style={styles.chart}>
          {trend.map((value, index) => (
            <View key={index} style={styles.barWrap}>
              <View style={[styles.bar, { height: 18 + value * 10 }]} />
            </View>
          ))}
        </View>
      </Card>

      <Card style={styles.riskCard}>
        <AppText variant="subtitle">{t(language, "highRiskRows")}</AppText>
        <RiskRow location="GH2 · SB · T2 · R1" level="high" language={language} />
        <RiskRow location="GH1 · SA · T1 · R2" level="medium" language={language} />
      </Card>

      {recentScans.map((scan) => (
        <Card key={scan.id} style={styles.scanCard}>
          <View style={styles.rowBetween}>
            <View>
              <AppText variant="subtitle">{scan.crop}</AppText>
              <AppText variant="caption">{scan.location}</AppText>
            </View>
            <StressBadge level={scan.stress} language={language} />
          </View>
          <AppText variant="caption">{scan.time}</AppText>
        </Card>
      ))}
    </Screen>
  );
}

function RiskRow({ location, level, language }: { location: string; level: string; language: "en" | "zh" }) {
  return (
    <View style={styles.riskRow}>
      <AppText>{location}</AppText>
      <StressBadge level={level} language={language} />
    </View>
  );
}

const styles = StyleSheet.create({
  trendCard: {
    gap: 14
  },
  chart: {
    height: 130,
    flexDirection: "row",
    alignItems: "flex-end",
    gap: 10
  },
  barWrap: {
    flex: 1,
    justifyContent: "flex-end",
    height: "100%"
  },
  bar: {
    borderRadius: 5,
    backgroundColor: colors.primaryMid
  },
  riskCard: {
    gap: 12
  },
  riskRow: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    gap: 12
  },
  scanCard: {
    gap: 10
  },
  rowBetween: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    gap: 12
  }
});
