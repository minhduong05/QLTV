import { useEffect, useMemo, useState } from "react";
import { request } from "../api";
import { Card, ErrorBox, PageTitle, Table } from "../components/ui";

const initialSupplier = { name: "", phone: "", email: "", address: "" };
const initialPurchase = { supplier_id: "", book_title_id: "", quantity: "", unit_price: "", shelf_location: "", barcodes: "", note: "" };
const initialBook = { title: "", isbn: "", category_id: "", publisher_id: "", author_ids: [], language: "Tiếng Việt", publication_year: "" };

export function AcquisitionsPage({ token }) {
  const [suppliers, setSuppliers] = useState([]);
  const [books, setBooks] = useState([]);
  const [lookups, setLookups] = useState({ categories: [], authors: [], publishers: [] });
  const [items, setItems] = useState([]);
  const [supplier, setSupplier] = useState(initialSupplier);
  const [purchase, setPurchase] = useState(initialPurchase);
  const [newBook, setNewBook] = useState(initialBook);
  const [bookMode, setBookMode] = useState("existing");
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  const load = async () => {
    const [supplierData, bookData, purchaseData, categories, authors, publishers] = await Promise.all([
      request("/acquisitions/suppliers", { token }),
      request("/catalog/books?include_inactive=true", { token }),
      request("/acquisitions", { token }),
      request("/catalog/categories", { token }),
      request("/catalog/authors", { token }),
      request("/catalog/publishers", { token }),
    ]);
    setSuppliers(supplierData);
    setBooks(bookData);
    setItems(purchaseData);
    setLookups({ categories, authors, publishers });
  };

  useEffect(() => { load().catch((err) => setError(err.message)); }, [token]);

  const supplierById = useMemo(() => Object.fromEntries(suppliers.map((item) => [item.id, item])), [suppliers]);

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

  async function addSupplier(event) {
    event.preventDefault();
    await runAction(
      () => request("/acquisitions/suppliers", { token, method: "POST", body: { ...supplier, email: supplier.email || null, address: supplier.address || null } }),
      "Đã thêm nhà cung cấp."
    );
    setSupplier(initialSupplier);
  }

  async function createLookup(type, name) {
    const created = await request(`/catalog/${type}`, { token, method: "POST", body: { name } });
    await load();
    return created;
  }

  async function receive(event) {
    event.preventDefault();
    await runAction(async () => {
      let bookTitleId = Number(purchase.book_title_id);
      if (bookMode === "new") {
        const createdBook = await request("/catalog/books", {
          token,
          method: "POST",
          body: {
            ...newBook,
            category_id: Number(newBook.category_id),
            publisher_id: newBook.publisher_id ? Number(newBook.publisher_id) : null,
            publication_year: newBook.publication_year ? Number(newBook.publication_year) : null,
            author_ids: newBook.author_ids.map(Number),
            isbn: newBook.isbn || null,
          },
        });
        bookTitleId = createdBook.id;
      }

      const barcodes = purchase.barcodes.split(/\r?\n|,/).map((item) => item.trim()).filter(Boolean);
      await request("/acquisitions", {
        token,
        method: "POST",
        body: {
          supplier_id: Number(purchase.supplier_id),
          note: purchase.note || null,
          items: [{
            book_title_id: bookTitleId,
            quantity: Number(purchase.quantity),
            unit_price: Number(purchase.unit_price),
            shelf_location: purchase.shelf_location || null,
            barcodes,
          }],
        },
      });
    }, "Đã lập phiếu nhập và tạo bản sao trong kho.");
    setPurchase(initialPurchase);
    setNewBook(initialBook);
    setBookMode("existing");
  }

  return <>
    <PageTitle title="Nhập sách" description="Lập phiếu nhập cho đầu sách có sẵn hoặc tạo nhanh đầu sách mới, sau đó hệ thống tạo đủ bản sao vật lý." />
    <ErrorBox message={error} />
    {message && <p className="mb-4 rounded-lg bg-emerald-50 p-3 text-sm text-emerald-700">{message}</p>}

    <div className="grid gap-6 xl:grid-cols-[1fr_24rem]">
      <div>
        <Table>
          <thead className="bg-slate-50 text-slate-500"><tr><th className="p-4">Số phiếu</th><th className="p-4">Nhà cung cấp</th><th className="p-4">Ngày nhập</th><th className="p-4">Tổng tiền</th></tr></thead>
          <tbody>
            {items.map((item) => <tr className="border-t" key={item.id}>
              <td className="p-4">PN-{item.id}</td>
              <td className="p-4">{supplierById[item.supplier_id]?.name || `#${item.supplier_id}`}</td>
              <td className="p-4">{new Date(item.received_at).toLocaleDateString("vi-VN")}</td>
              <td className="p-4">{item.total_amount.toLocaleString("vi-VN")} đ</td>
            </tr>)}
            {!items.length && <tr><td colSpan="4" className="p-8 text-center text-slate-500">Chưa có phiếu nhập.</td></tr>}
          </tbody>
        </Table>
      </div>

      <div className="grid content-start gap-4">
        <Card>
          <h2 className="font-semibold">Nhà cung cấp</h2>
          <form onSubmit={addSupplier} className="mt-4 grid gap-3">
            <input placeholder="Tên nhà cung cấp" value={supplier.name} onChange={(event) => setSupplier({ ...supplier, name: event.target.value })} required />
            <input placeholder="Số điện thoại" value={supplier.phone} onChange={(event) => setSupplier({ ...supplier, phone: event.target.value })} />
            <input type="email" placeholder="Email" value={supplier.email} onChange={(event) => setSupplier({ ...supplier, email: event.target.value })} />
            <input placeholder="Địa chỉ" value={supplier.address} onChange={(event) => setSupplier({ ...supplier, address: event.target.value })} />
            <button className="bg-slate-800 text-white">Thêm nhà cung cấp</button>
          </form>
        </Card>

        <Card>
          <h2 className="font-semibold">Lập phiếu nhập</h2>
          <form onSubmit={receive} className="mt-4 grid gap-3">
            <select value={purchase.supplier_id} onChange={(event) => setPurchase({ ...purchase, supplier_id: event.target.value })} required>
              <option value="">Nhà cung cấp</option>
              {suppliers.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}
            </select>

            <div className="grid grid-cols-2 gap-2">
              <button type="button" onClick={() => setBookMode("existing")} className={bookMode === "existing" ? "bg-indigo-600 text-white" : "border border-slate-300"}>Đầu sách có sẵn</button>
              <button type="button" onClick={() => setBookMode("new")} className={bookMode === "new" ? "bg-indigo-600 text-white" : "border border-slate-300"}>Đầu sách mới</button>
            </div>

            {bookMode === "existing" ? <select value={purchase.book_title_id} onChange={(event) => setPurchase({ ...purchase, book_title_id: event.target.value })} required>
              <option value="">Đầu sách</option>
              {books.map((item) => <option key={item.id} value={item.id}>{item.title}</option>)}
            </select> : <div className="grid gap-3 rounded-lg border border-slate-200 p-3">
              <input placeholder="Tên sách mới" value={newBook.title} onChange={(event) => setNewBook({ ...newBook, title: event.target.value })} required />
              <input placeholder="ISBN" value={newBook.isbn} onChange={(event) => setNewBook({ ...newBook, isbn: event.target.value })} />
              <select value={newBook.category_id} onChange={(event) => setNewBook({ ...newBook, category_id: event.target.value })} required>
                <option value="">Thể loại</option>
                {lookups.categories.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}
              </select>
              <select value={newBook.publisher_id} onChange={(event) => setNewBook({ ...newBook, publisher_id: event.target.value })}>
                <option value="">Nhà xuất bản</option>
                {lookups.publishers.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}
              </select>
              <select multiple className="h-24" value={newBook.author_ids} onChange={(event) => setNewBook({ ...newBook, author_ids: Array.from(event.target.selectedOptions, (option) => option.value) })}>
                {lookups.authors.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}
              </select>
              <input type="number" placeholder="Năm xuất bản" value={newBook.publication_year} onChange={(event) => setNewBook({ ...newBook, publication_year: event.target.value })} />
            </div>}

            <input type="number" min="1" placeholder="Số lượng bản sao nhập" value={purchase.quantity} onChange={(event) => setPurchase({ ...purchase, quantity: event.target.value })} required />
            <input type="number" min="0" placeholder="Đơn giá mỗi bản" value={purchase.unit_price} onChange={(event) => setPurchase({ ...purchase, unit_price: event.target.value })} required />
            <input placeholder="Vị trí kệ áp dụng cho toàn bộ số lượng nhập, ví dụ A1-03" value={purchase.shelf_location} onChange={(event) => setPurchase({ ...purchase, shelf_location: event.target.value })} />
            <textarea rows="3" placeholder="Mã vạch tùy chọn, mỗi dòng hoặc cách nhau bằng dấu phẩy. Bỏ trống thì hệ thống tự sinh đủ theo số lượng." value={purchase.barcodes} onChange={(event) => setPurchase({ ...purchase, barcodes: event.target.value })} />
            <input placeholder="Ghi chú phiếu nhập" value={purchase.note} onChange={(event) => setPurchase({ ...purchase, note: event.target.value })} />
            <button className="bg-indigo-600 text-white">Nhập sách</button>
          </form>
        </Card>

        <Card>
          <h2 className="font-semibold">Thêm nhanh danh mục</h2>
          <div className="mt-4 grid gap-2">
            <button onClick={() => { const name = window.prompt("Tên thể loại mới"); if (name) createLookup("categories", name).catch((err) => setError(err.message)); }} className="border border-slate-300 hover:bg-slate-50">Thêm thể loại</button>
            <button onClick={() => { const name = window.prompt("Tên tác giả mới"); if (name) createLookup("authors", name).catch((err) => setError(err.message)); }} className="border border-slate-300 hover:bg-slate-50">Thêm tác giả</button>
            <button onClick={() => { const name = window.prompt("Tên nhà xuất bản mới"); if (name) createLookup("publishers", name).catch((err) => setError(err.message)); }} className="border border-slate-300 hover:bg-slate-50">Thêm nhà xuất bản</button>
          </div>
        </Card>
      </div>
    </div>
  </>;
}
