import { create } from "zustand";
import { Language } from "@/lib/i18n";

export type AiProvider = "gemini" | "prototype";
export type AiModel = "gemini-3.6-flash" | "gpt-5.6-terra";

type AppState = {
  language: Language;
  aiProvider: AiProvider;
  aiModel: AiModel;
  accessCode: string;
  setLanguage: (language: Language) => void;
  setAiProvider: (provider: AiProvider) => void;
  setAiModel: (model: AiModel) => void;
  setAccessCode: (accessCode: string) => void;
};

export const useAppStore = create<AppState>((set) => ({
  language: "en",
  aiProvider: "gemini",
  aiModel: "gemini-3.6-flash",
  accessCode: "",
  setLanguage: (language) => set({ language }),
  setAiProvider: (aiProvider) => set({ aiProvider }),
  setAiModel: (aiModel) => set({ aiModel }),
  setAccessCode: (accessCode) => set({ accessCode })
}));
