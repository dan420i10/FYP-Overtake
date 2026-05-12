import { Outlet, useLocation } from "react-router";
import Navbar from "./Navbar";
import Chatbot from "./Chatbot";
import ThemeProvider from "./ThemeProvider";
import { Toaster } from "sonner";

export default function Root() {
  const location = useLocation();
  const isLoginPage = location.pathname === "/";

  return (
    <ThemeProvider>
      <div
        className={
          isLoginPage
            ? "h-dvh max-h-dvh overflow-hidden bg-background"
            : "min-h-screen bg-background"
        }
      >
        <Toaster position="top-right" richColors />
        {!isLoginPage && <Navbar />}
        <Outlet />
        {!isLoginPage && <Chatbot />}
      </div>
    </ThemeProvider>
  );
}
