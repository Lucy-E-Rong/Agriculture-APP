import { StyleSheet, View } from "react-native";
import { AppText } from "@/components/AppText";
import { Card } from "@/components/Card";
import { PrimaryButton } from "@/components/PrimaryButton";
import { Screen } from "@/components/Screen";
import { StressBadge } from "@/components/StressBadge";
import { crops } from "@/lib/mockData";
import { t } from "@/lib/i18n";
import { useAppStore } from "@/store/appStore";

export default function CropsScreen() {
  const language = useAppStore((state) => state.language);

  return (
    <Screen>
      <View style={styles.header}>
        <View>
          <AppText variant="title">{t(language, "crops")}</AppText>
          <AppText variant="caption">{t(language, "mockNotice")}</AppText>
        </View>
        <PrimaryButton variant="secondary">{t(language, "addCrop")}</PrimaryButton>
      </View>

      <Card style={styles.formPreview}>
        <AppText variant="label">{t(language, "addCrop")}</AppText>
        <Field label={t(language, "cropName")} value="Lettuce" />
        <Field label={t(language, "variety")} value="Romaine" />
        <Field label={t(language, "locationPicker")} value="GH1 · SA · T1 · R3" />
      </Card>

      {crops.map((crop) => (
        <Card key={crop.id} style={styles.cropCard}>
          <View style={styles.rowBetween}>
            <View style={styles.cropMain}>
              <AppText variant="subtitle">{crop.name}</AppText>
              <AppText variant="caption">{crop.variety}</AppText>
            </View>
            <StressBadge level={crop.stress} language={language} />
          </View>
          <AppText>{crop.location}</AppText>
          <AppText variant="caption">{crop.plantedAt} · {crop.lastScan}</AppText>
        </Card>
      ))}
    </Screen>
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
  header: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    gap: 12
  },
  formPreview: {
    gap: 10
  },
  field: {
    gap: 3
  },
  cropCard: {
    gap: 10
  },
  cropMain: {
    flex: 1
  },
  rowBetween: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    gap: 12
  }
});

