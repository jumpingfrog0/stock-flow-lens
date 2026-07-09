import type { MoneyFlowSummaryRequest, MoneyFlowSummaryResponse } from "@/types/money-flow";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

export class ApiError extends Error {
  status: number;
  errorCode?: string;

  constructor(message: string, status: number, errorCode?: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.errorCode = errorCode;
  }
}

export async function fetchMoneyFlowSummary(
  request: MoneyFlowSummaryRequest,
): Promise<MoneyFlowSummaryResponse> {
  const response = await fetch(`${API_BASE_URL}/api/money-flow/summary`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    let message = "查询失败";
    let errorCode: string | undefined;
    try {
      const body = await response.json();
      message = body?.detail?.message || message;
      errorCode = body?.detail?.errorCode;
    } catch {
      message = response.statusText || message;
    }
    throw new ApiError(message, response.status, errorCode);
  }

  return response.json();
}
