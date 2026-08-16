import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { account } from "../api";
import { useAuth } from "../authContext";

/** Price alert for one variant. Two modes: a concrete target price, or
 *  "any record low" — the alert counterpart to the all-time-low flag on the
 *  Deals page. */
export default function PriceAlertBox({ variantId, currentPrice }) {
  const { user } = useAuth();
  const [alert, setAlert] = useState(null);
  const [target, setTarget] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);

  const load = useCallback(async () => {
    if (!user) return;
    try {
      const data = await account.alerts();
      const existing = data.alerts.find((entry) => entry.variant_id === variantId) || null;
      setAlert(existing);
      setTarget(existing?.target_price_eur != null ? String(existing.target_price_eur) : "");
    } catch (err) {
      console.error(err);
    }
  }, [user, variantId]);

  useEffect(() => {
    load();
  }, [load]);

  if (!user) {
    return (
      <div className="alert-box muted">
        <Link to="/login">Melde dich an</Link>, um für diesen Artikel einen Preisalarm zu setzen.
      </div>
    );
  }

  const save = async (targetEur) => {
    setBusy(true);
    setError(null);
    try {
      const created = await account.createAlert(variantId, targetEur);
      setAlert(created);
      setTarget(created.target_price_eur != null ? String(created.target_price_eur) : "");
    } catch (err) {
      setError(err.detail || "Der Preisalarm konnte nicht gespeichert werden.");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="alert-box">
      <div className="alert-title">Preisalarm</div>

      {alert ? (
        <div className="alert-active">
          {alert.target_price_eur != null
            ? `Aktiv: Wir melden uns, sobald der Preis auf ${alert.target_price_eur.toFixed(2)} € oder darunter fällt.`
            : "Aktiv: Wir melden uns bei jedem neuen Tiefstpreis."}
          {alert.last_notified_at && (
            <span className="alert-note">
              {" "}
              Zuletzt benachrichtigt am {new Date(alert.last_notified_at).toLocaleDateString("de-DE")}.
            </span>
          )}
        </div>
      ) : (
        <p className="alert-note">
          Wir schicken dir eine E-Mail, sobald der Preis fällt — höchstens einmal je neuem Tiefstand.
        </p>
      )}

      <div className="alert-controls">
        <label>
          Zielpreis
          <input
            type="number"
            min="0"
            step="0.01"
            value={target}
            placeholder={(currentPrice * 0.9).toFixed(2)}
            onChange={(e) => setTarget(e.target.value)}
          />
          €
        </label>
        <button
          type="button"
          className="primary-button"
          disabled={busy || target === "" || Number(target) <= 0}
          onClick={() => save(Number(target))}
        >
          {alert?.target_price_eur != null ? "Zielpreis ändern" : "Alarm setzen"}
        </button>
        <button type="button" className="text-button" disabled={busy} onClick={() => save(null)}>
          Nur bei neuem Tiefstpreis
        </button>
        {alert && (
          <button
            type="button"
            className="text-button"
            disabled={busy}
            onClick={async () => {
              setBusy(true);
              try {
                await account.deleteAlert(variantId);
                setAlert(null);
                setTarget("");
              } finally {
                setBusy(false);
              }
            }}
          >
            Alarm entfernen
          </button>
        )}
      </div>

      {error && <div className="auth-error">{error}</div>}
    </div>
  );
}
