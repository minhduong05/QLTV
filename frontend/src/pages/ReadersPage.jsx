import { useEffect, useState } from "react";
import { request } from "../api";
import { Card, ErrorBox, PageTitle, Table } from "../components/ui";

const initialReader = { card_number: "", full_name: "", email: "", phone: "", expires_at: "" };

const cardRequestLabels = {
  pending: "Chờ duyệt",
  approved: "Đã duyệt",
  rejected: "Từ chối",
  cancelled: "Đã hủy",
};

export function ReadersPage({ token }) {
  const [readers, setReaders] = useState([]);
  const [cardRequests, setCardRequests] = useState([]);
  const [types, setTypes] = useState([]);
  const [form, setForm] = useState(initialReader);
  const [payment, setPayment] = useState({ reader_id: "", amount: "", note: "" });
  const [readerTypeName, setReaderTypeName] = useState("");
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  const load = async () => {
    const [readerData, requestData, typeData] = await Promise.all([
      request("/readers", { token }),
      request("/readers/card-requests", { token }),
      request("/readers/types", { token }),
    ]);
    setReaders(readerData);
    setCardRequests(requestData);
    setTypes(typeData);
  };

  useEffect(() => { load().catch((err) => setError(err.message)); }, [token]);

  async function runAction(action, successMessage) {
    setError("");
    setMessage("");
    try {
      await action();
      setMessage(successMessage);
      await load();
    } catch (err) {
      setError(err.message);
    }
  }

  async function createReader(event) {
    event.preventDefault();
    await runAction(
      () => request("/readers", { token, method: "POST", body: { ...form, email: form.email || null, phone: form.phone || null, reader_type_id: form.reader_type_id ? Number(form.reader_type_id) : null } }),
      "Đã tạo thẻ bạn đọc trực tiếp."
    );
    setForm(initialReader);
  }

  async function createReaderType(event) {
    event.preventDefault();
    await runAction(
      () => request("/readers/types", { token, method: "POST", body: { name: readerTypeName } }),
      "Đã thêm loại bạn đọc."
    );
    setReaderTypeName("");
  }

  async function collectPayment(event) {
    event.preventDefault();
    await runAction(
      () => request("/readers/payments", { token, method: "POST", body: { reader_id: Number(payment.reader_id), amount: Number(payment.amount), note: payment.note || null } }),
      "Đã lập phiếu thu tiền phạt."
    );
    setPayment({ reader_id: "", amount: "", note: "" });
  }

  function approveCardRequest(requestId) {
    return runAction(
      () => request(`/readers/card-requests/${requestId}/approve`, { token, method: "POST", body: { note: "Hồ sơ hợp lệ, cấp thẻ online." } }),
      "Đã duyệt yêu cầu và tạo thẻ bạn đọc."
    );
  }

  function rejectCardRequest(requestId) {
    return runAction(
      () => request(`/readers/card-requests/${requestId}/reject`, { token, method: "POST", body: { note: "Hồ sơ chưa đủ thông tin, vui lòng cập nhật và gửi lại." } }),
      "Đã từ chối yêu cầu cấp thẻ."
    );
  }

  const pendingCardRequests = cardRequests.filter((item) => item.status === "pending");
  const recentCardRequests = cardRequests.filter((item) => item.status !== "pending").slice(0, 8);

  return <>
    <PageTitle title="Bạn đọc và thu tiền" description="Quản lý thẻ thư viện, duyệt yêu cầu cấp thẻ online, hạn thẻ và công nợ quá hạn." />
    <ErrorBox message={error} />
    {message && <p className="mb-4 rounded-lg bg-emerald-50 p-3 text-sm text-emerald-700">{message}</p>}
    <div className="grid gap-6 xl:grid-cols-[1fr_21rem]">
      <div className="grid gap-4">
        <Card>
          <h2 className="font-semibold">Yêu cầu cấp thẻ online</h2>
          <div className="mt-4 divide-y">
            {pendingCardRequests.map((item) => <div key={item.id} className="flex flex-wrap items-center justify-between gap-3 py-3">
              <div>
                <p className="font-medium">{item.full_name}</p>
                <p className="text-sm text-slate-500">{item.email} · {item.phone} · {new Date(item.requested_at).toLocaleDateString("vi-VN")}</p>
                <p className="text-sm text-slate-500">{item.address}</p>
              </div>
              <div className="flex gap-2">
                <button onClick={() => approveCardRequest(item.id)} className="bg-indigo-600 text-sm text-white">Duyệt cấp thẻ</button>
                <button onClick={() => rejectCardRequest(item.id)} className="border border-slate-300 text-sm hover:bg-slate-50">Từ chối</button>
              </div>
            </div>)}
            {!pendingCardRequests.length && <p className="py-3 text-sm text-slate-500">Không có yêu cầu cấp thẻ đang chờ.</p>}
          </div>
        </Card>

        <Table>
          <thead className="bg-slate-50 text-slate-500"><tr><th className="p-4">Bạn đọc</th><th className="p-4">Liên hệ</th><th className="p-4">Hạn thẻ</th><th className="p-4">Công nợ</th></tr></thead>
          <tbody>
            {readers.map((reader) => <tr key={reader.id} className="border-t">
              <td className="p-4 font-medium">{reader.full_name}<div className="text-xs font-normal text-slate-500">{reader.card_number}</div></td>
              <td className="p-4">{reader.email || reader.phone || "—"}</td>
              <td className="p-4">{reader.expires_at}</td>
              <td className={reader.balance ? "p-4 font-semibold text-rose-600" : "p-4 text-emerald-600"}>{reader.balance.toLocaleString("vi-VN")} đ</td>
            </tr>)}
            {!readers.length && <tr><td colSpan="4" className="p-8 text-center text-slate-500">Chưa có bạn đọc.</td></tr>}
          </tbody>
        </Table>
      </div>

      <div className="grid content-start gap-4">
        <Card>
          <h2 className="font-semibold">Tạo thẻ bạn đọc tại quầy</h2>
          <form onSubmit={createReader} className="mt-4 grid gap-3">
            <input placeholder="Mã thẻ" value={form.card_number} onChange={(event) => setForm({ ...form, card_number: event.target.value })} required />
            <input placeholder="Họ và tên" value={form.full_name} onChange={(event) => setForm({ ...form, full_name: event.target.value })} required />
            <input type="email" placeholder="Email" value={form.email} onChange={(event) => setForm({ ...form, email: event.target.value })} />
            <input placeholder="Số điện thoại" value={form.phone} onChange={(event) => setForm({ ...form, phone: event.target.value })} />
            <select value={form.reader_type_id || ""} onChange={(event) => setForm({ ...form, reader_type_id: event.target.value })}>
              <option value="">Loại bạn đọc</option>
              {types.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}
            </select>
            <label className="text-sm">Hạn thẻ<input className="mt-1 w-full" type="date" value={form.expires_at} onChange={(event) => setForm({ ...form, expires_at: event.target.value })} required /></label>
            <button className="bg-indigo-600 text-white">Lưu thẻ</button>
          </form>
        </Card>

        <Card>
          <h2 className="font-semibold">Loại bạn đọc</h2>
          <form onSubmit={createReaderType} className="mt-4 grid gap-3">
            <input placeholder="Ví dụ: Sinh viên, Giảng viên" value={readerTypeName} onChange={(event) => setReaderTypeName(event.target.value)} required />
            <button className="bg-slate-800 text-white">Thêm loại</button>
          </form>
        </Card>

        <Card>
          <h2 className="font-semibold">Thu tiền phạt</h2>
          <form onSubmit={collectPayment} className="mt-4 grid gap-3">
            <select value={payment.reader_id} onChange={(event) => setPayment({ ...payment, reader_id: event.target.value })} required>
              <option value="">Chọn bạn đọc</option>
              {readers.filter((reader) => reader.balance > 0).map((reader) => <option key={reader.id} value={reader.id}>{reader.card_number} · {reader.full_name} ({reader.balance.toLocaleString("vi-VN")} đ)</option>)}
            </select>
            <input type="number" min="1" placeholder="Số tiền thu" value={payment.amount} onChange={(event) => setPayment({ ...payment, amount: event.target.value })} required />
            <input placeholder="Ghi chú" value={payment.note} onChange={(event) => setPayment({ ...payment, note: event.target.value })} />
            <button className="bg-emerald-600 text-white">Lập phiếu thu</button>
          </form>
        </Card>

        <Card>
          <h2 className="font-semibold">Yêu cầu thẻ gần đây</h2>
          <div className="mt-3 divide-y">
            {recentCardRequests.map((item) => <div key={item.id} className="py-3 text-sm">
              <p className="font-medium">{item.full_name}</p>
              <p className="text-slate-500">{cardRequestLabels[item.status] ?? item.status}{item.reader_id ? ` · thẻ #${item.reader_id}` : ""}</p>
            </div>)}
            {!recentCardRequests.length && <p className="py-3 text-sm text-slate-500">Chưa có yêu cầu đã xử lý.</p>}
          </div>
        </Card>
      </div>
    </div>
  </>;
}
