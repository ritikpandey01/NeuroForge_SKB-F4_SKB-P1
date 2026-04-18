import { ReactNode } from "react";

import { Card, CardContent } from "@/components/ui/card";

type Props = { title: string; description: string; step: string; children?: ReactNode };

export function Placeholder({ title, description, step, children }: Props) {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight text-slate-900">{title}</h1>
        <p className="mt-1 text-sm text-slate-500">{description}</p>
      </div>
      <Card>
        <CardContent className="py-12 text-center">
          <div className="text-sm font-medium text-slate-700">Coming next</div>
          <div className="mt-1 text-xs text-slate-500">
            This module is scheduled for {step} of the build order.
          </div>
          {children && <div className="mt-6">{children}</div>}
        </CardContent>
      </Card>
    </div>
  );
}
