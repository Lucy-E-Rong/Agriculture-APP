import { create } from "zustand";
import { Language } from "@/lib/i18n";

export type AiProvider = "gemini" | "api_provider" | "local_vlm" | "mock";

type AppState = {
  language: Language;
  aiProvider: AiProvider;
  setLanguage: (language: Language) => void;
  setAiProvider: (provider: AiProvider) => void;
};

export const useAppStore = create<AppState>((set) => ({
  language: "en",
  aiProvider: "gemini",
  setLanguage: (language) => set({ language }),
  setAiProvider: (aiProvider) => set({ aiProvider })
}));
