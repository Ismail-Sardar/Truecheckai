import {
  //BrowserRouter as Router,
  Routes,
  Route,
  useLocation,
} from "react-router-dom";
import { Toaster } from "react-hot-toast";

import Header from "./assets/components/header";
import Home from "./assets/components/home";
import Pricing from "./assets/components/pricing";
import Login from "./assets/components/login";
import Signup from "./assets/components/signup";
import Footer from "./assets/components/footer";
import Checkout from "./checkout";
import Result from "./assets/components/result";

function AppContent() {
  const location = useLocation();

  const hideHeader =
    location.pathname === "/checkout" ||
    location.pathname === "/signup" ||
    location.pathname === "/login";

  const hideFooter =
    location.pathname === "/pricing" ||
    location.pathname === "/login" ||
    location.pathname === "/signup" ||
    location.pathname === "/checkout" ||
    location.pathname === "/result";

  return (
    <>
      {!hideHeader && <Header />}
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/pricing" element={<Pricing />} />
        <Route path="/login" element={<Login />} />
        <Route path="/signup" element={<Signup />} />
        <Route path="/checkout" element={<Checkout />} />
        <Route path="/result" element={<Result />} />
      </Routes>
      {!hideFooter && <Footer />}
    </>
  );
}

function App() {
  return (
    <>
      <Toaster position="top-center" />
      <AppContent />
    </>
  );
}

export default App;
