import { useState } from "react";

/** Shared shell for the dashboard charts.
 *
 *  Every chart ships a table twin: the tooltip enhances, it never gates a
 *  value. The toggle lives here so both charts get it the same way.
 */
export default function ChartFrame({ title, note, tableHead, tableRows, children }) {
  const [showTable, setShowTable] = useState(false);

  return (
    <section className="chart-frame">
      <div className="chart-frame-head">
        <div>
          <h3 className="chart-title">{title}</h3>
          {note && <p className="coverage-note">{note}</p>}
        </div>
        <button type="button" className="text-button" onClick={() => setShowTable((shown) => !shown)}>
          {showTable ? "Diagramm zeigen" : "Als Tabelle"}
        </button>
      </div>

      {showTable ? (
        <div className="chart-table-wrap">
          <table className="data-table">
            <thead>
              <tr>
                {tableHead.map((head) => (
                  <th key={head}>{head}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {tableRows.map((row, index) => (
                <tr key={row[0] + index}>
                  {row.map((cell, cellIndex) => (
                    <td key={cellIndex} className={cellIndex === 0 ? "" : "num"}>
                      {cell}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        children
      )}
    </section>
  );
}
