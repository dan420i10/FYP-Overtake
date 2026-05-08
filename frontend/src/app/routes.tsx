import { createBrowserRouter } from "react-router";
import Root from "./components/Root";
import Login from "./components/Login";
import Dashboard from "./components/Dashboard";
import Predictions from "./components/Predictions";
import Profile from "./components/Profile";
import Statistics from "./components/Statistics";
import Settings from "./components/Settings";
import Notifications from "./components/Notifications";

export const router = createBrowserRouter([
  {
    path: "/",
    Component: Root,
    children: [
      { index: true, Component: Login },
      { path: "dashboard", Component: Dashboard },
      { path: "predictions", Component: Predictions },
      { path: "profile", Component: Profile },
      { path: "statistics", Component: Statistics },
      { path: "settings", Component: Settings },
      { path: "notifications", Component: Notifications },
    ],
  },
]);
