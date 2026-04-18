import { cva, type VariantProps } from "class-variance-authority";
import { ButtonHTMLAttributes, forwardRef } from "react";

import { cn } from "@/lib/utils";

const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand focus-visible:ring-offset-2 disabled:opacity-50 disabled:pointer-events-none",
  {
    variants: {
      variant: {
        default: "bg-brand text-white hover:bg-brand-800",
        ghost: "hover:bg-slate-100 text-slate-700",
        outline: "border border-slate-300 bg-white hover:bg-slate-50 text-slate-700",
      },
      size: {
        default: "h-9 px-4",
        sm: "h-8 px-3 text-xs",
        icon: "h-9 w-9",
      },
    },
    defaultVariants: { variant: "default", size: "default" },
  },
);

type Props = ButtonHTMLAttributes<HTMLButtonElement> & VariantProps<typeof buttonVariants>;

export const Button = forwardRef<HTMLButtonElement, Props>(function Button(
  { className, variant, size, ...rest },
  ref,
) {
  return (
    <button
      ref={ref}
      className={cn(buttonVariants({ variant, size }), className)}
      {...rest}
    />
  );
});
