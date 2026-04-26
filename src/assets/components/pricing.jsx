import styles from "./Pricing.module.css";
import { IoCheckmark } from "react-icons/io5";
import { useNavigate } from "react-router-dom";
function Pricing() {
  const navigate = useNavigate();
  const handleGetStartedClick = () => {
    navigate("/checkout");
  };
  const handleLoginClick = () => {
    navigate("/login");
  };

  return (
    <div className={styles.price}>
      <h1 className={styles.heading}>Choose Your Plan</h1>
      <div className={styles.cards}>
        <div className={styles.card}>
          <h1>Free Plan</h1>
          <p>
            <IoCheckmark />
            No credit card required.
          </p>
          <p>
            <IoCheckmark />
            Quickly check image/video real or AI-generated.
          </p>
          <p>
            <IoCheckmark />
            20 Free Credits.
          </p>

          <button onClick={handleLoginClick} className={styles.login}>
            Login
          </button>
        </div>
        <div className={styles.card}>
          <h1>Pro Plan – ₹799/month </h1>
          <p>
            <IoCheckmark />
            High-accuracy .
          </p>
          <p>
            <IoCheckmark />
            Get original from verified sources/databases.
          </p>
          <p>
            <IoCheckmark /> Unlimited Scans per month.
          </p>
          <button onClick={handleGetStartedClick} className={styles.login}>
            Get Started
          </button>
        </div>
      </div>
    </div>
  );
}

export default Pricing;
