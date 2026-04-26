import React from "react";
import { useLocation } from "react-router-dom";
import styles from "./Result.module.css";
import { useAuth } from "../../context/AuthContext";

const Result = () => {
  const location = useLocation();
  const { isSubscribed, upgradeSubscription } = useAuth();

  const {
    type,
    label,
    scores,
    file,
    graph_base64,
    ocr_text,
    ocr_flags,
    frame_analysis,
    frames_sampled,
    structured_report, // <--- structured_report yahan se nikal liya hai
  } = location.state || {};

  // Normalize mimetype (e.g. "image/jpeg" -> "image")
  const normalizeType = (t) => {
    if (!t) return "";
    if (t.startsWith("image/")) return "image";
    if (t.startsWith("video/")) return "video";
    if (t.includes("pdf") || t.includes("document")) return "document";
    return t;
  };

  const normalizedType = normalizeType(type);

  const renderMedia = () => {
    console.log("type:", type, "normalized:", normalizedType, "file:", file);
    if (!file) {
      return <p>No file uploaded</p>;
    }

    switch (normalizedType) {
      case "video":
        return <video controls src={file} className={styles.previewVid} />;
      case "image":
        return (
          <img
            src={file}
            alt="Uploaded content"
            className={styles.previewImg}
          />
        );
      case "document":
        return (
          <iframe
            src={file}
            title="Document preview"
            className={styles.previewDoc}
          />
        );
      default:
        return <p>Unsupported file type for preview.</p>;
    }
  };

  return (
    <div className={styles.container}>
      <h1 className={styles.title}>🔍 Deepfake Analysis Report</h1>

      {/* --- Section 1: Display Original Content --- */}
      <div className={styles.card}>
        <h2>🖼️ User Upload</h2>
        {renderMedia()}
      </div>

      {/* --- Section 2: General Analysis Scores and Graph --- */}
      <div className={styles.card}>
        <h2>📊 Analysis Report</h2>
        {scores ? (
          <ul>
            <li>Real: {(scores.real * 100).toFixed(2)}%</li>
            <li>AI-Generated: {(scores.ai * 100).toFixed(2)}%</li>
            <li>Edited: {(scores.edited * 100).toFixed(2)}%</li>
          </ul>
        ) : (
          <p>No analysis score available</p>
        )}
        {graph_base64 && (
          <img
            src={`data:image/png;base64,${graph_base64}`}
            alt="Prediction Graph"
            className={styles.graphImg}
          />
        )}
      </div>

      {/* --- Section 3: Document OCR --- */}
      {normalizedType === "document" && (
        <div className={styles.card}>
          <h2>📑 OCR Extracted Text</h2>
          {ocr_text ? (
            <pre className={styles.ocrText}>{ocr_text}</pre>
          ) : (
            <p>No text detected</p>
          )}
          {ocr_flags && ocr_flags.length > 0 && (
            <div className={styles.flags}>
              <h3>⚠️ Potential Issues</h3>
              <ul>
                {ocr_flags.map((flag, index) => (
                  <li key={index}>{flag}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {/* --- Section 4: Video Analysis --- */}
      {normalizedType === "video" && (
        <div className={styles.card}>
          <h2>🎥 Video Deepfake Analysis</h2>
          <p>Frames Analyzed: {frames_sampled}</p>
          {frame_analysis && (
            <ul>
              {Object.entries(frame_analysis).map(([lbl, count]) => (
                <li key={lbl}>
                  {lbl}: {count} frames
                </li>
              ))}
            </ul>
          )}
        </div>
      )}

      {/* --- Section 5: Final Prediction (Non-blurred) --- */}
      <div className={styles.card}>
        <h2>✅ Final Prediction</h2>
        <p
          className={`${styles.prediction} ${
            label?.includes("AI") || label?.includes("Edited")
              ? styles.deepfake
              : styles.real
          }`}
        >
          {label || "No prediction available"}
        </p>
      </div>

      {/* --- Section 6: Detailed Analysis (Blurred for non-subscribed) --- */}
      <div
        className={`${styles.card} ${
          !isSubscribed ? styles.reportBlurred : ""
        }`}
      >
        <h2>🔬 Detailed Analysis</h2>
        <div className={styles.structuredReport}>
          {structured_report && structured_report.length > 0 ? (
            structured_report.map((item, index) => (
              <div key={index} className={styles.reportItem}>
                <h4>{item.title}</h4>
                <p dangerouslySetInnerHTML={{ __html: item.details }}></p>
              </div>
            ))
          ) : (
            <p>No detailed analysis available.</p>
          )}
        </div>
      </div>

      {/* --- Subscription Prompt (Overlays blurred content) --- */}
      {/*{!isSubscribed && (
        <div className={styles.subscriptionPrompt}>
          <div className={styles.promptBox}>
            {" "}
            {/* ✅ Naya box add karein *
            <div className={styles.card}>
              <h2>✅ Final Prediction</h2>
              <p
                className={`${styles.prediction} ${
                  label?.includes("AI") || label?.includes("Edited")
                    ? styles.deepfake
                    : styles.real
                }`}
              >
                {label || "No prediction available"}
              </p>
            </div>
            <h3>Unlock Full Detailed Report</h3>
            <p>
              Subscribe to view the conclusive report and its detailed
              breakdown.
            </p>
            <button
              onClick={upgradeSubscription}
              className={styles.subscribeBtn}
            >
              Upgrade Now
            </button>
          </div>
        </div>
      )}*/}
    </div>
  );
};

export default Result;
