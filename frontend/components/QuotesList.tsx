"use client";

import { useCallback, useEffect, useState } from "react";

import type { Quote, QuoteListResponse } from "../types/quote";

type Props = {
  apiUrl: string;
  token: string;
  role: string;
  onSelectQuote: (quote: Quote) => void;
};

const PAGE_SIZE = 15;

const STATUS_OPTIONS = [
  { value: "", label: "All statuses" },
  { value: "READY_FOR_APPROVAL", label: "Ready for approval" },
  { value: "REVIEW_REQUIRED", label: "Review required" },
  { value: "APPROVED", label: "Approved" },
  { value: "REJECTED", label: "Rejected" },
  { value: "CONVERTED_TO_ORDER", label: "Converted to order" },
];

function statusBadgeClass(status: string): string {
  switch (status) {
    case "APPROVED":
    case "CONVERTED_TO_ORDER":
      return "bg-emerald-100 text-emerald-700";
    case "REJECTED":
      return "bg-red-100 text-red-700";
    case "REVIEW_REQUIRED":
      return "bg-amber-100 text-amber-700";
    default:
      return "bg-slate-100 text-slate-700";
  }
}

function formatStatus(status: string): string {
  return status
    .toLowerCase()
    .split("_")
    .map((word) => word[0]?.toUpperCase() + word.slice(1))
    .join(" ");
}

function formatDate(value: string | null | undefined): string {
  if (!value) return "—";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "—";
  return date.toLocaleDateString(undefined, {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

export default function QuotesList({
  apiUrl,
  token,
  role,
  onSelectQuote,
}: Props) {
  const [quotes, setQuotes] = useState<Quote[]>([]);
  const [total, setTotal] = useState(0);
  const [skip, setSkip] = useState(0);
  const [status, setStatus] = useState("");
  const [searchInput, setSearchInput] = useState("");
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const isManager = role === "manager" || role === "admin";

  const loadQuotes = useCallback(async () => {
    if (!token) return;

    setLoading(true);
    setError("");

    try {
      const params = new URLSearchParams({
        skip: String(skip),
        limit: String(PAGE_SIZE),
      });

      if (status) params.set("status", status);
      if (search) params.set("search", search);

      const response = await fetch(
        `${apiUrl}/quotes?${params.toString()}`,
        {
          headers: { Authorization: `Bearer ${token}` },
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Failed to load quotes");
      }

      const payload = data as QuoteListResponse;
      setQuotes(payload.quotes);
      setTotal(payload.total);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to load quotes"
      );
    } finally {
      setLoading(false);
    }
  }, [apiUrl, token, skip, status, search]);

  useEffect(() => {
    Promise.resolve().then(() => {
      loadQuotes();
    });
  }, [loadQuotes]);

  useEffect(() => {
    const timeout = setTimeout(() => {
      setSkip(0);
      setSearch(searchInput.trim());
    }, 350);

    return () => clearTimeout(timeout);
  }, [searchInput]);

  const page = Math.floor(skip / PAGE_SIZE) + 1;
  const pageCount = Math.max(1, Math.ceil(total / PAGE_SIZE));

  return (
    <div>
      <div className="mb-6 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <p className="text-sm text-slate-500">
            {isManager
              ? "All company quotes."
              : "Quotes you've created."}
          </p>
        </div>

        <div className="flex flex-col gap-3 sm:flex-row">
          <input
            type="text"
            value={searchInput}
            onChange={(event) =>
              setSearchInput(event.target.value)
            }
            placeholder="Search quote ID, customer, rep, order..."
            className="w-full rounded-xl border border-slate-300 bg-white px-4 py-2.5 text-sm outline-none focus:border-blue-500 sm:w-72"
          />

          <select
            value={status}
            onChange={(event) => {
              setSkip(0);
              setStatus(event.target.value);
            }}
            className="rounded-xl border border-slate-300 bg-white px-4 py-2.5 text-sm outline-none focus:border-blue-500"
          >
            {STATUS_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </div>
      </div>

      {error && (
        <div className="mb-4 rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">
          {error}
        </div>
      )}

      <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
        <div className="overflow-x-auto">
          <table className="min-w-full text-left text-sm">
            <thead className="bg-slate-50 text-slate-600">
              <tr>
                <th className="px-6 py-4">Quote ID</th>
                <th className="px-6 py-4">Customer</th>
                <th className="px-6 py-4">Status</th>
                <th className="px-6 py-4 text-right">Subtotal</th>
                <th className="px-6 py-4 text-right">Margin</th>
                <th className="px-6 py-4 text-right">Risk</th>
                {isManager && (
                  <th className="px-6 py-4">Rep</th>
                )}
                <th className="px-6 py-4">Created</th>
                <th className="px-6 py-4" />
              </tr>
            </thead>

            <tbody>
              {loading ? (
                <tr>
                  <td
                    colSpan={isManager ? 8 : 7}
                    className="px-6 py-10 text-center text-slate-400"
                  >
                    Loading quotes...
                  </td>
                </tr>
              ) : quotes.length === 0 ? (
                <tr>
                  <td
                    colSpan={isManager ? 8 : 7}
                    className="px-6 py-10 text-center text-slate-400"
                  >
                    No quotes match your filters.
                  </td>
                </tr>
              ) : (
                quotes.map((q) => (
                  <tr
                    key={q.quote_id}
                    className="border-t border-slate-100 hover:bg-slate-50"
                  >
                    <td className="whitespace-nowrap px-6 py-4 font-mono text-xs font-semibold text-blue-700">
                      {q.quote_id}
                    </td>

                    <td className="min-w-48 px-6 py-4">
                      <p className="font-medium">
                        {q.customer_name}
                      </p>
                      <p className="text-xs text-slate-500">
                        {q.customer_id}
                      </p>
                    </td>

                    <td className="whitespace-nowrap px-6 py-4">
                      <span
                        className={`rounded-full px-3 py-1 text-xs font-semibold ${statusBadgeClass(
                          q.quote_status
                        )}`}
                      >
                        {formatStatus(q.quote_status)}
                      </span>
                    </td>

                    <td className="whitespace-nowrap px-6 py-4 text-right font-semibold">
                      ${q.quote_subtotal.toFixed(2)}
                    </td>

                    <td className="whitespace-nowrap px-6 py-4 text-right">
                      {q.estimated_margin_pct.toFixed(1)}%
                    </td>

                    <td className="whitespace-nowrap px-6 py-4 text-right">
                      {q.risk_count > 0 ? (
                        <span className="rounded-full bg-amber-100 px-2.5 py-1 text-xs font-semibold text-amber-700">
                          {q.risk_count}
                        </span>
                      ) : (
                        <span className="text-slate-400">
                          0
                        </span>
                      )}
                    </td>

                    {isManager && (
                      <td className="whitespace-nowrap px-6 py-4 text-slate-600">
                        {q.created_by || "unassigned"}
                      </td>
                    )}

                    <td className="whitespace-nowrap px-6 py-4 text-slate-500">
                      {formatDate(q.created_at)}
                    </td>

                    <td className="whitespace-nowrap px-6 py-4 text-right">
                      <button
                        onClick={() => onSelectQuote(q)}
                        className="text-sm font-semibold text-blue-600 hover:text-blue-700"
                      >
                        View
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        <div className="flex items-center justify-between border-t border-slate-200 px-6 py-4 text-sm text-slate-500">
          <span>
            {total === 0
              ? "0 results"
              : `Showing ${skip + 1}–${Math.min(
                  skip + PAGE_SIZE,
                  total
                )} of ${total}`}
          </span>

          <div className="flex items-center gap-3">
            <button
              onClick={() =>
                setSkip((current) =>
                  Math.max(0, current - PAGE_SIZE)
                )
              }
              disabled={skip === 0 || loading}
              className="rounded-lg border border-slate-300 px-3 py-1.5 font-medium disabled:opacity-40"
            >
              Previous
            </button>

            <span>
              Page {page} of {pageCount}
            </span>

            <button
              onClick={() =>
                setSkip((current) =>
                  current + PAGE_SIZE < total
                    ? current + PAGE_SIZE
                    : current
                )
              }
              disabled={skip + PAGE_SIZE >= total || loading}
              className="rounded-lg border border-slate-300 px-3 py-1.5 font-medium disabled:opacity-40"
            >
              Next
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
