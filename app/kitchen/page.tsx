"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Order } from "@/models/order"
import { format } from "date-fns"
import { ko } from "date-fns/locale"
import { Bell, Check } from "lucide-react"

export default function KitchenDisplayPage() {
  const [orders, setOrders] = useState<Order[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedStatus, setSelectedStatus] = useState<string>("preparing")

  useEffect(() => {
    fetchOrders()
    const interval = setInterval(fetchOrders, 30000) // 30초마다 갱신
    return () => clearInterval(interval)
  }, [selectedStatus])

  const fetchOrders = async () => {
    try {
      const response = await fetch(`/api/orders?status=${selectedStatus}`)
      const data = await response.json()
      setOrders(data)
    } catch (error) {
      console.error("주문 목록을 가져오는데 실패했습니다:", error)
    } finally {
      setLoading(false)
    }
  }

  const handleStatusChange = async (orderId: string, newStatus: string) => {
    try {
      const response = await fetch(`/api/orders/${orderId}`, {
        method: "PATCH",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ status: newStatus }),
      })

      if (!response.ok) {
        throw new Error("상태 변경에 실패했습니다.")
      }

      await fetchOrders()
    } catch (error) {
      console.error("상태 변경 중 오류 발생:", error)
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

  if (loading) {
    return <div>로딩 중...</div>
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold">주방 디스플레이</h1>
        <div className="flex items-center gap-2">
          <Button
            variant={selectedStatus === "preparing" ? "default" : "outline"}
            onClick={() => setSelectedStatus("preparing")}
          >
            준비 중
          </Button>
          <Button
            variant={selectedStatus === "ready" ? "default" : "outline"}
            onClick={() => setSelectedStatus("ready")}
          >
            준비 완료
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {orders.map((order) => (
          <Card key={order.id} className="relative">
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="text-xl">
                  테이블 {order.tableNumber}번
                </CardTitle>
                {getStatusBadge(order.status)}
              </div>
              <p className="text-sm text-muted-foreground">
                {format(order.createdAt, "HH:mm", { locale: ko })}
              </p>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {order.items.map((item) => (
                  <div key={item.menuId} className="flex items-center justify-between">
                    <div>
                      <p className="font-medium">{item.menu.name}</p>
                      <p className="text-sm text-muted-foreground">
                        {item.quantity}개
                      </p>
                    </div>
                    {order.status === "preparing" ? (
                      <Button
                        size="sm"
                        onClick={() => handleStatusChange(order.id, "ready")}
                      >
                        <Check className="h-4 w-4 mr-2" />
                        완료
                      </Button>
                    ) : (
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => handleStatusChange(order.id, "served")}
                      >
                        <Bell className="h-4 w-4 mr-2" />
                        서빙
                      </Button>
                    )}
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  )
} 