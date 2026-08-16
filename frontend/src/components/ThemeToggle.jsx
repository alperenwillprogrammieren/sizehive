import { setTheme, useTheme } from "../theme";

const OPTIONS = [
  { value: "system", label: "Auto", title: "Systemeinstellung folgen" },
  { value: "light", label: "Hell", title: "Helles Design" },
  { value: "dark", label: "Dunkel", title: "Dunkles Design" },
];

export default function ThemeToggle() {
  const theme = useTheme();

  return (
    <div className="theme-toggle" role="group" aria-label="Farbschema">
      {OPTIONS.map((option) => (
        <button
          key={option.value}
          type="button"
          title={option.title}
          aria-pressed={theme === option.value}
          className={`theme-option${theme === option.value ? " active" : ""}`}
          onClick={() => setTheme(option.value)}
        >
          {option.label}
        </button>
      ))}
    </div>
  );
}
