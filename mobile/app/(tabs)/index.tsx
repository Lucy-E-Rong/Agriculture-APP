import { Pressable, StyleSheet, View } from "react-native";
import { Link } from "expo-router";
import { Settings } from "lucide-react-native";
import { AppText } from "@/components/AppText";
import { Card } from "@/components/Card";
import { PrimaryButton } from "@/components/PrimaryButton";
import { Screen } from "@/components/Screen";
import { StressBadge } from "@/components/StressBadge";
import { colors } from "@/constants/colors";
import { recentScans } from "@/lib/mockData";
import { t } from "@/lib/i18n";
import { useAppStore } from "@/store/appStore";

export default function DashboardScreen() {
  const language = useAppStore((state) => state.language);

  return (
    <Screen>
      <View style={styles.header}>
        <View>
          <AppText variant="title">{t(language, "appName")}</AppText>
          <AppText variant="caption">{t(language, "mockNotice")}</AppText>
        </View>
        <Link href="/settings" asChild>
          <Pressable style={styles.iconButton}>
            <Settings stroke={colors.primary} size={22} />
          </Pressable>
        </Link>
      </View>

      <View style={styles.statsGrid}>
        <StatCard label={t(language, "todayScans")} value="24" />
        <StatCard label={t(language, "activeAlerts")} value="3" />
        <StatCard label={t(language, "greenhouses")} value="2" />
      </View>

      <View style={styles.quickActions}>
        <Link href="/(tabs)/scan" asChild>
          <PrimaryButton>{t(language, "scanNow")}</PrimaryButton>
        </Link>
        <Link href="/(tabs)/crops" asChild>
          <PrimaryButton variant="secondary">{t(language, "addCrop")}</PrimaryButton>
        </Link>
      </View>

      <AppText variant="subtitle">{t(language, "recentScans")}</AppText>
      {recentScans.map((scan) => (
        <Card key={scan.id} style={styles.scanCard}>
          <View style={styles.rowBetween}>
            <View style={styles.scanText}>
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

function StatCard({ label, value }: { label: string; value: string }) {
  return (
    <Card style={styles.statCard}>
      <AppText variant="title" style={styles.statValue}>
        {value}
      </AppText>
      <AppText variant="caption">{label}</AppText>
    </Card>
  );
}

const styles = StyleSheet.create({
  header: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between"
  },
  iconButton: {
    width: 42,
    height: 42,
    borderRadius: 8,
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: colors.primaryTint
  },
  statsGrid: {
    flexDirection: "row",
    gap: 10
  },
  statCard: {
    flex: 1,
    minHeight: 92,
    justifyContent: "space-between"
  },
  statValue: {
    color: colors.primary
  },
  quickActions: {
    flexDirection: "row",
    gap: 10
  },
  scanCard: {
    gap: 10
  },
  rowBetween: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    gap: 12
  },
  scanText: {
    flex: 1,
    gap: 2
  }
});
