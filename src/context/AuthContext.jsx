// AuthContext.jsx

/*import { createContext, useContext, useState } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios"; // Only if you're using it in signup

// ✅ Export the AuthContext so useAuth() can access it
export const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [credits, setCredits] = useState(0);
  const navigate = useNavigate();

  // Signup function using backend
  const signup = async (formData) => {
    try {
      const response = await axios.post(
        "http://localhost:5000/api/signup",
        formData
      );
      console.log(response.data.message);
      setUser({
        name: formData.username,
        email: formData.email,
      });
      setCredits(20);
      navigate("/");
    } catch (error) {
      alert(
        error.response?.data?.message || "An error occurred during signup."
      );
    }
  };

  const googleLogin = (googleUserData) => {
    setUser({
      name: googleUserData.name,
      email: googleUserData.email,
      picture: googleUserData.picture,
    });
    setCredits(20);
    navigate("/");
  };

  const deductCredits = (amount) => {
    setCredits((currentCredits) => currentCredits - amount);
  };

  const logout = () => {
    setUser(null);
    setCredits(0);
    navigate("/login");
  };

  const value = {
    user,
    credits,
    isAuthenticated: !!user,
    signup,
    googleLogin,
    deductCredits,
    logout,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

// ✅ Export the custom hook
export const useAuth = () => {
  return useContext(AuthContext);
};*/

// AuthContext.jsx (full updated file)
// src/context/AuthContext.jsx
// context/AuthContext.jsx
// src/context/AuthContext.jsx

// src/context/AuthContext.jsx

/*import { createContext, useContext, useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import toast from "react-hot-toast";

const API_URL = "http://localhost:5000";

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    const token = localStorage.getItem("token");
    if (token) {
      const axiosWithToken = axios.create({
        headers: { Authorization: `Bearer ${token}` },
      });
      axiosWithToken
        .get(`${API_URL}/profile`)
        .then((response) => setUser(response.data.user))
        .catch(() => logout());
    }
  }, []);

  const googleLogin = async (credentialResponse) => {
    try {
      const googleToken = credentialResponse?.credential;
      if (!googleToken) {
        throw new Error("Google credential missing");
      }

      const response = await axios.post(`${API_URL}/google-login`, {
        token: googleToken,
      });

      const { token, user: userData } = response.data;
      localStorage.setItem("token", token);
      setUser(userData);

      navigate("/");
      toast.success("Google login successful!");
    } catch (error) {
      console.error("Google login failed:", error);
      toast.error(
        error.response?.data?.message || error.message || "Google login failed."
      );
    }
  };

  const logout = () => {
    setUser(null);
    localStorage.removeItem("token");
    navigate("/login");
  };

  const value = {
    user,
    isAuthenticated: !!user,
    isSubscribed: user?.is_subscribed || false,
    googleLogin,
    logout,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = () => {
  return useContext(AuthContext);
};*/

/*import { createContext, useContext, useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import toast from "react-hot-toast";

const API_URL = "http://localhost:5000";

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null); // ✅ Fixed: No extra space
  const navigate = useNavigate();

  // Logout function (defined early for useEffect)
  const logout = () => {
    setUser(null); // ✅ Fixed: No extra space
    localStorage.removeItem("token");
    navigate("/login");
  };

  // Refetch user profile to update local state (e.g., after credit deduction)
  const refetchUser = async () => {
    // ✅ Fixed: No extra space in function name/call
    const token = localStorage.getItem("token");
    if (!token) {
      logout();
      return;
    }

    try {
      const response = await axios.get(`${API_URL}/profile`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setUser(response.data.user); // ✅ Fixed: No extra space
    } catch (error) {
      console.error("Failed to refetch user:", error);
      if (error.response?.status === 401) {
        logout(); // Token invalid/expired
      }
    }
  };

  // Initial load: Check token and fetch user if valid
  useEffect(() => {
    const token = localStorage.getItem("token");
    if (token) {
      refetchUser(); // ✅ Fixed: No extra space
    }
  }, []);

  const googleLogin = async (credentialResponse) => {
    try {
      const googleToken = credentialResponse?.credential;
      if (!googleToken) throw new Error("Google credential missing");

      const response = await axios.post(
        `${API_URL}/google-login`,
        { token: googleToken },
        { withCredentials: true } // Important for CORS cookies
      );

      const { token, user: userData } = response.data;
      localStorage.setItem("token", token);
      setUser(userData); // ✅ Fixed: No extra space

      navigate("/");
      toast.success("Google login successful!");
    } catch (error) {
      console.error("Google login failed:", error);
      toast.error(
        error.response?.data?.message || error.message || "Google login failed."
      );
    }
  };

  // Context value: Includes credits and refetchUser
  const value = {
    user,
    isAuthenticated: !!user,
    isSubscribed: user?.is_subscribed || false,
    credits: user?.credits || 0, // ✅ Provides credits
    googleLogin,
    logout,
    refetchUser, // ✅ Exposes refetchUser  for components
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = () => {
  return useContext(AuthContext);
};
*/

// src/context/AuthContext.jsx

import {
  createContext,
  useContext,
  useState,
  useEffect,
  useCallback,
} from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import toast from "react-hot-toast";

const API_URL = "http://localhost:5000";

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const navigate = useNavigate();

  // Define logout early so it can be used anywhere
  const logout = useCallback(() => {
    setUser(null);
    localStorage.removeItem("token");
    navigate("/login");
  }, [navigate]);

  const refetchUser = useCallback(async () => {
    const token = localStorage.getItem("token");
    if (!token) {
      logout();
      return;
    }
    try {
      const response = await axios.get(`${API_URL}/profile`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setUser(response.data.user);
    } catch (error) {
      console.error("Failed to refetch user:", error);
      logout(); // Token is likely invalid/expired
    }
  }, [logout]);

  // Check for a token on initial app load
  useEffect(() => {
    const token = localStorage.getItem("token");
    if (token) {
      refetchUser();
    }
  }, [refetchUser]);

  // --- NEW: LOGIN FUNCTION ---
  const login = async (credentials) => {
    try {
      const response = await axios.post(`${API_URL}/login`, credentials);
      const { token, user: userData } = response.data;
      localStorage.setItem("token", token);
      setUser(userData);
      navigate("/");
      toast.success("Login successful!");
    } catch (error) {
      console.error("Login failed:", error);
      toast.error(error.response?.data?.error || "Login failed.");
    }
  };

  // --- NEW: SIGNUP FUNCTION ---
  const signup = async (formData) => {
    try {
      const response = await axios.post(`${API_URL}/signup`, formData);
      const { token, user: userData } = response.data;
      localStorage.setItem("token", token);
      setUser(userData);
      navigate("/");
      toast.success("Signup successful!");
    } catch (error) {
      console.error("Signup failed:", error);
      toast.error(error.response?.data?.error || "Signup failed.");
    }
  };

  const googleLogin = async (credentialResponse) => {
    try {
      const googleToken = credentialResponse?.credential;
      if (!googleToken) throw new Error("Google credential missing");

      const response = await axios.post(`${API_URL}/google-login`, {
        token: googleToken,
      });
      const { token, user: userData } = response.data;
      localStorage.setItem("token", token);
      setUser(userData);
      navigate("/");
      toast.success("Google login successful!");
    } catch (error) {
      console.error("Google login failed:", error);
      toast.error(error.response?.data?.error || "Google login failed.");
    }
  };

  const value = {
    user,
    isAuthenticated: !!user,
    isSubscribed: user?.is_subscribed || false,
    credits: user?.credits ?? 0,
    login, // <-- Expose login
    signup, // <-- Expose signup
    googleLogin,
    logout,
    refetchUser,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = () => {
  return useContext(AuthContext);
};
