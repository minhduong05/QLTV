import { useEffect, useMemo, useState } from "react";
import { request } from "../api";
import { Card, ErrorBox, PageTitle } from "../components/ui";

const ticketStatusLabels = {
  pending_review: "Chờ kiểm tra",
  changes_requested: "Chờ bạn đọc phản hồi",
  approved_waiting_pickup: "Đã duyệt, chờ lấy",
  borrowed: "Đã mượn",
  rejected: "Từ chối",
  cancelled: "Đã hủy",
};

const itemStatusLabels = {
  pending: "Chờ kiểm tra",
  available: "Có bản sao",
  unavailable: "Hết bản sao",
  reserved: "Đã giữ chỗ",
  skipped: "Bỏ qua",
};

export function CirculationPage({ token }) {
  const [loans, setLoans] = useState([]);
  const [tickets, setTickets] = useState([]);
  const [readers, setReaders] = useState([]);
  const [books, setBooks] = useState([]);
  const [readerId, setReaderId] = useState("");
  const [copyIds, setCopyIds] = useState([]);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  const load = async () => {
    const [loanData, ticketData, readerData, bookData] = await Promise.all([
      request("/loans?only_open=true", { token }),
      request("/loans/tickets", { token }),
      request("/readers", { token }),
      request("/catalog/books", { token }),
    ]);
    setLoans(loanData);
    setTickets(ticketData);
    setReaders(readerData);
    setBooks(bookData);
  };

  useEffect(() => { load().catch((err) => setError(err.message)); }, [token]);

  const copies = useMemo(() => books.flatMap((book) => book.copies.filter((copy) => copy.status === "available").map((copy) => ({ ...copy, bookTitle: book.title }))), [books]);
  const activeTickets = tickets.filter((item) => ["pending_review", "changes_requested", "approved_waiting_pickup"].includes(item.status));
  const recentTickets = tickets.filter((item) => !["pending_review", "changes_requested", "approved_waiting_pickup"].includes(item.status)).slice(0, 8);

  async function runAction(action, successMessage) {
    setError("");
    setMessage("");
    try {
      const result = await action();
      setMessage(typeof successMessage === "function" ? successMessage(result) : successMessage);
      await load();
    } catch (err) {
      setError(err.message);
    }
  }

  async function checkout(event) {
    event.preventDefault();
    await runAction(
      () => request("/loans/checkout", { token, method: "POST", body: { reader_id: Number(readerId), book_copy_ids: copyIds.map(Number) } }),
      "Đã lập phiếu mượn trực tiếp."
    );
    setReaderId("");
    setCopyIds([]);
  }

  function reviewTicket(ticketId) {
    return runAction(
      () => request(`/loans/tickets/${ticketId}/review`, { token, method: "POST", body: {} }),
      (ticket) => ticket.status === "approved_waiting_pickup"
        ? `Phiếu #${ticket.id} đủ sách và đã được duyệt, chờ bạn đọc đến lấy.`
        : `Phiếu #${ticket.id} thiếu bản sao, đã gửi phản hồi để bạn đọc chọn sửa hoặc mượn phần còn sẵn.`
    );
  }

  function approveAvailable(ticketId) {
    return runAction(
      () => request(`/loans/tickets/${ticketId}/approve-available`, { token, method: "POST", body: { note: "Thủ thư duyệt các đầu sách còn bản sao." } }),
      (ticket) => `Đã duyệt phiếu #${ticket.id} với các đầu sách còn bản sao, chờ bạn đọc đến lấy.`
    );
  }

  function rejectTicket(ticketId) {
    return runAction(
      () => request(`/loans/tickets/${ticketId}/reject`, { token, method: "POST", body: { note: "Thủ thư từ chối phiếu đăng ký mượn." } }),
      "Đã từ chối phiếu đăng ký mượn."
    );
  }

  function pickupTicket(ticketId) {
    return runAction(
      () => request(`/loans/tickets/${ticketId}/pickup`, { token, method: "POST", body: {} }),
      (loan) => `Đã xác nhận bạn đọc lấy sách và tạo phiếu mượn #${loan.id}.`
    );
  }

  function renew(loanId) {
    return runAction(
      () => request(`/loans/${loanId}/renew`, { token, method: "POST", body: {} }),
      `Đã gia hạn phiếu #${loanId}.`
    );
  }

  function returnItem(loanId, itemId) {
    return runAction(
      () => request(`/loans/${loanId}/items/${itemId}/return`, { token, method: "POST", body: {} }),
      "Đã nhận trả sách, cập nhật kho và công nợ nếu có phạt."
    );
  }

  return <>
    <PageTitle title="Mượn, trả và gia hạn" description="Xử lý phiếu mượn online, lập phiếu trực tiếp tại quầy, xác nhận lấy sách, trả sách và gia hạn." />
    <ErrorBox message={error} />
    {message && <p className="mb-4 rounded-lg bg-emerald-50 p-3 text-sm text-emerald-700">{message}</p>}
    <div className="grid gap-6 xl:grid-cols-[1fr_22rem]">
      <div className="grid gap-4">
        <Card>
          <h2 className="font-semibold">Phiếu đăng ký mượn online</h2>
          <div className="mt-4 divide-y">
            {activeTickets.map((ticket) => <div key={ticket.id} className="py-4">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <p className="font-medium">Phiếu #{ticket.id} · {ticket.reader_name}</p>
                  <p className="text-sm text-slate-500">{ticket.card_number} · {ticketStatusLabels[ticket.status] ?? ticket.status}</p>
                  {ticket.staff_note && <p className="mt-2 rounded bg-slate-50 p-2 text-sm text-slate-600">{ticket.staff_note}</p>}
                </div>
                <div className="flex flex-wrap gap-2">
                  {ticket.status === "pending_review" && <button onClick={() => reviewTicket(ticket.id)} className="bg-indigo-600 text-sm text-white">Kiểm tra</button>}
                  {["pending_review", "changes_requested"].includes(ticket.status) && <button onClick={() => approveAvailable(ticket.id)} className="border border-indigo-200 text-sm text-indigo-700 hover:bg-indigo-50">Duyệt phần có sẵn</button>}
                  {ticket.status === "approved_waiting_pickup" && <button onClick={() => pickupTicket(ticket.id)} className="bg-emerald-600 text-sm text-white">Xác nhận đã lấy</button>}
                  {ticket.status !== "approved_waiting_pickup" && <button onClick={() => rejectTicket(ticket.id)} className="border border-slate-300 text-sm hover:bg-slate-50">Từ chối</button>}
                </div>
              </div>
              <div className="mt-3 grid gap-2 md:grid-cols-2">
                {ticket.items.map((item) => <div key={item.id} className="rounded border border-slate-200 p-3 text-sm">
                  <p className="font-medium">{item.title}</p>
                  <p className="text-slate-500">{itemStatusLabels[item.status] ?? item.status} · còn {item.available_copies} bản sao{item.reserved_barcode ? ` · giữ ${item.reserved_barcode}` : ""}</p>
                  {item.unavailable_reason && <p className="mt-1 text-rose-600">{item.unavailable_reason}</p>}
                </div>)}
              </div>
            </div>)}
            {!activeTickets.length && <p className="py-3 text-sm text-slate-500">Không có phiếu online cần xử lý.</p>}
          </div>
        </Card>

        {loans.map((loan) => <Card key={loan.id}>
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <h2 className="font-semibold">Phiếu #{loan.id} · {loan.reader.full_name}</h2>
              <p className="text-sm text-slate-500">Mượn: {new Date(loan.loaned_at).toLocaleDateString("vi-VN")} · Hạn trả: {new Date(loan.due_at).toLocaleDateString("vi-VN")} · Gia hạn: {loan.renewal_count}</p>
            </div>
            <button onClick={() => renew(loan.id)} className="border border-indigo-200 text-sm text-indigo-700 hover:bg-indigo-50">Gia hạn</button>
          </div>
          <ul className="mt-4 divide-y">
            {loan.items.filter((item) => !item.returned_at).map((item) => <li key={item.id} className="flex items-center justify-between gap-3 py-3">
              <span><b>{item.book_copy.barcode}</b><span className="ml-2 text-xs text-slate-500">{item.book_copy.shelf_location || "Không rõ kệ"}</span></span>
              <button onClick={() => returnItem(loan.id, item.id)} className="bg-emerald-600 text-sm text-white">Nhận trả</button>
            </li>)}
          </ul>
        </Card>)}
        {!loans.length && <Card><p className="text-slate-500">Không có phiếu mượn đang mở.</p></Card>}
      </div>

      <div className="grid content-start gap-4">
        <Card className="h-fit">
          <h2 className="font-semibold">Lập phiếu mượn trực tiếp</h2>
          <form onSubmit={checkout} className="mt-4 grid gap-3">
            <select value={readerId} onChange={(event) => setReaderId(event.target.value)} required>
              <option value="">Chọn bạn đọc</option>
              {readers.filter((reader) => reader.is_active).map((reader) => <option key={reader.id} value={reader.id}>{reader.card_number} · {reader.full_name}</option>)}
            </select>
            <select multiple className="h-52" value={copyIds} onChange={(event) => setCopyIds(Array.from(event.target.selectedOptions, (option) => option.value))} required>
              {copies.map((copy) => <option key={copy.id} value={copy.id}>{copy.barcode} · {copy.bookTitle}</option>)}
            </select>
            <p className="text-xs text-slate-500">Giữ Ctrl/Cmd để chọn nhiều cuốn.</p>
            <button className="bg-indigo-600 text-white">Xác nhận mượn</button>
          </form>
        </Card>

        <Card>
          <h2 className="font-semibold">Phiếu online đã xử lý</h2>
          <div className="mt-3 divide-y">
            {recentTickets.map((ticket) => <div key={ticket.id} className="py-3 text-sm">
              <p className="font-medium">Phiếu #{ticket.id} · {ticket.reader_name}</p>
              <p className="text-slate-500">{ticketStatusLabels[ticket.status] ?? ticket.status}{ticket.loan_id ? ` · phiếu mượn #${ticket.loan_id}` : ""}</p>
            </div>)}
            {!recentTickets.length && <p className="py-3 text-sm text-slate-500">Chưa có phiếu đã xử lý.</p>}
          </div>
        </Card>
      </div>
    </div>
  </>;
}
