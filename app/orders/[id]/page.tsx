"use client"

import { useState, useEffect } from "react"
import { useParams, useRouter } from "next/navigation"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Order } from "@/models/order"
import { format } from "date-fns"
import { ko } from "date-fns/locale"
import { StatusDialog } from "@/components/orders/status-dialog"
import { PrintDialog } from "@/components/orders/print-dialog"
import { PaymentDialog } from "@/components/orders/payment-dialog"

export default function OrderDetailPage() {
  const params = useParams()
  const router = useRouter()
  const [order, setOrder] = useState<Order | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchOrder()
  }, [params.id])

  const fetchOrder = async () => {
    try {
      const response = await fetch(`/api/orders/${params.id}`)
      const data = await response.json()
      setOrder(data)
    } catch (error) {
      console.error("주문 정보를 가져오는데 실패했습니다:", error)
    } finally {
      setLoading(false)
    }
  }

  const handleStatusChange = async (newStatus: string) => {
    try {
      const response = await fetch(`/api/orders/${params.id}`, {
        method: "PATCH",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ status: newStatus }),
      })

      if (!response.ok) {
        throw new Error("상태 변경에 실패했습니다.")
      }

      await fetchOrder()
    } catch (error) {
      console.error("상태 변경 중 오류 발생:", error)
    }
  }

  const handlePaymentComplete = async () => {
    await fetchOrder()
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

  if (loading) {
    return <div>로딩 중...</div>
  }

  if (!order) {
    return <div>주문을 찾을 수 없습니다.</div>
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold">주문 상세</h1>
        <div className="flex items-center gap-2">
          {order && <PrintDialog order={order} />}
          {order.paymentStatus === "pending" && (
            <PaymentDialog
              orderId={order.id}
              totalAmount={order.totalAmount}
              onPaymentComplete={handlePaymentComplete}
            />
          )}
          <Button variant="outline" onClick={() => router.back()}>
            목록으로
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>주문 정보</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <p className="text-sm text-muted-foreground">주문 번호</p>
              <p className="font-medium">{order.id}</p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">테이블</p>
              <p className="font-medium">{order.tableNumber}번</p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">주문 시간</p>
              <p className="font-medium">
                {format(order.createdAt, "yyyy년 MM월 dd일 HH:mm", { locale: ko })}
              </p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">상태</p>
              <div className="flex items-center gap-2">
                {getStatusBadge(order.status)}
                <StatusDialog
                  orderId={order.id}
                  currentStatus={order.status}
                  onStatusChange={handleStatusChange}
                />
              </div>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">결제 상태</p>
              {getPaymentStatusBadge(order.paymentStatus)}
            </div>
            <div>
              <p className="text-sm text-muted-foreground">결제 방법</p>
              <p className="font-medium">{order.paymentMethod || "-"}</p>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>주문 항목</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {order.items.map((item) => (
                <div key={item.menuId} className="flex items-center justify-between">
                  <div>
                    <p className="font-medium">{item.menu.name}</p>
                    <p className="text-sm text-muted-foreground">
                      {item.price.toLocaleString()}원 x {item.quantity}개
                    </p>
                  </div>
                  <p className="font-medium">
                    {(item.price * item.quantity).toLocaleString()}원
                  </p>
                </div>
              ))}
              <div className="border-t pt-4">
                <div className="flex items-center justify-between">
                  <p className="font-medium">총 금액</p>
                  <p className="font-bold text-lg">
                    {order.totalAmount.toLocaleString()}원
                  </p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
} 