/*import style from "./Login.module.css";
import { FaRegUser } from "react-icons/fa";
import { TbLockPassword } from "react-icons/tb";
import { MdOutlineEmail } from "react-icons/md";
import { BiLogInCircle } from "react-icons/bi";
import { useState } from "react";
import axios from "axios";
import { useNavigate } from "react-router-dom";
function Login() {
  const [formdata, setformdata] = useState({
    username: "",
    password: "",
    /*email: "",*
  });
  const navigate = useNavigate();
  /*const handlechange = (event) => {
    console.log(event.target.value);
    setformdata(event.target.value);
  };*
  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const response = await axios.post(
        "http://localhost:5000/login", // ✅ correct API
        formdata
      );
      alert(response.data.message || "Login successful ✅");
      navigate("/#header");
    } catch (error) {
      if (error.response && error.response.data) {
        alert(error.response.data.message || "Login failed ❌");
      } else {
        alert("Login failed. Try again.");
      }
    }
  };
  /*const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const response = await axios.post(
        "http://localhost:5000/login",
        formdata
      );

      // Save user info in localStorage
      const userData = {
        name: response.data.name || formdata.username,
        picture: "/default-avatar.png", // show default image for now
      };
      localStorage.setItem("user", JSON.stringify(userData));

      alert("Login successful ✅");
      navigate("/");
      window.location.reload(); // refresh header
    } catch (error) {
      if (error.response && error.response.data) {
        alert(error.response.data.message);
      } else {
        alert("Login failed. Try again.");
      }
    }
  };*

  const handlechange = (event) => {
    const { name, value } = event.target;
    setformdata((prevData) => ({
      ...prevData,
      [name]: value,
    }));
  };

  return (
    <div className={style.login}>
      <h1>Login in to TrueCheckai</h1>
      <div className={style.form}>
        <form onSubmit={handleSubmit}>
          <label htmlFor="username">
            {" "}
            <FaRegUser />
            Username
          </label>
          <input
            value={formdata.username}
            type="text"
            name="username"
            placeholder="Enter Name"
            onChange={handlechange}
            required
          />
          <label htmlFor="password">
            <TbLockPassword />
            Password
          </label>
          <input
            value={formdata.password}
            type="password"
            name="password"
            placeholder="Password"
            onChange={handlechange}
            required
          />
          {/*<label htmlFor="mail">
            <MdOutlineEmail />
            Email
          </label>
          <input
            value={formdata.email}
            type="email"
            name="email"
            placeholder="Enter email"
            onChange={handlechange}
            required
          />*

          <button type="submit">
            {" "}
            <BiLogInCircle />
            Login
          </button>
        </form>
        <div className={styles.orDivider}>── OR ──</div>
        {/* Google Login *

        <GoogleLogin
          onSuccess={googleLogin} // BAS ITNA KARNA HAI! Poora response direct bhej do.
          onError={() => {
            console.log("Google Login Failed");
          }}
        />
      </div>
    </div>
  );
}

export default Login;*/

import React, { useState } from "react";
import style from "./Login.module.css";
import { FaRegUser } from "react-icons/fa";
import { TbLockPassword } from "react-icons/tb";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../../context/AuthContext"; // 1. Import useAuth
import toast from "react-hot-toast"; // 2. Import toast for notifications
import GoogleLogin from "./googlelogin"; // 3. Import GoogleLogin component

function Login() {
  const [formData, setFormData] = useState({
    email: "", // 4. Changed from username to email
    password: "",
  });
  //const navigate = useNavigate();
  const { login, googleLogin } = useAuth(); // 5. Get login functions from context

  const handleChange = (event) => {
    const { name, value } = event.target;
    setFormData((prevData) => ({
      ...prevData,
      [name]: value,
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!formData.email || !formData.password) {
      toast.error("Please enter both email and password.");
      return;
    }
    // 6. Call the login function from the context
    await login(formData);
  };

  return (
    <div className={style.login}>
      <h1>Login in to TrueCheckai</h1>
      <div className={style.form}>
        <form onSubmit={handleSubmit}>
          <label htmlFor="email">
            <FaRegUser />
            Email
          </label>
          <input
            value={formData.email}
            type="email"
            name="email"
            placeholder="Enter Email"
            onChange={handleChange}
            required
          />
          <label htmlFor="password">
            <TbLockPassword />
            Password
          </label>
          <input
            value={formData.password}
            type="password"
            name="password"
            placeholder="Password"
            onChange={handleChange}
            required
          />
          <button type="submit">Login</button>
        </form>
        <div className={style.orDivider}>── OR ──</div>

        {/* 7. Pass the googleLogin function directly */}
        <GoogleLogin
          onSuccess={googleLogin}
          onError={() => {
            toast.error("Google Login Failed. Please try again.");
          }}
        />

        <p className={style.signupLink}>
          Don't have an account? <Link to="/signup">Sign up</Link>
        </p>
      </div>
    </div>
  );
}

export default Login;
