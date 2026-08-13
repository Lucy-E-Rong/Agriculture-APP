import { Tabs } from "expo-router";
import { BarChart3, Home, Leaf, MapPinned, ScanLine } from "lucide-react-native";
import { colors } from "@/constants/colors";
import { useAppStore } from "@/store/appStore";
import { t } from "@/lib/i18n";

export default function TabsLayout() {
  const language = useAppStore((state) => state.language);

  return (
    <Tabs
      screenOptions={{
        headerShown: false,
        tabBarActiveTintColor: colors.primary,
        tabBarInactiveTintColor: colors.textMuted,
        tabBarStyle: {
          backgroundColor: colors.white,
          borderTopColor: colors.border,
          height: 78,
          paddingBottom: 18,
          paddingTop: 10
        },
        tabBarLabelStyle: {
          fontSize: 11,
          fontWeight: "700"
        }
      }}
    >
      <Tabs.Screen
        name="index"
        options={{
          title: t(language, "dashboard"),
          tabBarIcon: ({ color, size }) => <Home stroke={color} size={size} />
        }}
      />
      <Tabs.Screen
        name="crops"
        options={{
          title: t(language, "crops"),
          tabBarIcon: ({ color, size }) => <Leaf stroke={color} size={size} />
        }}
      />
      <Tabs.Screen
        name="scan"
        options={{
          title: t(language, "scan"),
          tabBarIcon: ({ color, size }) => <ScanLine stroke={color} size={size} />
        }}
      />
      <Tabs.Screen
        name="locations"
        options={{
          title: t(language, "locations"),
          tabBarIcon: ({ color, size }) => <MapPinned stroke={color} size={size} />
        }}
      />
      <Tabs.Screen
        name="reports"
        options={{
          title: t(language, "reports"),
          tabBarIcon: ({ color, size }) => <BarChart3 stroke={color} size={size} />
        }}
      />
    </Tabs>
  );
}
