import AsyncStorage from "@react-native-async-storage/async-storage";
import { PropsWithChildren, useEffect, useState } from "react";
import { ActivityIndicator, SafeAreaView, StyleSheet, TextInput, View } from "react-native";
import { AppText } from "@/components/AppText";
import { PrimaryButton } from "@/components/PrimaryButton";
import { colors } from "@/constants/colors";
import { verifyAccessCode } from "@/lib/api";
import { useAppStore } from "@/store/appStore";

const ACCESS_CODE_STORAGE_KEY = "farmscout.demoAccessCode";

export function AccessGate({ children }: PropsWithChildren) {
  const accessCode = useAppStore((state) => state.accessCode);
  const setAccessCode = useAppStore((state) => state.setAccessCode);
  const [input, setInput] = useState("");
  const [checkingStoredCode, setCheckingStoredCode] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    async function restoreAccess() {
      const storedCode = await AsyncStorage.getItem(ACCESS_CODE_STORAGE_KEY);
      if (storedCode) {
        try {
          await verifyAccessCode(storedCode);
          setAccessCode(storedCode);
        } catch {
          await AsyncStorage.removeItem(ACCESS_CODE_STORAGE_KEY);
        }
      }
      setCheckingStoredCode(false);
    }

    restoreAccess();
  }, [setAccessCode]);

  async function unlock() {
    const candidate = input.trim();
    if (!candidate) {
      setError("Enter the access code provided by the FarmScout team. / 请输入测试访问码。");
      return;
    }

    setSubmitting(true);
    setError("");
    try {
      await verifyAccessCode(candidate);
      await AsyncStorage.setItem(ACCESS_CODE_STORAGE_KEY, candidate);
      setAccessCode(candidate);
    } catch {
      setError("The access code is incorrect. / 访问码不正确。");
    } finally {
      setSubmitting(false);
    }
  }

  if (checkingStoredCode) {
    return (
      <SafeAreaView style={styles.loading}>
        <ActivityIndicator color={colors.primary} />
      </SafeAreaView>
    );
  }

  if (accessCode) {
    return children;
  }

  return (
    <SafeAreaView style={styles.page}>
      <View style={styles.panel}>
        <View style={styles.brandMark}>
          <AppText style={styles.brandLeaf}>◉</AppText>
        </View>
        <AppText variant="title" style={styles.title}>FarmScout</AppText>
        <AppText style={styles.description}>
          Private crop-scouting demo. Enter the access code shared by the FarmScout team.
        </AppText>
        <AppText variant="caption" style={styles.description}>
          这是内部测试版本，请输入 FarmScout 团队提供的访问码。
        </AppText>
        <TextInput
          autoCapitalize="none"
          autoCorrect={false}
          onChangeText={setInput}
          onSubmitEditing={unlock}
          placeholder="Access code / 访问码"
          placeholderTextColor={colors.textMuted}
          secureTextEntry
          style={styles.input}
          value={input}
        />
        <PrimaryButton disabled={submitting} onPress={unlock}>
          {submitting ? "Checking..." : "Open demo / 进入测试"}
        </PrimaryButton>
        {submitting ? <ActivityIndicator color={colors.primary} /> : null}
        {error ? <AppText variant="caption" style={styles.error}>{error}</AppText> : null}
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  loading: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: colors.cream
  },
  page: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: colors.cream,
    padding: 24
  },
  panel: {
    width: "100%",
    maxWidth: 420,
    gap: 14,
    padding: 28,
    borderRadius: 20,
    borderWidth: 1,
    borderColor: colors.border,
    backgroundColor: colors.white
  },
  brandMark: {
    width: 50,
    height: 50,
    borderRadius: 16,
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: colors.primaryTint
  },
  brandLeaf: {
    color: colors.primary,
    fontSize: 26,
    fontWeight: "800"
  },
  title: {
    color: colors.primary
  },
  description: {
    color: colors.textSecondary
  },
  input: {
    minHeight: 48,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: 10,
    backgroundColor: colors.cream,
    color: colors.textPrimary,
    paddingHorizontal: 14,
    fontSize: 16
  },
  error: {
    color: "#A33A2B"
  }
});
