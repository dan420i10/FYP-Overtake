import { useState, useEffect } from "react";
import { useNavigate } from "react-router";
import { Mail, Lock, AlertCircle, CheckCircle } from "lucide-react";
import { authService } from "../../services/authService";

export default function Login() {
  const [isLogin, setIsLogin] = useState(true);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [emailExists, setEmailExists] = useState<boolean | null>(null);
  const [checkingEmail, setCheckingEmail] = useState(false);
  const navigate = useNavigate();

  // Form states
  const [formData, setFormData] = useState({
    name: "",
    email: "",
    password: "",
    confirmPassword: "",
    age: "",
  });

  // Check if email is already registered during signup
  useEffect(() => {
    if (!isLogin && formData.email) {
      const timer = setTimeout(async () => {
        try {
          setCheckingEmail(true);
          const result = await authService.verifyEmail(formData.email);
          setEmailExists(result.exists);
        } catch (err) {
          console.error("Error checking email:", err);
        } finally {
          setCheckingEmail(false);
        }
      }, 500);

      return () => clearTimeout(timer);
    }
  }, [formData.email, isLogin]);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
    setError(null);
    setSuccess(null);
  };

  const validateForm = (): boolean => {
    if (isLogin) {
      if (!formData.email || !formData.password) {
        setError("Email and password are required");
        return false;
      }
    } else {
      if (!formData.name || !formData.email || !formData.password || !formData.confirmPassword) {
        setError("All fields are required");
        return false;
      }
      if (formData.name.length < 2) {
        setError("Name must be at least 2 characters");
        return false;
      }
      if (formData.password.length < 6) {
        setError("Password must be at least 6 characters");
        return false;
      }
      if (formData.password !== formData.confirmPassword) {
        setError("Passwords do not match");
        return false;
      }
      if (emailExists) {
        setError("Email is already registered");
        return false;
      }
    }
    return true;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateForm()) return;

    setLoading(true);
    setError(null);
    setSuccess(null);

    try {
      if (isLogin) {
        const response = await authService.login({
          email: formData.email,
          password: formData.password,
        });
        
        // Save token and user data
        authService.setToken(response.token);
        authService.setUserData(response.user);
        
        setSuccess("Login successful! Redirecting...");
        setTimeout(() => navigate("/dashboard"), 1000);
      } else {
        const response = await authService.signup({
          name: formData.name,
          email: formData.email,
          password: formData.password,
          age: formData.age ? parseInt(formData.age) : undefined,
        });
        
        // Save token and user data
        authService.setToken(response.token);
        authService.setUserData(response.user);
        
        setSuccess("Account created successfully! Redirecting...");
        setTimeout(() => navigate("/dashboard"), 1000);
      }
    } catch (err: any) {
      setError(err.message || "An error occurred. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const handleTabChange = (tab: boolean) => {
    setIsLogin(tab);
    setError(null);
    setSuccess(null);
    setFormData({
      name: "",
      email: "",
      password: "",
      confirmPassword: "",
      age: "",
    });
    setEmailExists(null);
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
              onClick={() => handleTabChange(true)}
              className={`flex-1 rounded-lg py-2 transition-all ${
                isLogin
                  ? "bg-[#e10600] text-white shadow-lg shadow-[#e10600]/20"
                  : "text-muted-foreground hover:text-white"
              }`}
            >
              Login
            </button>
            <button
              onClick={() => handleTabChange(false)}
              className={`flex-1 rounded-lg py-2 transition-all ${
                !isLogin
                  ? "bg-[#e10600] text-white shadow-lg shadow-[#e10600]/20"
                  : "text-muted-foreground hover:text-white"
              }`}
            >
              Sign Up
            </button>
          </div>

          {/* Error Message */}
          {error && (
            <div className="flex gap-3 rounded-lg bg-red-500/10 border border-red-500/20 p-3 text-sm text-red-400">
              <AlertCircle className="h-5 w-5 flex-shrink-0 mt-0.5" />
              <span>{error}</span>
            </div>
          )}

          {/* Success Message */}
          {success && (
            <div className="flex gap-3 rounded-lg bg-green-500/10 border border-green-500/20 p-3 text-sm text-green-400">
              <CheckCircle className="h-5 w-5 flex-shrink-0 mt-0.5" />
              <span>{success}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Name Field (Sign Up Only) */}
            {!isLogin && (
              <div className="space-y-2">
                <label className="text-sm text-foreground">Full Name</label>
                <input
                  type="text"
                  name="name"
                  placeholder="John Doe"
                  value={formData.name}
                  onChange={handleInputChange}
                  className="w-full rounded-lg border border-border bg-secondary/30 py-3 px-4 text-foreground placeholder:text-muted-foreground focus:border-[#e10600] focus:outline-none focus:ring-2 focus:ring-[#e10600]/20"
                  required={!isLogin}
                />
              </div>
            )}

            {/* Email Field */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <label className="text-sm text-foreground">Email</label>
                {!isLogin && checkingEmail && <span className="text-xs text-muted-foreground">Checking...</span>}
                {!isLogin && emailExists === false && (
                  <span className="text-xs text-green-400">Email available</span>
                )}
                {!isLogin && emailExists === true && (
                  <span className="text-xs text-red-400">Email already registered</span>
                )}
              </div>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 h-5 w-5 -translate-y-1/2 text-muted-foreground" />
                <input
                  type="email"
                  name="email"
                  placeholder="you@example.com"
                  value={formData.email}
                  onChange={handleInputChange}
                  className="w-full rounded-lg border border-border bg-secondary/30 py-3 pl-11 pr-4 text-foreground placeholder:text-muted-foreground focus:border-[#e10600] focus:outline-none focus:ring-2 focus:ring-[#e10600]/20"
                  required
                />
              </div>
            </div>

            {/* Password Field */}
            <div className="space-y-2">
              <label className="text-sm text-foreground">Password</label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 h-5 w-5 -translate-y-1/2 text-muted-foreground" />
                <input
                  type="password"
                  name="password"
                  placeholder="••••••••"
                  value={formData.password}
                  onChange={handleInputChange}
                  className="w-full rounded-lg border border-border bg-secondary/30 py-3 pl-11 pr-4 text-foreground placeholder:text-muted-foreground focus:border-[#e10600] focus:outline-none focus:ring-2 focus:ring-[#e10600]/20"
                  required
                />
              </div>
            </div>

            {/* Confirm Password Field (Sign Up Only) */}
            {!isLogin && (
              <div className="space-y-2">
                <label className="text-sm text-foreground">Confirm Password</label>
                <div className="relative">
                  <Lock className="absolute left-3 top-1/2 h-5 w-5 -translate-y-1/2 text-muted-foreground" />
                  <input
                    type="password"
                    name="confirmPassword"
                    placeholder="••••••••"
                    value={formData.confirmPassword}
                    onChange={handleInputChange}
                    className="w-full rounded-lg border border-border bg-secondary/30 py-3 pl-11 pr-4 text-foreground placeholder:text-muted-foreground focus:border-[#e10600] focus:outline-none focus:ring-2 focus:ring-[#e10600]/20"
                    required={!isLogin}
                  />
                </div>
              </div>
            )}

            {/* Age Field (Sign Up Only) */}
            {!isLogin && (
              <div className="space-y-2">
                <label className="text-sm text-foreground">Age (Optional)</label>
                <input
                  type="number"
                  name="age"
                  placeholder="Enter your age"
                  value={formData.age}
                  onChange={handleInputChange}
                  min="0"
                  max="150"
                  className="w-full rounded-lg border border-border bg-secondary/30 py-3 px-4 text-foreground placeholder:text-muted-foreground focus:border-[#e10600] focus:outline-none focus:ring-2 focus:ring-[#e10600]/20"
                />
              </div>
            )}

            {/* Submit Button */}
            <button
              type="submit"
              disabled={loading || (!isLogin && emailExists === true)}
              className={`w-full rounded-lg bg-gradient-to-r from-[#e10600] to-[#c00500] py-3 font-semibold text-white shadow-xl shadow-[#e10600]/30 transition-all ${
                loading || (!isLogin && emailExists === true)
                  ? "opacity-50 cursor-not-allowed"
                  : "hover:shadow-2xl hover:shadow-[#e10600]/40"
              }`}
            >
              {loading ? (
                <span className="flex items-center justify-center gap-2">
                  <div className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent"></div>
                  {isLogin ? "Logging in..." : "Creating account..."}
                </span>
              ) : (
                isLogin ? "Login" : "Create Account"
              )}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
