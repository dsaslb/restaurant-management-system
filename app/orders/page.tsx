"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Order } from "@/models/order"
import { format } from "date-fns"
import { ko } from "date-fns/locale"
import { Plus, Search } from "lucide-react"
import { useRouter } from "next/navigation"

export default function OrdersPage() {
  const router = useRouter()
  const [orders, setOrders] = useState<Order[]>([])
  const [selectedStatus, setSelectedStatus] = useState<string | null>(null)
  const [searchQuery, setSearchQuery] = useState("")
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchOrders()
  }, [selectedStatus])

  const fetchOrders = async () => {
    try {
      const url = new URL("/api/orders", window.location.origin)
      if (selectedStatus) {
        url.searchParams.append("status", selectedStatus)
      }
      const response = await fetch(url)
      const data = await response.json()
      setOrders(data)
    } catch (error) {
      console.error("주문 목록을 가져오는데 실패했습니다:", error)
    } finally {
      setLoading(false)
    }
  }

  const getStatusBadge = (status: string) => {
    const statusConfig = {
      pending: { label: "대기 중", className: "bg-yellow-100 text-yellow-800" },
      preparing: { label: "준비 중", className: "bg-blue-100 text-blue-800" },
      ready: { label: "준비 완료", className: "bg-green-100 text-green-800" },
      served: { label: "서빙 완료", className: "bg-purple-100 text-purple-800" },
      completed: { label: "완료", className: "bg-gray-100 text-gray-800" },
      cancelled: { label: "취소", className: "bg-red-100 text-red-800" },
    }

    const config = statusConfig[status as keyof typeof statusConfig]
    return (
      <Badge variant="outline" className={config.className}>
        {config.label}
      </Badge>
    )
  }

  const getPaymentStatusBadge = (status: string) => {
    const statusConfig = {
      pending: { label: "미결제", className: "bg-yellow-100 text-yellow-800" },
      paid: { label: "결제 완료", className: "bg-green-100 text-green-800" },
      refunded: { label: "환불", className: "bg-red-100 text-red-800" },
    }

    const config = statusConfig[status as keyof typeof statusConfig]
    return (
      <Badge variant="outline" className={config.className}>
        {config.label}
      </Badge>
    )
  }

  const statuses = [
    { value: "pending", label: "대기 중" },
    { value: "preparing", label: "준비 중" },
    { value: "ready", label: "준비 완료" },
    { value: "served", label: "서빙 완료" },
    { value: "completed", label: "완료" },
    { value: "cancelled", label: "취소" },
  ]

  const filteredOrders = orders.filter((order) => {
    const searchLower = searchQuery.toLowerCase()
    return (
      order.id.toLowerCase().includes(searchLower) ||
      order.tableNumber.toString().includes(searchQuery) ||
      format(order.createdAt, "yyyy-MM-dd HH:mm", { locale: ko }).includes(searchQuery)
    )
  })

  if (loading) {
    return <div>로딩 중...</div>
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold">주문 관리</h1>
        <Button onClick={() => router.push("/orders/new")}>
          <Plus className="mr-2 h-4 w-4" />
          새 주문
        </Button>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>주문 목록</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="flex items-center gap-4">
              <div className="relative flex-1">
                <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="주문 번호, 테이블, 날짜로 검색..."
                  className="pl-8"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                />
              </div>
              <div className="flex gap-2">
                {statuses.map((status) => (
                  <Button
                    key={status.value}
                    variant={selectedStatus === status.value ? "default" : "outline"}
                    onClick={() => setSelectedStatus(status.value)}
                  >
                    {status.label}
                  </Button>
                ))}
              </div>
            </div>

            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>주문 번호</TableHead>
                  <TableHead>테이블</TableHead>
                  <TableHead>주문 시간</TableHead>
                  <TableHead>주문 항목</TableHead>
                  <TableHead>총 금액</TableHead>
                  <TableHead>상태</TableHead>
                  <TableHead>결제 상태</TableHead>
                  <TableHead>액션</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredOrders.map((order) => (
                  <TableRow key={order.id}>
                    <TableCell>{order.id}</TableCell>
                    <TableCell>{order.tableNumber}번</TableCell>
                    <TableCell>
                      {format(order.createdAt, "yyyy-MM-dd HH:mm", { locale: ko })}
                    </TableCell>
                    <TableCell>
                      {order.items.map((item) => (
                        <div key={item.menuId}>
                          {item.quantity}개
                        </div>
                      ))}
                    </TableCell>
                    <TableCell>{order.totalAmount.toLocaleString()}원</TableCell>
                    <TableCell>{getStatusBadge(order.status)}</TableCell>
                    <TableCell>{getPaymentStatusBadge(order.paymentStatus)}</TableCell>
                    <TableCell>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => router.push(`/orders/${order.id}`)}
                      >
                        상세 보기
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>
    </div>
  )
} 