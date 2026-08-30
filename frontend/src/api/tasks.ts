import { apiFetch } from "./client";
import type { Task, CreateTaskRequest } from "../types/task";

export function createTask(body: CreateTaskRequest): Promise<Task> {
  return apiFetch<Task>("/tasks", { method: "POST", body: JSON.stringify(body) });
}

export function getTask(taskId: string): Promise<Task> {
  return apiFetch<Task>(`/tasks/${taskId}`);
}