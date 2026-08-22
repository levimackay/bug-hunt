import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import "./index.css";
import { App } from "./App";
import { AuthProvider } from "./auth/AuthProvider";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <BrowserRouter>
      <AuthProvider>
        <div className="h-screen w-screen overflow-hidden">
          <App />
        </div>
      </AuthProvider>
    </BrowserRouter>
  </StrictMode>,
);
