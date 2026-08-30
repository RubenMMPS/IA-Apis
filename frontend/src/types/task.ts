export type TaskStatus = "queued" | "running" | "completed" | "failed";

export interface Task {
  id: string;
  status: TaskStatus;
  original_request: string;
  result_summary: string | null;
  error_message: string | null;
  created_at: string;
  updated_at: string;
}

export interface CreateTaskRequest {
  original_request: string;
}