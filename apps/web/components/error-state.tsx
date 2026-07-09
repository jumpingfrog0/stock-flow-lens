import { AlertTriangle } from "lucide-react";

type ErrorStateProps = {
  title?: string;
  message: string;
};

export function ErrorState({ title = "查询失败", message }: ErrorStateProps) {
  return (
    <div className="flex items-start gap-3 rounded border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-900">
      <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" aria-hidden="true" />
      <div>
        <div className="font-medium">{title}</div>
        <div className="mt-1 text-red-800">{message}</div>
      </div>
    </div>
  );
}
