import { useEffect, useId, useRef, useState } from "react";
import { fetchSuggestions } from "../api";

const KIND_LABELS = { brand: "Marke", model: "Modell", category: "Kategorie" };

/** Search box with an autocomplete dropdown over brands, models and
 *  categories. Picking a suggestion sets the free-text term — it is a
 *  shortcut into the existing `q` filter, not a new filter dimension. */
export default function SearchSuggest({ value, onChange, onSubmit }) {
  const [suggestions, setSuggestions] = useState([]);
  const [open, setOpen] = useState(false);
  const [active, setActive] = useState(-1);
  const listId = useId();
  const boxRef = useRef(null);

  useEffect(() => {
    const term = value.trim();
    if (term.length < 2) {
      setSuggestions([]);
      return undefined;
    }

    let cancelled = false;
    const handle = setTimeout(() => {
      fetchSuggestions(term)
        .then((data) => {
          if (!cancelled) {
            setSuggestions(data.suggestions);
            setActive(-1);
          }
        })
        .catch((err) => console.error(err));
    }, 200);

    return () => {
      cancelled = true;
      clearTimeout(handle);
    };
  }, [value]);

  // Clicking anywhere else closes the list.
  useEffect(() => {
    const onDocClick = (event) => {
      if (boxRef.current && !boxRef.current.contains(event.target)) setOpen(false);
    };
    document.addEventListener("mousedown", onDocClick);
    return () => document.removeEventListener("mousedown", onDocClick);
  }, []);

  const choose = (suggestion) => {
    onChange(suggestion.value);
    onSubmit?.(suggestion.value);
    setOpen(false);
    setActive(-1);
  };

  const onKeyDown = (event) => {
    if (!open || suggestions.length === 0) return;
    if (event.key === "ArrowDown") {
      event.preventDefault();
      setActive((index) => (index + 1) % suggestions.length);
    } else if (event.key === "ArrowUp") {
      event.preventDefault();
      setActive((index) => (index <= 0 ? suggestions.length - 1 : index - 1));
    } else if (event.key === "Enter" && active >= 0) {
      event.preventDefault();
      choose(suggestions[active]);
    } else if (event.key === "Escape") {
      setOpen(false);
    }
  };

  const visible = open && suggestions.length > 0;

  return (
    <div className="search-bar" ref={boxRef}>
      <input
        type="search"
        placeholder="Suche nach Marke, Modell, Beschreibung…"
        value={value}
        role="combobox"
        aria-expanded={visible}
        aria-controls={listId}
        aria-autocomplete="list"
        aria-activedescendant={active >= 0 ? `${listId}-${active}` : undefined}
        onChange={(e) => {
          onChange(e.target.value);
          setOpen(true);
        }}
        onFocus={() => setOpen(true)}
        onKeyDown={onKeyDown}
      />

      {visible && (
        <ul className="suggest-list" id={listId} role="listbox">
          {suggestions.map((suggestion, index) => (
            <li key={`${suggestion.kind}-${suggestion.value}`}>
              <button
                type="button"
                id={`${listId}-${index}`}
                role="option"
                aria-selected={index === active}
                className={`suggest-option${index === active ? " active" : ""}`}
                onMouseEnter={() => setActive(index)}
                onClick={() => choose(suggestion)}
              >
                <span className="suggest-value">{suggestion.value}</span>
                <span className="suggest-kind">{KIND_LABELS[suggestion.kind] || suggestion.kind}</span>
                <span className="suggest-count">{suggestion.count}</span>
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
