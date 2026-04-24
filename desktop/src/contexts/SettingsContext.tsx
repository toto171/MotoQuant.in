// App-wide user preferences — persisted to localStorage.
// Provides unit conversions helpers so every display site can use
// displaySpeed() / displayMass() / displayTorque() without knowing
// which unit system is active.

import {
  createContext,
  useContext,
  useEffect,
  useState,
  ReactNode,
  useCallback,
} from "react";

export type Units = "metric" | "imperial";
export type Theme = "dark" | "system";

interface Settings {
  units: Units;
  theme: Theme;
  defaultVenueId: number | null;
  useAdaptiveDt: boolean;
}

const STORAGE_KEY = "mq_settings";

const DEFAULTS: Settings = {
  units: "metric",
  theme: "dark",
  defaultVenueId: null,
  useAdaptiveDt: false,
};

function load(): Settings {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw) return { ...DEFAULTS, ...JSON.parse(raw) };
  } catch {
    // corrupt storage — use defaults
  }
  return { ...DEFAULTS };
}

function save(s: Settings) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(s));
  } catch {
    // storage full / private mode — silent
  }
}

function applyTheme(theme: Theme) {
  const prefersDark =
    window.matchMedia?.("(prefers-color-scheme: dark)").matches ?? true;
  const isDark = theme === "dark" || (theme === "system" && prefersDark);
  document.documentElement.classList.toggle("dark", isDark);
}

// ─── Context definition ──────────────────────────────────────────────────

interface SettingsContextValue extends Settings {
  setUnits: (u: Units) => void;
  setTheme: (t: Theme) => void;
  setDefaultVenueId: (id: number | null) => void;
  setUseAdaptiveDt: (v: boolean) => void;
  // Display helpers
  displaySpeed: (kmh: number | null | undefined, dec?: number) => string;
  displayMass: (kg: number | null | undefined, dec?: number) => string;
  displayTorque: (nm: number | null | undefined, dec?: number) => string;
  speedUnit: string;
  massUnit: string;
  torqueUnit: string;
}

const SettingsContext = createContext<SettingsContextValue | null>(null);

export function SettingsProvider({ children }: { children: ReactNode }) {
  const [settings, setSettings] = useState<Settings>(load);

  // Apply theme on every settings change.
  useEffect(() => {
    applyTheme(settings.theme);
    save(settings);
  }, [settings]);

  // Also re-apply when system preference changes (for theme="system").
  useEffect(() => {
    const mq = window.matchMedia?.("(prefers-color-scheme: dark)");
    if (!mq) return;
    const handler = () => {
      if (settings.theme === "system") applyTheme("system");
    };
    mq.addEventListener("change", handler);
    return () => mq.removeEventListener("change", handler);
  }, [settings.theme]);

  const patch = useCallback((patch: Partial<Settings>) => {
    setSettings((prev) => ({ ...prev, ...patch }));
  }, []);

  const { units } = settings;

  const displaySpeed = useCallback(
    (kmh: number | null | undefined, dec = 1) => {
      if (kmh == null) return "—";
      if (units === "imperial") return `${(kmh * 0.6214).toFixed(dec)}`;
      return `${kmh.toFixed(dec)}`;
    },
    [units],
  );

  const displayMass = useCallback(
    (kg: number | null | undefined, dec = 1) => {
      if (kg == null) return "—";
      if (units === "imperial") return `${(kg * 2.2046).toFixed(dec)}`;
      return `${kg.toFixed(dec)}`;
    },
    [units],
  );

  const displayTorque = useCallback(
    (nm: number | null | undefined, dec = 1) => {
      if (nm == null) return "—";
      if (units === "imperial") return `${(nm * 0.7376).toFixed(dec)}`;
      return `${nm.toFixed(dec)}`;
    },
    [units],
  );

  const value: SettingsContextValue = {
    ...settings,
    setUnits: (u) => patch({ units: u }),
    setTheme: (t) => patch({ theme: t }),
    setDefaultVenueId: (id) => patch({ defaultVenueId: id }),
    setUseAdaptiveDt: (v) => patch({ useAdaptiveDt: v }),
    displaySpeed,
    displayMass,
    displayTorque,
    speedUnit: units === "imperial" ? "mph" : "km/h",
    massUnit: units === "imperial" ? "lb" : "kg",
    torqueUnit: units === "imperial" ? "ft·lb" : "Nm",
  };

  return (
    <SettingsContext.Provider value={value}>
      {children}
    </SettingsContext.Provider>
  );
}

export function useSettings(): SettingsContextValue {
  const ctx = useContext(SettingsContext);
  if (!ctx) throw new Error("useSettings must be used inside <SettingsProvider>");
  return ctx;
}
