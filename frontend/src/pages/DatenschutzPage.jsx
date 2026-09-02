/** Privacy policy. The "Verantwortlicher" section needs the same operator
 *  details as ImpressumPage — fill in both together. The rest describes
 *  actual data flows (see CLAUDE.md: passwordless auth, localStorage
 *  collections, SMTP mailer) rather than generic boilerplate. */
export default function DatenschutzPage() {
  return (
    <div className="impressum-page">
      <h1>Datenschutzerklärung</h1>

      <h2 className="section-title">Verantwortlicher</h2>
      <p>
        [Vor- und Nachname bzw. Firmenname]
        <br />
        [Straße und Hausnummer]
        <br />
        [PLZ und Ort]
        <br />
        E-Mail: [E-Mail-Adresse]
      </p>

      <h2 className="section-title">Server-Logs</h2>
      <p>
        Beim Aufruf von sizehive werden durch den Hosting-Anbieter automatisch technische
        Zugriffsdaten erfasst (z. B. IP-Adresse, Zeitpunkt, aufgerufene Seite), wie es bei jedem
        Webserver-Betrieb notwendig ist. Diese Daten dienen ausschließlich der Betriebssicherheit
        und werden nicht mit anderen Datenquellen zusammengeführt.
      </p>

      <h2 className="section-title">Lokale Speicherung im Browser</h2>
      <p>
        Merkliste, gespeicherte Suchen, zuletzt angesehene Artikel und die Vergleichsliste werden
        ohne Konto ausschließlich lokal in Ihrem Browser gespeichert (localStorage) und nicht an
        unsere Server übertragen. Sie können diese Daten jederzeit über die Funktionen der
        jeweiligen Seite oder über die Browsereinstellungen löschen.
      </p>

      <h2 className="section-title">Konto, Login und Benachrichtigungen</h2>
      <p>
        Der Login erfolgt passwortlos per Magic-Link: Wir speichern dabei nur einen Hash Ihres
        Login- bzw. Sitzungs-Tokens, niemals den Token selbst im Klartext. Ihre E-Mail-Adresse
        verwenden wir ausschließlich, um Ihnen den Login-Link sowie von Ihnen eingerichtete
        Preisalarme und Suchagenten-Benachrichtigungen zuzustellen. Eine Weitergabe an Dritte
        findet nicht statt.
      </p>

      <h2 className="section-title">Cookies</h2>
      <p>
        Nach dem Login setzen wir ein technisch notwendiges Session-Cookie (httpOnly), um Sie
        eingeloggt zu halten. Es dient keinen Analyse- oder Marketingzwecken und wird nicht an
        Dritte übermittelt.
      </p>

      <h2 className="section-title">Partner-Shops und Affiliate-Links</h2>
      <p>
        Produktdaten (Preise, Bilder, Verfügbarkeit) beziehen wir automatisiert aus den
        Datenfeeds angeschlossener Partner-Shops. Klicks auf "Zum Shop ↗" führen über
        Affiliate-Links zum jeweiligen Shop; dort gilt dessen eigene Datenschutzerklärung.
      </p>

      <h2 className="section-title">Ihre Rechte</h2>
      <p>
        Sie haben das Recht auf Auskunft, Berichtigung, Löschung und Einschränkung der
        Verarbeitung Ihrer personenbezogenen Daten sowie auf Datenübertragbarkeit. Wenden Sie
        sich dazu an die oben genannte Kontaktadresse.
      </p>
    </div>
  );
}
