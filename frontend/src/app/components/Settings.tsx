import { Settings as SettingsIcon, Bell, Moon, Globe, Lock, Database } from "lucide-react";
import * as Switch from "@radix-ui/react-switch";
import { useTheme } from "next-themes";
import { toast } from "sonner";
import { useNavigate } from "react-router";

export default function Settings() {
  const { theme, setTheme } = useTheme();
  const navigate = useNavigate();

  const handleDarkModeToggle = (checked: boolean) => {
    setTheme(checked ? "dark" : "light");
    toast.success(`${checked ? "Dark" : "Light"} mode enabled`);
  };

  const handleChangePassword = () => {
    toast.info("Password change form will open here");
  };

  const handleTwoFactor = () => {
    toast.info("Two-factor authentication setup coming soon");
  };

  const handleDownloadData = () => {
    toast.success("Preparing your data export... This may take a few minutes.");
  };

  const handleDeleteAccount = () => {
    toast.error("Account deletion requires confirmation. Contact support for assistance.");
  };

  const handleSaveChanges = () => {
    toast.success("Settings saved successfully!");
  };

  const handleCancel = () => {
    navigate("/dashboard");
  };

  const handleLanguageChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    toast.success(`Language changed to ${e.target.value}`);
  };

  const handleTimezoneChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    toast.success(`Timezone changed to ${e.target.value}`);
  };

  return (
    <div className="min-h-screen bg-background py-8">
      <div className="container mx-auto max-w-4xl px-6">
        <div className="mb-8">
          <h1 className="mb-2 text-4xl font-bold tracking-tight text-foreground">
            Settings
          </h1>
          <p className="text-muted-foreground">
            Manage your account preferences and application settings
          </p>
        </div>

        <div className="space-y-6">
          <div className="overflow-hidden rounded-2xl border border-border bg-gradient-to-br from-card/80 to-secondary/40 p-6 backdrop-blur-xl">
            <div className="mb-4 flex items-center gap-2">
              <Moon className="h-5 w-5 text-[#e10600]" />
              <h3 className="text-lg font-semibold text-foreground">Appearance</h3>
            </div>
            <div className="space-y-4">
              <div className="flex items-center justify-between rounded-lg border border-border bg-secondary/30 p-4">
                <div>
                  <div className="font-semibold text-foreground">Dark Mode</div>
                  <div className="text-sm text-muted-foreground">
                    Toggle between light and dark theme
                  </div>
                </div>
                <Switch.Root
                  checked={theme === "dark"}
                  onCheckedChange={handleDarkModeToggle}
                  className="relative h-6 w-11 rounded-full bg-secondary outline-none data-[state=checked]:bg-[#e10600]"
                >
                  <Switch.Thumb className="block h-5 w-5 translate-x-0.5 rounded-full bg-white transition-transform duration-100 will-change-transform data-[state=checked]:translate-x-[22px]" />
                </Switch.Root>
              </div>
            </div>
          </div>

          <div className="overflow-hidden rounded-2xl border border-border bg-gradient-to-br from-card/80 to-secondary/40 p-6 backdrop-blur-xl">
            <div className="mb-4 flex items-center gap-2">
              <Bell className="h-5 w-5 text-[#e10600]" />
              <h3 className="text-lg font-semibold text-foreground">Notifications</h3>
            </div>
            <div className="space-y-4">
              <div className="flex items-center justify-between rounded-lg border border-border bg-secondary/30 p-4">
                <div>
                  <div className="font-semibold text-foreground">Race Reminders</div>
                  <div className="text-sm text-muted-foreground">
                    Get notified before races start
                  </div>
                </div>
                <Switch.Root
                  defaultChecked
                  onCheckedChange={(checked) =>
                    toast.success(
                      checked ? "Race reminders enabled" : "Race reminders disabled"
                    )
                  }
                  className="relative h-6 w-11 rounded-full bg-secondary outline-none data-[state=checked]:bg-[#e10600]"
                >
                  <Switch.Thumb className="block h-5 w-5 translate-x-0.5 rounded-full bg-white transition-transform duration-100 will-change-transform data-[state=checked]:translate-x-[22px]" />
                </Switch.Root>
              </div>

              <div className="flex items-center justify-between rounded-lg border border-border bg-secondary/30 p-4">
                <div>
                  <div className="font-semibold text-foreground">Prediction Results</div>
                  <div className="text-sm text-muted-foreground">
                    Notify when your predictions are scored
                  </div>
                </div>
                <Switch.Root
                  defaultChecked
                  onCheckedChange={(checked) =>
                    toast.success(
                      checked
                        ? "Prediction result notifications enabled"
                        : "Prediction result notifications disabled"
                    )
                  }
                  className="relative h-6 w-11 rounded-full bg-secondary outline-none data-[state=checked]:bg-[#e10600]"
                >
                  <Switch.Thumb className="block h-5 w-5 translate-x-0.5 rounded-full bg-white transition-transform duration-100 will-change-transform data-[state=checked]:translate-x-[22px]" />
                </Switch.Root>
              </div>

              <div className="flex items-center justify-between rounded-lg border border-border bg-secondary/30 p-4">
                <div>
                  <div className="font-semibold text-foreground">Email Notifications</div>
                  <div className="text-sm text-muted-foreground">
                    Receive updates via email
                  </div>
                </div>
                <Switch.Root
                  onCheckedChange={(checked) =>
                    toast.success(
                      checked ? "Email notifications enabled" : "Email notifications disabled"
                    )
                  }
                  className="relative h-6 w-11 rounded-full bg-secondary outline-none data-[state=checked]:bg-[#e10600]"
                >
                  <Switch.Thumb className="block h-5 w-5 translate-x-0.5 rounded-full bg-white transition-transform duration-100 will-change-transform data-[state=checked]:translate-x-[22px]" />
                </Switch.Root>
              </div>
            </div>
          </div>

          <div className="overflow-hidden rounded-2xl border border-border bg-gradient-to-br from-card/80 to-secondary/40 p-6 backdrop-blur-xl">
            <div className="mb-4 flex items-center gap-2">
              <Globe className="h-5 w-5 text-[#e10600]" />
              <h3 className="text-lg font-semibold text-foreground">Preferences</h3>
            </div>
            <div className="space-y-4">
              <div className="rounded-lg border border-border bg-secondary/30 p-4">
                <div className="mb-2 font-semibold text-foreground">Language</div>
                <select
                  onChange={handleLanguageChange}
                  className="w-full rounded-lg border border-border bg-secondary/50 px-4 py-2 text-foreground outline-none focus:border-[#e10600] focus:ring-2 focus:ring-[#e10600]/20"
                >
                  <option>English (US)</option>
                  <option>English (UK)</option>
                  <option>Spanish</option>
                  <option>French</option>
                  <option>German</option>
                </select>
              </div>

              <div className="rounded-lg border border-border bg-secondary/30 p-4">
                <div className="mb-2 font-semibold text-foreground">Time Zone</div>
                <select
                  onChange={handleTimezoneChange}
                  className="w-full rounded-lg border border-border bg-secondary/50 px-4 py-2 text-foreground outline-none focus:border-[#e10600] focus:ring-2 focus:ring-[#e10600]/20"
                >
                  <option>UTC (GMT +0)</option>
                  <option>EST (GMT -5)</option>
                  <option>PST (GMT -8)</option>
                  <option>CET (GMT +1)</option>
                  <option>JST (GMT +9)</option>
                </select>
              </div>
            </div>
          </div>

          <div className="overflow-hidden rounded-2xl border border-border bg-gradient-to-br from-card/80 to-secondary/40 p-6 backdrop-blur-xl">
            <div className="mb-4 flex items-center gap-2">
              <Lock className="h-5 w-5 text-[#e10600]" />
              <h3 className="text-lg font-semibold text-foreground">Security</h3>
            </div>
            <div className="space-y-3">
              <button
                onClick={handleChangePassword}
                className="w-full rounded-lg border border-border bg-secondary/30 px-4 py-3 text-left text-foreground transition-all hover:bg-secondary/50"
              >
                <div className="font-semibold">Change Password</div>
                <div className="text-sm text-muted-foreground">Update your password</div>
              </button>
              <button
                onClick={handleTwoFactor}
                className="w-full rounded-lg border border-border bg-secondary/30 px-4 py-3 text-left text-foreground transition-all hover:bg-secondary/50"
              >
                <div className="font-semibold">Two-Factor Authentication</div>
                <div className="text-sm text-muted-foreground">Add extra security to your account</div>
              </button>
            </div>
          </div>

          <div className="overflow-hidden rounded-2xl border border-border bg-gradient-to-br from-card/80 to-secondary/40 p-6 backdrop-blur-xl">
            <div className="mb-4 flex items-center gap-2">
              <Database className="h-5 w-5 text-[#e10600]" />
              <h3 className="text-lg font-semibold text-foreground">Data & Privacy</h3>
            </div>
            <div className="space-y-3">
              <button
                onClick={handleDownloadData}
                className="w-full rounded-lg border border-border bg-secondary/30 px-4 py-3 text-left text-foreground transition-all hover:bg-secondary/50"
              >
                <div className="font-semibold">Download My Data</div>
                <div className="text-sm text-muted-foreground">Export your prediction history</div>
              </button>
              <button
                onClick={handleDeleteAccount}
                className="w-full rounded-lg border border-[#ef4444]/20 bg-[#ef4444]/10 px-4 py-3 text-left text-[#ef4444] transition-all hover:bg-[#ef4444]/20"
              >
                <div className="font-semibold">Delete Account</div>
                <div className="text-sm opacity-80">Permanently delete your account and data</div>
              </button>
            </div>
          </div>

          <div className="flex justify-end gap-4">
            <button
              onClick={handleCancel}
              className="rounded-lg border border-border bg-secondary px-6 py-3 text-foreground transition-all hover:bg-secondary/80"
            >
              Cancel
            </button>
            <button
              onClick={handleSaveChanges}
              className="rounded-lg bg-gradient-to-r from-[#e10600] to-[#c00500] px-6 py-3 font-semibold text-white shadow-xl shadow-[#e10600]/30 transition-all hover:shadow-2xl hover:shadow-[#e10600]/40"
            >
              Save Changes
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
