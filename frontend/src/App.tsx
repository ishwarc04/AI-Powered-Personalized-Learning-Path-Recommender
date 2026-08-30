/**
 * App.tsx — Root router for PathMind.
 */

import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import Onboarding from "./pages/Onboarding";
import SkillTree from "./pages/SkillTree";
import Dashboard from "./pages/Dashboard";
import { useStore } from "./store/useStore";

function RequireSession({ children }: { children: React.ReactNode }) {
  const learnerId = useStore((s) => s.learnerId);
  if (!learnerId) return <Navigate to="/" replace />;
  return <>{children}</>;
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Onboarding />} />
        <Route
          path="/tree"
          element={
            <RequireSession>
              <SkillTree />
            </RequireSession>
          }
        />
        <Route
          path="/dashboard"
          element={
            <RequireSession>
              <Dashboard />
            </RequireSession>
          }
        />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
