import { Route, Routes } from "react-router-dom";
import { Dashboard } from "./pages/Dashboard";
import { TicketDetail } from "./pages/TicketDetail";
import { Workspace } from "./pages/Workspace";
import { Submit } from "./pages/Submit";
import { PrView } from "./pages/PrView";
import { ReviewView } from "./pages/ReviewView";
import { ScoreView } from "./pages/ScoreView";
import { Profile } from "./pages/Profile";

export function App() {
  return (
    <Routes>
      <Route path="/" element={<Dashboard />} />
      <Route path="/tickets/:scenarioId" element={<TicketDetail />} />
      <Route path="/investigations/:investigationId" element={<Workspace />} />
      <Route path="/investigations/:investigationId/submit" element={<Submit />} />
      <Route path="/investigations/:investigationId/pr" element={<PrView />} />
      <Route path="/investigations/:investigationId/review" element={<ReviewView />} />
      <Route path="/investigations/:investigationId/score" element={<ScoreView />} />
      <Route path="/profile" element={<Profile />} />
    </Routes>
  );
}
