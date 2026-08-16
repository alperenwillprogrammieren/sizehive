import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { account } from "../api";
import { useAuth } from "../authContext";
import { useVariantsByIds } from "../useVariants";

function formatDate(iso) {
  return iso ? new Date(iso).toLocaleDateString("de-DE") : "—";
}

function AlertList({ alerts, onDelete }) {
  const { items } = useVariantsByIds(alerts.map((a) => a.variant_id));
  const byId = new Map(items.map((item) => [item.variant_id, item]));

  if (alerts.length === 0) {
    return (
      <p className="tagline">
        Noch keine Preisalarme. Du setzt sie auf der Seite eines Artikels — <Link to="/deals">bei den Deals</Link>{" "}
        findest du Kandidaten.
      </p>
    );
  }

  return (
    <ul className="account-list">
      {alerts.map((alert) => {
        const item = byId.get(alert.variant_id);
        return (
          <li key={alert.id}>
            <div className="account-item-main">
              <Link to={`/product/${alert.variant_id}`} className="account-item-title">
                {item ? `${item.brand} ${item.model_name}` : `Variante ${alert.variant_id}`}
              </Link>
              <span className="account-item-note">
                {alert.target_price_eur != null
                  ? `Ziel: ${alert.target_price_eur.toFixed(2)} €`
                  : "bei jedem neuen Tiefstpreis"}
                {item && ` · aktuell ${item.price_eur.toFixed(2)} €`}
                {alert.last_notified_at && ` · zuletzt gemeldet ${formatDate(alert.last_notified_at)}`}
              </span>
            </div>
            <button type="button" className="text-button" onClick={() => onDelete(alert.variant_id)}>
              Entfernen
            </button>
          </li>
        );
      })}
    </ul>
  );
}

export default function AccountPage() {
  const { user, loading, signOut } = useAuth();
  const [alerts, setAlerts] = useState([]);
  const [agents, setAgents] = useState([]);

  const load = useCallback(async () => {
    if (!user) return;
    try {
      const [alertData, agentData] = await Promise.all([account.alerts(), account.agents()]);
      setAlerts(alertData.alerts);
      setAgents(agentData.agents);
    } catch (err) {
      console.error(err);
    }
  }, [user]);

  useEffect(() => {
    load();
  }, [load]);

  if (loading) return <div className="status-message">Lädt…</div>;

  if (!user) {
    return (
      <div className="auth-page">
        <h1>Konto</h1>
        <p className="tagline">
          <Link to="/login">Melde dich an</Link>, um Preisalarme und Suchagenten zu verwalten.
        </p>
      </div>
    );
  }

  return (
    <div className="account-page">
      <div className="page-header">
        <div>
          <h1>Konto</h1>
          <p className="tagline">Angemeldet als {user.email}</p>
        </div>
        <button type="button" className="text-button" onClick={signOut}>
          Abmelden
        </button>
      </div>

      <h2 className="section-title">Preisalarme</h2>
      <AlertList
        alerts={alerts}
        onDelete={async (variantId) => {
          await account.deleteAlert(variantId);
          await load();
        }}
      />

      <h2 className="section-title">Suchagenten</h2>
      <p className="tagline">
        Ein Suchagent meldet ausschließlich Angebote, die <em>nach</em> seiner Einrichtung neu dazugekommen sind —
        nie den Bestand.
      </p>
      {agents.length === 0 ? (
        <p className="tagline">
          Noch keine Suchagenten. In der <Link to="/">Suche</Link> kannst du eine gespeicherte Suche zum Agenten
          machen.
        </p>
      ) : (
        <ul className="account-list">
          {agents.map((agent) => (
            <li key={agent.id}>
              <div className="account-item-main">
                <Link to={`/?${agent.query}`} className="account-item-title">
                  {agent.name}
                </Link>
                <span className="account-item-note">
                  zuletzt geprüft: {formatDate(agent.last_run_at)}
                </span>
              </div>
              <button
                type="button"
                className="text-button"
                onClick={async () => {
                  await account.deleteAgent(agent.id);
                  await load();
                }}
              >
                Entfernen
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
