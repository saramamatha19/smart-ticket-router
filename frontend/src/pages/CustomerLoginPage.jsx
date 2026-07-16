// React hooks
import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { LogIn } from "lucide-react";

// Components
import Spinner from "../components/Spinner";

// Auth
import { useCustomerAuth } from "../context/useCustomerAuth";

// Customer login form -- log in to submit tickets and see your own
// ticket history. New here? See CustomerRegisterPage.
function CustomerLoginPage() {

  const { login } = useCustomerAuth();
  const navigate = useNavigate();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {

    e.preventDefault();
    setError("");
    setLoading(true);

    try {

      await login(email, password);
      navigate("/", { replace: true });

    } catch (err) {

      console.error(err);
      setError("Incorrect email or password.");

    } finally {

      setLoading(false);

    }

  };

  return (

    <div className="login-page">
      <div className="card login-card">

        <h2>Log In</h2>

        <form onSubmit={handleSubmit}>

          <div className="form-field">
            <label htmlFor="customer-email">Email</label>
            <input
              id="customer-email"
              type="text"
              value={email}
              disabled={loading}
              onChange={(e) => setEmail(e.target.value)}
              autoFocus
            />
          </div>

          <div className="form-field">
            <label htmlFor="customer-password">Password</label>
            <input
              id="customer-password"
              type="password"
              value={password}
              disabled={loading}
              onChange={(e) => setPassword(e.target.value)}
            />
          </div>

          {error && <p className="field-error">{error}</p>}

          <button type="submit" className="btn-primary" disabled={loading}>
            {loading ? (
              <>
                <Spinner size={16} /> Logging in...
              </>
            ) : (
              <>
                <LogIn size={16} /> Log In
              </>
            )}
          </button>

        </form>

        <p className="auth-switch">
          Don&apos;t have an account? <Link to="/register">Sign up</Link>
        </p>

      </div>
    </div>

  );
}

export default CustomerLoginPage;
