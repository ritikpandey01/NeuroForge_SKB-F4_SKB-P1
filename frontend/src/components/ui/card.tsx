import { HTMLAttributes } from "react";

import { cn } from "@/lib/utils";

export function Card({ className, ...rest }: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn(
        "rounded-xl border border-slate-200 bg-white shadow-sm",
        className,
      )}
      {...rest}
    />
  );
}

export function CardHeader({ className, ...rest }: HTMLAttributes<HTMLDivElement>) {
  return <div className={cn("px-5 pt-4 pb-2", className)} {...rest} />;
}

export function CardTitle({ className, ...rest }: HTMLAttributes<HTMLHeadingElement>) {
  return (
    <h3
      className={cn("text-sm font-semibold tracking-tight text-slate-700", className)}
      {...rest}
    />
  );
}

export function CardContent({ className, ...rest }: HTMLAttributes<HTMLDivElement>) {
  return <div className={cn("px-5 pb-5", className)} {...rest} />;
}
