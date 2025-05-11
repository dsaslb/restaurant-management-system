"use client";

import { useEffect, useState } from "react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Table, TableHeader, TableRow, TableHead, TableBody, TableCell } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogTrigger,
} from "@/components/ui/dialog";

interface Payroll {
  id: string;
  employee: string;
  type: string;
  amount: string;
  date: string;
  status?: string; // 상태 필터 확장
}

export default function PayrollPage() {
  const [payrolls, setPayrolls] = useState<Payroll[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [search, setSearch] = useState("");
  const [filterType, setFilterType] = useState<string | null>(null);
  const [selectedPayroll, setSelectedPayroll] = useState<Payroll | null>(null);
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [filterStatus, setFilterStatus] = useState<string | null>(null);

  // 페이지가 처음 렌더링될 때 급여 목록을 불러옵니다.
  useEffect(() => {
    fetchPayrolls();
  }, []);

  // 급여 목록을 서버에서 불러오는 함수
  const fetchPayrolls = async () => {
    setIsLoading(true);
    try {
      const response = await fetch("/api/payroll");
      const data = await response.json();
      // 예시: 상태가 없으면 모두 "지급 완료"로 세팅
      setPayrolls(data.map((p: Payroll) => ({ ...p, status: p.status || "지급 완료" })));
    } catch (error) {
      console.error("급여 목록을 가져오는데 실패했습니다:", error);
    } finally {
      setIsLoading(false);
    }
  };

  // 총 급여 합계 계산
  const totalAmount = payrolls.reduce((sum, p) => {
    const num = parseInt(p.amount.replace(/[^0-9]/g, ""));
    return sum + (isNaN(num) ? 0 : num);
  }, 0);

  // 지급유형 목록 추출
  const typeList = Array.from(new Set(payrolls.map((p) => p.type)));
  // 상태 목록 추출
  const statusList = Array.from(new Set(payrolls.map((p) => p.status)));

  // 검색 및 필터링된 데이터
  const filteredPayrolls = payrolls.filter((pay) => {
    const matchesSearch =
      pay.employee.includes(search) ||
      pay.id.includes(search) ||
      pay.amount.includes(search);
    const matchesType = filterType ? pay.type === filterType : true;
    const matchesStatus = filterStatus ? pay.status === filterStatus : true;
    // 지급일 범위 필터
    const matchesStart = startDate ? pay.date >= startDate : true;
    const matchesEnd = endDate ? pay.date <= endDate : true;
    return matchesSearch && matchesType && matchesStatus && matchesStart && matchesEnd;
  });

  // PDF 다운로드 예시 함수
  const handleDownloadPDF = (pay: Payroll) => {
    // 실제로는 pay.pdfUrl 등에서 파일을 받아야 함
    // 예시로 Blob을 만들어 다운로드
    const blob = new Blob([
      `급여명세서\n\n지급 ID: ${pay.id}\n직원명: ${pay.employee}\n지급유형: ${pay.type}\n금액: ${pay.amount}\n지급일: ${pay.date}\n상태: ${pay.status}`
    ], { type: "application/pdf" });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${pay.id}_급여명세서.pdf`;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
  };

  return (
    <div className="container mx-auto py-8 space-y-8">
      <h1 className="text-2xl font-bold mb-4 dark:text-white">급여 관리</h1>

      {/* 통계 카드 */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardHeader>
            <CardTitle>총 지급 급여</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold text-blue-600 dark:text-blue-300">
              {totalAmount.toLocaleString()}원
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>직원 수</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold">
              {payrolls.length}
            </p>
          </CardContent>
        </Card>
      </div>

      {/* 검색/필터 UI */}
      <div className="flex flex-col sm:flex-row gap-2 items-center mb-4 flex-wrap">
        <Input
          placeholder="직원명, 지급ID, 금액 검색..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="max-w-xs"
        />
        <div className="flex gap-2 flex-wrap">
          <Button
            variant={!filterType ? "default" : "outline"}
            onClick={() => setFilterType(null)}
          >
            전체
          </Button>
          {typeList.map((type) => (
            <Button
              key={type}
              variant={filterType === type ? "default" : "outline"}
              onClick={() => setFilterType(type)}
            >
              {type}
            </Button>
          ))}
        </div>
        {/* 지급일 범위 필터 */}
        <div className="flex gap-2 items-center">
          <label className="text-sm">지급일</label>
          <Input type="date" value={startDate} onChange={e => setStartDate(e.target.value)} />
          <span>~</span>
          <Input type="date" value={endDate} onChange={e => setEndDate(e.target.value)} />
        </div>
        {/* 상태 필터 */}
        <div className="flex gap-2 flex-wrap">
          <Button
            variant={!filterStatus ? "default" : "outline"}
            onClick={() => setFilterStatus(null)}
          >
            전체 상태
          </Button>
          {statusList.map((status) => (
            <Button
              key={status}
              variant={filterStatus === status ? "default" : "outline"}
              onClick={() => setFilterStatus(status)}
            >
              {status}
            </Button>
          ))}
        </div>
      </div>

      {/* 급여 목록 테이블 */}
      <Card>
        <CardHeader>
          <CardTitle>급여 목록</CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>지급 ID</TableHead>
                <TableHead>직원명</TableHead>
                <TableHead>지급 유형</TableHead>
                <TableHead>금액</TableHead>
                <TableHead>지급일</TableHead>
                <TableHead>상태</TableHead>
                <TableHead>상세</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredPayrolls.map((pay) => (
                <TableRow key={pay.id}>
                  <TableCell>{pay.id}</TableCell>
                  <TableCell>{pay.employee}</TableCell>
                  <TableCell>
                    <Badge variant={pay.type === "월급제" ? "default" : "outline"}>
                      {pay.type}
                    </Badge>
                  </TableCell>
                  <TableCell>{pay.amount}</TableCell>
                  <TableCell>{pay.date}</TableCell>
                  <TableCell>
                    <Badge variant="outline" className="bg-green-100 text-green-800">
                      {pay.status}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <Dialog>
                      <DialogTrigger asChild>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => setSelectedPayroll(pay)}
                        >
                          상세보기
                        </Button>
                      </DialogTrigger>
                      <DialogContent>
                        <DialogHeader>
                          <DialogTitle>급여 상세 정보</DialogTitle>
                          <DialogDescription>
                            {pay.employee}님의 급여 상세 내역입니다.
                          </DialogDescription>
                        </DialogHeader>
                        <div className="space-y-2">
                          <div>
                            <span className="font-semibold">지급 ID:</span> {pay.id}
                          </div>
                          <div>
                            <span className="font-semibold">직원명:</span> {pay.employee}
                          </div>
                          <div>
                            <span className="font-semibold">지급 유형:</span> {pay.type}
                          </div>
                          <div>
                            <span className="font-semibold">금액:</span> {pay.amount}
                          </div>
                          <div>
                            <span className="font-semibold">지급일:</span> {pay.date}
                          </div>
                          <div>
                            <span className="font-semibold">상태:</span> {pay.status}
                          </div>
                        </div>
                        <div className="pt-4">
                          <Button onClick={() => handleDownloadPDF(pay)} variant="outline">
                            PDF 다운로드
                          </Button>
                        </div>
                      </DialogContent>
                    </Dialog>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
          {isLoading && <p className="text-center py-4">불러오는 중...</p>}
          {!isLoading && filteredPayrolls.length === 0 && (
            <p className="text-center py-4 text-gray-500">급여 데이터가 없습니다.</p>
          )}
        </CardContent>
      </Card>
    </div>
  );
} 