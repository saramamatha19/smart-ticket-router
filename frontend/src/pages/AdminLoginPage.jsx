// React hooks
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { LogIn } from "lucide-react";

// Components
import Spinner from "../components/Spinner";

// Auth
import { useAuth } from "../context/useAuth";

// Admin login form -- the only account is the one hardcoded in the
// backend's .env (ADMIN_USERNAME / ADMIN_PASSWORD).
function AdminLoginPage() {

  const { login } = useAuth();
  const navigate = useNavigate();

  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {

    e.preventDefault();
    setError("");
    setLoading(true);

    try {

      await login(username, password);
      navigate("/admin", { replace: true });

    } catch (err) {

      console.error(err);
      setError("Incorrect username or password.");

    } finally {

      setLoading(false);

    }

  };

  return (

    <div className="login-page">
      <div className="card login-card">

        <h2>Admin Login</h2>

        <form onSubmit={handleSubmit}>

          <div className="form-field">
            <label htmlFor="username">Username</label>
            <input
              id="username"
              type="text"
              value={username}
              disabled={loading}
              onChange={(e) => setUsername(e.target.value)}
              autoFocus
            />
          </div>

          <div className="form-field">
            <label htmlFor="password">Password</label>
            <input
              id="password"
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

      </div>
    </div>

  );
}

export default AdminLoginPage;
