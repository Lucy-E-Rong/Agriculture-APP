import { useState } from "react";
import { ActivityIndicator, Image, Pressable, StyleSheet, View } from "react-native";
import * as ImageManipulator from "expo-image-manipulator";
import * as ImagePicker from "expo-image-picker";
import { AppText } from "@/components/AppText";
import { Card } from "@/components/Card";
import { PrimaryButton } from "@/components/PrimaryButton";
import { Screen } from "@/components/Screen";
import { StressBadge } from "@/components/StressBadge";
import { colors } from "@/constants/colors";
import { analyzeScan, AnalyzeScanResult } from "@/lib/api";
import { t } from "@/lib/i18n";
import { useAppStore } from "@/store/appStore";

const MAX_IMAGE_DIMENSION = 1600;
const FALLBACK_IMAGE_DIMENSION = 1200;
const SAFE_BASE64_LENGTH = 3_500_000;

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
  const [result, setResult] = useState<AnalyzeScanResult | undefined>();
  const [preparingImage, setPreparingImage] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | undefined>();

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
      const response = await analyzeScan({
        accessCode,
        imageBase64,
        imageUri,
        imageMimeType,
        provider: aiProvider,
        language,
        cropId: "crop-1",
        greenhouseId: "gh-1",
        sectionId: "sec-a",
        tableId: "table-1",
        rowId: "row-1"
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
        <AppText variant="caption">{t(language, "locationPicker")}: GH1 · SA · T1 · R1</AppText>
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
            label={t(language, "localVlm")}
            active={aiProvider === "local_vlm"}
            onPress={() => setAiProvider("local_vlm")}
          />
        </View>
      </Card>

      <Card style={styles.locationCard}>
        <Field label={t(language, "greenhouse")} value="Greenhouse 1" />
        <Field label={t(language, "section")} value="Section A" />
        <Field label={t(language, "table")} value="Table 1" />
        <Field label={t(language, "row")} value="Row 1 · Romaine" />
      </Card>

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

      {result ? (
        <Card style={styles.resultCard}>
          <View style={styles.resultHeader}>
            <AppText variant="subtitle">{t(language, "diagnosis")}</AppText>
            <StressBadge level={result.stress_level} language={language} />
          </View>
          {!result.image_quality.usable ? (
            <View style={styles.section}>
              <AppText variant="label">{t(language, "imageQuality")}</AppText>
              {result.image_quality.issues.map((item) => <AppText key={item}>• {item}</AppText>)}
              {result.image_quality.retake_guidance.map((item) => <AppText key={item}>• {item}</AppText>)}
            </View>
          ) : null}
          <Field label={t(language, "severity")} value={`${result.severity_score}/5`} />
          <Field label={t(language, "confidence")} value={`${Math.round(result.confidence * 100)}%`} />
          <AppText>{result.diagnosis}</AppText>
          {result.observed_symptoms.length ? (
            <View style={styles.section}>
              <AppText variant="label">{t(language, "visibleSigns")}</AppText>
              {result.observed_symptoms.map((item, index) => (
                <AppText key={`${item.type}-${index}`}>• {item.description} ({item.location})</AppText>
              ))}
            </View>
          ) : null}
          {result.possible_causes.length ? (
            <View style={styles.section}>
              <AppText variant="label">{t(language, "possibleCauses")}</AppText>
              {result.possible_causes.map((item, index) => (
                <AppText key={`${item.category}-${index}`}>• {item.category}: {item.reason}</AppText>
              ))}
            </View>
          ) : null}
          <AppText variant="label">{t(language, "recommendations")}</AppText>
          {result.recommendations.map((item) => (
            <AppText key={item}>• {item}</AppText>
          ))}
          {result.needs_human_review ? <AppText style={styles.review}>{t(language, "humanReview")}</AppText> : null}
        </Card>
      ) : null}
    </Screen>
  );
}

function ProviderButton({ label, active, onPress }: { label: string; active: boolean; onPress: () => void }) {
  return (
    <Pressable onPress={onPress} style={[styles.providerButton, active && styles.providerButtonActive]}>
      <AppText style={[styles.providerText, active && styles.providerTextActive]}>{label}</AppText>
    </Pressable>
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
  field: {
    gap: 3
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
  resultCard: {
    gap: 12
  },
  resultHeader: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between"
  },
  section: {
    gap: 7
  },
  review: {
    color: colors.amberDark,
    fontWeight: "800"
  }
});
