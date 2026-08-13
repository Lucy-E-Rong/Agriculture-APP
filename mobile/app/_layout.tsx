import { Stack } from "expo-router";
import { StatusBar } from "expo-status-bar";
import { AccessGate } from "@/components/AccessGate";

export default function RootLayout() {
  return (
    <>
      <StatusBar style="dark" />
      <AccessGate>
        <Stack screenOptions={{ headerShown: false }} />
      </AccessGate>
    </>
  );
}
