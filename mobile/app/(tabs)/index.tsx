import { useCallback, useState } from "react";
import { ActivityIndicator, Pressable, StyleSheet, View } from "react-native";
import { Link, useFocusEffect } from "expo-router";
import { Settings } from "lucide-react-native";
import { AppText } from "@/components/AppText";
import { Card } from "@/components/Card";
import { PrimaryButton } from "@/components/PrimaryButton";
import { Screen } from "@/components/Screen";
import { StressBadge } from "@/components/StressBadge";
import { colors } from "@/constants/colors";
import { getRecentScans, RecentScan } from "@/lib/api";
import { t } from "@/lib/i18n";
import { useAppStore } from "@/store/appStore";

export default function DashboardScreen() {
  const language = useAppStore((state) => state.language);
  const accessCode = useAppStore((state) => state.accessCode);
  const [recentScans, setRecentScans] = useState<RecentScan[]>([]);
  const [loadingRecent, setLoadingRecent] = useState(true);
  const [recentError, setRecentError] = useState(false);

  useFocusEffect(
    useCallback(() => {
      let active = true;
      setLoadingRecent(true);
      setRecentError(false);
      getRecentScans(accessCode)
        .then((scans) => {
          if (active) setRecentScans(scans);
        })
        .catch(() => {
          if (active) {
            setRecentScans([]);
            setRecentError(true);
          }
        })
        .finally(() => {
          if (active) setLoadingRecent(false);
        });
      return () => {
        active = false;
      };
    }, [accessCode])
  );

  return (
    <Screen>
      <View style={styles.header}>
        <View>
          <AppText variant="title">{t(language, "appName")}</AppText>
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
      {loadingRecent ? <ActivityIndicator color={colors.primary} /> : null}
      {!loadingRecent && recentError ? <AppText variant="caption">{t(language, "recentScansError")}</AppText> : null}
      {!loadingRecent && !recentError && recentScans.length === 0 ? (
        <AppText variant="caption">{t(language, "emptyState")}</AppText>
      ) : null}
      {recentScans.map((scan) => (
        <Link key={scan.id} href={`/scans/${scan.id}`} asChild>
          <Pressable>
            <Card style={styles.scanCard}>
              <View style={styles.rowBetween}>
                <View style={styles.scanText}>
                  <AppText variant="subtitle">{t(language, "lettuceScan")}</AppText>
                  <AppText variant="caption">{scan.location_snapshot.display ?? t(language, "unknown")}</AppText>
                </View>
                <StressBadge level={scan.stress_level} language={language} />
              </View>
              <AppText variant="caption">{formatScanTime(scan.created_at, language)}</AppText>
            </Card>
          </Pressable>
        </Link>
      ))}
    </Screen>
  );
}

function formatScanTime(value: string, language: "en" | "zh") {
  return new Intl.DateTimeFormat(language === "zh" ? "zh-CN" : "en-US", {
    dateStyle: "medium",
    timeStyle: "short"
  }).format(new Date(value));
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
