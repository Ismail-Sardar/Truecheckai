/*import { Link } from "react-router-dom";
import styles from "./Header.module.css";
import { RiSearchEyeLine } from "react-icons/ri";

function Header() {
  return (
    <header id="header" className={styles.head}>
      <div className={styles.logo}>
        <div>TrueCheckai</div>
        <RiSearchEyeLine className={styles.icon} />
      </div>
      <div className={styles.navcon}>
        <a href="#contents">Home</a>
        <a href="#Features">Feature</a>
        <Link to="/pricing">Pricing</Link>
        <a href="#">About</a>
        <button className={styles.login}>Login</button>
      </div>
    </header>
  );
}

export default Header;*/

/*import { Link, useNavigate, useLocation } from "react-router-dom";
import styles from "./Header.module.css";
import { RiSearchEyeLine } from "react-icons/ri";
import { jwtDecode } from "jwt-decode";
import { useState, useEffect } from "react";

function Header() {
  const navigate = useNavigate();
  const location = useLocation();
  const [user, setUser] = useState(null);

  // Load user from localStorage on mount
  useEffect(() => {
    const token = localStorage.getItem("google_token");
    if (token) {
      try {
        const decoded = jwtDecode(token);

        setUser(decoded);
      } catch (err) {
        console.error("Invalid token", err);
      }
    }
  }, []);

  const handleAnchorClick = (e, id) => {
    e.preventDefault();

    if (location.pathname !== "/") {
      navigate("/");
      setTimeout(() => {
        document.getElementById(id)?.scrollIntoView({ behavior: "smooth" });
      }, 100);
    } else {
      document.getElementById(id)?.scrollIntoView({ behavior: "smooth" });
    }
  };

  const handleLoginClick = () => {
    navigate("/signup");
  };

  const handleLogout = () => {
    localStorage.removeItem("google_token");
    setUser(null);
    navigate("/");
  };

  return (
    <header className={styles.head}>
      <div className={styles.logo}>
        <div>TrueCheckai</div>
        <RiSearchEyeLine className={styles.icon} />
      </div>
      <div className={styles.navcon}>
        <a href="/#contents" onClick={(e) => handleAnchorClick(e, "contents")}>
          Home
        </a>
        <a href="/#features" onClick={(e) => handleAnchorClick(e, "features")}>
          Features
        </a>
        <Link to="/pricing">Pricing</Link>
        <a href="/#about" onClick={(e) => handleAnchorClick(e, "about")}>
          About
        </a>

        {user ? (
          <>
            <img
              src={user.picture}
              alt="profile"
              style={{
                width: "35px",
                borderRadius: "50%",
                marginRight: "10px",
              }}
            />
            <button onClick={handleLogout} className={styles.login}>
              Logout
            </button>
          </>
        ) : (
          <button onClick={handleLoginClick} className={styles.login}>
            Signup
          </button>
        )}
      </div>
    </header>
  );
}

export default Header;
*/

/*import { Link, useNavigate, useLocation } from "react-router-dom";
import styles from "./Header.module.css";
import { RiSearchEyeLine } from "react-icons/ri";

import { useAuth } from "../../context/AuthContext.jsx";
function Header() {
  const navigate = useNavigate();
  const location = useLocation();

  // ✅ 2. Get everything from the AuthContext instead of local state
  const { isAuthenticated, user, credits, logout } = useAuth();

  const handleAnchorClick = (e, id) => {
    e.preventDefault();

    if (location.pathname !== "/") {
      navigate("/");
      setTimeout(() => {
        document.getElementById(id)?.scrollIntoView({ behavior: "smooth" });
      }, 100);
    } else {
      document.getElementById(id)?.scrollIntoView({ behavior: "smooth" });
    }
  };

  return (
    <header className={styles.head}>
      <div className={styles.logo}>
        <div>TrueCheckai</div>
        <RiSearchEyeLine className={styles.icon} />
      </div>
      <div className={styles.navcon}>
        <a href="/#contents" onClick={(e) => handleAnchorClick(e, "contents")}>
          Home
        </a>
        <a href="/#features" onClick={(e) => handleAnchorClick(e, "features")}>
          Features
        </a>
        <Link to="/pricing">Pricing</Link>
        <a href="/#about" onClick={(e) => handleAnchorClick(e, "about")}>
          About
        </a>

        {/* ✅ 3. Use isAuthenticated for cleaner conditional logic *
        {isAuthenticated ? (
          <>
            <span style={{ color: "white", marginRight: "10px" }}>
              Credits: {credits}
            </span>
            <img
              src={user.picture}
              alt="profile"
              style={{
                width: "35px",
                height: "35px",
                borderRadius: "50%",
                marginRight: "10px",
              }}
            />
            <button onClick={logout} className={styles.login}>
              Logout
            </button>
          </>
        ) : (
          <button onClick={() => navigate("/signup")} className={styles.login}>
            Signup
          </button>
        )}
      </div>
    </header>
  );
}

export default Header;*/

// src/components/Header.jsx

import { Link, useNavigate, useLocation } from "react-router-dom";
import styles from "./Header.module.css";
import { RiSearchEyeLine } from "react-icons/ri";
import { useState } from "react"; // 1. useState import karein
import { useAuth } from "../../context/AuthContext.jsx";

function Header() {
  const navigate = useNavigate();
  const location = useLocation();
  //const { isAuthenticated, user, credits, logout } = useAuth();
  const { isAuthenticated, user, isSubscribed, credits, logout } = useAuth(); // isSubscribed ko lein

  const [isDropdownOpen, setIsDropdownOpen] = useState(false);

  const handleAnchorClick = (e, id) => {
    e.preventDefault();
    if (location.pathname !== "/") {
      navigate("/");
      setTimeout(() => {
        document.getElementById(id)?.scrollIntoView({ behavior: "smooth" });
      }, 100);
    } else {
      document.getElementById(id)?.scrollIntoView({ behavior: "smooth" });
    }
  };

  return (
    <header className={styles.head}>
      <div className={styles.logo}>
        <div>TrueCheckai</div>
        <RiSearchEyeLine className={styles.icon} />
      </div>
      <div className={styles.navcon}>
        <a href="/" onClick={(e) => handleAnchorClick(e, "contents")}>
          Home
        </a>
        <a href="/#features" onClick={(e) => handleAnchorClick(e, "features")}>
          Features
        </a>
        <Link to="/pricing">Pricing</Link>
        <a href="/#about" onClick={(e) => handleAnchorClick(e, "about")}>
          About
        </a>

        {isAuthenticated ? (
          <div className={styles.profileContainer}>
            <span className={styles.credits}>
              {isSubscribed ? "✨ Unlimited" : `Credits: ${user.credits}`}
            </span>

            {user.picture ? (
              <img
                src={user.picture}
                alt="profile"
                className={styles.profilePic}
                onClick={() => setIsDropdownOpen(!isDropdownOpen)}
              />
            ) : (
              <div
                className={styles.profileInitial}
                onClick={() => setIsDropdownOpen(!isDropdownOpen)}
              >
                {user.username?.charAt(0).toUpperCase()}
              </div>
            )}

            {isDropdownOpen && (
              <div className={styles.dropdownMenu}>
                <div className={styles.dropdownInfo}>
                  Signed in as <br /> <strong>{user.username}</strong>
                </div>
                <hr className={styles.dropdownDivider} />
                <button
                  onClick={() => {
                    logout();
                    setIsDropdownOpen(false);
                    navigate("/");
                  }}
                >
                  Logout
                </button>
              </div>
            )}
          </div>
        ) : (
          <button onClick={() => navigate("/signup")} className={styles.login}>
            Signup
          </button>
        )}
      </div>
    </header>
  );
}

export default Header;

/*import { Link, useNavigate, useLocation } from "react-router-dom";
import styles from "./Header.module.css";
import { RiSearchEyeLine } from "react-icons/ri";
import { useState, useRef, useEffect } from "react"; // 1. useRef and useEffect import karein
import { useAuth } from "../../context/AuthContext.jsx";

function Header() {
  const navigate = useNavigate();
  const location = useLocation();
  const { user, isSubscribed, logout } = useAuth();

  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const dropdownRef = useRef(null); // 2. Dropdown ke liye ek ref banayein

  const handleAnchorClick = (e, id) => {
    e.preventDefault();
    if (location.pathname !== "/") {
      navigate("/");
      setTimeout(() => {
        document.getElementById(id)?.scrollIntoView({ behavior: "smooth" });
      }, 100);
    } else {
      document.getElementById(id)?.scrollIntoView({ behavior: "smooth" });
    }
  };

  // 3. Dropdown ke bahar click karne par use band karne ka logic
  useEffect(() => {
    function handleClickOutside(event) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsDropdownOpen(false);
      }
    }
    // Event listener add karein
    document.addEventListener("mousedown", handleClickOutside);
    return () => {
      // Cleanup: component unmount hone par listener hata dein
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, [dropdownRef]);

  return (
    <header className={styles.head}>
      <div className={styles.logo}>
        <Link to="/" className={styles.logoLink}>
          TrueCheckai
          <RiSearchEyeLine className={styles.icon} />
        </Link>
      </div>
      <div className={styles.navcon}>
        <a href="/#contents" onClick={(e) => handleAnchorClick(e, "contents")}>
          Home
        </a>
        <a href="/#features" onClick={(e) => handleAnchorClick(e, "features")}>
          Features
        </a>
        <Link to="/pricing">Pricing</Link>
        <a href="/#about" onClick={(e) => handleAnchorClick(e, "about")}>
          About
        </a>

        {user ? (
          // 4. ref ko container mein attach karein
          <div className={styles.profileContainer} ref={dropdownRef}>
            {/* ✅ UPDATED LOGIC: Subscribed user ke liye "Unlimited" dikhayein *
            <span className={styles.credits}>
              {isSubscribed ? "✨ Unlimited" : `Credits: ${user.credits}`}
            </span>

            {/* ✅ UPDATED LOGIC: Agar profile picture nahi hai toh initial dikhayein *
            {user.picture ? (
              <img
                src={user.picture}
                alt="profile"
                className={styles.profilePic}
                onClick={() => setIsDropdownOpen(!isDropdownOpen)}
              />
            ) : (
              <div
                className={styles.profileInitial}
                onClick={() => setIsDropdownOpen(!isDropdownOpen)}
              >
                {user.username?.charAt(0).toUpperCase()}
              </div>
            )}

            {isDropdownOpen && (
              <div className={styles.dropdownMenu}>
                <div className={styles.dropdownInfo}>
                  Signed in as <br /> <strong>{user.username}</strong>
                </div>
                <hr className={styles.dropdownDivider} />
                <button
                  onClick={() => {
                    logout();
                    setIsDropdownOpen(false);
                  }}
                >
                  Logout
                </button>
              </div>
            )}
          </div>
        ) : (
          <div className={styles.authButtons}>
            <button onClick={() => navigate("/login")} className={styles.login}>
              Login
            </button>
            <button
              onClick={() => navigate("/signup")}
              className={styles.signup}
            >
              Signup
            </button>
          </div>
        )}
      </div>
    </header>
  );
}

export default Header;
*/
