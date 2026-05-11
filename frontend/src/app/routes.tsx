import { createBrowserRouter } from "react-router";
import Root from "./components/Root";
import Login from "./components/Login";
import Dashboard from "./components/Dashboard";
import Predictions from "./components/Predictions";
import Profile from "./components/Profile";
import Statistics from "./components/Statistics";
import Settings from "./components/Settings";
import Notifications from "./components/Notifications";
import ProtectedRoute from "./components/ProtectedRoute";

export const router = createBrowserRouter([
  {
    path: "/",
    Component: Root,
    children: [
      { index: true, Component: Login },
      {
        path: "dashboard",
        element: (
          <ProtectedRoute>
            <Dashboard />
          </ProtectedRoute>
        ),
      },
      {
        path: "predictions",
        element: (
          <ProtectedRoute>
            <Predictions />
          </ProtectedRoute>
        ),
      },
      {
        path: "profile",
        element: (
          <ProtectedRoute>
            <Profile />
          </ProtectedRoute>
        ),
      },
      {
        path: "statistics",
        element: (
          <ProtectedRoute>
            <Statistics />
          </ProtectedRoute>
        ),
      },
      {
        path: "settings",
        element: (
          <ProtectedRoute>
            <Settings />
          </ProtectedRoute>
        ),
      },
      {
        path: "notifications",
        element: (
          <ProtectedRoute>
            <Notifications />
          </ProtectedRoute>
        ),
      },
    ],
  },
]);
