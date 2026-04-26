/*import React, { useState } from "react";
import { Carousel } from "react-bootstrap";
import { ToastContainer, toast } from "react-toastify";
import { useNavigate } from "react-router-dom";
import "react-toastify/dist/ReactToastify.css";

import styles from "./Contents.module.css";
import img1 from "./img1.png";
import img2 from "./img2.png";
import img3 from "./img3.png";
import img4 from "./img4.png";

function Contents() {
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleFileChange = (e) => {
    const uploadedFile = e.target.files[0];
    if (uploadedFile) {
      setFile(uploadedFile);
      toast.success(`✅ "${uploadedFile.name}" uploaded successfully!`);
    }
  };
  // In your contents.jsx or equivalent React component file

  const handleAnalyze = async () => {
    if (!file) {
      toast.error("⚠️ Please upload an image to analyze.");
      return;
    }

    setLoading(true);
    const formData = new FormData();
    formData.append("file", file);

    try {
      const response = await fetch("http://localhost:5000/predict", {
        method: "POST",
        body: formData,
      });

      const data = await response.json();

      // ✅ This is the crucial check
      if (response.ok) {
        navigate("/result", {
          state: {
            type: data.type,
            label: data.label,
            scores: data.scores,
            file: URL.createObjectURL(file),
            graph_base64: data.graph_base64,
            ocr_text: data.ocr_text,
            ocr_flags: data.ocr_flags,
            frame_analysis: data.frame_analysis,
            frames_sampled: data.frames_sampled,
          },
        });
      } else {
        // ERROR: The response has an 'error' property instead
        // We use the error message from the server for a more informative toast
        toast.error(`❌ Analysis failed: ${data.error || "Unknown error"}`);
      }
    } catch (error) {
      console.error("Error analyzing file:", error);
      toast.error("❌ A network or server error occurred.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div id="contents" className={styles.Contents}>
      <ToastContainer position="top-center" autoClose={2000} />

      <div className={styles.punch}>
        <h1 className={styles.title}>TrueCheckai</h1>
        <h2 className={styles.tagline}>
          Your AI Guardian Against Digital Deception.
        </h2>

        <div className={styles.upload}>
          <label className={styles.btn1}>
            Upload img/video
            <input
              type="file"
              accept="image/*,video/*"
              onChange={handleFileChange}
              style={{ display: "none" }}
            />
          </label>

          <button
            className={styles.btn2}
            onClick={handleAnalyze}
            disabled={loading}
          >
            {loading ? "Analyzing..." : "Analyze"}
          </button>
        </div>
      </div>

      <div className={styles.slide}>
        <div className={styles.carol}>
          <Carousel>
            <Carousel.Item>
              <img className="d-block w-100" src={img1} alt="Car" />
            </Carousel.Item>
            <Carousel.Item>
              <img className="d-block w-100" src={img2} alt="McLaren" />
            </Carousel.Item>
            <Carousel.Item>
              <img className="d-block w-100" src={img3} alt="Porsche" />
            </Carousel.Item>
            <Carousel.Item>
              <img className="d-block w-100" src={img4} alt="Mercedes" />
            </Carousel.Item>
          </Carousel>
        </div>
      </div>
    </div>
  );
}

export default Contents;*/

/*import React, { useState } from "react";
import { Carousel } from "react-bootstrap";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../../context/AuthContext";
import toast from "react-hot-toast"; // react-hot-toast ka istemal karein
import axios from "axios"; // axios import karein

// Styles and images
import styles from "./Contents.module.css";
import img1 from "./img1.png";
import img2 from "./img2.png";
import img3 from "./img3.png";
import img4 from "./img4.png";

// Axios instance banayein jo har request ke saath token bhejega
const axiosInstance = axios.create({
  baseURL: "http://localhost:5000", // Aapke backend ka URL
});
axiosInstance.interceptors.request.use((config) => {
  const token = localStorage.getItem("token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

function Contents() {
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  // isSubscribed ko yahan AuthContext se lein
  const { isAuthenticated, isSubscribed, credits, deductCredits } = useAuth();

  const handleFileChange = (e) => {
    const uploadedFile = e.target.files[0];
    if (uploadedFile) {
      setFile(uploadedFile);
      toast.success(`"${uploadedFile.name}" selected.`);
    }
  };

  const handleAnalyze = async () => {
    // 1. Check for login
    if (!isAuthenticated) {
      toast.error("Please login or signup first to analyze files.");
      return;
    }
    // 2. Check for file
    if (!file) {
      toast.error("Please upload an image or video to analyze.");
      return;
    }

    const cost = file.type.startsWith("video/") ? 5 : 1;

    // 3. Naya Hybrid Logic: Agar subscribed nahi hai, toh hi credit check karein
    if (!isSubscribed && credits < cost) {
      toast.error(
        "You have run out of credits. Subscribe for unlimited analysis!"
      );
      navigate("/pricing"); // User ko pricing page par bhej dein
      return;
    }

    setLoading(true);
    const loadingToast = toast.loading("Analyzing your file...");
    const formData = new FormData();
    formData.append("file", file);

    try {
      const response = await axiosInstance.post("/predict", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });

      toast.dismiss(loadingToast);
      toast.success("Analysis complete!");

      // UI update ke liye credit deduct karein (agar user subscribed nahi hai)
      if (!isSubscribed) {
        deductCredits(cost);
      }

      navigate("/result", {
        state: { ...response.data, file: URL.createObjectURL(file) },
      });
    } catch (error) {
      toast.dismiss(loadingToast);
      console.error("Error analyzing file:", error);
      toast.error(
        error.response?.data?.error || "An error occurred during analysis."
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div id="contents" className={styles.Contents}>
      {/* Note: <Toaster /> component App.jsx mein hona chahiye *

      <div className={styles.punch}>
        <h1 className={styles.title}>TrueCheckai</h1>
        <h2 className={styles.tagline}>
          Your AI Guardian Against Digital Deception.
        </h2>

        <div className={styles.upload}>
          <label className={styles.btn1}>
            Upload img/video
            <input
              type="file"
              accept="image/*,video/*"
              onChange={handleFileChange}
              style={{ display: "none" }}
            />
          </label>
          <button
            className={styles.btn2}
            onClick={handleAnalyze}
            disabled={loading}
          >
            {loading ? "Analyzing..." : "Analyze"}
          </button>
        </div>
      </div>

      <div className={styles.slide}>
        <div className={styles.carol}>
          <Carousel>
            <Carousel.Item>
              <img className="d-block w-100" src={img1} alt="Slide 1" />
            </Carousel.Item>
            <Carousel.Item>
              <img className="d-block w-100" src={img2} alt="Slide 2" />
            </Carousel.Item>
            <Carousel.Item>
              <img className="d-block w-100" src={img3} alt="Slide 3" />
            </Carousel.Item>
            <Carousel.Item>
              <img className="d-block w-100" src={img4} alt="Slide 4" />
            </Carousel.Item>
          </Carousel>
        </div>
      </div>
    </div>
  );
}

export default Contents;*/

import React, { useState } from "react";
import { Carousel } from "react-bootstrap";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../../context/AuthContext"; // Adjust path if needed (e.g., '../../../context/AuthContext')
import toast from "react-hot-toast";
import axios from "axios";

// Styles and images
import styles from "./Contents.module.css";
import img1 from "./img1.png";
import img2 from "./img2.png";
import img3 from "./img3.png";
import img4 from "./img4.png";

// Axios instance with token interceptor
const axiosInstance = axios.create({
  baseURL: "http://localhost:5000",
});
axiosInstance.interceptors.request.use((config) => {
  const token = localStorage.getItem("token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

function Contents() {
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  // Destructure from useAuth (credits and refetchUser   now available)
  const { isAuthenticated, isSubscribed, credits, refetchUser } = useAuth();

  const handleFileChange = (e) => {
    const uploadedFile = e.target.files[0];
    if (uploadedFile) {
      setFile(uploadedFile);
      toast.success(`"${uploadedFile.name}" selected.`);
    }
  };

  const handleAnalyze = async () => {
    // 1. Check for login
    if (!isAuthenticated) {
      toast.error("Please login or signup first to analyze files.");
      navigate("/signup");
      return;
    }

    // 2. Check for file
    if (!file) {
      toast.error("Please upload an image or video to analyze.");
      return;
    }

    // 3. Pre-check credits (for UX: avoid unnecessary API call)
    const cost = file.type.startsWith("video/") ? 5 : 1;
    if (!isSubscribed && credits < cost) {
      toast.error(
        `Insufficient credits (${credits}/${cost} needed). Subscribe for unlimited analysis!`
      );
      navigate("/pricing");
      return;
    }

    setLoading(true);
    const loadingToast = toast.loading("Analyzing your file...");

    const formData = new FormData();
    formData.append("file", file);

    try {
      const response = await axiosInstance.post("/predict", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });

      toast.dismiss(loadingToast);
      toast.success("Analysis complete!");

      // Backend already deducted credits. Refetch to update local state
      await refetchUser();

      // Navigate to results with data
      navigate("/result", {
        state: { ...response.data, file: URL.createObjectURL(file) },
      });
    } catch (error) {
      toast.dismiss(loadingToast);
      console.error("Error analyzing file:", error);

      // Handle specific backend errors for better UX
      if (error.response?.status === 401) {
        toast.error("Session expired. Please login again.");
        refetchUser(); // This will trigger logout if invalid
      } else if (error.response?.status === 402) {
        toast.error(
          "Insufficient credits. Subscribe for unlimited analysis or buy more!"
        );
        navigate("/pricing");
      } else if (error.response?.status === 503) {
        toast.error("AI analyzer is temporarily unavailable. Try again later.");
      } else {
        toast.error(
          error.response?.data?.error || "An error occurred during analysis."
        );
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div id="contents" className={styles.Contents}>
      <div className={styles.punch}>
        <h1 className={styles.title}>TrueCheckai</h1>
        <h2 className={styles.tagline}>
          Your AI Guardian Against Digital Deception.
        </h2>

        <div className={styles.upload}>
          <label className={styles.btn1}>
            Upload img/video
            <input
              type="file"
              accept="image/*,video/*"
              onChange={handleFileChange}
              style={{ display: "none" }}
              disabled={loading}
            />
          </label>
          <button
            className={styles.btn2}
            onClick={handleAnalyze}
            disabled={loading || !file}
          >
            {loading ? "Analyzing..." : "Analyze"}
          </button>
        </div>

        {/* Optional: Show current credits for better UX */}
        {/*{isAuthenticated && (
          <p className={styles.creditsInfo}>
            Credits: {credits} {isSubscribed && "(Unlimited)"}
          </p>
        )}*/}
      </div>

      <div className={styles.slide}>
        <div className={styles.carol}>
          <Carousel>
            <Carousel.Item>
              <img className="d-block w-100" src={img1} alt="Slide 1" />
            </Carousel.Item>
            <Carousel.Item>
              <img className="d-block w-100" src={img2} alt="Slide 2" />
            </Carousel.Item>
            <Carousel.Item>
              <img className="d-block w-100" src={img3} alt="Slide 3" />
            </Carousel.Item>
            <Carousel.Item>
              <img className="d-block w-100" src={img4} alt="Slide 4" />
            </Carousel.Item>
          </Carousel>
        </div>
      </div>
    </div>
  );
}

export default Contents; // ✅ This is the default export - ensures home.jsx can import it
