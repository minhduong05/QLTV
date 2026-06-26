import { useEffect, useMemo, useState } from "react";
import { request } from "../api";
import { Card, ErrorBox, PageTitle, Stat, Table } from "../components/ui";

const ticketStatusLabels = {
  pending_review: "Chờ thủ thư kiểm tra",
  reviewed: "Đã kiểm tra, chờ duyệt giữ chỗ",
  changes_requested: "Cần bạn đọc phản hồi",
  approved_waiting_pickup: "Đã duyệt, chờ đến lấy",
  borrowed: "Đã mượn",
  rejected: "Từ chối",
  cancelled: "Đã hủy",
};

const itemStatusLabels = {
  pending: "Chờ kiểm tra",
  available: "Đủ bản sao",
  unavailable: "Thiếu bản sao",
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
  const [readerTypes, setReaderTypes] = useState([]);
  const [loans, setLoans] = useState([]);
  const [tickets, setTickets] = useState([]);
  const [books, setBooks] = useState([]);
  const [selectedQuantities, setSelectedQuantities] = useState({});
  const [editingTicketId, setEditingTicketId] = useState(null);
  const [search, setSearch] = useState("");
  const [cardForm, setCardForm] = useState({ full_name: currentUser.full_name, phone: "", date_of_birth: "", address: "", reader_type_id: "" });
  const [ticketNote, setTicketNote] = useState("");
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  async function load() {
    const [bookData, typeData] = await Promise.all([
      request(`/catalog/books${search ? `?search=${encodeURIComponent(search)}` : ""}`),
      request("/readers/types").catch(() => []),
    ]);
    setBooks(bookData);
    setReaderTypes(typeData);

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
  const selectedItems = Object.entries(selectedQuantities).filter(([, quantity]) => Number(quantity) > 0);

  function toggleBook(bookId) {
    setSelectedQuantities((current) => {
      const next = { ...current };
      if (next[bookId]) delete next[bookId];
      else next[bookId] = 1;
      return next;
    });
  }

  function setBookQuantity(bookId, quantity) {
    const nextQuantity = Math.max(1, Math.min(10, Number(quantity) || 1));
    setSelectedQuantities((current) => ({ ...current, [bookId]: nextQuantity }));
  }

  async function registerCard(event) {
    event.preventDefault();
    setError("");
    setMessage("");
    try {
      await request("/readers/me/card-request", {
        token,
        method: "POST",
        body: { ...cardForm, reader_type_id: cardForm.reader_type_id ? Number(cardForm.reader_type_id) : null },
      });
      setMessage("Đã gửi yêu cầu cấp thẻ đọc. Thủ thư sẽ kiểm tra hồ sơ và duyệt online.");
      setCardForm({ full_name: currentUser.full_name, phone: "", date_of_birth: "", address: "", reader_type_id: "" });
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
    if (!selectedItems.length) {
      setError("Hãy chọn ít nhất một đầu sách để lập phiếu.");
      return;
    }
    setError("");
    setMessage("");
    const body = {
      items: selectedItems.map(([id, quantity]) => ({ book_title_id: Number(id), quantity: Number(quantity) })),
      note: ticketNote || null,
    };
    try {
      if (editingTicketId) {
        await request(`/loans/tickets/${editingTicketId}`, { token, method: "PUT", body });
        setMessage("Đã gửi lại phiếu sau khi điều chỉnh.");
      } else {
        await request("/loans/tickets", { token, method: "POST", body });
        setMessage("Đã gửi phiếu đăng ký mượn. Thủ thư sẽ kiểm tra số bản sao vật lý và phản hồi.");
      }
      setSelectedQuantities({});
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
    const nextQuantities = {};
    ticket.items.filter((item) => item.status !== "unavailable").forEach((item) => {
      nextQuantities[item.book_title_id] = item.requested_quantity;
    });
    setEditingTicketId(ticket.id);
    setSelectedQuantities(nextQuantities);
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
      <PageTitle title="Tài khoản bạn đọc" description="Đăng ký thẻ đọc online, lập phiếu mượn theo số lượng và theo dõi trạng thái duyệt." />
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
              <thead className="bg-slate-50 text-slate-500"><tr><th className="p-4">Chọn</th><th className="p-4">Đầu sách</th><th className="p-4">Phân loại</th><th className="p-4">Tình trạng</th><th className="p-4">Số lượng</th></tr></thead>
              <tbody>
                {availableBooks.map((book) => <tr key={book.id} className="border-t">
                  <td className="p-4"><input type="checkbox" checked={Boolean(selectedQuantities[book.id])} onChange={() => toggleBook(book.id)} disabled={!cardValid} /></td>
                  <td className="p-4 font-medium">{book.title}<div className="text-xs font-normal text-slate-500">{book.isbn || "Không có ISBN"} · {book.authors.map((author) => author.name).join(", ") || "Chưa có tác giả"}</div></td>
                  <td className="p-4">{book.category.name}</td>
                  <td className={book.available ? "p-4 font-semibold text-emerald-700" : "p-4 text-rose-600"}>{book.available}/{book.copies.length} cuốn sẵn có{book.reserved ? ` · ${book.reserved} đang giữ chỗ` : ""}</td>
                  <td className="p-4"><input className="w-20" type="number" min="1" max="10" disabled={!selectedQuantities[book.id]} value={selectedQuantities[book.id] || ""} onChange={(event) => setBookQuantity(book.id, event.target.value)} /></td>
                </tr>)}
                {!availableBooks.length && <tr><td colSpan="5" className="p-8 text-center text-slate-500">Không tìm thấy sách.</td></tr>}
              </tbody>
            </Table>
            <Card className="mt-4">
              <div className="grid gap-3 md:grid-cols-[1fr_auto]">
                <input placeholder="Ghi chú cho thủ thư nếu cần" value={ticketNote} onChange={(event) => setTicketNote(event.target.value)} />
                <button disabled={!cardValid || !selectedItems.length} className={cardValid && selectedItems.length ? "bg-indigo-600 text-white" : "border border-slate-300 text-slate-400"}>
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
              <input placeholder="Họ và tên trên thẻ" value={cardForm.full_name} onChange={(event) => setCardForm({ ...cardForm, full_name: event.target.value })} required />
              <input value={currentUser.email} disabled title="Email lấy theo tài khoản đăng nhập" />
              <input placeholder="Số điện thoại" value={cardForm.phone} onChange={(event) => setCardForm({ ...cardForm, phone: event.target.value })} minLength="8" required />
              <label className="grid gap-1 text-sm">Ngày sinh<input type="date" value={cardForm.date_of_birth} onChange={(event) => setCardForm({ ...cardForm, date_of_birth: event.target.value })} required /></label>
              <input placeholder="Địa chỉ" value={cardForm.address} onChange={(event) => setCardForm({ ...cardForm, address: event.target.value })} minLength="5" required />
              <select value={cardForm.reader_type_id} onChange={(event) => setCardForm({ ...cardForm, reader_type_id: event.target.value })}>
                <option value="">Loại bạn đọc</option>
                {readerTypes.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}
              </select>
              <button className="bg-indigo-600 text-white">Gửi yêu cầu cấp thẻ</button>
            </form>
          </Card>}

          <Card>
            <h2 className="font-semibold">Thông tin thẻ</h2>
            <dl className="mt-4 grid gap-3 text-sm">
              <div><dt className="text-slate-500">Họ tên</dt><dd className="font-medium">{profile?.full_name ?? cardRequest?.full_name ?? currentUser.full_name}</dd></div>
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
                  {["pending_review", "reviewed", "changes_requested", "approved_waiting_pickup"].includes(ticket.status) && <button onClick={() => cancelTicket(ticket.id)} className="border border-slate-300 text-xs hover:bg-slate-50">Hủy</button>}
                </div>
                {ticket.staff_note && <p className="mt-2 rounded bg-slate-50 p-2 text-slate-600">{ticket.staff_note}</p>}
                <ul className="mt-2 grid gap-1">
                  {ticket.items.map((item) => <li key={item.id} className="flex justify-between gap-2">
                    <span>{item.title} × {item.requested_quantity}</span>
                    <span className={item.status === "unavailable" ? "text-rose-600" : "text-slate-500"}>{itemStatusLabels[item.status] ?? item.status}{item.approved_quantity ? ` (${item.approved_quantity})` : ""}</span>
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
