/*import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import "./index.css";
import App from "./App.jsx";
import "bootstrap/dist/css/bootstrap.min.css";

createRoot(document.getElementById("root")).render(
  <StrictMode>
    <App />
  </StrictMode>
);
*/

/*import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import App from "./App";
import { AuthProvider } from "./assets/components/AuthContext.jsx";
import { GoogleOAuthProvider } from "@react-oauth/google";

const clientId =
  "813989156011-6aht2rsbeqq09qvqeushsv3rnpbr8bv2.apps.googleusercontent.com";

ReactDOM.createRoot(document.getElementById("root")).render(
  <GoogleOAuthProvider clientId={clientId}>
    <AuthProvider>
      <BrowserRouter>
        <App />
      </BrowserRouter>
    </AuthProvider>
  </GoogleOAuthProvider>
);
*/

// main.jsx (after fix)
import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom"; // Add this import
import { AuthProvider } from "./context/AuthContext.jsx";
import App from "./App.jsx";
import { GoogleOAuthProvider } from "@react-oauth/google";
/*const clientId =
  "813989156011-6aht2rsbeqq09qvqeushsv3rnpbr8bv2.apps.googleusercontent.com";*/
const clientId =
  import.meta.env.VITE_GOOGLE_CLIENT_ID ||
  "813989156011-6aht2rsbeqq09qvqeushsv3rnpbr8bv2.apps.googleusercontent.com";
ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <GoogleOAuthProvider clientId={clientId}>
      <BrowserRouter>
        {" "}
        {/* Wrap everything here */}
        <AuthProvider>
          <App />
        </AuthProvider>
      </BrowserRouter>
    </GoogleOAuthProvider>
  </React.StrictMode>
);
