import { useState } from "react";
import { Routes, Route, Navigate } from "react-router-dom";
import { Loader2 } from "lucide-react";
import { Layout } from "@/components/Layout";
import { SimulatePage } from "@/pages/SimulatePage";
import { BikesPage } from "@/pages/BikesPage";
import { BuildPage } from "@/pages/BuildPage";
import { AutotunePage } from "@/pages/AutotunePage";
import { ComparePage } from "@/pages/ComparePage";
import { HistoryPage } from "@/pages/HistoryPage";
import { SettingsPage } from "@/pages/SettingsPage";
import { LoginScreen } from "@/pages/LoginScreen";
import { ToastStack } from "@/components/Toast";
import { KeyboardShortcutsModal } from "@/components/KeyboardShortcutsModal";
import { useKeyboardShortcuts } from "@/hooks/useKeyboardShortcuts";
import { useAuth } from "@/contexts/AuthContext";

function AppInner() {
  const [shortcutsOpen, setShortcutsOpen] = useState(false);

  useKeyboardShortcuts({
    onOpenShortcuts: () => setShortcutsOpen(true),
    onCloseShortcuts: () => setShortcutsOpen(false),
  });

  return (
    <>
      <Layout>
        <Routes>
          <Route path="/" element={<Navigate to="/simulate" replace />} />
          <Route path="/simulate" element={<SimulatePage />} />
          <Route path="/bikes" element={<BikesPage />} />
          <Route path="/build" element={<BuildPage />} />
          <Route path="/autotune" element={<AutotunePage />} />
          <Route path="/compare" element={<ComparePage />} />
          <Route path="/history" element={<HistoryPage />} />
          <Route path="/settings" element={<SettingsPage />} />
          <Route path="*" element={<Navigate to="/simulate" replace />} />
        </Routes>
      </Layout>
      <ToastStack />
      {shortcutsOpen && (
        <KeyboardShortcutsModal onClose={() => setShortcutsOpen(false)} />
      )}
    </>
  );
}

export function App() {
  // Whole-app auth gate: no simulator until the hosted server has issued a
  // valid session. The server is the license authority; the client only
  // presents credentials and reacts to its verdict.
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-carbon-950 text-carbon-400">
        <div className="flex items-center gap-2 text-sm">
          <Loader2 className="w-4 h-4 animate-spin" aria-hidden="true" />
          Connecting to MotoQuant servers…
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <LoginScreen />;
  }

  return <AppInner />;
}
