import { useEffect, useMemo, useState } from "react";
import { request } from "../api";
import { Card, ErrorBox, PageTitle, Table } from "../components/ui";

const initialReader = {
  card_number: "",
  full_name: "",
  cccd: "",
  email: "",
  phone: "",
  address: "",
  date_of_birth: "",
  reader_type_id: "",
  expires_at: "",
};

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
  const [selectedCardRequest, setSelectedCardRequest] = useState(null);
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

  const pendingCardRequests = cardRequests.filter((item) => item.status === "pending");
  const recentCardRequests = cardRequests.filter((item) => item.status !== "pending").slice(0, 8);
  const debtReaders = readers.filter((reader) => reader.balance > 0);
  const selectedDebtReader = useMemo(() => readers.find((reader) => reader.id === Number(payment.reader_id)), [readers, payment.reader_id]);
  const selectedCardRequestType = types.find((item) => item.id === selectedCardRequest?.reader_type_id);

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
      () => request("/readers", {
        token,
        method: "POST",
        body: {
          ...form,
          email: form.email || null,
          phone: form.phone || null,
          address: form.address || null,
          date_of_birth: form.date_of_birth || null,
          reader_type_id: form.reader_type_id ? Number(form.reader_type_id) : null,
        },
      }),
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
      "Đã lập phiếu thu. Công nợ bạn đọc đã được giảm tương ứng."
    );
    setPayment({ reader_id: "", amount: "", note: "" });
  }

  function approveCardRequest(requestId) {
    setSelectedCardRequest(null);
    return runAction(
      () => request(`/readers/card-requests/${requestId}/approve`, { token, method: "POST", body: { note: "Hồ sơ hợp lệ, cấp thẻ online." } }),
      "Đã duyệt yêu cầu và tạo thẻ bạn đọc."
    );
  }

  function rejectCardRequest(requestId) {
    const note = window.prompt("Lý do từ chối", "Hồ sơ chưa đủ thông tin, vui lòng cập nhật và gửi lại.");
    if (note === null) return null;
    setSelectedCardRequest(null);
    return runAction(
      () => request(`/readers/card-requests/${requestId}/reject`, { token, method: "POST", body: { note } }),
      "Đã từ chối yêu cầu cấp thẻ."
    );
  }

  return <>
    <PageTitle title="Bạn đọc, cấp thẻ và thu phạt" description="Duyệt thẻ đọc online, tạo thẻ tại quầy, theo dõi công nợ và lập phiếu thu." />
    <ErrorBox message={error} />
    {message && <p className="mb-4 rounded-lg bg-emerald-50 p-3 text-sm text-emerald-700">{message}</p>}

    <div className="grid gap-6 xl:grid-cols-[1fr_23rem]">
      <div className="grid gap-4">
        <Card>
          <h2 className="font-semibold">Duyệt yêu cầu cấp thẻ online</h2>
          <div className="mt-4 divide-y">
            {pendingCardRequests.map((item) => <div key={item.id} className="flex flex-wrap items-center justify-between gap-3 py-3">
              <div>
                <p className="font-medium">{item.full_name}</p>
                <p className="text-sm text-slate-500">{item.email} · {item.phone} · {new Date(item.requested_at).toLocaleDateString("vi-VN")}</p>
                <p className="text-sm text-slate-500">CCCD: {item.cccd || "Chưa có"} · Ngày sinh: {item.date_of_birth}</p>
              </div>
              <div className="flex gap-2">
                <button onClick={() => setSelectedCardRequest(item)} className="bg-slate-800 text-sm text-white">Xem chi tiết</button>
                <button onClick={() => rejectCardRequest(item.id)} className="border border-slate-300 text-sm hover:bg-slate-50">Từ chối</button>
              </div>
            </div>)}
            {!pendingCardRequests.length && <p className="py-3 text-sm text-slate-500">Không có yêu cầu cấp thẻ đang chờ.</p>}
          </div>
        </Card>

        {selectedCardRequest && <Card>
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <h2 className="font-semibold">Chi tiết yêu cầu cấp thẻ</h2>
              <p className="mt-1 text-sm text-slate-500">Kiểm tra hồ sơ trước khi duyệt tạo thẻ bạn đọc.</p>
            </div>
            <button onClick={() => setSelectedCardRequest(null)} className="border border-slate-300 text-sm hover:bg-slate-50">Đóng</button>
          </div>
          <dl className="mt-4 grid gap-3 text-sm md:grid-cols-2">
            <div><dt className="text-slate-500">Họ tên</dt><dd className="font-medium">{selectedCardRequest.full_name}</dd></div>
            <div><dt className="text-slate-500">CCCD</dt><dd className="font-medium">{selectedCardRequest.cccd || "Chưa có"}</dd></div>
            <div><dt className="text-slate-500">Email</dt><dd className="font-medium">{selectedCardRequest.email}</dd></div>
            <div><dt className="text-slate-500">Số điện thoại</dt><dd className="font-medium">{selectedCardRequest.phone}</dd></div>
            <div><dt className="text-slate-500">Ngày sinh</dt><dd className="font-medium">{selectedCardRequest.date_of_birth}</dd></div>
            <div><dt className="text-slate-500">Loại bạn đọc</dt><dd className="font-medium">{selectedCardRequestType?.name || "Chưa chọn"}</dd></div>
            <div className="md:col-span-2"><dt className="text-slate-500">Địa chỉ</dt><dd className="font-medium">{selectedCardRequest.address}</dd></div>
          </dl>
          <div className="mt-4 flex flex-wrap gap-2">
            <button onClick={() => approveCardRequest(selectedCardRequest.id)} className="bg-indigo-600 text-sm text-white">Duyệt cấp thẻ</button>
            <button onClick={() => rejectCardRequest(selectedCardRequest.id)} className="border border-slate-300 text-sm hover:bg-slate-50">Từ chối</button>
          </div>
        </Card>}

        <Table>
          <thead className="bg-slate-50 text-slate-500"><tr><th className="p-4">Bạn đọc</th><th className="p-4">Liên hệ</th><th className="p-4">Hạn thẻ</th><th className="p-4">Công nợ</th></tr></thead>
          <tbody>
            {readers.map((reader) => <tr key={reader.id} className="border-t">
              <td className="p-4 font-medium">{reader.full_name}<div className="text-xs font-normal text-slate-500">{reader.card_number}{reader.cccd ? ` · CCCD ${reader.cccd}` : ""}</div></td>
              <td className="p-4">{reader.email || reader.phone || "—"}<div className="text-xs text-slate-500">{reader.address || ""}</div></td>
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
            <input placeholder="CCCD/CMND" value={form.cccd} onChange={(event) => setForm({ ...form, cccd: event.target.value })} minLength="9" maxLength="20" required />
            <input type="email" placeholder="Email" value={form.email} onChange={(event) => setForm({ ...form, email: event.target.value })} />
            <input placeholder="Số điện thoại" value={form.phone} onChange={(event) => setForm({ ...form, phone: event.target.value })} />
            <label className="text-sm">Ngày sinh<input className="mt-1 w-full" type="date" value={form.date_of_birth} onChange={(event) => setForm({ ...form, date_of_birth: event.target.value })} /></label>
            <input placeholder="Địa chỉ" value={form.address} onChange={(event) => setForm({ ...form, address: event.target.value })} />
            <select value={form.reader_type_id} onChange={(event) => setForm({ ...form, reader_type_id: event.target.value })}>
              <option value="">Loại bạn đọc</option>
              {types.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}
            </select>
            <label className="text-sm">Hạn thẻ<input className="mt-1 w-full" type="date" value={form.expires_at} onChange={(event) => setForm({ ...form, expires_at: event.target.value })} required /></label>
            <button className="bg-indigo-600 text-white">Lưu thẻ</button>
          </form>
        </Card>

        <Card>
          <h2 className="font-semibold">Thu tiền phạt / công nợ</h2>
          <p className="mt-2 text-sm text-slate-500">Công nợ chỉ phát sinh khi nhận trả sách quá hạn. Phiếu thu ở đây chỉ ghi nhận số tiền bạn đọc đã nộp và trừ vào công nợ.</p>
          <form onSubmit={collectPayment} className="mt-4 grid gap-3">
            <select value={payment.reader_id} onChange={(event) => setPayment({ ...payment, reader_id: event.target.value, amount: "" })} required>
              <option value="">Chọn bạn đọc đang có công nợ</option>
              {debtReaders.map((reader) => <option key={reader.id} value={reader.id}>{reader.card_number} · {reader.full_name} ({reader.balance.toLocaleString("vi-VN")} đ)</option>)}
            </select>
            {selectedDebtReader && <div className="rounded-lg bg-rose-50 p-3 text-sm text-rose-700">
              Công nợ hiện tại: <b>{selectedDebtReader.balance.toLocaleString("vi-VN")} đ</b>
              <button type="button" onClick={() => setPayment({ ...payment, amount: String(selectedDebtReader.balance) })} className="ml-3 border border-rose-200 text-xs text-rose-700 hover:bg-white">Thu toàn bộ</button>
            </div>}
            <input type="number" min="1" max={selectedDebtReader?.balance || undefined} placeholder="Số tiền thu" value={payment.amount} onChange={(event) => setPayment({ ...payment, amount: event.target.value })} required />
            <input placeholder="Ghi chú phiếu thu" value={payment.note} onChange={(event) => setPayment({ ...payment, note: event.target.value })} />
            <button disabled={!selectedDebtReader} className={selectedDebtReader ? "bg-emerald-600 text-white" : "border border-slate-300 text-slate-400"}>Lập phiếu thu</button>
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
