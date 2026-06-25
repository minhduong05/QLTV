import { useEffect, useState } from "react";
import { request } from "../api";
import { Card, ErrorBox, PageTitle, Stat } from "../components/ui";

export function DashboardPage({ token }) {
  const [data, setData] = useState(null); const [error, setError] = useState("");
  useEffect(() => { request("/reports/overview", { token }).then(setData).catch((err) => setError(err.message)); }, [token]);
  return <><PageTitle title="Tổng quan thư viện" description="Các chỉ số vận hành được tính từ dữ liệu mượn, kho và bạn đọc." /><ErrorBox message={error} />
    <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-6"><Stat label="Đầu sách" value={data?.titles} /><Stat label="Cuốn sẵn có" value={data?.available_copies} /><Stat label="Bạn đọc hoạt động" value={data?.active_readers} /><Stat label="Phiếu đang mượn" value={data?.open_loans} /><Stat label="Cuốn quá hạn" value={data?.overdue_items} warning /><Stat label="Công nợ (đ)" value={data?.unpaid_fines?.toLocaleString("vi-VN")} warning /></div>
    <Card className="mt-6"><h2 className="font-semibold">Quy trình vận hành</h2><p className="mt-2 text-sm leading-6 text-slate-600">Khai báo danh mục → nhập/tạo cuốn sách → tạo thẻ bạn đọc → lập phiếu mượn → gia hạn hoặc nhận trả → thu phạt và xem báo cáo.</p></Card>
  </>;
}
