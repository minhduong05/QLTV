import { useEffect, useState } from "react";
import { request } from "../api";
import { Card, ErrorBox, PageTitle, Table } from "../components/ui";

const roleLabels = { admin: "Quản trị", librarian: "Thủ thư", reader: "Bạn đọc" };

export function AdminPage({ token, currentUser }) {
  const [users, setUsers] = useState([]);
  const [settings, setSettings] = useState([]);
  const [form, setForm] = useState({ full_name: "", email: "", password: "", role: "librarian" });
  const [error, setError] = useState("");
  const [saved, setSaved] = useState("");

  const load = async () => {
    const [userData, settingData] = await Promise.all([request("/users", { token }), request("/settings", { token })]);
    setUsers(userData);
    setSettings(settingData);
  };

  useEffect(() => { load().catch((err) => setError(err.message)); }, [token]);

  async function runAction(action, successMessage) {
    setError("");
    setSaved("");
    try {
      await action();
      setSaved(successMessage);
      await load();
    } catch (err) {
      setError(err.message);
    }
  }

  async function addUser(event) {
    event.preventDefault();
    await runAction(
      () => request("/users", { token, method: "POST", body: form }),
      "Đã tạo tài khoản nội bộ."
    );
    setForm({ full_name: "", email: "", password: "", role: "librarian" });
  }

  function toggleUserActive(user) {
    const nextActive = !user.is_active;
    return runAction(
      () => request(`/users/${user.id}`, { token, method: "PATCH", body: { is_active: nextActive } }),
      nextActive ? "Đã mở khóa tài khoản." : "Đã khóa tài khoản."
    );
  }

  function deleteUser(user) {
    const confirmed = window.confirm(`Xóa tài khoản "${user.email}" khỏi hệ thống? Chỉ tài khoản đã qua 1 ngày và chưa phát sinh nghiệp vụ mới được xóa. Tài khoản đã phát sinh nghiệp vụ nên khóa để giữ lịch sử.`);
    if (!confirmed) return null;
    return runAction(
      () => request(`/users/${user.id}`, { token, method: "DELETE" }),
      "Đã xóa tài khoản."
    );
  }

  async function saveSetting(item) {
    await runAction(
      () => request(`/settings/${item.key}`, { token, method: "PUT", body: { value: item.value, description: item.description } }),
      `Đã lưu ${item.key}`
    );
  }

  return <>
    <PageTitle title="Quản trị hệ thống" description="Tài khoản vận hành, quyền truy cập và quy định mượn/trả được kiểm soát tại đây." />
    <ErrorBox message={error} />
    {saved && <p className="mb-4 rounded-lg bg-emerald-50 p-3 text-sm text-emerald-700">{saved}</p>}
    <div className="grid gap-6 xl:grid-cols-2">
      <Card>
        <h2 className="font-semibold">Người dùng hệ thống</h2>
        <Table>
          <thead className="bg-slate-50 text-slate-500">
            <tr>
              <th className="p-3">Họ tên</th>
              <th className="p-3">Email</th>
              <th className="p-3">Vai trò</th>
              <th className="p-3">Trạng thái</th>
              <th className="p-3">Thao tác</th>
            </tr>
          </thead>
          <tbody>
            {users.map((item) => {
              const isSelf = currentUser?.id === item.id;
              return <tr className="border-t" key={item.id}>
                <td className="p-3">{item.full_name}</td>
                <td className="p-3">{item.email}</td>
                <td className="p-3">{roleLabels[item.role] ?? item.role}</td>
                <td className={item.is_active ? "p-3 text-emerald-700" : "p-3 text-rose-600"}>{item.is_active ? "Hoạt động" : "Đã khóa"}</td>
                <td className="p-3">
                  <div className="flex flex-wrap gap-2">
                    <button disabled={isSelf} onClick={() => toggleUserActive(item)} className={isSelf ? "border border-slate-200 text-xs text-slate-400" : "border border-slate-300 text-xs hover:bg-slate-50"}>
                      {item.is_active ? "Khóa" : "Mở khóa"}
                    </button>
                    <button disabled={isSelf} onClick={() => deleteUser(item)} className={isSelf ? "border border-slate-200 text-xs text-slate-400" : "border border-rose-200 text-xs text-rose-700 hover:bg-rose-50"}>
                      Xóa
                    </button>
                  </div>
                </td>
              </tr>;
            })}
          </tbody>
        </Table>

        <form onSubmit={addUser} className="mt-4 grid gap-3 sm:grid-cols-2">
          <input placeholder="Họ tên" value={form.full_name} onChange={(event) => setForm({ ...form, full_name: event.target.value })} required />
          <input type="email" placeholder="Email" value={form.email} onChange={(event) => setForm({ ...form, email: event.target.value })} required />
          <input type="password" minLength="6" placeholder="Mật khẩu" value={form.password} onChange={(event) => setForm({ ...form, password: event.target.value })} required />
          <select value={form.role} onChange={(event) => setForm({ ...form, role: event.target.value })}>
            <option value="librarian">Thủ thư</option>
            <option value="admin">Quản trị viên</option>
          </select>
          <button className="bg-indigo-600 text-white sm:col-span-2">Tạo người dùng nội bộ</button>
        </form>
      </Card>

      <Card>
        <h2 className="font-semibold">Quy định thư viện</h2>
        <div className="mt-4 grid gap-3">
          {settings.map((item) => <div key={item.key} className="grid gap-2 rounded-lg border border-slate-200 p-3 sm:grid-cols-[1fr_6rem_auto]">
            <label className="text-sm"><b>{item.key}</b><span className="mt-1 block text-slate-500">{item.description}</span></label>
            <input value={item.value} onChange={(event) => setSettings(settings.map((entry) => entry.key === item.key ? { ...entry, value: event.target.value } : entry))} />
            <button onClick={() => saveSetting(item)} className="border border-slate-300 text-sm hover:bg-slate-50">Lưu</button>
          </div>)}
        </div>
      </Card>
    </div>
  </>;
}
