import { useEffect, useMemo, useState } from "react";
import { request } from "../api";
import { Card, ErrorBox, PageTitle, Stat, Table } from "../components/ui";

const ticketStatusLabels = {
  pending_review: "Chờ thủ thư kiểm tra",
  changes_requested: "Cần bạn đọc phản hồi",
  approved_waiting_pickup: "Đã duyệt, chờ đến lấy",
  borrowed: "Đã mượn",
  rejected: "Từ chối",
  cancelled: "Đã hủy",
};

const itemStatusLabels = {
  pending: "Chờ kiểm tra",
  available: "Có bản sao",
  unavailable: "Hết bản sao",
  reserved: "Đã giữ chỗ",
  skipped: "Không mượn",
};

const cardRequestLabels = {
  pending: "Chờ thủ thư duyệt",
  approved: "Đã duyệt",
  rejected: "Từ chối",
  cancelled: "Đã hủy",
};

function isCardValid(profile) {
  return Boolean(profile?.is_active && profile?.expires_at && new Date(profile.expires_at) >= new Date(new Date().toDateString()));
}

export function ReaderPortalPage({ token, currentUser, onLogout }) {
  const [profile, setProfile] = useState(null);
  const [cardRequest, setCardRequest] = useState(null);
  const [loans, setLoans] = useState([]);
  const [tickets, setTickets] = useState([]);
  const [books, setBooks] = useState([]);
  const [selectedBookIds, setSelectedBookIds] = useState([]);
  const [editingTicketId, setEditingTicketId] = useState(null);
  const [search, setSearch] = useState("");
  const [cardForm, setCardForm] = useState({ phone: "", date_of_birth: "", address: "" });
  const [ticketNote, setTicketNote] = useState("");
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  async function load() {
    const bookData = await request(`/catalog/books${search ? `?search=${encodeURIComponent(search)}` : ""}`);
    setBooks(bookData);

    const [profileData, cardRequestData] = await Promise.all([
      request("/readers/me", { token }).catch(() => null),
      request("/readers/me/card-request", { token }).catch(() => null),
    ]);
    setProfile(profileData);
    setCardRequest(cardRequestData);

    if (!profileData) {
      setLoans([]);
      setTickets([]);
      return;
    }

    const [loanData, ticketData] = await Promise.all([
      request("/readers/me/loans", { token }),
      request("/loans/tickets/me", { token }),
    ]);
    setLoans(loanData);
    setTickets(ticketData);
  }

  useEffect(() => { load().catch((err) => setError(err.message)); }, [token]);

  const cardValid = isCardValid(profile);
  const activeLoans = useMemo(() => loans.flatMap((loan) => loan.items.filter((item) => !item.returned_at).map((item) => ({ loan, item }))), [loans]);
  const availableBooks = useMemo(() => books.map((book) => ({
    ...book,
    available: book.copies.filter((copy) => copy.status === "available").length,
    reserved: book.copies.filter((copy) => copy.status === "reserved").length,
  })), [books]);

  function toggleBook(bookId) {
    setSelectedBookIds((current) => current.includes(bookId) ? current.filter((id) => id !== bookId) : [...current, bookId]);
  }

  async function registerCard(event) {
    event.preventDefault();
    setError("");
    setMessage("");
    try {
      await request("/readers/me/card-request", { token, method: "POST", body: cardForm });
      setMessage("Đã gửi yêu cầu cấp thẻ đọc. Thủ thư sẽ kiểm tra và duyệt online.");
      setCardForm({ phone: "", date_of_birth: "", address: "" });
      await load();
    } catch (err) {
      setError(err.message);
    }
  }

  async function submitTicket(event) {
    event.preventDefault();
    if (!cardValid) {
      setError("Bạn cần có thẻ đọc đang hoạt động và còn hạn trước khi đăng ký mượn sách.");
      return;
    }
    if (!selectedBookIds.length) {
      setError("Hãy chọn ít nhất một đầu sách để lập phiếu.");
      return;
    }
    setError("");
    setMessage("");
    const body = { items: selectedBookIds.map((id) => ({ book_title_id: id, quantity: 1 })), note: ticketNote || null };
    try {
      if (editingTicketId) {
        await request(`/loans/tickets/${editingTicketId}`, { token, method: "PUT", body });
        setMessage("Đã gửi lại phiếu sau khi điều chỉnh.");
      } else {
        await request("/loans/tickets", { token, method: "POST", body });
        setMessage("Đã gửi phiếu đăng ký mượn. Thủ thư sẽ kiểm tra bản sao vật lý và phản hồi.");
      }
      setSelectedBookIds([]);
      setEditingTicketId(null);
      setTicketNote("");
      await load();
    } catch (err) {
      setError(err.message);
    }
  }

  async function cancelTicket(ticketId) {
    setError("");
    setMessage("");
    try {
      await request(`/loans/tickets/${ticketId}/cancel`, { token, method: "POST", body: {} });
      setMessage("Đã hủy phiếu đăng ký mượn.");
      await load();
    } catch (err) {
      setError(err.message);
    }
  }

  async function acceptAvailable(ticketId) {
    setError("");
    setMessage("");
    try {
      await request(`/loans/tickets/${ticketId}/approve-available`, { token, method: "POST", body: { note: "Bạn đọc đồng ý mượn các đầu sách còn bản sao." } });
      setMessage("Đã xác nhận mượn phần còn sẵn. Phiếu được duyệt và chờ bạn đến thư viện lấy sách.");
      await load();
    } catch (err) {
      setError(err.message);
    }
  }

  function editTicket(ticket) {
    setEditingTicketId(ticket.id);
    setSelectedBookIds(ticket.items.filter((item) => item.status !== "unavailable").map((item) => item.book_title_id));
    setTicketNote(ticket.note || "");
    window.scrollTo({ top: 240, behavior: "smooth" });
  }

  const pendingCardRequest = cardRequest?.status === "pending";
  const showCardForm = !profile && !pendingCardRequest;

  return <div className="min-h-screen bg-slate-100">
    <header className="border-b border-slate-200 bg-white">
      <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-3 px-5 py-4">
        <div>
          <p className="text-sm font-semibold uppercase tracking-widest text-indigo-600">Cổng bạn đọc</p>
          <h1 className="text-2xl font-bold text-slate-900">Thư Viện Số</h1>
        </div>
        <div className="flex items-center gap-3">
          <span className="text-sm text-slate-600">{currentUser.full_name}</span>
          <button onClick={onLogout} className="border border-slate-300 text-sm hover:bg-slate-50">Đăng xuất</button>
        </div>
      </div>
    </header>

    <main className="mx-auto max-w-7xl p-5 lg:p-8">
      <PageTitle title="Tài khoản bạn đọc" description="Đăng ký thẻ đọc online, lập phiếu mượn nhiều sách và theo dõi trạng thái duyệt." />
      <ErrorBox message={error} />
      {message && <p className="mb-4 rounded-lg bg-emerald-50 p-3 text-sm text-emerald-700">{message}</p>}
      {!profile && pendingCardRequest && <p className="mb-4 rounded-lg bg-amber-50 p-3 text-sm text-amber-800">Yêu cầu cấp thẻ của bạn đang chờ thủ thư duyệt. Khi được duyệt, hệ thống sẽ tạo mã thẻ và mở quyền đăng ký mượn sách.</p>}
      {!profile && !pendingCardRequest && <p className="mb-4 rounded-lg bg-amber-50 p-3 text-sm text-amber-800">Tài khoản của bạn chưa có thẻ đọc. Hãy gửi yêu cầu cấp thẻ trước khi đăng ký mượn sách.</p>}
      {profile && !cardValid && <p className="mb-4 rounded-lg bg-amber-50 p-3 text-sm text-amber-800">Thẻ đọc của bạn đã hết hạn hoặc bị khóa, vì vậy chưa thể đăng ký mượn sách.</p>}

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <Stat label="Mã thẻ" value={profile?.card_number ?? "Chưa có"} />
        <Stat label="Hạn thẻ" value={profile?.expires_at ?? cardRequestLabels[cardRequest?.status] ?? "Chưa đăng ký"} warning={profile && !cardValid} />
        <Stat label="Sách đang mượn" value={activeLoans.length} />
        <Stat label="Công nợ" value={`${(profile?.balance ?? 0).toLocaleString("vi-VN")} đ`} warning={(profile?.balance ?? 0) > 0} />
      </div>

      <div className="mt-6 grid gap-6 xl:grid-cols-[1fr_25rem]">
        <section>
          <div className="mb-3 flex gap-2">
            <input className="w-full" placeholder="Tìm sách theo tên, ISBN hoặc tác giả" value={search} onChange={(event) => setSearch(event.target.value)} />
            <button onClick={() => load().catch((err) => setError(err.message))} className="bg-slate-800 text-white">Tìm</button>
          </div>
          <form onSubmit={submitTicket}>
            <Table>
              <thead className="bg-slate-50 text-slate-500"><tr><th className="p-4">Chọn</th><th className="p-4">Đầu sách</th><th className="p-4">Phân loại</th><th className="p-4">Tình trạng</th></tr></thead>
              <tbody>
                {availableBooks.map((book) => <tr key={book.id} className="border-t">
                  <td className="p-4"><input type="checkbox" checked={selectedBookIds.includes(book.id)} onChange={() => toggleBook(book.id)} disabled={!cardValid} /></td>
                  <td className="p-4 font-medium">{book.title}<div className="text-xs font-normal text-slate-500">{book.isbn || "Không có ISBN"} · {book.authors.map((author) => author.name).join(", ") || "Chưa có tác giả"}</div></td>
                  <td className="p-4">{book.category.name}</td>
                  <td className={book.available ? "p-4 font-semibold text-emerald-700" : "p-4 text-rose-600"}>{book.available}/{book.copies.length} cuốn sẵn có{book.reserved ? ` · ${book.reserved} đang giữ chỗ` : ""}</td>
                </tr>)}
                {!availableBooks.length && <tr><td colSpan="4" className="p-8 text-center text-slate-500">Không tìm thấy sách.</td></tr>}
              </tbody>
            </Table>
            <Card className="mt-4">
              <div className="grid gap-3 md:grid-cols-[1fr_auto]">
                <input placeholder="Ghi chú cho thủ thư nếu cần" value={ticketNote} onChange={(event) => setTicketNote(event.target.value)} />
                <button disabled={!cardValid || !selectedBookIds.length} className={cardValid && selectedBookIds.length ? "bg-indigo-600 text-white" : "border border-slate-300 text-slate-400"}>
                  {editingTicketId ? "Gửi lại phiếu" : "Gửi phiếu đăng ký mượn"}
                </button>
              </div>
            </Card>
          </form>
        </section>

        <div className="grid content-start gap-4">
          {showCardForm && <Card>
            <h2 className="font-semibold">Gửi yêu cầu cấp thẻ đọc</h2>
            {cardRequest?.status === "rejected" && <p className="mt-2 text-sm text-rose-600">Yêu cầu trước bị từ chối{cardRequest.note ? `: ${cardRequest.note}` : "."}</p>}
            <form onSubmit={registerCard} className="mt-4 grid gap-3">
              <input placeholder="Số điện thoại" value={cardForm.phone} onChange={(event) => setCardForm({ ...cardForm, phone: event.target.value })} minLength="8" required />
              <label className="grid gap-1 text-sm">Ngày sinh<input type="date" value={cardForm.date_of_birth} onChange={(event) => setCardForm({ ...cardForm, date_of_birth: event.target.value })} required /></label>
              <input placeholder="Địa chỉ" value={cardForm.address} onChange={(event) => setCardForm({ ...cardForm, address: event.target.value })} minLength="5" required />
              <button className="bg-indigo-600 text-white">Gửi yêu cầu cấp thẻ</button>
            </form>
          </Card>}

          <Card>
            <h2 className="font-semibold">Thông tin thẻ</h2>
            <dl className="mt-4 grid gap-3 text-sm">
              <div><dt className="text-slate-500">Họ tên</dt><dd className="font-medium">{profile?.full_name ?? currentUser.full_name}</dd></div>
              <div><dt className="text-slate-500">Email</dt><dd className="font-medium">{profile?.email ?? currentUser.email}</dd></div>
              <div><dt className="text-slate-500">Số điện thoại</dt><dd className="font-medium">{profile?.phone || cardRequest?.phone || "Chưa có"}</dd></div>
              <div><dt className="text-slate-500">Địa chỉ</dt><dd className="font-medium">{profile?.address || cardRequest?.address || "Chưa có"}</dd></div>
            </dl>
          </Card>

          <Card>
            <h2 className="font-semibold">Phiếu đăng ký mượn</h2>
            <div className="mt-3 divide-y">
              {tickets.map((ticket) => <div key={ticket.id} className="py-3 text-sm">
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <p className="font-medium">Phiếu #{ticket.id} · {ticketStatusLabels[ticket.status] ?? ticket.status}</p>
                    <p className="text-slate-500">{new Date(ticket.requested_at).toLocaleDateString("vi-VN")}</p>
                  </div>
                  {["pending_review", "changes_requested", "approved_waiting_pickup"].includes(ticket.status) && <button onClick={() => cancelTicket(ticket.id)} className="border border-slate-300 text-xs hover:bg-slate-50">Hủy</button>}
                </div>
                {ticket.staff_note && <p className="mt-2 rounded bg-slate-50 p-2 text-slate-600">{ticket.staff_note}</p>}
                <ul className="mt-2 grid gap-1">
                  {ticket.items.map((item) => <li key={item.id} className="flex justify-between gap-2">
                    <span>{item.title}</span>
                    <span className={item.status === "unavailable" ? "text-rose-600" : "text-slate-500"}>{itemStatusLabels[item.status] ?? item.status}</span>
                  </li>)}
                </ul>
                {ticket.status === "changes_requested" && <div className="mt-3 flex flex-wrap gap-2">
                  <button onClick={() => acceptAvailable(ticket.id)} className="bg-indigo-600 text-xs text-white">Mượn phần còn sẵn</button>
                  <button onClick={() => editTicket(ticket)} className="border border-slate-300 text-xs hover:bg-slate-50">Sửa phiếu</button>
                </div>}
              </div>)}
              {!tickets.length && <p className="py-3 text-sm text-slate-500">Bạn chưa có phiếu đăng ký mượn.</p>}
            </div>
          </Card>

          <Card>
            <h2 className="font-semibold">Sách đang mượn</h2>
            <div className="mt-3 divide-y">
              {activeLoans.map(({ loan, item }) => <div key={item.id} className="py-3 text-sm">
                <p className="font-medium">{item.book_copy.barcode}</p>
                <p className="text-slate-500">Phiếu #{loan.id} · hạn trả {new Date(loan.due_at).toLocaleDateString("vi-VN")}</p>
              </div>)}
              {!activeLoans.length && <p className="py-3 text-sm text-slate-500">Bạn chưa có sách đang mượn.</p>}
            </div>
          </Card>
        </div>
      </div>
    </main>
  </div>;
}
