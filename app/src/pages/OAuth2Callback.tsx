import { useParams, useNavigate } from "react-router-dom";
import { useEffect } from "react";

const OAuth2Callback = () => {
  const { user_email } = useParams();
  const navigate = useNavigate();

  useEffect(() => {
    if (user_email) {
      // Store the user email in session storage
      sessionStorage.setItem("user_email", user_email);

      // Redirect to the homepage
      navigate("/home");
    }
  }, [user_email, navigate]);

  return (
    <div>
      <h1>Processing...</h1>
      <p>Redirecting to your homepage...</p>
    </div>
  );
};

export default OAuth2Callback;
