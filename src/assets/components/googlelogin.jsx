/*import { GoogleLogin } from "@react-oauth/google";
import jwt_decode from "jwt-decode";
// This is the new, correct way
//import { jwtDecode } from "jwt-decode"; // Use curly braces {} and camelCase
function GoogleLoginButton() {
  const handleSuccess = (credentialResponse) => {
    const decoded = jwt_decode(credentialResponse.credential);
    // Corrected usage
    //const userObject = jwtDecode(credentialResponse.credential);

    const userData = {
      name: decoded.name,
      email: decoded.email,
      picture: decoded.picture, // google profile photo
    };

    // Save user info in localStorage
    localStorage.setItem("user", JSON.stringify(userData));
    window.location.href = "/"; // reload to update header
  };

  return (
    <GoogleLogin
      onSuccess={handleSuccess}
      onError={() => alert("Google login failed")}
    />
  );
}

export default GoogleLoginButton;
*/

/*import { GoogleLogin } from "@react-oauth/google";
import { jwtDecode } from "jwt-decode"; // Corrected import

function GoogleLoginButton() {
  const handleSuccess = (credentialResponse) => {
    const decoded = jwtDecode(credentialResponse.credential); // Corrected usage

    const userData = {
      name: decoded.name,
      email: decoded.email,
      picture: decoded.picture,
    };

    localStorage.setItem("user", JSON.stringify(userData));
    window.location.href = "/";
  };

  return (
    <GoogleLogin
      onSuccess={handleSuccess}
      onError={() => alert("Google login failed")}
    />
  );
}

export default GoogleLoginButton;*/

import { GoogleLogin } from "@react-oauth/google";
import axios from "axios";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../../context/AuthContext"; // Make sure this path is correct

function GoogleLoginButton() {
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSuccess = async (credentialResponse) => {
    try {
      // 1. Send Google's token to your backend
      const response = await axios.post("http://localhost:5000/google-login", {
        token: credentialResponse.credential,
      });

      // 2. Check for a successful response from your backend
      if (response.status === 200 && response.data.token) {
        // 3. Use the login function from your AuthContext to save the user and your app's token
        login(response.data.user, response.data.token);

        // 4. Navigate to the homepage
        navigate("/");
      } else {
        // Handle cases where the backend might not return a token
        alert("Login failed: Could not retrieve auth token from server.");
      }
    } catch (error) {
      console.error("Google login failed:", error);
      alert("Google login failed. Please try again.");
    }
  };

  const handleError = () => {
    console.error("Google login process failed");
    alert("Google login failed.");
  };

  return <GoogleLogin onSuccess={handleSuccess} onError={handleError} />;
}

export default GoogleLoginButton;
