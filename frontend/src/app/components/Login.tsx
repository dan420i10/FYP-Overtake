import { useState } from "react";
import { useNavigate } from "react-router";
import { Mail, Lock, Chrome } from "lucide-react";

export default function Login() {
  const [isLogin, setIsLogin] = useState(true);
  const navigate = useNavigate();

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    navigate("/dashboard");
  };

  return (
    <div className="flex min-h-screen">
      <div className="relative hidden w-1/2 overflow-hidden lg:block">
        <div className="absolute inset-0 bg-gradient-to-br from-black/80 via-black/60 to-transparent z-10"></div>
        <img
          src="https://images.unsplash.com/photo-1568605117036-5fe5e7bab0b7?q=80&w=2070"
          alt="F1 Racing"
          className="h-full w-full object-cover"
        />
        <div className="absolute inset-0 z-20 flex flex-col items-start justify-end p-12">
          <div className="space-y-2">
            <h1 className="bg-gradient-to-r from-white to-gray-300 bg-clip-text text-5xl font-bold tracking-tight text-transparent">
              Predict. Compete. Win.
            </h1>
            <p className="text-xl text-gray-300">
              The ultimate F1 fantasy prediction platform
            </p>
          </div>
          <div className="mt-8 flex gap-4">
            <div className="h-1 w-20 rounded-full bg-[#e10600]"></div>
            <div className="h-1 w-12 rounded-full bg-white/30"></div>
            <div className="h-1 w-8 rounded-full bg-white/20"></div>
          </div>
        </div>
      </div>

      <div className="flex w-full items-center justify-center bg-background lg:w-1/2">
        <div className="w-full max-w-md space-y-8 px-8">
          <div className="text-center">
            <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-2xl bg-gradient-to-br from-[#e10600] to-[#a00500] shadow-2xl shadow-[#e10600]/30">
              <div className="text-3xl">🏎️</div>
            </div>
            <h2 className="text-3xl font-bold tracking-tight text-foreground">
              OverTake
            </h2>
            <p className="mt-2 text-muted-foreground">
              AI-Powered F1 Race Predictions
            </p>
          </div>

          <div className="flex gap-2 rounded-xl bg-secondary/50 p-1">
            <button
              onClick={() => setIsLogin(true)}
              className={`flex-1 rounded-lg py-2 transition-all ${
                isLogin
                  ? "bg-[#e10600] text-white shadow-lg shadow-[#e10600]/20"
                  : "text-muted-foreground hover:text-white"
              }`}
            >
              Login
            </button>
            <button
              onClick={() => setIsLogin(false)}
              className={`flex-1 rounded-lg py-2 transition-all ${
                !isLogin
                  ? "bg-[#e10600] text-white shadow-lg shadow-[#e10600]/20"
                  : "text-muted-foreground hover:text-white"
              }`}
            >
              Sign Up
            </button>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <label className="text-sm text-foreground">Email</label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 h-5 w-5 -translate-y-1/2 text-muted-foreground" />
                <input
                  type="email"
                  placeholder="you@example.com"
                  className="w-full rounded-lg border border-border bg-secondary/30 py-3 pl-11 pr-4 text-foreground placeholder:text-muted-foreground focus:border-[#e10600] focus:outline-none focus:ring-2 focus:ring-[#e10600]/20"
                  required
                />
              </div>
            </div>

            <div className="space-y-2">
              <label className="text-sm text-foreground">Password</label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 h-5 w-5 -translate-y-1/2 text-muted-foreground" />
                <input
                  type="password"
                  placeholder="••••••••"
                  className="w-full rounded-lg border border-border bg-secondary/30 py-3 pl-11 pr-4 text-foreground placeholder:text-muted-foreground focus:border-[#e10600] focus:outline-none focus:ring-2 focus:ring-[#e10600]/20"
                  required
                />
              </div>
            </div>

            {!isLogin && (
              <div className="space-y-2">
                <label className="text-sm text-foreground">Confirm Password</label>
                <div className="relative">
                  <Lock className="absolute left-3 top-1/2 h-5 w-5 -translate-y-1/2 text-muted-foreground" />
                  <input
                    type="password"
                    placeholder="••••••••"
                    className="w-full rounded-lg border border-border bg-secondary/30 py-3 pl-11 pr-4 text-foreground placeholder:text-muted-foreground focus:border-[#e10600] focus:outline-none focus:ring-2 focus:ring-[#e10600]/20"
                    required
                  />
                </div>
              </div>
            )}

            {isLogin && (
              <div className="text-right">
                <button type="button" className="text-sm text-[#e10600] hover:underline">
                  Forgot password?
                </button>
              </div>
            )}

            <button
              type="submit"
              className="w-full rounded-lg bg-gradient-to-r from-[#e10600] to-[#c00500] py-3 font-semibold text-white shadow-xl shadow-[#e10600]/30 transition-all hover:shadow-2xl hover:shadow-[#e10600]/40"
            >
              {isLogin ? "Login" : "Create Account"}
            </button>

            <div className="relative">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-border"></div>
              </div>
              <div className="relative flex justify-center text-sm">
                <span className="bg-background px-2 text-muted-foreground">Or continue with</span>
              </div>
            </div>

            <button
              type="button"
              className="flex w-full items-center justify-center gap-3 rounded-lg border border-border bg-secondary/30 py-3 text-foreground transition-all hover:bg-secondary/50"
            >
              <Chrome className="h-5 w-5" />
              <span>Continue with Google</span>
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
