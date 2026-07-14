"use client";

import { FormEvent, useState } from "react";
import MetricCard from "../components/MetricCard";
import DetailRow from "../components/DetailRow";
import QuoteActions from "../components/QuoteActions";

import type {
  ActiveView,
  AuditLog,
  Quote,
} from "../types/quote";

const API_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";



export default function Home() {
  const [email, setEmail] = useState("sai@example.com");
  const [password, setPassword] = useState("QuoteIQ123!");
  const [token, setToken] = useState("");
  const [userMessage, setUserMessage] = useState("");

  const [customerId, setCustomerId] = useState("CUST-1001");
  const [rfqText, setRfqText] = useState(
    "25 pcs 2x4x8 SPF Stud\n40 sheets 1/2 inch drywall\n12 pcs 7/16 OSB 4x8"
  );

  const [quote, setQuote] = useState<Quote | null>(null);
  const [auditLogs, setAuditLogs] = useState<AuditLog[]>([]);
  const [loading, setLoading] = useState(false);
  const [activeView, setActiveView] =
    useState<ActiveView>("dashboard");

  async function login(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoading(true);
    setUserMessage("");

    try {
      const response = await fetch(`${API_URL}/auth/login`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          email,
          password,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Login failed");
      }

      setToken(data.access_token);
      setUserMessage("Login successful.");
      setActiveView("dashboard");
    } catch (error) {
      setUserMessage(
        error instanceof Error ? error.message : "Login failed"
      );
    } finally {
      setLoading(false);
    }
  }

  async function processRfq(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (!token) {
      setUserMessage("Please log in first.");
      return;
    }

    setLoading(true);
    setUserMessage("");

    try {
      const response = await fetch(`${API_URL}/rfqs/process-v2`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          customer_id: customerId,
          rfq_text: rfqText,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          typeof data.detail === "string"
            ? data.detail
            : "RFQ processing failed"
        );
      }

      setQuote(data);
      setUserMessage("Quote generated successfully.");
      setActiveView("dashboard");
    } catch (error) {
      setUserMessage(
        error instanceof Error
          ? error.message
          : "RFQ processing failed"
      );
    } finally {
      setLoading(false);
    }
  }

  async function loadAuditLogs() {
    if (!token) {
      setUserMessage("Please log in first.");
      return;
    }

    setLoading(true);
    setUserMessage("");

    try {
      const response = await fetch(`${API_URL}/admin/audit`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          typeof data.detail === "string"
            ? data.detail
            : "Unable to load audit logs"
        );
      }

      setAuditLogs(data.logs || []);
      setActiveView("audit");
    } catch (error) {
      setUserMessage(
        error instanceof Error
          ? error.message
          : "Unable to load audit logs"
      );
    } finally {
      setLoading(false);
    }
  }

  function logout() {
    setToken("");
    setQuote(null);
    setAuditLogs([]);
    setUserMessage("Logged out.");
    setActiveView("dashboard");
  }

  if (!token) {
    return (
      <main className="min-h-screen bg-slate-950 text-white">
        <div className="mx-auto flex min-h-screen max-w-7xl items-center justify-center px-6 py-10">
          <div className="grid w-full overflow-hidden rounded-3xl border border-slate-800 bg-slate-900 shadow-2xl lg:grid-cols-2">
            <section className="hidden bg-gradient-to-br from-blue-600 to-indigo-950 p-12 lg:block">
              <p className="mb-8 text-sm font-semibold uppercase tracking-[0.3em] text-blue-100">
                Enterprise Quote Automation
              </p>

              <h1 className="max-w-lg text-5xl font-bold leading-tight">
                Turn customer RFQs into accurate sales quotes.
              </h1>

              <p className="mt-6 max-w-lg text-lg leading-8 text-blue-100">
                QuoteIQ extracts requested products, matches catalog
                SKUs, applies pricing rules, evaluates margin risk and
                creates ERP-ready sales orders.
              </p>

              <div className="mt-12 grid grid-cols-2 gap-4">
                {[
                  "RFQ extraction",
                  "SKU matching",
                  "Pricing controls",
                  "Audit tracking",
                ].map((feature) => (
                  <div
                    key={feature}
                    className="rounded-2xl border border-white/20 bg-white/10 p-4"
                  >
                    <p className="font-medium">{feature}</p>
                  </div>
                ))}
              </div>
            </section>

            <section className="p-8 sm:p-12">
              <div className="mb-10">
                <div className="mb-5 inline-flex h-12 w-12 items-center justify-center rounded-2xl bg-blue-600 text-xl font-bold">
                  Q
                </div>

                <h2 className="text-3xl font-bold">
                  Sign in to QuoteIQ
                </h2>

                <p className="mt-2 text-slate-400">
                  Access the quote-to-order operations dashboard.
                </p>
              </div>

              <form onSubmit={login} className="space-y-5">
                <label className="block">
                  <span className="mb-2 block text-sm font-medium text-slate-300">
                    Email
                  </span>

                  <input
                    type="email"
                    value={email}
                    onChange={(event) =>
                      setEmail(event.target.value)
                    }
                    className="w-full rounded-xl border border-slate-700 bg-slate-950 px-4 py-3 outline-none focus:border-blue-500"
                    required
                  />
                </label>

                <label className="block">
                  <span className="mb-2 block text-sm font-medium text-slate-300">
                    Password
                  </span>

                  <input
                    type="password"
                    value={password}
                    onChange={(event) =>
                      setPassword(event.target.value)
                    }
                    className="w-full rounded-xl border border-slate-700 bg-slate-950 px-4 py-3 outline-none focus:border-blue-500"
                    required
                  />
                </label>

                <button
                  type="submit"
                  disabled={loading}
                  className="w-full rounded-xl bg-blue-600 px-5 py-3 font-semibold transition hover:bg-blue-500 disabled:opacity-60"
                >
                  {loading ? "Signing in..." : "Sign in"}
                </button>
              </form>

              {userMessage && (
                <p className="mt-5 rounded-xl border border-slate-700 bg-slate-950 p-3 text-sm text-slate-300">
                  {userMessage}
                </p>
              )}
            </section>
          </div>
        </div>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-slate-100 text-slate-950">
      <div className="flex min-h-screen">
        <aside className="hidden w-72 flex-col bg-slate-950 p-6 text-white lg:flex">
          <div className="mb-10 flex items-center gap-3">
            <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-blue-600 text-lg font-bold">
              Q
            </div>

            <div>
              <h1 className="text-xl font-bold">QuoteIQ</h1>
              <p className="text-xs text-slate-400">
                Quote-to-Order Platform
              </p>
            </div>
          </div>

          <nav className="space-y-2">
            <button
              onClick={() => setActiveView("dashboard")}
              className={`w-full rounded-xl px-4 py-3 text-left ${
                activeView === "dashboard"
                  ? "bg-blue-600"
                  : "text-slate-300 hover:bg-slate-800"
              }`}
            >
              Dashboard
            </button>

            <button
              onClick={() => setActiveView("rfq")}
              className={`w-full rounded-xl px-4 py-3 text-left ${
                activeView === "rfq"
                  ? "bg-blue-600"
                  : "text-slate-300 hover:bg-slate-800"
              }`}
            >
              Process RFQ
            </button>

            <button
              onClick={loadAuditLogs}
              className={`w-full rounded-xl px-4 py-3 text-left ${
                activeView === "audit"
                  ? "bg-blue-600"
                  : "text-slate-300 hover:bg-slate-800"
              }`}
            >
              Audit Logs
            </button>
          </nav>

          <div className="mt-auto rounded-2xl border border-slate-800 bg-slate-900 p-4">
            <p className="break-all text-sm font-medium">{email}</p>
            <p className="mt-1 text-xs text-slate-400">
              Authenticated user
            </p>

            <button
              onClick={logout}
              className="mt-4 text-sm font-semibold text-red-400"
            >
              Log out
            </button>
          </div>
        </aside>

        <section className="min-w-0 flex-1">
          <header className="border-b border-slate-200 bg-white px-6 py-5 lg:px-10">
            <div className="flex items-center justify-between gap-4">
              <div>
                <p className="text-sm font-medium text-blue-600">
                  Operations workspace
                </p>

                <h2 className="text-2xl font-bold">
                  {activeView === "dashboard" && "Quote Dashboard"}
                  {activeView === "rfq" && "Process Customer RFQ"}
                  {activeView === "audit" && "Enterprise Audit Log"}
                </h2>
              </div>

              <button
                onClick={() => setActiveView("rfq")}
                className="rounded-xl bg-blue-600 px-5 py-3 text-sm font-semibold text-white hover:bg-blue-500"
              >
                New Quote
              </button>
            </div>
          </header>

          <div className="p-6 lg:p-10">
            {userMessage && (
              <div className="mb-6 rounded-xl border border-blue-200 bg-blue-50 p-4 text-sm text-blue-800">
                {userMessage}
              </div>
            )}

            {activeView === "dashboard" && (
              <>
                <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-4">
                  <MetricCard
                    label="Latest quote"
                    value={quote?.quote_id || "No quote yet"}
                  />

                  <MetricCard
                    label="Quote value"
                    value={
                      quote
                        ? `$${quote.quote_subtotal.toFixed(2)}`
                        : "$0.00"
                    }
                  />

                  <MetricCard
                    label="Estimated margin"
                    value={
                      quote
                        ? `${quote.estimated_margin_pct.toFixed(2)}%`
                        : "0%"
                    }
                  />

                  <MetricCard
                    label="Risk flags"
                    value={String(quote?.risk_count || 0)}
                  />
                </div>

                <div className="mt-8 grid gap-6 xl:grid-cols-[1.4fr_1fr]">
                  <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
                    <div className="mb-6 flex items-center justify-between gap-4">
                      <div>
                        <h3 className="text-lg font-bold">
                          Latest quote
                        </h3>
                        <p className="text-sm text-slate-500">
                          Current quote processing result
                        </p>
                      </div>

                      {quote && (
                        <span className="rounded-full bg-emerald-100 px-3 py-1 text-xs font-semibold text-emerald-700">
                          {quote.quote_status}
                        </span>
                      )}
                    </div>

                    {quote ? (
                      <div className="space-y-4">
                        <DetailRow
                          label="Customer"
                          value={quote.customer_name}
                        />
                        <DetailRow
                          label="Customer ID"
                          value={quote.customer_id}
                        />
                        <DetailRow
                          label="Price class"
                          value={quote.price_class}
                        />
                        <DetailRow
                          label="Items extracted"
                          value={String(
                            quote.extracted_line_count
                          )}
                        />
                        <DetailRow
                          label="Items matched"
                          value={String(
                            quote.matched_line_count
                          )}
                        />
                        <DetailRow
                          label="Confidence"
                          value={`${quote.quote_confidence}%`}
                        />
                      </div>
                    ) : (
                      <div className="rounded-xl border border-dashed border-slate-300 p-10 text-center">
                        <p className="font-medium text-slate-700">
                          No quote has been generated.
                        </p>
                        <button
                          onClick={() => setActiveView("rfq")}
                          className="mt-4 text-sm font-semibold text-blue-600"
                        >
                          Process your first RFQ
                        </button>
                      </div>
                    )}
                  </div>

                  <div className="rounded-2xl bg-slate-950 p-6 text-white shadow-sm">
                    <p className="text-sm font-medium text-blue-400">
                      QuoteIQ workflow
                    </p>

                    <h3 className="mt-2 text-2xl font-bold">
                      RFQ to ERP-ready order
                    </h3>

                    <div className="mt-7 space-y-4">
                      {[
                        "Extract requested products",
                        "Match catalog SKUs",
                        "Apply pricing rules",
                        "Validate margin risk",
                        "Create approval-ready quote",
                      ].map((step, index) => (
                        <div
                          key={step}
                          className="flex items-center gap-4"
                        >
                          <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-blue-600 text-sm font-bold">
                            {index + 1}
                          </div>
                          <p className="text-sm text-slate-200">
                            {step}
                          </p>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>

                {quote && quote.priced_lines?.length > 0 && (
                  <div className="mt-8 overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
                    <div className="border-b border-slate-200 p-6">
                      <h3 className="text-lg font-bold">
                        Quote line items
                      </h3>
                      <p className="mt-1 text-sm text-slate-500">
                        Product matches, pricing rules and margins.
                      </p>
                    </div>

                    <div className="overflow-x-auto">
                      <table className="min-w-full text-left text-sm">
                        <thead className="bg-slate-50 text-slate-600">
                          <tr>
                            <th className="px-6 py-4">SKU</th>
                            <th className="px-6 py-4">Product</th>
                            <th className="px-6 py-4 text-right">
                              Quantity
                            </th>
                            <th className="px-6 py-4 text-right">
                              Unit Price
                            </th>
                            <th className="px-6 py-4 text-right">
                              Total
                            </th>
                            <th className="px-6 py-4 text-right">
                              Margin
                            </th>
                            <th className="px-6 py-4">Status</th>
                          </tr>
                        </thead>

                        <tbody>
                          {quote.priced_lines.map((line, index) => (
                            <tr
                              key={`${line.sku}-${index}`}
                              className="border-t border-slate-100"
                            >
                              <td className="whitespace-nowrap px-6 py-4 font-mono text-xs font-semibold text-blue-700">
                                {line.sku}
                              </td>

                              <td className="min-w-64 px-6 py-4">
                                <p className="font-medium">
                                  {line.product_name}
                                </p>
                                <p className="mt-1 text-xs text-slate-500">
                                  {line.pricing_rule_applied}
                                </p>
                              </td>

                              <td className="whitespace-nowrap px-6 py-4 text-right">
                                {line.quantity}{" "}
                                {line.uom_raw || ""}
                              </td>

                              <td className="whitespace-nowrap px-6 py-4 text-right">
                                ${line.unit_price.toFixed(2)}
                              </td>

                              <td className="whitespace-nowrap px-6 py-4 text-right font-semibold">
                                ${line.line_total.toFixed(2)}
                              </td>

                              <td className="whitespace-nowrap px-6 py-4 text-right">
                                {line.margin_pct.toFixed(2)}%
                              </td>

                              <td className="px-6 py-4">
                                <span
                                  className={`rounded-full px-3 py-1 text-xs font-semibold ${
                                    line.risk_flag
                                      ? "bg-amber-100 text-amber-700"
                                      : "bg-emerald-100 text-emerald-700"
                                  }`}
                                >
                                  {line.risk_flag ? "Review" : "Pass"}
                                </span>
                              </td>
                            </tr>
                          ))}
                        </tbody>

                        <tfoot className="border-t-2 border-slate-200 bg-slate-50">
                          <tr>
                            <td
                              colSpan={4}
                              className="px-6 py-4 text-right font-semibold"
                            >
                              Quote subtotal
                            </td>
                            <td className="px-6 py-4 text-right text-lg font-bold">
                              ${quote.quote_subtotal.toFixed(2)}
                            </td>
                            <td className="px-6 py-4 text-right font-semibold">
                              {quote.estimated_margin_pct.toFixed(2)}%
                            </td>
                            <td className="px-6 py-4" />
                          </tr>
                        </tfoot>
                      </table>
                    </div>
                  </div>
                )}
                {quote && (
    <QuoteActions
    quote={quote}
    token={token}
    apiUrl={API_URL}
    userEmail={email}
    onQuoteUpdated={setQuote}
    onMessage={setUserMessage}
    onLoading={setLoading}
  />
)}
              </>
            )}

            {activeView === "rfq" && (
              <form
                onSubmit={processRfq}
                className="mx-auto max-w-4xl rounded-2xl border border-slate-200 bg-white p-7 shadow-sm"
              >
                <div className="mb-7">
                  <h3 className="text-xl font-bold">
                    Customer request for quotation
                  </h3>

                  <p className="mt-2 text-sm text-slate-500">
                    Enter the customer ID and paste the original RFQ
                    text. QuoteIQ will extract, match and price the
                    requested products.
                  </p>
                </div>

                <label className="block">
                  <span className="mb-2 block text-sm font-semibold">
                    Customer ID
                  </span>

                  <select
                    value={customerId}
                    onChange={(event) =>
                      setCustomerId(event.target.value)
                    }
                    className="w-full rounded-xl border border-slate-300 bg-white px-4 py-3 outline-none focus:border-blue-500"
                  >
                    <option value="CUST-1001">
                      CUST-1001 — ABC Construction
                    </option>
                    <option value="CUST-1002">
                      CUST-1002 — Desert Ridge Builders
                    </option>
                    <option value="CUST-1004">
                      CUST-1004 — Sun Valley Framing
                    </option>
                  </select>
                </label>

                <label className="mt-6 block">
                  <span className="mb-2 block text-sm font-semibold">
                    RFQ text
                  </span>

                  <textarea
                    value={rfqText}
                    onChange={(event) =>
                      setRfqText(event.target.value)
                    }
                    rows={11}
                    className="w-full resize-none rounded-xl border border-slate-300 px-4 py-3 font-mono text-sm outline-none focus:border-blue-500"
                    required
                  />
                </label>

                <div className="mt-7 flex justify-end">
                  <button
                    type="submit"
                    disabled={loading}
                    className="rounded-xl bg-blue-600 px-6 py-3 font-semibold text-white hover:bg-blue-500 disabled:opacity-60"
                  >
                    {loading
                      ? "Processing RFQ..."
                      : "Generate Quote"}
                  </button>
                </div>
              </form>
            )}

            {activeView === "audit" && (
              <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
                <div className="border-b border-slate-200 p-6">
                  <h3 className="text-lg font-bold">
                    Audit activity
                  </h3>
                  <p className="mt-1 text-sm text-slate-500">
                    Traceable enterprise activity and user actions.
                  </p>
                </div>

                <div className="overflow-x-auto">
                  <table className="min-w-full text-left text-sm">
                    <thead className="bg-slate-50 text-slate-600">
                      <tr>
                        <th className="px-6 py-4">Timestamp</th>
                        <th className="px-6 py-4">Actor</th>
                        <th className="px-6 py-4">Action</th>
                        <th className="px-6 py-4">Entity</th>
                        <th className="px-6 py-4">Status</th>
                      </tr>
                    </thead>

                    <tbody>
                      {auditLogs.map((log) => (
                        <tr
                          key={log.id}
                          className="border-t border-slate-100"
                        >
                          <td className="whitespace-nowrap px-6 py-4 text-slate-500">
                            {new Date(
                              log.timestamp
                            ).toLocaleString()}
                          </td>

                          <td className="px-6 py-4">
                            <p className="font-medium">
                              {log.actor_email}
                            </p>
                            <p className="text-xs text-slate-500">
                              {log.actor_role}
                            </p>
                          </td>

                          <td className="px-6 py-4 font-medium">
                            {log.action}
                          </td>

                          <td className="px-6 py-4">
                            {log.entity_id || log.entity_type}
                          </td>

                          <td className="px-6 py-4">
                            <span className="rounded-full bg-emerald-100 px-3 py-1 text-xs font-semibold text-emerald-700">
                              {log.status}
                            </span>
                          </td>
                        </tr>
                      ))}

                      {!auditLogs.length && (
                        <tr>
                          <td
                            colSpan={5}
                            className="px-6 py-12 text-center text-slate-500"
                          >
                            No audit events found.
                          </td>
                        </tr>
                      )}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>
        </section>
      </div>
    </main>
  );
}

