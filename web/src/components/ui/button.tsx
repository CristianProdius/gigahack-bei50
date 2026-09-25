import type { ButtonHTMLAttributes } from "react";
import { cn } from "@/lib/utils";

type Props = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "default" | "outline" | "ghost";
};

export function Button({ className, variant = "default", ...props }: Props) {
  const styles = {
    default: "bg-emerald-700 text-white hover:bg-emerald-800",
    outline: "border border-stone-300 bg-white hover:bg-stone-50",
    ghost: "hover:bg-stone-100",
  }[variant];
  return (
    <button
      className={cn(
        "inline-flex items-center justify-center rounded-md px-3 py-1.5 text-sm font-medium disabled:opacity-50",
        styles,
        className,
      )}
      {...props}
    />
  );
}
