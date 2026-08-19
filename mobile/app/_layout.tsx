import { Stack } from "expo-router";
import { StatusBar } from "expo-status-bar";
import { AccessGate } from "@/components/AccessGate";
import { Analytics } from "@vercel/analytics/react";

export default function RootLayout() {
  return (
    <>
      <StatusBar style="dark" />
      <AccessGate>
        <Stack screenOptions={{ headerShown: false }} />
      </AccessGate>
      <Analytics />
    </>
  );
}
