import { useEffect, useState } from "react";
import { request } from "./api";
import { AdminPage } from "./pages/AdminPage";
import { AcquisitionsPage } from "./pages/AcquisitionsPage";
import { CatalogPage } from "./pages/CatalogPage";
import { CirculationPage } from "./pages/CirculationPage";
import { DashboardPage } from "./pages/DashboardPage";
import { ReaderPortalPage } from "./pages/ReaderPortalPage";
import { ReadersPage } from "./pages/ReadersPage";
import { ReportsPage } from "./pages/ReportsPage";

const staffNavigation = [
  ["dashboard", "Tổng quan"],
  ["catalog", "Sách & kho"],
  ["readers", "Bạn đọc & thu tiền"],
  ["circulation", "Mượn / trả"],
  ["acquisitions", "Nhập sách"],
  ["reports", "Báo cáo"],
  ["admin", "Quản trị"],
];

const demoAccounts = [
  ["Admin", "admin@example.com", "admin123"],
  ["Bạn đọc", "reader@example.com", "reader123"],
];

function Login({ onLoggedIn }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [mode, setMode] = useState("login");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    request("/auth/setup-status")
      .then((status) => {
        if (!status.has_admin) setMode("setup");
      })
      .catch(() => {});
  }, []);

  function fillDemo(nextEmail, nextPassword) {
    setEmail(nextEmail);
    setPassword(nextPassword);
    setError("");
  }

  async function submit(event) {
    event.preventDefault();
    setLoading(true);
    setError("");
    try {
      if (mode === "setup") {
        await request("/auth/bootstrap", { method: "POST", body: { full_name: fullName, email, password } });
      }
      if (mode === "register") {
        await request("/auth/register-reader", {
          method: "POST",
          body: {
            full_name: fullName,
            email,
            password,
          },
        });
      }
      const token = await request("/auth/login", { method: "POST", body: { email, password } });
      onLoggedIn(token.access_token);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  const isRegistering = mode === "register" || mode === "setup";
  const title = mode === "setup" ? "Tạo quản trị viên đầu tiên" : mode === "register" ? "Đăng ký tài khoản bạn đọc" : "Đăng nhập thư viện";

  return <main className="grid min-h-screen place-items-center bg-slate-100 p-5">
    <form onSubmit={submit} className="w-full max-w-lg rounded-lg bg-white p-8 shadow-xl shadow-slate-300/50">
      <p className="text-sm font-semibold uppercase tracking-widest text-indigo-600">Quản lý thư viện</p>
      <h1 className="mt-2 text-3xl font-bold text-slate-900">{title}</h1>
      <p className="mt-2 text-slate-500">
        {mode === "register" ? "Tạo tài khoản trước; sau khi đăng nhập bạn cần đăng ký thẻ đọc thì mới mượn sách được." : "Dùng tài khoản mẫu hoặc tài khoản đã được tạo trong hệ thống."}
      </p>

      {mode === "login" && <div className="mt-5 grid gap-2 rounded-lg border border-slate-200 bg-slate-50 p-3 text-sm">
        <p className="font-semibold text-slate-700">Tài khoản mẫu</p>
        {demoAccounts.map(([label, demoEmail, demoPassword]) => (
          <button key={demoEmail} type="button" onClick={() => fillDemo(demoEmail, demoPassword)} className="flex items-center justify-between rounded-md px-3 py-2 text-left hover:bg-white">
            <span>{label}: <b>{demoEmail}</b></span>
            <span className="text-slate-500">{demoPassword}</span>
          </button>
        ))}
      </div>}

      <div className="mt-6 grid gap-4">
        {isRegistering && <label className="grid gap-1 text-sm font-medium">Họ và tên<input value={fullName} onChange={(event) => setFullName(event.target.value)} required /></label>}
        <label className="grid gap-1 text-sm font-medium">Email<input type="email" value={email} onChange={(event) => setEmail(event.target.value)} required /></label>
        <label className="grid gap-1 text-sm font-medium">Mật khẩu<input type="password" value={password} onChange={(event) => setPassword(event.target.value)} minLength="6" required /></label>
        {error && <p className="rounded-lg bg-rose-50 p-3 text-sm text-rose-700">{error}</p>}
        <button disabled={loading} className="bg-indigo-600 text-white hover:bg-indigo-700">
          {loading ? "Đang xử lý..." : mode === "login" ? "Đăng nhập" : "Tạo tài khoản và đăng nhập"}
        </button>
        {mode !== "setup" && <div className="grid gap-2 text-sm sm:grid-cols-2">
          <button type="button" onClick={() => { setMode(mode === "login" ? "register" : "login"); setError(""); }} className="text-indigo-600 hover:bg-indigo-50">
            {mode === "login" ? "Đăng ký bạn đọc mới" : "Quay lại đăng nhập"}
          </button>
          <button type="button" onClick={() => fillDemo("admin@example.com", "admin123")} className="text-slate-600 hover:bg-slate-50">
            Điền tài khoản admin mẫu
          </button>
        </div>}
      </div>
    </form>
  </main>;
}

function StaffShell({ token, currentUser, onLogout }) {
  const [page, setPage] = useState("dashboard");
  const pageProps = { token };
  const pages = {
    dashboard: <DashboardPage {...pageProps} />,
    catalog: <CatalogPage {...pageProps} />,
    readers: <ReadersPage {...pageProps} />,
    circulation: <CirculationPage {...pageProps} />,
    acquisitions: <AcquisitionsPage {...pageProps} />,
    reports: <ReportsPage {...pageProps} />,
    admin: <AdminPage {...pageProps} currentUser={currentUser} />,
  };
  return <div className="min-h-screen lg:grid lg:grid-cols-[16rem_1fr]">
    <aside className="bg-slate-950 p-5 text-slate-100">
      <div className="mb-2 text-xl font-bold">Thư Viện Số</div>
      <p className="mb-8 text-sm text-slate-400">{currentUser.full_name} · {currentUser.role === "admin" ? "Quản trị" : "Thủ thư"}</p>
      <nav className="flex gap-2 overflow-auto lg:flex-col">
        {staffNavigation.map(([key, label]) => <button key={key} onClick={() => setPage(key)} className={page === key ? "bg-indigo-600 text-left" : "text-left text-slate-300 hover:bg-slate-800"}>{label}</button>)}
      </nav>
      <button onClick={onLogout} className="mt-8 w-full border border-slate-700 text-sm text-slate-300 hover:bg-slate-800">Đăng xuất</button>
    </aside>
    <main className="p-5 lg:p-8">{pages[page]}</main>
  </div>;
}

function AppShell({ token, onLogout }) {
  const [currentUser, setCurrentUser] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    request("/auth/me", { token }).then(setCurrentUser).catch((err) => setError(err.message));
  }, [token]);

  if (error) return <main className="grid min-h-screen place-items-center p-5"><p className="rounded-lg bg-rose-50 p-4 text-rose-700">{error}</p></main>;
  if (!currentUser) return <main className="grid min-h-screen place-items-center p-5"><p className="text-slate-500">Đang tải tài khoản...</p></main>;
  if (currentUser.role === "reader") return <ReaderPortalPage token={token} currentUser={currentUser} onLogout={onLogout} />;
  return <StaffShell token={token} currentUser={currentUser} onLogout={onLogout} />;
}

export default function App() {
  const [token, setToken] = useState(() => localStorage.getItem("library_token"));
  function loggedIn(nextToken) { localStorage.setItem("library_token", nextToken); setToken(nextToken); }
  function logout() { localStorage.removeItem("library_token"); setToken(null); }
  return token ? <AppShell token={token} onLogout={logout} /> : <Login onLoggedIn={loggedIn} />;
}
