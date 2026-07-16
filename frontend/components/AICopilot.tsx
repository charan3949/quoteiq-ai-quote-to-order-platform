"use client";

import { FormEvent, useMemo, useState } from "react";

type ChatMessage = { role: "user" | "assistant"; content: string };

type Props = {
  apiUrl: string;
  token: string;
  quoteId?: string | null;
};

const suggestions = [
  "Summarize this quote for a manager.",
  "Why is the margin low, and what should I review?",
  "Suggest a safer price strategy without violating margin controls.",
  "Which line items carry the most risk?",
  "What should happen before this quote is approved?",
];

export default function AICopilot({ apiUrl, token, quoteId }: Props) {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      role: "assistant",
      content:
        "I am QuoteIQ Copilot. Select or process a quote, then ask about pricing, margin, risk, approval readiness, or the next operational step.",
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const contextLabel = useMemo(
    () => (quoteId ? `Grounded in ${quoteId}` : "General workspace context"),
    [quoteId]
  );

  async function ask(question: string) {
    const clean = question.trim();
    if (!clean || loading) return;

    const nextMessages: ChatMessage[] = [
      ...messages,
      { role: "user", content: clean },
    ];
    setMessages(nextMessages);
    setInput("");
    setError("");
    setLoading(true);

    try {
      const response = await fetch(`${apiUrl}/enterprise/copilot`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          message: clean,
          quote_id: quoteId || null,
          history: nextMessages.slice(-10),
        }),
      });
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || "Copilot request failed");
      }
      setMessages((current) => [
        ...current,
        { role: "assistant", content: data.answer },
      ]);
    } catch (caught) {
      setError(
        caught instanceof Error ? caught.message : "Copilot request failed"
      );
    } finally {
      setLoading(false);
    }
  }

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    void ask(input);
  }

  return (
    <div className="grid gap-6 xl:grid-cols-[1fr_320px]">
      <section className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
        <div className="flex items-center justify-between border-b border-slate-200 px-6 py-5">
          <div>
            <p className="text-xs font-bold uppercase tracking-[0.2em] text-blue-600">
              AI Copilot
            </p>
            <h3 className="mt-1 text-xl font-bold">Commercial decision support</h3>
          </div>
          <span className="rounded-full bg-emerald-100 px-3 py-1 text-xs font-semibold text-emerald-700">
            {contextLabel}
          </span>
        </div>

        <div className="h-[520px] space-y-4 overflow-y-auto bg-slate-50 p-6">
          {messages.map((message, index) => (
            <div
              key={`${message.role}-${index}`}
              className={`max-w-[86%] rounded-2xl px-4 py-3 text-sm leading-6 whitespace-pre-wrap ${
                message.role === "user"
                  ? "ml-auto bg-blue-600 text-white"
                  : "border border-slate-200 bg-white text-slate-700"
              }`}
            >
              {message.content}
            </div>
          ))}
          {loading && (
            <div className="inline-flex rounded-2xl border bg-white px-4 py-3 text-sm text-slate-500">
              Analyzing QuoteIQ context…
            </div>
          )}
        </div>

        <form onSubmit={submit} className="border-t border-slate-200 p-4">
          {error && (
            <p className="mb-3 rounded-xl border border-red-200 bg-red-50 p-3 text-sm text-red-700">
              {error}
            </p>
          )}
          <div className="flex gap-3">
            <textarea
              value={input}
              onChange={(event) => setInput(event.target.value)}
              placeholder="Ask about margin, pricing, risk, approval readiness, or next steps…"
              className="min-h-24 flex-1 resize-none rounded-xl border border-slate-300 px-4 py-3 text-sm outline-none focus:border-blue-500"
              maxLength={4000}
            />
            <button
              type="submit"
              disabled={loading || !input.trim()}
              className="self-end rounded-xl bg-blue-600 px-5 py-3 text-sm font-semibold text-white hover:bg-blue-500 disabled:opacity-50"
            >
              Send
            </button>
          </div>
        </form>
      </section>

      <aside className="space-y-5">
        <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
          <h4 className="font-bold">Suggested questions</h4>
          <div className="mt-4 space-y-2">
            {suggestions.map((suggestion) => (
              <button
                key={suggestion}
                onClick={() => void ask(suggestion)}
                disabled={loading}
                className="w-full rounded-xl border border-slate-200 px-3 py-3 text-left text-sm text-slate-700 hover:border-blue-300 hover:bg-blue-50 disabled:opacity-50"
              >
                {suggestion}
              </button>
            ))}
          </div>
        </div>

        <div className="rounded-2xl bg-slate-950 p-5 text-white">
          <p className="text-xs font-bold uppercase tracking-widest text-blue-400">
            Guardrails
          </p>
          <ul className="mt-4 space-y-3 text-sm text-slate-300">
            <li>Uses QuoteIQ data supplied by the backend.</li>
            <li>Does not approve, edit, email, or create orders.</li>
            <li>Calls out missing evidence instead of inventing facts.</li>
            <li>Authorized users retain final decision ownership.</li>
          </ul>
        </div>
      </aside>
    </div>
  );
}
