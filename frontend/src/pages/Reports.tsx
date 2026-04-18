import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { GenerateReport } from "@/features/reports/GenerateReport";
import { ReportList } from "@/features/reports/ReportList";

export default function Reports() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight text-slate-900">
          Sustainability Reports
        </h1>
        <p className="mt-1 text-sm text-slate-500">
          Auto-generated disclosure PDFs for BRSR, GRI 305, and TCFD. Every figure resolves
          through the emissions traceability chain — activity → factor → CO₂e. AI-written
          exec summaries are optional and never block the PDF.
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Generate new report</CardTitle>
        </CardHeader>
        <CardContent>
          <GenerateReport />
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Saved reports</CardTitle>
        </CardHeader>
        <CardContent>
          <ReportList />
        </CardContent>
      </Card>
    </div>
  );
}
