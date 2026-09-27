"use server";

// A Server Action: the form in NewRunForm calls this function, but it runs on
// the Next.js server. So the browser never talks to FastAPI directly.
import { redirect } from "next/navigation";

import { API_URL, authHeaders } from "@/lib/api";

export type NewRunState = { error: string | null };

export async function createRun(_previous: NewRunState, formData: FormData): Promise<NewRunState> {
  const input = String(formData.get("input") ?? "").trim();
  if (!input) return { error: "Type a question for the agent first." };

  let runId: number;
  try {
    const res = await fetch(`${API_URL}/api/runs`, {
      method: "POST",
      headers: { "Content-Type": "application/json", ...authHeaders() },
      body: JSON.stringify({
        input,
        version: formData.get("version"),
        use_judge: formData.get("use_judge") === "on",
      }),
    });
    if (!res.ok) return { error: `The API returned ${res.status}: ${await res.text()}` };
    runId = (await res.json()).id;
  } catch {
    return { error: "Could not reach the AgentLens API. Is the backend running?" };
  }

  // redirect() works by throwing, so it has to stay outside the try/catch.
  redirect(`/runs/${runId}`);
}
