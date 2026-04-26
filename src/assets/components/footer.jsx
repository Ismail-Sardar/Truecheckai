import styles from "./Footer.module.css";

function Footer() {
  return (
    <footer className={styles.footer}>
      <p>© 2025 TrueCheckai. All rights reserved.</p>
      <div className={styles.links}>
        <a href="#">Privacy Policy</a>
        <a href="#">Terms of Use</a>
        <a href="#">Contact Us</a>
      </div>
    </footer>
  );
}

export default Footer;
