import { StyleSheet, View } from "react-native";
import { AppText } from "@/components/AppText";
import { Card } from "@/components/Card";
import { PrimaryButton } from "@/components/PrimaryButton";
import { Screen } from "@/components/Screen";
import { StressBadge } from "@/components/StressBadge";
import { locations } from "@/lib/mockData";
import { t } from "@/lib/i18n";
import { useAppStore } from "@/store/appStore";
import { colors } from "@/constants/colors";

export default function LocationsScreen() {
  const language = useAppStore((state) => state.language);

  return (
    <Screen>
      <View style={styles.header}>
        <View>
          <AppText variant="title">{t(language, "locations")}</AppText>
          <AppText variant="caption">Greenhouse → Section → Table → Row</AppText>
        </View>
        <PrimaryButton variant="secondary">{t(language, "addLocation")}</PrimaryButton>
      </View>

      {locations.map((greenhouse) => (
        <Card key={greenhouse.id} style={styles.greenhouseCard}>
          <View style={styles.titleRow}>
            <AppText variant="subtitle">{greenhouse.name}</AppText>
            <AppText style={styles.shortId}>{greenhouse.shortId}</AppText>
          </View>
          {greenhouse.sections.map((section) => (
            <View key={section.id} style={styles.sectionBlock}>
              <AppText variant="label">{section.name}</AppText>
              {section.tables.map((table) => (
                <View key={table.id} style={styles.tableBlock}>
                  <AppText>{t(language, "table")} {table.number}</AppText>
                  <View style={styles.rowGrid}>
                    {table.rows.map((row) => (
                      <View key={row.id} style={styles.rowCell}>
                        <AppText variant="label">R{row.number}</AppText>
                        <AppText variant="caption" numberOfLines={1}>{row.crop ?? t(language, "emptyState")}</AppText>
                        <StressBadge level={row.stress} language={language} />
                      </View>
                    ))}
                  </View>
                </View>
              ))}
            </View>
          ))}
        </Card>
      ))}
    </Screen>
  );
}

const styles = StyleSheet.create({
  header: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    gap: 12
  },
  greenhouseCard: {
    gap: 14
  },
  titleRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center"
  },
  shortId: {
    color: colors.primary,
    fontWeight: "800"
  },
  sectionBlock: {
    borderTopColor: colors.border,
    borderTopWidth: 1,
    paddingTop: 12,
    gap: 10
  },
  tableBlock: {
    gap: 10
  },
  rowGrid: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 8
  },
  rowCell: {
    width: "31%",
    minHeight: 108,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: 8,
    padding: 9,
    gap: 7,
    backgroundColor: colors.cream
  }
});

