import { Route, Routes } from "react-router-dom";

import Anomalies from "./pages/Anomalies";
import AuditLog from "./pages/AuditLog";
import Dashboard from "./pages/Dashboard";
import DataManagement from "./pages/DataManagement";
import Emissions from "./pages/Emissions";
import Reports from "./pages/Reports";
import Scenarios from "./pages/Scenarios";
import Settings from "./pages/Settings";
import Suppliers from "./pages/Suppliers";

export function AppRoutes() {
  return (
    <Routes>
      <Route path="/" element={<Dashboard />} />
      <Route path="/data" element={<DataManagement />} />
      <Route path="/emissions" element={<Emissions />} />
      <Route path="/suppliers" element={<Suppliers />} />
      <Route path="/anomalies" element={<Anomalies />} />
      <Route path="/scenarios" element={<Scenarios />} />
      <Route path="/reports" element={<Reports />} />
      <Route path="/audit" element={<AuditLog />} />
      <Route path="/settings" element={<Settings />} />
      <Route
        path="*"
        element={
          <div className="text-center text-sm text-slate-500">Page not found.</div>
        }
      />
    </Routes>
  );
}
