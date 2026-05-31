import { useState } from "react";
import { Routes, Route, Navigate } from "react-router-dom";
import { Layout } from "@/components/Layout";
import { SimulatePage } from "@/pages/SimulatePage";
import { BikesPage } from "@/pages/BikesPage";
import { BuildPage } from "@/pages/BuildPage";
import { AutotunePage } from "@/pages/AutotunePage";
import { ComparePage } from "@/pages/ComparePage";
import { HistoryPage } from "@/pages/HistoryPage";
import { SettingsPage } from "@/pages/SettingsPage";
import { ToastStack } from "@/components/Toast";
import { KeyboardShortcutsModal } from "@/components/KeyboardShortcutsModal";
import { useKeyboardShortcuts } from "@/hooks/useKeyboardShortcuts";

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
  return <AppInner />;
}
