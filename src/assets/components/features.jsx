import React from "react";
import style from "./Features.module.css";

function Feature() {
  return (
    <div id="features" className={style.banner}>
      {/* Netflix-style title animation */}
      <svg width="100%" height="250">
        <text
          x="50%"
          y="50%"
          dominantBaseline="middle"
          textAnchor="middle"
          className={style.fes}
        >
          Feature
        </text>
      </svg>

      {/* 3D Carousel */}
      <div className={style.slider}>
        <div className={style.carouselInner}>
          <div className={style.item}>
            ⚡ Real-time Analysis
            <br />
            Processes and verifies instantly during upload or streaming.
          </div>
          <div className={style.item}>
            🎯 Original Media Retrieval
            <br />
            Matches with known databases for original verification.
          </div>
          <div className={style.item}>
            🧠 Deepfake Detection
            <br />
            Detects AI-generated or tampered media via forensics.
          </div>
          <div className={style.item}>
            🛡️ Tamper-Proof Reports
            <br />
            Verifiable certificates for legal and public records.
          </div>
        </div>
      </div>
    </div>
  );
}

export default Feature;
