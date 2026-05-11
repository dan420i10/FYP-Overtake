import { User, Mail, Calendar, Trophy, TrendingUp, Target } from "lucide-react";
import { toast } from "sonner";
import { useEffect, useState } from "react";
import { authService } from "../../services/authService";

interface UserData {
  id: number;
  name: string;
  email: string;
  age?: number;
}

export default function Profile() {
  const [userData, setUserData] = useState<UserData | null>(null);

  useEffect(() => {
    const data = authService.getUserData();
    if (data) {
      setUserData(data);
    }
  }, []);

  const handleEditProfile = () => {
    toast.success("Edit profile feature coming soon!");
  };

  if (!userData) {
    return (
      <div className="min-h-screen bg-background py-8 flex items-center justify-center">
        <div className="text-foreground">Loading profile...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background py-8">
      <div className="container mx-auto px-6">
        <div className="mb-8">
          <h1 className="mb-2 text-4xl font-bold tracking-tight text-foreground">
            My Profile
          </h1>
          <p className="text-muted-foreground">
            Manage your account and view your prediction history
          </p>
        </div>

        <div className="grid gap-6 lg:grid-cols-3">
          <div className="space-y-6 lg:col-span-1">
            <div className="overflow-hidden rounded-2xl border border-border bg-gradient-to-br from-card/80 to-secondary/40 p-6 backdrop-blur-xl">
              <div className="mb-6 flex flex-col items-center">
                <div className="mb-4 flex h-24 w-24 items-center justify-center rounded-full bg-gradient-to-br from-[#e10600] to-[#a00500]">
                  <User className="h-12 w-12 text-white" />
                </div>
                <h2 className="text-2xl font-bold text-foreground">{userData.name}</h2>
                <p className="text-sm text-muted-foreground">@{userData.email.split("@")[0]}</p>
              </div>

              <div className="space-y-3">
                <div className="flex items-center gap-3 rounded-lg bg-secondary/30 p-3">
                  <Mail className="h-5 w-5 text-[#e10600]" />
                  <div>
                    <div className="text-xs text-muted-foreground">Email</div>
                    <div className="text-sm text-foreground break-all">{userData.email}</div>
                  </div>
                </div>
                {userData.age && (
                  <div className="flex items-center gap-3 rounded-lg bg-secondary/30 p-3">
                    <Calendar className="h-5 w-5 text-[#00d4ff]" />
                    <div>
                      <div className="text-xs text-muted-foreground">Age</div>
                      <div className="text-sm text-foreground">{userData.age} years</div>
                    </div>
                  </div>
                )}
                <div className="flex items-center gap-3 rounded-lg bg-secondary/30 p-3">
                  <div className="h-5 w-5 text-[#ffd700] flex items-center justify-center">🆔</div>
                  <div>
                    <div className="text-xs text-muted-foreground">User ID</div>
                    <div className="text-sm text-foreground">#{userData.id}</div>
                  </div>
                </div>
              </div>

              <button
                onClick={handleEditProfile}
                className="mt-6 w-full rounded-lg bg-gradient-to-r from-[#e10600] to-[#c00500] px-6 py-3 font-semibold text-white shadow-xl shadow-[#e10600]/30 transition-all hover:shadow-2xl hover:shadow-[#e10600]/40"
              >
                Edit Profile
              </button>
            </div>
          </div>

          <div className="space-y-6 lg:col-span-2">
            <div className="overflow-hidden rounded-2xl border border-border bg-gradient-to-br from-card/80 to-secondary/40 p-6 backdrop-blur-xl">
              <h3 className="mb-6 text-xl font-semibold text-foreground">Account Statistics</h3>
              <div className="grid gap-4 md:grid-cols-3">
                <div className="rounded-xl border border-[#e10600]/20 bg-gradient-to-br from-[#e10600]/10 to-transparent p-4">
                  <div className="mb-2 flex items-center gap-2">
                    <Trophy className="h-5 w-5 text-[#ffd700]" />
                    <span className="text-sm text-muted-foreground">Total Points</span>
                  </div>
                  <div className="text-3xl font-bold text-foreground">1,247</div>
                  <div className="text-xs text-[#00ff88]">From AI predictions</div>
                </div>

                <div className="rounded-xl border border-[#00d4ff]/20 bg-gradient-to-br from-[#00d4ff]/10 to-transparent p-4">
                  <div className="mb-2 flex items-center gap-2">
                    <TrendingUp className="h-5 w-5 text-[#00d4ff]" />
                    <span className="text-sm text-muted-foreground">Model Accuracy</span>
                  </div>
                  <div className="text-3xl font-bold text-foreground">78%</div>
                  <div className="text-xs text-[#00ff88]">+5% from last month</div>
                </div>

                <div className="rounded-xl border border-[#00ff88]/20 bg-gradient-to-br from-[#00ff88]/10 to-transparent p-4">
                  <div className="mb-2 flex items-center gap-2">
                    <Target className="h-5 w-5 text-[#00ff88]" />
                    <span className="text-sm text-muted-foreground">Predictions Run</span>
                  </div>
                  <div className="text-3xl font-bold text-foreground">24</div>
                  <div className="text-xs text-muted-foreground">6 races analyzed</div>
                </div>
              </div>
            </div>

            <div className="overflow-hidden rounded-2xl border border-border bg-gradient-to-br from-card/80 to-secondary/40 p-6 backdrop-blur-xl">
              <h3 className="mb-6 text-xl font-semibold text-foreground">Recent Activity</h3>
              <div className="space-y-3">
                {[
                  { race: "China GP", result: "Correct", points: "+68", date: "Apr 20, 2026" },
                  { race: "Japan GP", result: "Correct", points: "+71", date: "Apr 13, 2026" },
                  { race: "Australia GP", result: "Partial", points: "+42", date: "Apr 6, 2026" },
                  { race: "Saudi GP", result: "Correct", points: "+62", date: "Mar 30, 2026" },
                ].map((activity, index) => (
                  <div
                    key={index}
                    className="flex items-center justify-between rounded-lg border border-border bg-secondary/30 p-4 transition-all hover:bg-secondary/50"
                  >
                    <div>
                      <div className="font-semibold text-foreground">{activity.race}</div>
                      <div className="text-sm text-muted-foreground">{activity.date}</div>
                    </div>
                    <div className="text-right">
                      <div
                        className={`text-sm font-semibold ${
                          activity.result === "Correct" ? "text-[#00ff88]" : "text-[#ffd700]"
                        }`}
                      >
                        {activity.result}
                      </div>
                      <div className="text-sm text-foreground">{activity.points}</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
