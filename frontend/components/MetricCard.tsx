type MetricCardProps = {
  label: string;
  value: string;
  icon?: string;
  trend?: string;
};

export default function MetricCard({
  label,
  value,
  icon,
  trend,
}: MetricCardProps) {
  return (
    <div className="rounded-2xl bg-white border border-slate-200 shadow-sm p-6 hover:shadow-md transition-all">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-slate-500">
            {label}
          </p>

          <h2 className="mt-3 text-3xl font-bold text-slate-900">
            {value}
          </h2>

          {trend && (
            <p className="mt-2 text-sm text-emerald-600 font-medium">
              {trend}
            </p>
          )}
        </div>

        {icon && (
          <div className="flex h-14 w-14 items-center justify-center rounded-xl bg-blue-100 text-2xl">
            {icon}
          </div>
        )}
      </div>
    </div>
  );
}