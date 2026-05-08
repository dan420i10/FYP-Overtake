import { Link, useLocation, useNavigate } from "react-router";
import { Bell, User, Flag, Sun, Moon, Settings, LogOut, Trophy, BarChart3, Clock } from "lucide-react";
import { useTheme } from "next-themes";
import * as Popover from "@radix-ui/react-popover";
import * as DropdownMenu from "@radix-ui/react-dropdown-menu";

const notifications = [
  {
    id: 1,
    title: "Miami GP Ready for Prediction",
    description: "AI model ready to generate predictions for the upcoming race",
    time: "2 hours ago",
    unread: true,
    type: "info",
  },
  {
    id: 2,
    title: "AI Prediction Was Correct!",
    description: "The model accurately predicted China GP - 68 points earned",
    time: "1 day ago",
    unread: true,
    type: "success",
  },
  {
    id: 3,
    title: "New Season Starting Soon",
    description: "2026 F1 season begins in 3 days",
    time: "2 days ago",
    unread: false,
    type: "info",
  },
];

export default function Navbar() {
  const location = useLocation();
  const navigate = useNavigate();
  const { theme, setTheme } = useTheme();

  const isActive = (path: string) => location.pathname === path;

  const handleLogout = () => {
    navigate("/");
  };

  return (
    <nav className="sticky top-0 z-50 border-b border-border bg-card/80 backdrop-blur-xl">
      <div className="container mx-auto px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-8">
            <Link to="/dashboard" className="flex items-center gap-2">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-gradient-to-br from-[#e10600] to-[#a00500]">
                <Flag className="h-6 w-6 text-white" />
              </div>
              <span className="bg-gradient-to-r from-foreground to-muted-foreground bg-clip-text text-xl font-bold tracking-tight text-transparent">
                OverTake
              </span>
            </Link>

            <div className="flex gap-1">
              <Link
                to="/dashboard"
                className={`rounded-lg px-4 py-2 transition-all ${
                  isActive("/dashboard")
                    ? "bg-[#e10600] text-white shadow-lg shadow-[#e10600]/20"
                    : "text-muted-foreground hover:text-foreground"
                }`}
              >
                Dashboard
              </Link>
              <Link
                to="/predictions"
                className={`rounded-lg px-4 py-2 transition-all ${
                  isActive("/predictions")
                    ? "bg-[#e10600] text-white shadow-lg shadow-[#e10600]/20"
                    : "text-muted-foreground hover:text-foreground"
                }`}
              >
                Predictions
              </Link>
              <Link
                to="/statistics"
                className={`rounded-lg px-4 py-2 transition-all ${
                  isActive("/statistics")
                    ? "bg-[#e10600] text-white shadow-lg shadow-[#e10600]/20"
                    : "text-muted-foreground hover:text-foreground"
                }`}
              >
                Statistics
              </Link>
            </div>
          </div>

          <div className="flex items-center gap-4">
            <button
              onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
              className="rounded-lg p-2 text-muted-foreground transition-colors hover:bg-secondary hover:text-foreground"
              title={`Switch to ${theme === "dark" ? "light" : "dark"} mode`}
            >
              {theme === "dark" ? (
                <Sun className="h-5 w-5" />
              ) : (
                <Moon className="h-5 w-5" />
              )}
            </button>

            <Popover.Root>
              <Popover.Trigger asChild>
                <button className="relative rounded-lg p-2 text-muted-foreground transition-colors hover:bg-secondary hover:text-foreground">
                  <Bell className="h-5 w-5" />
                  <span className="absolute right-1 top-1 h-2 w-2 rounded-full bg-[#e10600]"></span>
                </button>
              </Popover.Trigger>
              <Popover.Portal>
                <Popover.Content
                  className="z-50 w-80 rounded-xl border border-border bg-card p-4 shadow-2xl outline-none data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0 data-[state=closed]:zoom-out-95 data-[state=open]:zoom-in-95"
                  sideOffset={5}
                  align="end"
                >
                  <div className="mb-4 flex items-center justify-between">
                    <h3 className="font-semibold text-foreground">Notifications</h3>
                    <span className="rounded-full bg-[#e10600] px-2 py-0.5 text-xs text-white">
                      {notifications.filter((n) => n.unread).length}
                    </span>
                  </div>
                  <div className="space-y-3">
                    {notifications.map((notification) => (
                      <button
                        key={notification.id}
                        onClick={() => navigate("/notifications")}
                        className={`w-full rounded-lg border p-3 text-left transition-all hover:bg-secondary/50 ${
                          notification.unread
                            ? "border-[#e10600]/20 bg-[#e10600]/5"
                            : "border-border"
                        }`}
                      >
                        <div className="mb-1 flex items-start justify-between gap-2">
                          <h4 className="text-sm font-semibold text-foreground">
                            {notification.title}
                          </h4>
                          {notification.unread && (
                            <div className="h-2 w-2 rounded-full bg-[#e10600]"></div>
                          )}
                        </div>
                        <p className="text-xs text-muted-foreground">
                          {notification.description}
                        </p>
                        <div className="mt-2 flex items-center gap-1 text-xs text-muted-foreground">
                          <Clock className="h-3 w-3" />
                          <span>{notification.time}</span>
                        </div>
                      </button>
                    ))}
                  </div>
                  <button
                    onClick={() => navigate("/notifications")}
                    className="mt-4 w-full rounded-lg bg-secondary py-2 text-sm text-foreground transition-colors hover:bg-secondary/80"
                  >
                    View All Notifications
                  </button>
                </Popover.Content>
              </Popover.Portal>
            </Popover.Root>

            <DropdownMenu.Root>
              <DropdownMenu.Trigger asChild>
                <button className="flex items-center gap-2 rounded-lg bg-secondary px-4 py-2 text-foreground transition-colors hover:bg-secondary/80">
                  <User className="h-5 w-5" />
                  <span>Profile</span>
                </button>
              </DropdownMenu.Trigger>
              <DropdownMenu.Portal>
                <DropdownMenu.Content
                  className="z-50 min-w-[220px] rounded-xl border border-border bg-card p-2 shadow-2xl outline-none data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0 data-[state=closed]:zoom-out-95 data-[state=open]:zoom-in-95"
                  sideOffset={5}
                  align="end"
                >
                  <div className="border-b border-border px-3 py-3">
                    <p className="font-semibold text-foreground">John Racer</p>
                    <p className="text-sm text-muted-foreground">john@f1predictor.com</p>
                  </div>

                  <DropdownMenu.Item
                    onClick={() => navigate("/profile")}
                    className="mt-2 flex cursor-pointer items-center gap-3 rounded-lg px-3 py-2 text-sm text-foreground outline-none transition-colors hover:bg-secondary focus:bg-secondary"
                  >
                    <User className="h-4 w-4" />
                    <span>My Profile</span>
                  </DropdownMenu.Item>

                  <DropdownMenu.Item
                    onClick={() => navigate("/statistics")}
                    className="flex cursor-pointer items-center gap-3 rounded-lg px-3 py-2 text-sm text-foreground outline-none transition-colors hover:bg-secondary focus:bg-secondary"
                  >
                    <Trophy className="h-4 w-4" />
                    <span>Prediction History</span>
                  </DropdownMenu.Item>

                  <DropdownMenu.Item
                    onClick={() => navigate("/statistics")}
                    className="flex cursor-pointer items-center gap-3 rounded-lg px-3 py-2 text-sm text-foreground outline-none transition-colors hover:bg-secondary focus:bg-secondary"
                  >
                    <BarChart3 className="h-4 w-4" />
                    <span>Statistics</span>
                  </DropdownMenu.Item>

                  <DropdownMenu.Item
                    onClick={() => navigate("/settings")}
                    className="flex cursor-pointer items-center gap-3 rounded-lg px-3 py-2 text-sm text-foreground outline-none transition-colors hover:bg-secondary focus:bg-secondary"
                  >
                    <Settings className="h-4 w-4" />
                    <span>Settings</span>
                  </DropdownMenu.Item>

                  <DropdownMenu.Separator className="my-2 h-px bg-border" />

                  <DropdownMenu.Item
                    onClick={handleLogout}
                    className="flex cursor-pointer items-center gap-3 rounded-lg px-3 py-2 text-sm text-[#e10600] outline-none transition-colors hover:bg-[#e10600]/10 focus:bg-[#e10600]/10"
                  >
                    <LogOut className="h-4 w-4" />
                    <span>Logout</span>
                  </DropdownMenu.Item>
                </DropdownMenu.Content>
              </DropdownMenu.Portal>
            </DropdownMenu.Root>
          </div>
        </div>
      </div>
    </nav>
  );
}
