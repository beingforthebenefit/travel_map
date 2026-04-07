import { STYLES } from "../lib/constants";

interface Props {
  active: string;
  hasApiKey: boolean;
  onSelect: (style: string) => void;
}

const STYLE_COLORS: Record<string, string> = {
  watercolor: "from-amber-100 to-sky-100",
  toner: "from-gray-100 to-gray-300",
  terrain: "from-green-100 to-amber-100",
  positron: "from-gray-50 to-blue-50",
  dark: "from-gray-800 to-gray-900",
  osm: "from-green-50 to-yellow-50",
};

export function StylePicker({ active, hasApiKey, onSelect }: Props) {
  return (
    <div className="grid grid-cols-3 gap-2">
      {STYLES.map((style) => {
        const disabled = style.requiresApiKey && !hasApiKey;
        const selected = active === style.name;
        return (
          <button
            key={style.name}
            className={`relative rounded-lg p-1 border-2 transition-all ${
              selected
                ? "border-blue-500 ring-2 ring-blue-200"
                : "border-transparent hover:border-gray-300"
            } ${disabled ? "opacity-50 cursor-not-allowed" : "cursor-pointer"}`}
            onClick={() => !disabled && onSelect(style.name)}
            disabled={disabled}
            title={disabled ? "Requires Stadia API key" : style.label}
          >
            <div
              className={`h-16 rounded bg-gradient-to-br ${STYLE_COLORS[style.name] || "from-gray-100 to-gray-200"}`}
            />
            <p className="text-xs mt-1 truncate">{style.label}</p>
            {disabled && (
              <span className="absolute top-1 right-1 text-xs" title="Requires API key">
                &#128274;
              </span>
            )}
          </button>
        );
      })}
    </div>
  );
}
