import { apiFetch } from "./client";
import type { Task, CreateTaskRequest, CodeArtifacts } from "../types/task";

export function createTask(body: CreateTaskRequest): Promise<Task> {
  return apiFetch<Task>("/tasks", { method: "POST", body: JSON.stringify(body) });
}

export function getTask(taskId: string): Promise<Task> {
  return apiFetch<Task>(`/tasks/${taskId}`);
}

export function getTaskCode(taskId: string): Promise<CodeArtifacts> {
  return apiFetch<CodeArtifacts>(`/tasks/${taskId}/code`);
}