import { Routes, Route, Navigate } from "react-router-dom";
import { Layout } from "@/components/Layout";
import { SimulatePage } from "@/pages/SimulatePage";
import { BikesPage } from "@/pages/BikesPage";
import { BuildPage } from "@/pages/BuildPage";
import { HistoryPage } from "@/pages/HistoryPage";
import { SettingsPage } from "@/pages/SettingsPage";

export function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Navigate to="/simulate" replace />} />
        <Route path="/simulate" element={<SimulatePage />} />
        <Route path="/bikes" element={<BikesPage />} />
        <Route path="/build" element={<BuildPage />} />
        <Route path="/history" element={<HistoryPage />} />
        <Route path="/settings" element={<SettingsPage />} />
        <Route path="*" element={<Navigate to="/simulate" replace />} />
      </Routes>
    </Layout>
  );
}
