// React hooks
import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { UserPlus } from "lucide-react";

// Components
import Spinner from "../components/Spinner";

// Auth
import { useCustomerAuth } from "../context/useCustomerAuth";

// Customer sign-up form. Registering logs the customer straight in
// (the backend returns a token immediately), matching login's behavior.
function CustomerRegisterPage() {

  const { register } = useCustomerAuth();
  const navigate = useNavigate();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {

    e.preventDefault();
    setError("");

    if (password.length < 8) {
      setError("Password must be at least 8 characters.");
      return;
    }

    if (password !== confirmPassword) {
      setError("Passwords do not match.");
      return;
    }

    setLoading(true);

    try {

      await register(email, password);
      navigate("/", { replace: true });

    } catch (err) {

      console.error(err);

      if (err.response?.status === 409) {
        setError("An account with this email already exists.");
      } else {
        setError("Could not create your account. Please try again.");
      }

    } finally {

      setLoading(false);

    }

  };

  return (

    <div className="login-page">
      <div className="card login-card">

        <h2>Create an Account</h2>

        <form onSubmit={handleSubmit}>

          <div className="form-field">
            <label htmlFor="register-email">Email</label>
            <input
              id="register-email"
              type="text"
              value={email}
              disabled={loading}
              onChange={(e) => setEmail(e.target.value)}
              autoFocus
            />
          </div>

          <div className="form-field">
            <label htmlFor="register-password">Password</label>
            <input
              id="register-password"
              type="password"
              value={password}
              disabled={loading}
              onChange={(e) => setPassword(e.target.value)}
            />
          </div>

          <div className="form-field">
            <label htmlFor="register-confirm-password">Confirm Password</label>
            <input
              id="register-confirm-password"
              type="password"
              value={confirmPassword}
              disabled={loading}
              onChange={(e) => setConfirmPassword(e.target.value)}
            />
          </div>

          {error && <p className="field-error">{error}</p>}

          <button type="submit" className="btn-primary" disabled={loading}>
            {loading ? (
              <>
                <Spinner size={16} /> Creating account...
              </>
            ) : (
              <>
                <UserPlus size={16} /> Sign Up
              </>
            )}
          </button>

        </form>

        <p className="auth-switch">
          Already have an account? <Link to="/login">Log in</Link>
        </p>

      </div>
    </div>

  );
}

export default CustomerRegisterPage;
