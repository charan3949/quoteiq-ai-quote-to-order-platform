"use client";

import { useEffect, useState } from "react";
import type { QuoteIntelligenceData } from "../types/quote";

type Props = { apiUrl: string; token: string; quoteId: string };

export default function QuoteIntelligence({ apiUrl, token, quoteId }: Props) {
  const [data, setData] = useState<QuoteIntelligenceData | null>(null);
  useEffect(() => {
    fetch(`${apiUrl}/enterprise/quotes/${quoteId}/intelligence`, { headers: { Authorization: `Bearer ${token}` } })
      .then(async r => { const d = await r.json(); if (!r.ok) throw new Error(d.detail); return d; })
      .then(setData).catch(() => setData(null));
  }, [apiUrl, token, quoteId]);
  if (!data) return null;
  return <div className="mt-6 grid gap-6 xl:grid-cols-2">
    <section className="rounded-2xl border border-blue-200 bg-blue-50 p-6"><div className="flex items-start justify-between"><div><p className="text-xs font-bold uppercase tracking-widest text-blue-700">AI Insights</p><h3 className="mt-2 text-xl font-bold">{data.recommendation}</h3></div><span className="rounded-full bg-white px-3 py-1 text-xs font-bold text-blue-700">{data.confidence_pct}% confidence</span></div><p className="mt-4 text-sm font-semibold">Risk: {data.risk_level}</p><ul className="mt-4 space-y-2 text-sm text-slate-700">{data.reasons.map(r=><li key={r}>✓ {r}</li>)}</ul></section>
    <section className="rounded-2xl border bg-white p-6 shadow-sm"><p className="text-xs font-bold uppercase tracking-widest text-slate-500">Quote Timeline</p><div className="mt-5 space-y-4">{data.timeline.map((e,i)=><div key={`${e.event}-${i}`} className="flex gap-3"><div className="mt-1 h-3 w-3 rounded-full bg-blue-600"/><div><p className="font-semibold">{e.event.replaceAll("_"," ")}</p><p className="text-xs text-slate-500">{e.timestamp ? new Date(e.timestamp).toLocaleString() : "Pending"}</p>{e.details && <p className="mt-1 text-sm text-slate-600">{e.details}</p>}</div></div>)}</div></section>
  </div>;
}
