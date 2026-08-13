import { create } from "zustand";
import { Language } from "@/lib/i18n";

export type AiProvider = "gemini" | "api_provider" | "local_vlm" | "mock";

type AppState = {
  language: Language;
  aiProvider: AiProvider;
  accessCode: string;
  setLanguage: (language: Language) => void;
  setAiProvider: (provider: AiProvider) => void;
  setAccessCode: (accessCode: string) => void;
};

export const useAppStore = create<AppState>((set) => ({
  language: "en",
  aiProvider: "gemini",
  accessCode: "",
  setLanguage: (language) => set({ language }),
  setAiProvider: (aiProvider) => set({ aiProvider }),
  setAccessCode: (accessCode) => set({ accessCode })
}));
