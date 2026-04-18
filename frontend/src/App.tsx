import { Route, Routes } from "react-router-dom";

import { RequireAuth } from "./components/auth/RequireAuth";
import { AppLayout } from "./components/layout/AppLayout";
import Login from "./pages/Login";
import { AppRoutes } from "./routes";

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route
        path="/*"
        element={
          <RequireAuth>
            <AppLayout>
              <AppRoutes />
            </AppLayout>
          </RequireAuth>
        }
      />
    </Routes>
  );
}
