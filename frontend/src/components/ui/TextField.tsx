import { useId } from "react";
import type { ReactNode } from "react";

interface TextFieldProps {
  readonly label: string;
  readonly value: string;
  readonly onChange: (value: string) => void;
  /** Validation message rendered below the control and wired via aria-describedby. */
  readonly error?: string | undefined;
  /** Render a multi-line `<textarea>` instead of an `<input>`. */
  readonly multiline?: boolean | undefined;
  readonly required?: boolean | undefined;
  readonly maxLength?: number | undefined;
  readonly placeholder?: string | undefined;
  readonly autoFocus?: boolean | undefined;
}

const CONTROL_BASE =
  "w-full rounded-control border-control border-border bg-surface px-3 py-2 font-body text-base text-ink placeholder:text-ink-muted focus-visible:outline focus-visible:outline-2 focus-visible:outline-ring";

/** Labeled text input/textarea with an optional error slot (FE-011: every input has a label). */
export function TextField({
  label,
  value,
  onChange,
  error,
  multiline = false,
  required = false,
  maxLength,
  placeholder,
  autoFocus = false,
}: TextFieldProps): ReactNode {
  const id = useId();
  const errorId = `${id}-error`;
  const controlClasses = [
    CONTROL_BASE,
    "min-h-tap-min",
    error ? "border-danger" : "",
  ]
    .join(" ")
    .trim();

  return (
    <div className="flex flex-col gap-1.5">
      <label
        htmlFor={id}
        className="font-label text-xs font-semibold uppercase tracking-widest text-ink-muted"
      >
        {label}
        {required ? <span className="text-danger"> *</span> : null}
      </label>
      {multiline ? (
        <textarea
          id={id}
          className={`${controlClasses} resize-y`}
          rows={3}
          value={value}
          required={required}
          maxLength={maxLength}
          placeholder={placeholder}
          aria-invalid={error ? true : undefined}
          aria-describedby={error ? errorId : undefined}
          autoFocus={autoFocus}
          onChange={(event) => {
            onChange(event.target.value);
          }}
        />
      ) : (
        <input
          id={id}
          type="text"
          className={controlClasses}
          value={value}
          required={required}
          maxLength={maxLength}
          placeholder={placeholder}
          aria-invalid={error ? true : undefined}
          aria-describedby={error ? errorId : undefined}
          autoFocus={autoFocus}
          onChange={(event) => {
            onChange(event.target.value);
          }}
        />
      )}
      {error ? (
        <p id={errorId} className="font-body text-sm text-danger">
          {error}
        </p>
      ) : null}
    </div>
  );
}
