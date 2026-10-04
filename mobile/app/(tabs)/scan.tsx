import { useState } from "react";
import { ActivityIndicator, Image, Pressable, StyleSheet, TextInput, View } from "react-native";
import * as ImageManipulator from "expo-image-manipulator";
import * as ImagePicker from "expo-image-picker";
import { AppText } from "@/components/AppText";
import { Card } from "@/components/Card";
import { PrimaryButton } from "@/components/PrimaryButton";
import { ScanAnalysisResult } from "@/components/ScanAnalysisResult";
import { Screen } from "@/components/Screen";
import { colors } from "@/constants/colors";
import { analyzeScan, PersistedAnalyzeScanResult, ScanLocationSnapshot } from "@/lib/api";
import { t } from "@/lib/i18n";
import { useAppStore } from "@/store/appStore";

const MAX_IMAGE_DIMENSION = 1600;
const FALLBACK_IMAGE_DIMENSION = 1200;
const SAFE_BASE64_LENGTH = 3_500_000;
type ContextField = Exclude<keyof ScanLocationSnapshot, "display" | "growth_stage">;
const EMPTY_CONTEXT: Record<ContextField, string> = {
  greenhouse: "",
  section: "",
  table: "",
  row: "",
  plant_id: "",
  sample_id: "",
  variety: "",
  period: ""
};

async function compressImage(
  uri: string,
  width: number,
  height: number,
  maxDimension: number,
  quality: number
) {
  const context = ImageManipulator.ImageManipulator.manipulate(uri);
  const largestDimension = Math.max(width, height);

  if (largestDimension > maxDimension) {
    context.resize(
      width >= height
        ? { width: maxDimension, height: null }
        : { width: null, height: maxDimension }
    );
  }

  const rendered = await context.renderAsync();
  return rendered.saveAsync({
    base64: true,
    compress: quality,
    format: ImageManipulator.SaveFormat.JPEG
  });
}

export default function ScanScreen() {
  const language = useAppStore((state) => state.language);
  const aiProvider = useAppStore((state) => state.aiProvider);
  const accessCode = useAppStore((state) => state.accessCode);
  const setAiProvider = useAppStore((state) => state.setAiProvider);
  const [imageUri, setImageUri] = useState<string | undefined>();
  const [imageBase64, setImageBase64] = useState<string | undefined>();
  const [imageMimeType, setImageMimeType] = useState("image/jpeg");
  const [result, setResult] = useState<PersistedAnalyzeScanResult | undefined>();
  const [preparingImage, setPreparingImage] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | undefined>();
  const [scanContext, setScanContext] = useState(EMPTY_CONTEXT);

  async function pickImage() {
    const picked = await ImagePicker.launchImageLibraryAsync({
      base64: false,
      mediaTypes: ImagePicker.MediaTypeOptions.Images,
      quality: 1
    });

    if (!picked.canceled) {
      setPreparingImage(true);
      setResult(undefined);
      setError(undefined);

      try {
        const asset = picked.assets[0];
        let prepared = await compressImage(
          asset.uri,
          asset.width,
          asset.height,
          MAX_IMAGE_DIMENSION,
          0.7
        );

        if ((prepared.base64?.length ?? 0) > SAFE_BASE64_LENGTH) {
          prepared = await compressImage(
            prepared.uri,
            prepared.width,
            prepared.height,
            FALLBACK_IMAGE_DIMENSION,
            0.5
          );
        }

        if (!prepared.base64 || prepared.base64.length > SAFE_BASE64_LENGTH) {
          throw new Error("Compressed image is still too large");
        }

        setImageUri(prepared.uri);
        setImageBase64(prepared.base64);
        setImageMimeType("image/jpeg");
      } catch {
        setImageUri(undefined);
        setImageBase64(undefined);
        setError(t(language, "imageProcessingFailed"));
      } finally {
        setPreparingImage(false);
      }
    }
  }

  async function submit() {
    if (!imageBase64) {
      setError(t(language, "selectImageFirst"));
      return;
    }

    setLoading(true);
    setError(undefined);
    try {
      const locationSnapshot = buildLocationSnapshot(scanContext);
      const response = await analyzeScan({
        accessCode,
        imageBase64,
        imageUri,
        imageMimeType,
        provider: aiProvider,
        language,
        ...(Object.keys(locationSnapshot).length ? { locationSnapshot } : {})
      });
      setResult(response);
    } catch (scanError) {
      setResult(undefined);
      setError(scanError instanceof Error ? scanError.message : "Analysis failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <Screen>
      <View>
        <AppText variant="title">{t(language, "scan")}</AppText>
        <AppText variant="caption">{t(language, "scanContextOptional")}</AppText>
      </View>

      <Card style={styles.providerCard}>
        <AppText variant="label">{t(language, "aiProvider")}</AppText>
        <View style={styles.segmented}>
          <ProviderButton
            label={t(language, "gemini")}
            active={aiProvider === "gemini"}
            onPress={() => setAiProvider("gemini")}
          />
          <ProviderButton
            label={t(language, "prototype")}
            active={aiProvider === "prototype"}
            onPress={() => setAiProvider("prototype")}
          />
        </View>
      </Card>

      <Card style={styles.locationCard}>
        <AppText variant="subtitle">{t(language, "scanContext")}</AppText>
        <AppText variant="caption">{t(language, "scanContextHint")}</AppText>
        <View style={styles.contextGrid}>
          <ContextInput label={t(language, "greenhouse")} value={scanContext.greenhouse} onChangeText={(value) => updateContext("greenhouse", value)} />
          <ContextInput label={t(language, "section")} value={scanContext.section} onChangeText={(value) => updateContext("section", value)} />
          <ContextInput label={t(language, "table")} value={scanContext.table} onChangeText={(value) => updateContext("table", value)} />
          <ContextInput label={t(language, "row")} value={scanContext.row} onChangeText={(value) => updateContext("row", value)} />
          <ContextInput label={t(language, "plantId")} value={scanContext.plant_id} onChangeText={(value) => updateContext("plant_id", value)} />
          <ContextInput label={t(language, "sampleId")} value={scanContext.sample_id} onChangeText={(value) => updateContext("sample_id", value)} />
          <ContextInput label={t(language, "variety")} value={scanContext.variety} onChangeText={(value) => updateContext("variety", value)} />
          <ContextInput label={t(language, "period")} value={scanContext.period} onChangeText={(value) => updateContext("period", value)} />
        </View>
      </Card>

      <EnvironmentalDataDemo language={language} />

      <Card style={styles.imageCard}>
        {imageUri ? (
          <Image source={{ uri: imageUri }} style={styles.preview} />
        ) : (
          <View style={styles.emptyImage}>
            <AppText variant="caption">{t(language, "chooseImage")}</AppText>
          </View>
        )}
        <PrimaryButton variant="secondary" disabled={preparingImage || loading} onPress={pickImage}>
          {preparingImage ? t(language, "preparingImage") : t(language, "chooseImage")}
        </PrimaryButton>
        <PrimaryButton disabled={preparingImage || loading || !imageBase64} onPress={submit}>
          {loading ? t(language, "analyzing") : t(language, "analyze")}
        </PrimaryButton>
        {preparingImage || loading ? <ActivityIndicator color={colors.primary} /> : null}
        {error ? <AppText variant="caption">{error}</AppText> : null}
      </Card>

      {result ? <ScanAnalysisResult result={result} language={language} /> : null}
    </Screen>
  );

  function updateContext(field: ContextField, value: string) {
    setScanContext((current) => ({ ...current, [field]: value }));
  }
}

function ProviderButton({ label, active, onPress }: { label: string; active: boolean; onPress: () => void }) {
  return (
    <Pressable onPress={onPress} style={[styles.providerButton, active && styles.providerButtonActive]}>
      <AppText style={[styles.providerText, active && styles.providerTextActive]}>{label}</AppText>
    </Pressable>
  );
}

function ContextInput({ label, value, onChangeText }: { label: string; value: string; onChangeText: (value: string) => void }) {
  return (
    <View style={styles.field}>
      <AppText variant="label">{label}</AppText>
      <TextInput
        accessibilityLabel={label}
        maxLength={120}
        onChangeText={onChangeText}
        style={styles.input}
        value={value}
      />
    </View>
  );
}

function EnvironmentalDataDemo({ language }: { language: "en" | "zh" }) {
  const [expanded, setExpanded] = useState(false);
  return (
    <Card style={styles.environmentCard}>
      <Pressable
        accessibilityRole="button"
        accessibilityState={{ expanded }}
        onPress={() => setExpanded((value) => !value)}
        style={styles.environmentHeader}
      >
        <View style={styles.environmentTitle}>
          <AppText variant="subtitle">{t(language, "environmentalData")}</AppText>
          <AppText variant="caption">{t(language, "demo")} · {t(language, "notConnected")}</AppText>
        </View>
        <AppText>{expanded ? "−" : "+"}</AppText>
      </Pressable>
      {expanded ? (
        <View style={styles.environmentValues}>
          <AppText variant="caption">{t(language, "environmentalDemoHint")}</AppText>
          <AppText>{t(language, "demoAirTemperature")}</AppText>
          <AppText>{t(language, "demoHumidity")}</AppText>
          <AppText>{t(language, "demoRootZoneMoisture")}</AppText>
        </View>
      ) : null}
    </Card>
  );
}

function buildLocationSnapshot(context: Record<ContextField, string>): ScanLocationSnapshot {
  const snapshot = Object.fromEntries(
    Object.entries(context)
      .map(([key, value]) => [key, value.trim()])
      .filter(([, value]) => value.length > 0)
  ) as ScanLocationSnapshot;
  const displayParts = [snapshot.greenhouse, snapshot.section, snapshot.table, snapshot.row].filter(Boolean);
  if (displayParts.length) snapshot.display = displayParts.join(" · ");
  return snapshot;
}

const styles = StyleSheet.create({
  providerCard: {
    gap: 10
  },
  segmented: {
    flexDirection: "row",
    gap: 8
  },
  providerButton: {
    flex: 1,
    minHeight: 42,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: colors.border,
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: colors.cream,
    paddingHorizontal: 8
  },
  providerButtonActive: {
    backgroundColor: colors.primary
  },
  providerText: {
    color: colors.primary,
    fontWeight: "800",
    textAlign: "center"
  },
  providerTextActive: {
    color: colors.white
  },
  locationCard: {
    gap: 10
  },
  contextGrid: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 10
  },
  field: {
    flexBasis: 220,
    flexGrow: 1,
    gap: 4
  },
  input: {
    minHeight: 42,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: colors.border,
    backgroundColor: colors.cream,
    color: colors.textPrimary,
    paddingHorizontal: 10,
    paddingVertical: 8
  },
  environmentCard: {
    gap: 10
  },
  environmentHeader: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between"
  },
  environmentTitle: {
    gap: 2
  },
  environmentValues: {
    gap: 7,
    paddingTop: 4
  },
  imageCard: {
    gap: 12
  },
  preview: {
    width: "100%",
    height: 220,
    borderRadius: 8
  },
  emptyImage: {
    height: 220,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: colors.border,
    backgroundColor: colors.cream,
    alignItems: "center",
    justifyContent: "center"
  },
});
