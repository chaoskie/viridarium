import type { ReactNode } from "react";
import { Route, Routes } from "react-router-dom";

import { AppShell } from "@/components/AppShell";
import { PlaceholderPage } from "@/components/PlaceholderPage";
import { AboutPage } from "@/features/about/AboutPage";
import { PlantDetailPage } from "@/features/plants/PlantDetailPage";
import { PlantsPage } from "@/features/plants/PlantsPage";
import { RoomsPage } from "@/features/rooms/RoomsPage";
import { SettingsPage } from "@/features/settings/SettingsPage";
import { TodayPage } from "@/features/today/TodayPage";

export function App(): ReactNode {
  return (
    <AppShell>
      <Routes>
        <Route path="/" element={<TodayPage />} />
        <Route path="/plants" element={<PlantsPage />} />
        <Route path="/plants/:id" element={<PlantDetailPage />} />
        <Route path="/rooms" element={<RoomsPage />} />
        <Route path="/journal" element={<PlaceholderPage title="Journal" />} />
        <Route path="/settings" element={<SettingsPage />} />
        <Route path="/about" element={<AboutPage />} />
        <Route path="*" element={<PlaceholderPage title="Not found" />} />
      </Routes>
    </AppShell>
  );
}
