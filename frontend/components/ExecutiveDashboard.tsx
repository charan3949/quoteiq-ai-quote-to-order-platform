"use client";

import { useEffect, useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import MetricCard from "./MetricCard";
import type {
  Bottlenecks,
  DashboardSummary,
  RepPerformance,
  TopCustomer,
  TrendPoint,
} from "../types/quote";

type Props = {
  apiUrl: string;
  token: string;
  role: string;
};

async function fetchJson(
  url: string,
  token: string
): Promise<unknown> {
  const response = await fetch(url, {
    headers: { Authorization: `Bearer ${token}` },
  });

  if (!response.ok) {
    const body = await response.json().catch(() => null);
    throw new Error(
      body?.detail || `Request failed (${response.status})`
    );
  }

  return response.json();
}

function currency(value: number): string {
  return `$${value.toLocaleString(undefined, {
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  })}`;
}

export default function ExecutiveDashboard({
  apiUrl,
  token,
  role,
}: Props) {
  const [summary, setSummary] = useState<DashboardSummary | null>(
    null
  );
  const [trend, setTrend] = useState<TrendPoint[]>([]);
  const [customers, setCustomers] = useState<TopCustomer[]>([]);
  const [reps, setReps] = useState<RepPerformance[]>([]);
  const [bottlenecks, setBottlenecks] =
    useState<Bottlenecks | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  const canViewAnalytics = role === "manager" || role === "admin";

  useEffect(() => {
    if (!canViewAnalytics || !token) {
      return;
    }

    let cancelled = false;

    Promise.resolve().then(() => {
      if (cancelled) return;

      setLoading(true);
      setError("");

      Promise.all([
      fetchJson(`${apiUrl}/analytics/summary`, token),
      fetchJson(`${apiUrl}/analytics/trend?months=6`, token),
      fetchJson(`${apiUrl}/analytics/customers?limit=5`, token),
      fetchJson(`${apiUrl}/analytics/reps`, token),
      fetchJson(`${apiUrl}/analytics/bottlenecks?limit=5`, token),
    ])
      .then(([s, t, c, r, b]) => {
        if (cancelled) return;

        setSummary(s as DashboardSummary);
        setTrend((t as { months: TrendPoint[] }).months);
        setCustomers(
          (c as { customers: TopCustomer[] }).customers
        );
        setReps((r as { reps: RepPerformance[] }).reps);
        setBottlenecks(b as Bottlenecks);
      })
      .catch((err) => {
        if (!cancelled) {
          setError(
            err instanceof Error
              ? err.message
              : "Failed to load dashboard analytics"
          );
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    });

    return () => {
      cancelled = true;
    };
  }, [apiUrl, token, canViewAnalytics]);

  if (!canViewAnalytics) {
    return (
      <div className="mb-8 rounded-2xl border border-dashed border-slate-300 bg-white p-8 text-center">
        <p className="font-semibold text-slate-700">
          Executive metrics are visible to managers and admins.
        </p>
        <p className="mt-1 text-sm text-slate-500">
          Your quotes still appear below. Ask a manager for
          approval-pipeline or revenue visibility.
        </p>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="mb-8 rounded-2xl border border-slate-200 bg-white p-8 text-center text-sm text-slate-500">
        Loading executive metrics...
      </div>
    );
  }

  if (error) {
    return (
      <div className="mb-8 rounded-2xl border border-red-200 bg-red-50 p-6 text-sm text-red-700">
        {error}
      </div>
    );
  }

  if (!summary) return null;

  const pendingRevenue = bottlenecks?.revenue_at_risk ?? 0;

  return (
    <div className="mb-10 space-y-6">
      <div>
        <h3 className="text-lg font-bold text-slate-900">
          Executive summary
        </h3>
        <p className="text-sm text-slate-500">
          Company-wide quote-to-order performance.
        </p>
      </div>

      <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-4">
        <MetricCard
          label="Total quotes"
          value={String(summary.total_quotes)}
        />
        <MetricCard
          label="Pending approval"
          value={String(summary.pending_quotes)}
        />
        <MetricCard
          label="Approved revenue"
          value={currency(summary.revenue)}
        />
        <MetricCard
          label="Conversion rate"
          value={`${summary.conversion_rate_pct}%`}
        />
        <MetricCard
          label="Avg approval time"
          value={
            summary.avg_approval_time_hours !== null
              ? `${summary.avg_approval_time_hours}h`
              : "N/A"
          }
        />
        <MetricCard
          label="Avg quote value"
          value={currency(summary.avg_quote_value)}
        />
        <MetricCard
          label="Rejected quotes"
          value={String(summary.rejected_quotes)}
        />
        <MetricCard
          label="Revenue at risk"
          value={currency(pendingRevenue)}
        />
      </div>

      {bottlenecks && bottlenecks.pending_count > 0 && (
        <div className="rounded-2xl border border-amber-200 bg-amber-50 p-5 text-sm text-amber-900">
          <span className="font-semibold">
            {bottlenecks.pending_count} quote
            {bottlenecks.pending_count === 1 ? "" : "s"} awaiting
            approval
          </span>{" "}
          — {currency(pendingRevenue)} in revenue is currently
          stuck in the approval pipeline
          {bottlenecks.oldest_pending[0] && (
            <>
              , oldest for{" "}
              {bottlenecks.oldest_pending[0].age_hours}h (
              {bottlenecks.oldest_pending[0].quote_id})
            </>
          )}
          .
        </div>
      )}

      <div className="grid gap-6 xl:grid-cols-2">
        <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <h4 className="mb-4 text-sm font-bold text-slate-700">
            Monthly revenue trend
          </h4>

          {trend.length === 0 ? (
            <p className="py-10 text-center text-sm text-slate-400">
              No historical data yet.
            </p>
          ) : (
            <ResponsiveContainer width="100%" height={220}>
              <LineChart data={trend}>
                <CartesianGrid
                  strokeDasharray="3 3"
                  stroke="#e2e8f0"
                />
                <XAxis
                  dataKey="month"
                  tick={{ fontSize: 12 }}
                  stroke="#94a3b8"
                />
                <YAxis tick={{ fontSize: 12 }} stroke="#94a3b8" />
                <Tooltip
                  formatter={(value) => currency(Number(value))}
                />
                <Line
                  type="monotone"
                  dataKey="revenue"
                  stroke="#2563eb"
                  strokeWidth={2}
                  dot={false}
                />
              </LineChart>
            </ResponsiveContainer>
          )}
        </div>

        <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <h4 className="mb-4 text-sm font-bold text-slate-700">
            Quotes created per month
          </h4>

          {trend.length === 0 ? (
            <p className="py-10 text-center text-sm text-slate-400">
              No historical data yet.
            </p>
          ) : (
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={trend}>
                <CartesianGrid
                  strokeDasharray="3 3"
                  stroke="#e2e8f0"
                />
                <XAxis
                  dataKey="month"
                  tick={{ fontSize: 12 }}
                  stroke="#94a3b8"
                />
                <YAxis
                  tick={{ fontSize: 12 }}
                  stroke="#94a3b8"
                  allowDecimals={false}
                />
                <Tooltip />
                <Bar
                  dataKey="quotes"
                  fill="#0f172a"
                  radius={[6, 6, 0, 0]}
                />
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>

      <div className="grid gap-6 xl:grid-cols-2">
        <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <h4 className="mb-4 text-sm font-bold text-slate-700">
            Top customers by revenue
          </h4>

          {customers.length === 0 ? (
            <p className="text-sm text-slate-400">
              No approved quotes yet.
            </p>
          ) : (
            <table className="w-full text-left text-sm">
              <thead className="text-slate-500">
                <tr>
                  <th className="pb-2 font-medium">Customer</th>
                  <th className="pb-2 text-right font-medium">
                    Quotes
                  </th>
                  <th className="pb-2 text-right font-medium">
                    Revenue
                  </th>
                  <th className="pb-2 text-right font-medium">
                    Approval %
                  </th>
                </tr>
              </thead>
              <tbody>
                {customers.map((c) => (
                  <tr
                    key={c.customer_id}
                    className="border-t border-slate-100"
                  >
                    <td className="py-2 font-medium">
                      {c.customer_name}
                    </td>
                    <td className="py-2 text-right">
                      {c.quote_count}
                    </td>
                    <td className="py-2 text-right">
                      {currency(c.revenue)}
                    </td>
                    <td className="py-2 text-right">
                      {c.approval_rate_pct}%
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>

        <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <h4 className="mb-4 text-sm font-bold text-slate-700">
            Sales rep leaderboard
          </h4>

          {reps.length === 0 ? (
            <p className="text-sm text-slate-400">
              No quotes created yet.
            </p>
          ) : (
            <table className="w-full text-left text-sm">
              <thead className="text-slate-500">
                <tr>
                  <th className="pb-2 font-medium">Rep</th>
                  <th className="pb-2 text-right font-medium">
                    Quotes
                  </th>
                  <th className="pb-2 text-right font-medium">
                    Revenue
                  </th>
                  <th className="pb-2 text-right font-medium">
                    Conversion %
                  </th>
                </tr>
              </thead>
              <tbody>
                {reps.map((r) => (
                  <tr
                    key={r.sales_rep}
                    className="border-t border-slate-100"
                  >
                    <td className="py-2 font-medium">
                      {r.sales_rep}
                    </td>
                    <td className="py-2 text-right">
                      {r.quote_count}
                    </td>
                    <td className="py-2 text-right">
                      {currency(r.revenue)}
                    </td>
                    <td className="py-2 text-right">
                      {r.conversion_rate_pct}%
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>

      {bottlenecks && bottlenecks.oldest_pending.length > 0 && (
        <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <h4 className="mb-4 text-sm font-bold text-slate-700">
            Oldest pending approvals
          </h4>

          <table className="w-full text-left text-sm">
            <thead className="text-slate-500">
              <tr>
                <th className="pb-2 font-medium">Quote</th>
                <th className="pb-2 font-medium">Customer</th>
                <th className="pb-2 font-medium">Rep</th>
                <th className="pb-2 text-right font-medium">
                  Value
                </th>
                <th className="pb-2 text-right font-medium">
                  Age
                </th>
              </tr>
            </thead>
            <tbody>
              {bottlenecks.oldest_pending.map((q) => (
                <tr
                  key={q.quote_id}
                  className="border-t border-slate-100"
                >
                  <td className="py-2 font-mono text-xs font-semibold text-blue-700">
                    {q.quote_id}
                  </td>
                  <td className="py-2">{q.customer_name}</td>
                  <td className="py-2">
                    {q.created_by || "unassigned"}
                  </td>
                  <td className="py-2 text-right">
                    {currency(q.quote_subtotal)}
                  </td>
                  <td className="py-2 text-right">
                    {q.age_hours}h
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
