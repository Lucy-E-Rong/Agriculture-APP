import { PropsWithChildren } from "react";
import { Pressable, StyleSheet } from "react-native";
import { colors } from "@/constants/colors";
import { AppText } from "@/components/AppText";

type Props = PropsWithChildren<{
  onPress?: () => void;
  variant?: "primary" | "secondary";
  disabled?: boolean;
}>;

export function PrimaryButton({ children, onPress, variant = "primary", disabled = false }: Props) {
  return (
    <Pressable
      disabled={disabled}
      onPress={onPress}
      style={({ pressed }) => [styles.button, styles[variant], pressed && styles.pressed, disabled && styles.disabled]}
    >
      <AppText style={[styles.text, variant === "secondary" && styles.secondaryText]}>{children}</AppText>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  button: {
    minHeight: 46,
    borderRadius: 8,
    alignItems: "center",
    justifyContent: "center",
    paddingHorizontal: 16
  },
  primary: {
    backgroundColor: colors.primary
  },
  secondary: {
    backgroundColor: colors.primaryTint,
    borderColor: colors.border,
    borderWidth: 1
  },
  pressed: {
    opacity: 0.75
  },
  disabled: {
    opacity: 0.45
  },
  text: {
    color: colors.white,
    fontWeight: "800"
  },
  secondaryText: {
    color: colors.primary
  }
});
