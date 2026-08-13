import { Pressable, StyleSheet, View } from "react-native";
import { AppText } from "@/components/AppText";
import { Card } from "@/components/Card";
import { Screen } from "@/components/Screen";
import { colors } from "@/constants/colors";
import { t } from "@/lib/i18n";
import { useAppStore } from "@/store/appStore";

export default function SettingsScreen() {
  const language = useAppStore((state) => state.language);
  const setLanguage = useAppStore((state) => state.setLanguage);

  return (
    <Screen>
      <View>
        <AppText variant="title">{t(language, "settings")}</AppText>
        <AppText variant="caption">{t(language, "defaultLanguage")}: English</AppText>
      </View>

      <Card style={styles.card}>
        <AppText variant="subtitle">{t(language, "language")}</AppText>
        <View style={styles.segmented}>
          <LanguageButton label={t(language, "english")} active={language === "en"} onPress={() => setLanguage("en")} />
          <LanguageButton label={t(language, "chinese")} active={language === "zh"} onPress={() => setLanguage("zh")} />
        </View>
      </Card>

      <Card style={styles.card}>
        <AppText variant="subtitle">{t(language, "workspace")}</AppText>
        <AppText>Biningu Farms</AppText>
        <AppText variant="caption">biningu.farmscout.app</AppText>
      </Card>

      <Card style={styles.card}>
        <AppText variant="subtitle">{t(language, "promptSettings")}</AppText>
        <AppText variant="caption">
          {language === "zh"
            ? "后端会保存默认提示词，并根据扫描位置、作物和语言生成结构化结果。"
            : "The backend stores the default prompt and produces structured results using location, crop, and language context."}
        </AppText>
      </Card>
    </Screen>
  );
}

function LanguageButton({ label, active, onPress }: { label: string; active: boolean; onPress: () => void }) {
  return (
    <Pressable onPress={onPress} style={[styles.languageButton, active && styles.languageButtonActive]}>
      <AppText style={[styles.languageText, active && styles.languageTextActive]}>{label}</AppText>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  card: {
    gap: 12
  },
  segmented: {
    flexDirection: "row",
    gap: 8
  },
  languageButton: {
    flex: 1,
    minHeight: 44,
    borderRadius: 8,
    borderColor: colors.border,
    borderWidth: 1,
    backgroundColor: colors.cream,
    alignItems: "center",
    justifyContent: "center"
  },
  languageButtonActive: {
    backgroundColor: colors.primary
  },
  languageText: {
    color: colors.primary,
    fontWeight: "800"
  },
  languageTextActive: {
    color: colors.white
  }
});
