import type { ButtonHTMLAttributes, ReactNode } from "react";

type ButtonVariant = "primary" | "ghost" | "danger";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  readonly variant?: ButtonVariant;
}

// Token-styled only (FE-002/FE-003); >=44px tap height (FE-011).
const VARIANT_CLASSES: Record<ButtonVariant, string> = {
  primary:
    "border-accent bg-accent text-ink-inverse hover:bg-accent-strong hover:border-accent-strong",
  ghost: "border-border bg-surface text-ink hover:bg-surface-sunken",
  danger:
    "border-danger bg-danger text-ink-inverse hover:opacity-90 focus-visible:outline-danger",
};

const BASE_CLASSES =
  "inline-flex min-h-tap-min items-center justify-center gap-2 rounded-control border-control px-4 font-label text-sm font-semibold uppercase tracking-widest transition-colors disabled:cursor-not-allowed disabled:opacity-50";

/** Shared button primitive. Variants: primary / ghost / danger. */
export function Button({
  variant = "primary",
  type = "button",
  className,
  children,
  ...rest
}: ButtonProps): ReactNode {
  const classes = [BASE_CLASSES, VARIANT_CLASSES[variant], className ?? ""]
    .join(" ")
    .trim();

  return (
    <button type={type} className={classes} {...rest}>
      {children}
    </button>
  );
}
