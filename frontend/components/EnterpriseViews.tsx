"use client";

import { useEffect, useMemo, useState } from "react";
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

import type {
  CustomerPortfolio,
  DashboardSummary,
  EnterpriseOrder,
  RepPerformance,
  TopCustomer,
  TrendPoint,
} from "../types/quote";

type View = "analytics" | "customers" | "erp" | "revenue" | "sales";

type Props = { apiUrl: string; token: string; view: View };

async function getJson(url: string, token: string) {
  const response = await fetch(url, { headers: { Authorization: `Bearer ${token}` } });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(data.detail || `Request failed (${response.status})`);
  return data;
}

const money = (value: number) => `$${value.toLocaleString(undefined, { maximumFractionDigits: 0 })}`;

export default function EnterpriseViews({ apiUrl, token, view }: Props) {
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [trend, setTrend] = useState<TrendPoint[]>([]);
  const [customers, setCustomers] = useState<CustomerPortfolio[]>([]);
  const [topCustomers, setTopCustomers] = useState<TopCustomer[]>([]);
  const [reps, setReps] = useState<RepPerformance[]>([]);
  const [orders, setOrders] = useState<EnterpriseOrder[]>([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    setError("");
    const calls: Promise<unknown>[] = [];
    if (["analytics", "revenue"].includes(view)) {
      calls.push(getJson(`${apiUrl}/analytics/summary`, token).then(setSummary));
      calls.push(getJson(`${apiUrl}/analytics/trend?months=12`, token).then((d) => setTrend(d.months || [])));
      calls.push(getJson(`${apiUrl}/analytics/customers?limit=10`, token).then((d) => setTopCustomers(d.customers || [])));
    }
    if (view === "customers") calls.push(getJson(`${apiUrl}/enterprise/customers`, token).then((d) => setCustomers(d.customers || [])));
    if (view === "sales") calls.push(getJson(`${apiUrl}/analytics/reps`, token).then((d) => setReps(d.reps || [])));
    if (view === "erp") calls.push(getJson(`${apiUrl}/enterprise/orders`, token).then((d) => setOrders(d.orders || [])));
    Promise.all(calls).catch((e) => setError(e instanceof Error ? e.message : "Unable to load data")).finally(() => setLoading(false));
  }, [apiUrl, token, view]);

  const orderTotal = useMemo(() => orders.reduce((sum, order) => sum + order.order_total, 0), [orders]);

  if (loading) return <Panel>Loading {view}...</Panel>;
  if (error) return <div className="rounded-2xl border border-red-200 bg-red-50 p-6 text-red-700">{error}</div>;

  if (view === "analytics") return (
    <div className="space-y-6">
      <Heading title="Analytics Center" subtitle="Operational performance across the complete quote-to-order funnel." />
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <Kpi label="Quotes" value={String(summary?.total_quotes ?? 0)} />
        <Kpi label="Approved revenue" value={money(summary?.revenue ?? 0)} />
        <Kpi label="Conversion" value={`${summary?.conversion_rate_pct ?? 0}%`} />
        <Kpi label="Avg quote" value={money(summary?.avg_quote_value ?? 0)} />
      </div>
      <ChartCard title="Quote volume and conversions"><ResponsiveContainer width="100%" height={300}><BarChart data={trend}><CartesianGrid strokeDasharray="3 3"/><XAxis dataKey="month"/><YAxis/><Tooltip/><Bar dataKey="quotes" fill="#2563eb"/><Bar dataKey="converted" fill="#10b981"/></BarChart></ResponsiveContainer></ChartCard>
    </div>
  );

  if (view === "customers") return (
    <div className="space-y-6"><Heading title="Customer Management" subtitle="Customer value, pipeline, pricing tier and credit visibility." />
      <div className="overflow-hidden rounded-2xl border bg-white shadow-sm"><table className="min-w-full text-left text-sm"><thead className="bg-slate-50"><tr>{["Customer","Price tier","Credit","Quotes","Approval","Revenue","Pipeline"].map(x=><th key={x} className="px-5 py-4">{x}</th>)}</tr></thead><tbody>{customers.map(c=><tr key={c.customer_id} className="border-t"><td className="px-5 py-4"><p className="font-semibold">{c.customer_name}</p><p className="text-xs text-slate-500">{c.customer_id} · {c.branch_id}</p></td><td className="px-5 py-4">{c.price_class}</td><td className="px-5 py-4"><Badge good={c.credit_status === "GOOD"}>{c.credit_status}</Badge></td><td className="px-5 py-4">{c.quote_count}</td><td className="px-5 py-4">{c.approval_rate_pct}%</td><td className="px-5 py-4 font-semibold">{money(c.revenue)}</td><td className="px-5 py-4">{money(c.pipeline)}</td></tr>)}</tbody></table></div>
    </div>
  );

  if (view === "erp") return (
    <div className="space-y-6"><Heading title="ERP Order Dashboard" subtitle="Approved quotes converted into ERP-ready sales orders." />
      <div className="grid gap-4 md:grid-cols-3"><Kpi label="ERP orders" value={String(orders.length)}/><Kpi label="Order value" value={money(orderTotal)}/><Kpi label="Integration" value="MOCK ERP"/></div>
      <div className="grid gap-4">{orders.map(o=><div key={o.sales_order_id} className="rounded-2xl border bg-white p-6 shadow-sm"><div className="flex flex-wrap items-start justify-between gap-4"><div><p className="font-mono text-sm font-bold text-blue-700">{o.sales_order_id}</p><h3 className="mt-1 text-lg font-bold">{o.customer_name}</h3><p className="text-sm text-slate-500">Source quote {o.source_quote_id}</p></div><Badge good>{o.order_status}</Badge></div><div className="mt-5 grid gap-4 sm:grid-cols-4"><Mini label="Order total" value={money(o.order_total)}/><Mini label="Lines" value={String(o.line_count)}/><Mini label="Target" value={o.target_erp}/><Mini label="Created" value={o.created_at ? new Date(o.created_at).toLocaleDateString() : "—"}/></div></div>)}</div>
    </div>
  );

  if (view === "revenue") return (
    <div className="space-y-6"><Heading title="Revenue Reports" subtitle="Revenue trend, customer concentration and pipeline conversion." />
      <div className="grid gap-4 md:grid-cols-3"><Kpi label="Approved revenue" value={money(summary?.revenue ?? 0)}/><Kpi label="Average quote" value={money(summary?.avg_quote_value ?? 0)}/><Kpi label="Converted orders" value={String(summary?.converted_quotes ?? 0)}/></div>
      <ChartCard title="Monthly approved revenue"><ResponsiveContainer width="100%" height={300}><LineChart data={trend}><CartesianGrid strokeDasharray="3 3"/><XAxis dataKey="month"/><YAxis/><Tooltip formatter={(v)=>money(Number(v))}/><Line type="monotone" dataKey="revenue" stroke="#2563eb" strokeWidth={3}/></LineChart></ResponsiveContainer></ChartCard>
      <div className="rounded-2xl border bg-white p-6 shadow-sm"><h3 className="mb-4 font-bold">Top customers by revenue</h3>{topCustomers.map((c,i)=><div key={c.customer_id} className="flex items-center justify-between border-t py-3 first:border-t-0"><span>{i+1}. {c.customer_name}</span><span className="font-semibold">{money(c.revenue)}</span></div>)}</div>
    </div>
  );

  return (
    <div className="space-y-6"><Heading title="Sales Performance Dashboard" subtitle="Rep productivity, conversion, margin quality and cycle time." />
      <div className="overflow-hidden rounded-2xl border bg-white shadow-sm"><table className="min-w-full text-left text-sm"><thead className="bg-slate-50"><tr>{["Sales rep","Quotes","Revenue","Conversion","Avg margin","Approval time"].map(x=><th key={x} className="px-5 py-4">{x}</th>)}</tr></thead><tbody>{reps.map(r=><tr key={r.sales_rep} className="border-t"><td className="px-5 py-4 font-semibold">{r.sales_rep}</td><td className="px-5 py-4">{r.quote_count}</td><td className="px-5 py-4 font-semibold">{money(r.revenue)}</td><td className="px-5 py-4">{r.conversion_rate_pct}%</td><td className="px-5 py-4">{r.avg_margin_pct}%</td><td className="px-5 py-4">{r.avg_approval_time_hours == null ? "N/A" : `${r.avg_approval_time_hours}h`}</td></tr>)}</tbody></table></div>
    </div>
  );
}

function Heading({title, subtitle}:{title:string;subtitle:string}) { return <div><h2 className="text-2xl font-bold">{title}</h2><p className="mt-1 text-sm text-slate-500">{subtitle}</p></div>; }
function Kpi({label,value}:{label:string;value:string}) { return <div className="rounded-2xl border bg-white p-5 shadow-sm"><p className="text-xs font-semibold uppercase tracking-wider text-slate-500">{label}</p><p className="mt-2 text-3xl font-bold">{value}</p></div>; }
function Mini({label,value}:{label:string;value:string}) { return <div><p className="text-xs uppercase tracking-wide text-slate-400">{label}</p><p className="mt-1 font-semibold">{value}</p></div>; }
function Badge({children,good}:{children:React.ReactNode;good?:boolean}) { return <span className={`rounded-full px-3 py-1 text-xs font-semibold ${good ? "bg-emerald-100 text-emerald-700" : "bg-amber-100 text-amber-700"}`}>{children}</span>; }
function Panel({children}:{children:React.ReactNode}) { return <div className="rounded-2xl border bg-white p-8 text-center text-slate-500">{children}</div>; }
function ChartCard({title,children}:{title:string;children:React.ReactNode}) { return <div className="rounded-2xl border bg-white p-6 shadow-sm"><h3 className="mb-5 font-bold">{title}</h3>{children}</div>; }
