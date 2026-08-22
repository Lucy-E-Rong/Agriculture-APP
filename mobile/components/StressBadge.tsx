import { StyleSheet, View } from "react-native";
import { colors } from "@/constants/colors";
import { AppText } from "@/components/AppText";
import { Language, t } from "@/lib/i18n";

type Stress = "none" | "low" | "medium" | "high" | "critical" | string;

type Props = {
  level: Stress;
  language: Language;
};

export function StressBadge({ level, language }: Props) {
  const normalized = level;
  const label =
    normalized === "low"
      ? t(language, "stressLow")
      : normalized === "medium"
        ? t(language, "stressMedium")
        : normalized === "high"
          ? t(language, "stressHigh")
          : normalized === "critical"
            ? t(language, "stressCritical")
          : t(language, "stressNone");

  return (
    <View style={[styles.badge, styles[normalized as "none" | "low" | "medium" | "high" | "critical"] ?? styles.none]}>
      <AppText variant="caption" style={[styles.text, styles[`${normalized}Text` as keyof typeof styles]]}>
        {label}
      </AppText>
    </View>
  );
}

const styles = StyleSheet.create({
  badge: {
    alignSelf: "flex-start",
    borderRadius: 999,
    paddingHorizontal: 10,
    paddingVertical: 5
  },
  text: {
    fontWeight: "800"
  },
  none: {
    backgroundColor: colors.primaryTint
  },
  low: {
    backgroundColor: colors.primaryTint
  },
  medium: {
    backgroundColor: "#FFF3D6"
  },
  high: {
    backgroundColor: "#FDEAEA"
  },
  critical: {
    backgroundColor: "#F8D7DA"
  },
  noneText: {
    color: colors.primary
  },
  lowText: {
    color: colors.primary
  },
  mediumText: {
    color: colors.amberDark
  },
  highText: {
    color: colors.danger
  },
  criticalText: {
    color: colors.danger
  }
});
