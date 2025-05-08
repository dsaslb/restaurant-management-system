"use client"

import { useEffect, useState } from "react"
import { io, Socket } from "socket.io-client"
import { Bell } from "lucide-react"
import { Button } from "@/components/ui/button"
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet"
import { Badge } from "@/components/ui/badge"
import { format } from "date-fns"
import { ko } from "date-fns/locale"

interface Notification {
  id: string
  type: "new_order" | "status_change" | "payment"
  message: string
  orderId: string
  createdAt: Date
}

export function OrderNotification() {
  const [socket, setSocket] = useState<Socket | null>(null)
  const [notifications, setNotifications] = useState<Notification[]>([])
  const [unreadCount, setUnreadCount] = useState(0)

  useEffect(() => {
    const socketInitializer = async () => {
      await fetch("/api/socket")
      const socket = io()

      socket.on("connect", () => {
        console.log("소켓 연결됨")
      })

      socket.on("new_order", (data) => {
        const notification: Notification = {
          id: Date.now().toString(),
          type: "new_order",
          message: `새로운 주문이 들어왔습니다. (테이블 ${data.tableNumber}번)`,
          orderId: data.id,
          createdAt: new Date(),
        }
        addNotification(notification)
        playNotificationSound()
      })

      socket.on("status_change", (data) => {
        const notification: Notification = {
          id: Date.now().toString(),
          type: "status_change",
          message: `주문 상태가 변경되었습니다. (${data.status})`,
          orderId: data.id,
          createdAt: new Date(),
        }
        addNotification(notification)
        playNotificationSound()
      })

      socket.on("payment", (data) => {
        const notification: Notification = {
          id: Date.now().toString(),
          type: "payment",
          message: `결제가 완료되었습니다. (${data.amount.toLocaleString()}원)`,
          orderId: data.id,
          createdAt: new Date(),
        }
        addNotification(notification)
        playNotificationSound()
      })

      setSocket(socket)
    }

    socketInitializer()

    return () => {
      if (socket) {
        socket.disconnect()
      }
    }
  }, [])

  const addNotification = (notification: Notification) => {
    setNotifications((prev) => [notification, ...prev])
    setUnreadCount((prev) => prev + 1)
  }

  const playNotificationSound = () => {
    const audio = new Audio("/notification.mp3")
    audio.play()
  }

  const handleNotificationClick = (notification: Notification) => {
    setUnreadCount((prev) => Math.max(0, prev - 1))
    // 주문 상세 페이지로 이동
    window.location.href = `/orders/${notification.orderId}`
  }

  return (
    <Sheet>
      <SheetTrigger asChild>
        <Button variant="outline" size="icon" className="relative">
          <Bell className="h-4 w-4" />
          {unreadCount > 0 && (
            <Badge
              variant="destructive"
              className="absolute -top-2 -right-2 h-5 w-5 flex items-center justify-center p-0"
            >
              {unreadCount}
            </Badge>
          )}
        </Button>
      </SheetTrigger>
      <SheetContent>
        <SheetHeader>
          <SheetTitle>알림</SheetTitle>
        </SheetHeader>
        <div className="mt-4 space-y-4">
          {notifications.length === 0 ? (
            <p className="text-center text-muted-foreground">알림이 없습니다.</p>
          ) : (
            notifications.map((notification) => (
              <div
                key={notification.id}
                className="flex items-start gap-4 p-4 rounded-lg border cursor-pointer hover:bg-accent"
                onClick={() => handleNotificationClick(notification)}
              >
                <div className="flex-1">
                  <p className="font-medium">{notification.message}</p>
                  <p className="text-sm text-muted-foreground">
                    {format(notification.createdAt, "yyyy년 MM월 dd일 HH:mm", {
                      locale: ko,
                    })}
                  </p>
                </div>
              </div>
            ))
          )}
        </div>
      </SheetContent>
    </Sheet>
  )
} 