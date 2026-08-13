import { PropsWithChildren } from "react";
import { StyleSheet, Text, TextProps } from "react-native";
import { colors } from "@/constants/colors";

type AppTextProps = PropsWithChildren<TextProps & {
  variant?: "title" | "subtitle" | "body" | "caption" | "label";
}>;

export function AppText({ children, style, variant = "body", ...props }: AppTextProps) {
  return (
    <Text {...props} style={[styles.base, styles[variant], style]}>
      {children}
    </Text>
  );
}

const styles = StyleSheet.create({
  base: {
    color: colors.textPrimary,
    letterSpacing: 0
  },
  title: {
    fontSize: 26,
    fontWeight: "800"
  },
  subtitle: {
    fontSize: 16,
    fontWeight: "700"
  },
  body: {
    fontSize: 14,
    lineHeight: 20
  },
  caption: {
    fontSize: 12,
    color: colors.textMuted
  },
  label: {
    fontSize: 11,
    fontWeight: "800",
    color: colors.textSecondary,
    textTransform: "uppercase"
  }
});

