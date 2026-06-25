export function PageTitle({ title, description, action }) {
  return <header className="mb-6 flex flex-wrap items-end justify-between gap-3"><div><h1 className="text-2xl font-bold text-slate-900">{title}</h1>{description && <p className="mt-1 text-slate-500">{description}</p>}</div>{action}</header>;
}

export function ErrorBox({ message }) { return message ? <p className="mb-4 rounded-lg bg-rose-50 p-3 text-sm text-rose-700">{message}</p> : null; }

export function Card({ children, className = "" }) { return <section className={`rounded-lg bg-white p-5 shadow-sm ${className}`}>{children}</section>; }

export function Stat({ label, value, warning }) { return <Card><p className="text-sm font-medium text-slate-500">{label}</p><p className={`mt-2 text-3xl font-bold ${warning ? "text-rose-600" : "text-slate-900"}`}>{value ?? "—"}</p></Card>; }

export function Table({ children }) { return <div className="overflow-x-auto rounded-lg bg-white shadow-sm"><table className="w-full text-left text-sm">{children}</table></div>; }
