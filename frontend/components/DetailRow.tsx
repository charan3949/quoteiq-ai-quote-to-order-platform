type DetailRowProps = {
  label: string;
  value: string;
};

export default function DetailRow({
  label,
  value,
}: DetailRowProps) {
  return (
    <div className="flex items-center justify-between border-b border-slate-100 pb-4">
      <span className="text-sm text-slate-500">{label}</span>
      <span className="text-sm font-semibold">{value}</span>
    </div>
  );
}