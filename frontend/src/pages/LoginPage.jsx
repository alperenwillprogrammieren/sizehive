import { useEffect, useRef, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { auth } from "../api";
import { useAuth } from "../authContext";

export default function LoginPage() {
  const [searchParams] = useSearchParams();
  const token = searchParams.get("token");
  const navigate = useNavigate();
  const { user, refresh } = useAuth();

  const [email, setEmail] = useState("");
  const [state, setState] = useState(token ? "verifying" : "idle");
  const [error, setError] = useState(null);
  const verified = useRef(false);

  useEffect(() => {
    // StrictMode mounts effects twice in dev; the token is single-use, so a
    // second verify would fail against a token the first call just burned.
    if (!token || verified.current) return;
    verified.current = true;

    auth
      .verify(token)
      .then(async () => {
        await refresh();
        setState("done");
        navigate("/konto", { replace: true });
      })
      .catch(() => {
        setState("idle");
        setError("Dieser Login-Link ist ungültig oder abgelaufen. Fordere einen neuen an.");
      });
  }, [token, refresh, navigate]);

  if (user) {
    return (
      <div className="auth-page">
        <h1>Angemeldet</h1>
        <p className="tagline">Du bist als {user.email} angemeldet.</p>
      </div>
    );
  }

  if (state === "verifying") {
    return <div className="status-message">Login wird geprüft…</div>;
  }

  return (
    <div className="auth-page">
      <h1>Anmelden</h1>
      <p className="tagline">
        Ohne Passwort: Du bekommst einen Anmeldelink per E-Mail. Ein Konto brauchst du nur für Preisalarme,
        Suchagenten und eine geräteübergreifende Merkliste.
      </p>

      {state === "sent" ? (
        <div className="auth-sent">
          Wenn es zu dieser Adresse ein Konto gibt oder gerade angelegt wurde, ist der Anmeldelink unterwegs.
          Er gilt 20 Minuten.
        </div>
      ) : (
        <form
          className="auth-form"
          onSubmit={async (event) => {
            event.preventDefault();
            setError(null);
            try {
              await auth.requestLink(email);
              setState("sent");
            } catch (err) {
              setError(
                err.status === 422
                  ? "Das sieht nicht nach einer gültigen E-Mail-Adresse aus."
                  : "Der Anmeldelink konnte nicht angefordert werden."
              );
            }
          }}
        >
          <label htmlFor="login-email">E-Mail-Adresse</label>
          <input
            id="login-email"
            type="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="du@example.com"
          />
          <button type="submit" className="primary-button">
            Anmeldelink schicken
          </button>
        </form>
      )}

      {error && <div className="auth-error">{error}</div>}
    </div>
  );
}
