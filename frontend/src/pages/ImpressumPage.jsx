/** Legal notice required under TMG §5. Placeholder content — fill in real
 *  operator details before the site goes live publicly. */
export default function ImpressumPage() {
  return (
    <div className="impressum-page">
      <h1>Impressum</h1>

      <h2 className="section-title">Angaben gemäß § 5 TMG</h2>
      <p>
        [Vor- und Nachname bzw. Firmenname]
        <br />
        [Straße und Hausnummer]
        <br />
        [PLZ und Ort]
        <br />
        [Land]
      </p>

      <h2 className="section-title">Kontakt</h2>
      <p>
        E-Mail: [E-Mail-Adresse]
        <br />
        Telefon: [optional]
      </p>

      <h2 className="section-title">Verantwortlich für den Inhalt nach § 18 Abs. 2 MStV</h2>
      <p>[Name und Anschrift wie oben, falls abweichend angeben]</p>

      <p className="impressum-beta-note">
        sizehive befindet sich derzeit in der Beta-Phase. Inhalte, Preise und Verfügbarkeiten
        werden automatisiert aus Partner-Shops übernommen und können Fehler enthalten.
      </p>
    </div>
  );
}
