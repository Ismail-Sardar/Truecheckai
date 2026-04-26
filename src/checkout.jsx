import React, { useEffect } from "react";
import "bootstrap/dist/css/bootstrap.min.css";
import style from "./Checkout.module.css";

function Checkout() {
  const amount = 799;

  // Load Razorpay script on component mount
  useEffect(() => {
    const loadRazorpayScript = () => {
      const script = document.createElement("script");
      script.src = "https://checkout.razorpay.com/v1/checkout.js";
      script.async = true;
      document.body.appendChild(script);
    };

    loadRazorpayScript();
  }, []);

  const handlePayment = async () => {
    try {
      const response = await fetch("http://localhost:5000/create-order", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ amount: 799 }),
      });

      const order = await response.json();

      // ⛔ Use TEST key while testing
      const options = {
        key: "rzp_test_lENL2EMmm4YrZs",
        amount: order.amount,
        currency: "INR",
        name: "TrueCheck AI",
        description: "Secure Your Media",
        order_id: order.id,
        handler: function (response) {
          alert(
            "Payment Successful! Payment ID: " + response.razorpay_payment_id
          );
          window.location.href = "/#contents"; // 🔁 redirect to home
        },
        prefill: {
          name: "User Name",
          email: "user@example.com",
        },
        theme: {
          color: "#3399cc",
        },
      };

      const rzp = new window.Razorpay(options);
      rzp.open();
    } catch (error) {
      console.error("❌ Payment initiation failed", error);
      alert("Payment initiation failed.");
    }
  };

  return (
    <div className={style.containerpy5}>
      <div className={style.rowjustify}>
        <div className={style.cardbody}>
          <div className={style.text}>
            <h2>Checkout</h2>
          </div>

          <hr />

          <div className={style.bill}>
            <h5>Order Summary</h5>
            <ul className={style.listgroup}>
              <li className="list-group-item d-flex justify-content-between">
                <span>
                  TrueCheck AI License <strong>₹{amount}</strong>
                </span>
              </li>
              <li className="list-group-item d-flex justify-content-between">
                <span>Platform Access</span>
                <span>Included</span>
              </li>
              <li className="list-group-item d-flex justify-content-between">
                <span>Support</span>
                <span>Included</span>
              </li>
              <li className="list-group-item d-flex justify-content-between">
                <span className="fw-bold">Total</span>
                <strong className={style.textsuccess}>₹{amount}</strong>
              </li>
            </ul>
          </div>

          <div className={style.btn}>
            <button
              onClick={handlePayment}
              /*className="btn btn-success btn-lg rounded-pill"
              className={style.btn1}*/
            >
              Pay
            </button>
          </div>

          <p className={style.raz}>
            🔒 100% secure payment powered by Razorpay
          </p>
        </div>
      </div>
    </div>
  );
}

export default Checkout;

// src/checkout.jsx

/*import React, { useEffect } from "react";
import "bootstrap/dist/css/bootstrap.min.css";
import style from "./Checkout.module.css";
import { useAuth } from "./context/AuthContext.jsx"; // 1. Import Auth context
import { useNavigate } from "react-router-dom"; // 2. Import navigation hook

function Checkout() {
  const amount = 799;
  const { user, token, login } = useAuth(); // 3. Get user, token, and login function
  const navigate = useNavigate(); // 4. Initialize navigate function

  // Load Razorpay script on component mount
  useEffect(() => {
    const loadRazorpayScript = () => {
      const script = document.createElement("script");
      script.src = "https://checkout.razorpay.com/v1/checkout.js";
      script.async = true;
      document.body.appendChild(script);
    };

    loadRazorpayScript();
  }, []);

  const handlePayment = async () => {
    // Ensure user and token are available before payment
    if (!token) {
      alert("You must be logged in to make a payment.");
      navigate("/login");
      return;
    }

    try {
      const response = await fetch("http://localhost:5000/create-order", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`, // Add token for authentication
        },
        body: JSON.stringify({ amount: 799 }),
      });

      const order = await response.json();
      if (!response.ok) {
        throw new Error(order.error || "Failed to create order.");
      }

      const options = {
        key: "rzp_test_lENL2EMmm4YrZs", // ⛔ Use TEST key while testing
        amount: order.amount,
        currency: "INR",
        name: "TrueCheck AI",
        description: "Secure Your Media",
        order_id: order.id,
        // --- THIS HANDLER IS UPDATED ---
        handler: async function (response) {
          try {
            // 5. Securely verify the payment with your backend
            const verifyResponse = await fetch(
              "http://localhost:5000/payment-success",
              {
                method: "POST",
                headers: {
                  "Content-Type": "application/json",
                  Authorization: `Bearer ${token}`,
                },
                body: JSON.stringify({
                  razorpay_payment_id: response.razorpay_payment_id,
                  razorpay_order_id: response.razorpay_order_id,
                  razorpay_signature: response.razorpay_signature,
                }),
              }
            );

            if (!verifyResponse.ok) {
              throw new Error("Payment verification failed.");
            }

            // 6. Fetch the updated user profile from the backend
            const profileResponse = await fetch(
              "http://localhost:5000/profile",
              {
                headers: { Authorization: `Bearer ${token}` },
              }
            );
            const updatedProfile = await profileResponse.json();

            // 7. Update the global user state so the UI refreshes everywhere
            if (updatedProfile.user) {
              login(updatedProfile.user, token);
              alert("Payment Successful! Your subscription is active.");
              // 8. Redirect to home page using React Router
              navigate("/");
            } else {
              throw new Error("Could not refresh user profile.");
            }
          } catch (error) {
            console.error("Error during payment verification:", error);
            alert(
              "An error occurred while confirming your payment. Please contact support."
            );
          }
        },
        prefill: {
          // Use actual user data from context
          name: user?.username || "User Name",
          email: user?.email || "user@example.com",
        },
        theme: {
          color: "#3399cc",
        },
      };

      const rzp = new window.Razorpay(options);
      rzp.open();
    } catch (error) {
      console.error("❌ Payment initiation failed", error);
      alert("Payment initiation failed: " + error.message);
    }
  };

  return (
    <div className={style.containerpy5}>
      <div className={style.rowjustify}>
        <div className={style.cardbody}>
          <div className={style.text}>
            <h2>Checkout</h2>
          </div>

          <hr />

          <div className={style.bill}>
            <h5>Order Summary</h5>
            <ul className={style.listgroup}>
              <li className="list-group-item d-flex justify-content-between">
                <span>
                  TrueCheck AI License <strong>₹{amount}</strong>
                </span>
              </li>
              <li className="list-group-item d-flex justify-content-between">
                <span>Platform Access</span>
                <span>Included</span>
              </li>
              <li className="list-group-item d-flex justify-content-between">
                <span>Support</span>
                <span>Included</span>
              </li>
              <li className="list-group-item d-flex justify-content-between">
                <span className="fw-bold">Total</span>
                <strong className={style.textsuccess}>₹{amount}</strong>
              </li>
            </ul>
          </div>

          <div className={style.btn}>
            {/* The button was commented out, I've restored it *
            <button
              onClick={handlePayment}
              className={`${style.btn1} btn btn-success btn-lg rounded-pill`}
            >
              Pay
            </button>
          </div>

          <p className={style.raz}>
            🔒 100% secure payment powered by Razorpay
          </p>
        </div>
      </div>
    </div>
  );
}

export default Checkout;*/

// src/checkout.jsx

/*import React, { useEffect } from "react";
import "bootstrap/dist/css/bootstrap.min.css";
import style from "./Checkout.module.css";
import { useNavigate } from "react-router-dom";
import { useAuth } from "./context/AuthContext"; // 1. Import useAuth
import toast from "react-hot-toast"; // 2. Import toast for notifications

function Checkout() {
  const amount = 799;
  const navigate = useNavigate();
  const { user, token, login } = useAuth(); // 3. Get user and token from context

  // Load Razorpay script on component mount
  useEffect(() => {
    const loadRazorpayScript = () => {
      const script = document.createElement("script");
      script.src = "https://checkout.razorpay.com/v1/checkout.js";
      script.async = true;
      document.body.appendChild(script);
    };
    loadRazorpayScript();
  }, []);

  const handlePayment = async () => {
    // 4. Check for token before initiating payment
    if (!token) {
      toast.error("Please login or signin to continue.");
      navigate("/signup");
      return;
    }

    try {
      const response = await fetch("http://localhost:5000/create-order", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`, // 5. THE FIX: Add auth token to header
        },
        body: JSON.stringify({ amount: 799 }),
      });

      const order = await response.json();
      if (!response.ok) {
        throw new Error(order.error || "Could not create payment order.");
      }

      const options = {
        key: "rzp_test_lENL2EMmm4YrZs",
        amount: order.amount,
        currency: "INR",
        name: "TrueCheck AI",
        description: "Secure Your Media",
        order_id: order.id,
        handler: async function (response) {
          try {
            // Also send token when verifying payment
            const verifyResponse = await fetch(
              "http://localhost:5000/payment-success",
              {
                method: "POST",
                headers: {
                  "Content-Type": "application/json",
                  Authorization: `Bearer ${token}`,
                },
                body: JSON.stringify({
                  razorpay_payment_id: response.razorpay_payment_id,
                  razorpay_order_id: response.razorpay_order_id,
                  razorpay_signature: response.razorpay_signature,
                }),
              }
            );

            if (!verifyResponse.ok)
              throw new Error("Payment verification failed.");

            // Update user state and redirect
            toast.success(
              "Payment Successful! Your subscription is now active."
            );
            const profileRes = await fetch("http://localhost:5000/profile", {
              headers: { Authorization: `Bearer ${token}` },
            });
            const updatedUser = await profileRes.json();
            login(updatedUser.user, token); // Update context
            navigate("/"); // Use React Router navigation
          } catch (error) {
            toast.error(error.message || "Payment verification failed.");
          }
        },
        prefill: {
          name: user?.username || "User Name", // Use actual user data
          email: user?.email || "user@example.com",
        },
        theme: {
          color: "#3399cc",
        },
      };

      const rzp = new window.Razorpay(options);
      rzp.open();
    } catch (error) {
      console.error("❌ Payment initiation failed", error);
      toast.error(error.message || "Payment initiation failed.");
    }
  };

  return (
    <div className={style.containerpy5}>
      <div className={style.rowjustify}>
        <div className={style.cardbody}>
          <div className={style.text}>
            <h2>Checkout</h2>
          </div>
          <hr />
          <div className={style.bill}>
            <h5>Order Summary</h5>
            <ul className={style.listgroup}>
              <li className="list-group-item d-flex justify-content-between">
                <span>
                  TrueCheck AI License <strong>₹{amount}</strong>
                </span>
              </li>
              <li className="list-group-item d-flex justify-content-between">
                <span className="fw-bold">Total</span>
                <strong className={style.textsuccess}>₹{amount}</strong>
              </li>
            </ul>
          </div>
          <div className={style.btn}>
            {/* Restored the button *
            <button
              onClick={handlePayment}
              className={`${style.btn1} btn btn-success btn-lg rounded-pill`}
            >
              Pay Now
            </button>
          </div>
          <p className={style.raz}>
            🔒 100% secure payment powered by Razorpay
          </p>
        </div>
      </div>
    </div>
  );
}

export default Checkout;*/

// src/checkout.jsx

/*import React, { useEffect, useState } from "react";
import toast from "react-hot-toast";
import { useNavigate } from "react-router-dom";
import { useAuth } from "./context/AuthContext";
import "bootstrap/dist/css/bootstrap.min.css";
import styles from "./Checkout.module.css";

// --- Configuration ---
// In a real app, move the key to a .env file (e.g., import.meta.env.VITE_RAZORPAY_KEY_ID)
const RAZORPAY_KEY = "rzp_test_lENL2EMmm4YrZs";
const PLAN_AMOUNT = 799;

function Checkout() {
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const { user, token, login } = useAuth();

  // Load the Razorpay script when the component mounts
  useEffect(() => {
    const script = document.createElement("script");
    script.src = "https://checkout.razorpay.com/v1/checkout.js";
    script.async = true;
    document.body.appendChild(script);
  }, []);

  const handlePayment = async () => {
    /*if (!token) {
      toast.error("Please login to complete your purchase.");
      navigate("/login");
      return;
    }*

    setLoading(true);
    const toastId = toast.loading("Initiating payment...");

    try {
      // Step 1: Create a payment order on the backend
      const orderResponse = await fetch("http://localhost:5000/create-order", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ amount: PLAN_AMOUNT }),
      });

      const order = await orderResponse.json();
      if (!orderResponse.ok) {
        throw new Error(order.error || "Could not create payment order.");
      }

      toast.dismiss(toastId);

      // Step 2: Configure and open the Razorpay payment modal
      const options = {
        key: RAZORPAY_KEY,
        amount: order.amount, // Amount in paise from the backend
        currency: "INR",
        name: "TrueCheck AI Subscription",
        description: "Monthly Unlimited Access Plan",
        order_id: order.id,
        handler: async (response) => {
          const paymentToastId = toast.loading("Verifying your payment...");
          try {
            // Step 3: Securely verify the payment on the backend
            const verifyResponse = await fetch(
              "http://localhost:5000/payment-success",
              {
                method: "POST",
                headers: {
                  "Content-Type": "application/json",
                  Authorization: `Bearer ${token}`,
                },
                body: JSON.stringify({
                  razorpay_payment_id: response.razorpay_payment_id,
                  razorpay_order_id: response.razorpay_order_id,
                  razorpay_signature: response.razorpay_signature,
                }),
              }
            );

            const result = await verifyResponse.json();
            if (!verifyResponse.ok) {
              throw new Error(result.error || "Payment verification failed.");
            }

            // Step 4: Update the global state and redirect
            toast.dismiss(paymentToastId);
            toast.success(result.message || "Payment successful!");
            login(result.user, token); // Update context with fresh user data from the API
            navigate("/");
          } catch (error) {
            toast.dismiss(paymentToastId);
            toast.error(error.message);
          }
        },
        prefill: {
          name: user?.username || "Valued User",
          email: user?.email,
        },
        theme: {
          color: "#3399cc",
        },
        modal: {
          ondismiss: () => {
            // Handle the case where the user closes the payment modal
            toast.error("Payment was cancelled.");
          },
        },
      };

      const rzp = new window.Razorpay(options);
      rzp.open();
    } catch (error) {
      toast.dismiss(toastId);
      toast.error(error.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={styles.containerpy5}>
      <div className={styles.rowjustify}>
        <div className={styles.cardbody}>
          <div className={styles.text}>
            <h2>Checkout</h2>
          </div>
          <hr />
          <div className={styles.bill}>
            <h5>Order Summary</h5>
            <ul className={styles.listgroup}>
              <li className="list-group-item d-flex justify-content-between">
                <span>
                  TrueCheck AI License <strong>₹{PLAN_AMOUNT}</strong>
                </span>
              </li>
              <li className="list-group-item d-flex justify-content-between">
                <span className="fw-bold">Total</span>
                <strong className={styles.textsuccess}>₹{PLAN_AMOUNT}</strong>
              </li>
            </ul>
          </div>
          <div className={styles.btn}>
            <button
              onClick={handlePayment}
              disabled={loading} // Disable button while loading
              className={`${styles.btn1} btn btn-success btn-lg rounded-pill`}
            >
              {loading ? "Processing..." : "Pay Now"}
            </button>
          </div>
          <p className={styles.raz}>
            🔒 100% secure payment powered by Razorpay
          </p>
        </div>
      </div>
    </div>
  );
}

export default Checkout;*/
