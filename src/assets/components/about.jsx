import styles from "./About.module.css";

function About() {
  return (
    <div id="about" className={styles.about}>
      <h1>About TrueCheckai</h1>
      <p>
        TrueCheckai is a next-gen AI tool built to detect deepfakes and
        manipulated content. Whether it's a video, image, or other media,
        TrueCheckai uses advanced AI models to ensure content authenticity.
      </p>
    </div>
  );
}

export default About;
