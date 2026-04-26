// Signup.jsx (full updated file)
import React, { useState } from "react";
import styles from "./Login.module.css"; // ✅ CHANGED: Use Signup-specific styles (create if needed; or reuse Login if identical)
import { useAuth } from "../../context/AuthContext"; // ✅ Adjust path if your AuthContext is elsewhere (e.g., "../components/AuthContext")
import { GoogleLogin } from "@react-oauth/google";
import { jwtDecode } from "jwt-decode";
// ✅ REMOVED: useNavigate import—no longer needed

function Signup() {
  const { signup, googleLogin } = useAuth();
  const [form, setForm] = useState({ username: "", email: "", password: "" });

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    signup(form); // AuthContext will handle navigation to home (/)
    // ✅ REMOVED: navigate("/"); // No longer needed—avoids conflicts
  };

  return (
    <div className={styles.container}>
      <h2>Signup for TrueCheckai</h2>
      {/* Normal Signup */}
      <form className={styles.form} onSubmit={handleSubmit}>
        <label>Username</label>
        <input
          type="text"
          name="username"
          placeholder="Enter Name"
          value={form.username}
          onChange={handleChange}
          required
        />

        <label>Password</label>
        <input
          type="password"
          name="password"
          placeholder="Password"
          value={form.password}
          onChange={handleChange}
          required
        />

        <label>Email</label>
        <input
          type="email"
          name="email"
          placeholder="Enter email"
          value={form.email}
          onChange={handleChange}
          required
        />

        <button type="submit" className={styles.submitBtn}>
          Signup
        </button>
      </form>
      <div className={styles.orDivider}>── OR ──</div>
      {/* Google Login */}

      <GoogleLogin
        onSuccess={googleLogin}
        onError={() => {
          console.log("Google Login Failed");
        }}
      />
    </div>
  );
}

export default Signup;
