import type { ReactNode } from "react";
import { Route, Routes } from "react-router-dom";

import { AppShell } from "@/components/AppShell";
import { PlaceholderPage } from "@/components/PlaceholderPage";
import { RoomsPage } from "@/features/rooms/RoomsPage";
import { TodayPage } from "@/features/today/TodayPage";

export function App(): ReactNode {
  return (
    <AppShell>
      <Routes>
        <Route path="/" element={<TodayPage />} />
        <Route path="/plants" element={<PlaceholderPage title="Plants" />} />
        <Route path="/rooms" element={<RoomsPage />} />
        <Route path="/journal" element={<PlaceholderPage title="Journal" />} />
        <Route
          path="/settings"
          element={<PlaceholderPage title="Settings" />}
        />
        <Route path="*" element={<PlaceholderPage title="Not found" />} />
      </Routes>
    </AppShell>
  );
}
