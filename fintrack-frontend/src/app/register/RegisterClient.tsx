"use client";

import { useState, FormEvent } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { signUp } from "@/lib/auth";
import {
  UserIcon,
  EnvelopeIcon,
  LockClosedIcon,
  EyeIcon,
  EyeSlashIcon,
  CheckCircleIcon,
  ExclamationCircleIcon,
  UserPlusIcon,
} from "@heroicons/react/24/outline";

export default function RegisterPage() {
  const [formData, setFormData] = useState({
    username: "",
    email: "",
    password: "",
    confirmPassword: "",
    full_name: "",
  });
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [focusedField, setFocusedField] = useState<string | null>(null);
  const [passwordStrength, setPasswordStrength] = useState(0);
  const router = useRouter();

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData({
      ...formData,
      [name]: value,
    });

    // Calculate password strength
    if (name === "password") {
      calculatePasswordStrength(value);
    }
  };

  const calculatePasswordStrength = (password: string) => {
    let strength = 0;
    if (password.length >= 8) strength += 1;
    if (/[A-Z]/.test(password)) strength += 1;
    if (/[a-z]/.test(password)) strength += 1;
    if (/[0-9]/.test(password)) strength += 1;
    if (/[^A-Za-z0-9]/.test(password)) strength += 1;
    setPasswordStrength(strength);
  };

  const getPasswordStrengthColor = () => {
    if (passwordStrength <= 2) return "bg-red-500";
    if (passwordStrength <= 3) return "bg-yellow-500";
    if (passwordStrength <= 4) return "bg-blue-500";
    return "bg-green-500";
  };

  const getPasswordStrengthText = () => {
    if (passwordStrength <= 2) return "Weak";
    if (passwordStrength <= 3) return "Fair";
    if (passwordStrength <= 4) return "Good";
    return "Strong";
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError("");

    // Validation
    if (formData.password !== formData.confirmPassword) {
      setError("Passwords do not match");
      return;
    }

    if (formData.password.length < 6) {
      setError("Password must be at least 6 characters long");
      return;
    }

    if (passwordStrength < 3) {
      setError("Please choose a stronger password");
      return;
    }

    if (!formData.email.includes("@")) {
      setError("Please enter a valid email address");
      return;
    }

    setIsLoading(true);

    try {
      const response = await signUp({
        email: formData.email,
        password: formData.password,
        username: formData.username,
        full_name: formData.full_name,
      });

      if (response.error) {
        setError(response.error);
      } else {
        // Registration successful, redirect to login
        router.push("/login?registered=true");
      }
    } catch (err) {
      setError("Registration failed. Please try again.");
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-900 via-blue-900 to-slate-900 p-4">
      <div className="max-w-md w-full space-y-8">
        {/* Header Card */}
        <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-8 shadow-2xl border border-white/20">
          <div className="text-center">
            <div className="mx-auto h-16 w-16 bg-gradient-to-r from-green-500 to-emerald-600 rounded-full flex items-center justify-center shadow-lg">
              <UserPlusIcon className="h-8 w-8 text-white" />
            </div>
            <h2 className="mt-6 text-3xl font-bold text-white">
              Create Account
            </h2>
            <p className="mt-2 text-sm text-slate-300">
              Join FinTrack and start managing your finances
            </p>
          </div>

          <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
            {/* Error Message */}
            {error && (
              <div className="bg-red-500/20 border border-red-500/30 text-red-300 px-4 py-3 rounded-lg flex items-center space-x-2">
                <ExclamationCircleIcon className="h-5 w-5 flex-shrink-0" />
                <span className="text-sm">{error}</span>
              </div>
            )}

            <div className="space-y-4">
              {/* Full Name Field */}
              <div className="relative">
                <label htmlFor="full_name" className="sr-only">
                  Full Name
                </label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                    <UserIcon
                      className={`h-5 w-5 transition-colors duration-200 ${
                        focusedField === "full_name"
                          ? "text-green-400"
                          : "text-slate-400"
                      }`}
                    />
                  </div>
                  <input
                    id="full_name"
                    name="full_name"
                    type="text"
                    autoComplete="name"
                    required
                    className="appearance-none relative block w-full pl-10 pr-3 py-3 border border-slate-600 placeholder-slate-400 text-white bg-slate-800/50 backdrop-blur-sm rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent transition-all duration-200"
                    placeholder="Full Name"
                    value={formData.full_name}
                    onChange={handleChange}
                    onFocus={() => setFocusedField("full_name")}
                    onBlur={() => setFocusedField(null)}
                  />
                </div>
              </div>

              {/* Username Field */}
              <div className="relative">
                <label htmlFor="username" className="sr-only">
                  Username
                </label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                    <UserIcon
                      className={`h-5 w-5 transition-colors duration-200 ${
                        focusedField === "username"
                          ? "text-green-400"
                          : "text-slate-400"
                      }`}
                    />
                  </div>
                  <input
                    id="username"
                    name="username"
                    type="text"
                    autoComplete="username"
                    required
                    className="appearance-none relative block w-full pl-10 pr-3 py-3 border border-slate-600 placeholder-slate-400 text-white bg-slate-800/50 backdrop-blur-sm rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent transition-all duration-200"
                    placeholder="Username"
                    value={formData.username}
                    onChange={handleChange}
                    onFocus={() => setFocusedField("username")}
                    onBlur={() => setFocusedField(null)}
                  />
                </div>
              </div>

              {/* Email Field */}
              <div className="relative">
                <label htmlFor="email" className="sr-only">
                  Email address
                </label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                    <EnvelopeIcon
                      className={`h-5 w-5 transition-colors duration-200 ${
                        focusedField === "email"
                          ? "text-green-400"
                          : "text-slate-400"
                      }`}
                    />
                  </div>
                  <input
                    id="email"
                    name="email"
                    type="email"
                    autoComplete="email"
                    required
                    className="appearance-none relative block w-full pl-10 pr-3 py-3 border border-slate-600 placeholder-slate-400 text-white bg-slate-800/50 backdrop-blur-sm rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent transition-all duration-200"
                    placeholder="Email address"
                    value={formData.email}
                    onChange={handleChange}
                    onFocus={() => setFocusedField("email")}
                    onBlur={() => setFocusedField(null)}
                  />
                </div>
              </div>

              {/* Password Field */}
              <div className="relative">
                <label htmlFor="password" className="sr-only">
                  Password
                </label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                    <LockClosedIcon
                      className={`h-5 w-5 transition-colors duration-200 ${
                        focusedField === "password"
                          ? "text-green-400"
                          : "text-slate-400"
                      }`}
                    />
                  </div>
                  <input
                    id="password"
                    name="password"
                    type={showPassword ? "text" : "password"}
                    autoComplete="new-password"
                    required
                    className="appearance-none relative block w-full pl-10 pr-12 py-3 border border-slate-600 placeholder-slate-400 text-white bg-slate-800/50 backdrop-blur-sm rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent transition-all duration-200"
                    placeholder="Password (min 6 characters)"
                    value={formData.password}
                    onChange={handleChange}
                    onFocus={() => setFocusedField("password")}
                    onBlur={() => setFocusedField(null)}
                  />
                  <button
                    type="button"
                    className="absolute inset-y-0 right-0 pr-3 flex items-center"
                    onClick={() => setShowPassword(!showPassword)}
                  >
                    {showPassword ? (
                      <EyeSlashIcon className="h-5 w-5 text-slate-400 hover:text-slate-300 transition-colors duration-200" />
                    ) : (
                      <EyeIcon className="h-5 w-5 text-slate-400 hover:text-slate-300 transition-colors duration-200" />
                    )}
                  </button>
                </div>

                {/* Password Strength Indicator */}
                {formData.password && (
                  <div className="mt-2">
                    <div className="flex items-center justify-between text-xs text-slate-400 mb-1">
                      <span>Password strength:</span>
                      <span
                        className={`font-medium ${
                          passwordStrength <= 2
                            ? "text-red-400"
                            : passwordStrength <= 3
                            ? "text-yellow-400"
                            : passwordStrength <= 4
                            ? "text-blue-400"
                            : "text-green-400"
                        }`}
                      >
                        {getPasswordStrengthText()}
                      </span>
                    </div>
                    <div className="w-full bg-slate-700 rounded-full h-2">
                      <div
                        className={`h-2 rounded-full transition-all duration-300 ${getPasswordStrengthColor()}`}
                        style={{ width: `${(passwordStrength / 5) * 100}%` }}
                      ></div>
                    </div>
                  </div>
                )}
              </div>

              {/* Confirm Password Field */}
              <div className="relative">
                <label htmlFor="confirmPassword" className="sr-only">
                  Confirm Password
                </label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                    <LockClosedIcon
                      className={`h-5 w-5 transition-colors duration-200 ${
                        focusedField === "confirmPassword"
                          ? "text-green-400"
                          : "text-slate-400"
                      }`}
                    />
                  </div>
                  <input
                    id="confirmPassword"
                    name="confirmPassword"
                    type={showConfirmPassword ? "text" : "password"}
                    autoComplete="new-password"
                    required
                    className="appearance-none relative block w-full pl-10 pr-12 py-3 border border-slate-600 placeholder-slate-400 text-white bg-slate-800/50 backdrop-blur-sm rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent transition-all duration-200"
                    placeholder="Confirm Password"
                    value={formData.confirmPassword}
                    onChange={handleChange}
                    onFocus={() => setFocusedField("confirmPassword")}
                    onBlur={() => setFocusedField(null)}
                  />
                  <button
                    type="button"
                    className="absolute inset-y-0 right-0 pr-3 flex items-center"
                    onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                  >
                    {showConfirmPassword ? (
                      <EyeSlashIcon className="h-5 w-5 text-slate-400 hover:text-slate-300 transition-colors duration-200" />
                    ) : (
                      <EyeIcon className="h-5 w-5 text-slate-400 hover:text-slate-300 transition-colors duration-200" />
                    )}
                  </button>
                </div>

                {/* Password Match Indicator */}
                {formData.confirmPassword && (
                  <div className="mt-2 flex items-center space-x-2">
                    {formData.password === formData.confirmPassword ? (
                      <>
                        <CheckCircleIcon className="h-4 w-4 text-green-400" />
                        <span className="text-xs text-green-400">
                          Passwords match
                        </span>
                      </>
                    ) : (
                      <>
                        <ExclamationCircleIcon className="h-4 w-4 text-red-400" />
                        <span className="text-xs text-red-400">
                          Passwords do not match
                        </span>
                      </>
                    )}
                  </div>
                )}
              </div>
            </div>

            {/* Submit Button */}
            <div>
              <button
                type="submit"
                disabled={isLoading}
                className="group relative w-full flex justify-center py-3 px-4 border border-transparent text-sm font-semibold rounded-lg text-white bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-700 hover:to-emerald-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 transform hover:scale-105 shadow-lg"
              >
                {isLoading ? (
                  <div className="flex items-center space-x-2">
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                    <span>Creating account...</span>
                  </div>
                ) : (
                  "Create Account"
                )}
              </button>
            </div>

            {/* Login Link */}
            <div className="text-center">
              <p className="text-sm text-slate-400">
                Already have an account?{" "}
                <Link
                  href="/login"
                  className="font-semibold text-green-400 hover:text-green-300 transition-colors duration-200"
                >
                  Sign in here
                </Link>
              </p>
            </div>
          </form>
        </div>

        {/* Footer */}
        <div className="text-center">
          <p className="text-xs text-slate-500">
            Multi-Agent AI Financial Intelligence System
          </p>
        </div>
      </div>
    </div>
  );
}
