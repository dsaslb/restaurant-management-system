"use client"

import { useState } from "react"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Printer } from "lucide-react"
import { Order } from "@/models/order"
import { format } from "date-fns"
import { ko } from "date-fns/locale"

interface PrintDialogProps {
  order: Order
}

export function PrintDialog({ order }: PrintDialogProps) {
  const [open, setOpen] = useState(false)

  const handlePrint = () => {
    const printWindow = window.open("", "_blank")
    if (!printWindow) return

    const content = `
      <!DOCTYPE html>
      <html>
        <head>
          <title>주문서 #${order.id}</title>
          <style>
            body {
              font-family: 'Noto Sans KR', sans-serif;
              padding: 20px;
              max-width: 800px;
              margin: 0 auto;
            }
            .header {
              text-align: center;
              margin-bottom: 20px;
            }
            .order-info {
              margin-bottom: 20px;
            }
            .items {
              width: 100%;
              border-collapse: collapse;
              margin-bottom: 20px;
            }
            .items th, .items td {
              border: 1px solid #ddd;
              padding: 8px;
              text-align: left;
            }
            .total {
              text-align: right;
              font-weight: bold;
            }
            .footer {
              margin-top: 40px;
              text-align: center;
              font-size: 12px;
              color: #666;
            }
            @media print {
              body {
                padding: 0;
              }
              .no-print {
                display: none;
              }
            }
          </style>
        </head>
        <body>
          <div class="header">
            <h1>주문서</h1>
            <p>주문 번호: ${order.id}</p>
          </div>
          
          <div class="order-info">
            <p>테이블: ${order.tableNumber}번</p>
            <p>주문 시간: ${format(order.createdAt, "yyyy년 MM월 dd일 HH:mm", { locale: ko })}</p>
            <p>상태: ${order.status}</p>
          </div>

          <table class="items">
            <thead>
              <tr>
                <th>메뉴</th>
                <th>수량</th>
                <th>가격</th>
                <th>소계</th>
              </tr>
            </thead>
            <tbody>
              ${order.items.map(item => `
                <tr>
                  <td>${item.menu.name}</td>
                  <td>${item.quantity}개</td>
                  <td>${item.price.toLocaleString()}원</td>
                  <td>${(item.price * item.quantity).toLocaleString()}원</td>
                </tr>
              `).join("")}
            </tbody>
          </table>

          <div class="total">
            <p>총 금액: ${order.totalAmount.toLocaleString()}원</p>
          </div>

          <div class="footer">
            <p>이 주문서는 컴퓨터로 출력된 것으로서 서명이 필요하지 않습니다.</p>
          </div>

          <div class="no-print" style="margin-top: 20px; text-align: center;">
            <button onclick="window.print()">인쇄하기</button>
          </div>
        </body>
      </html>
    `

    printWindow.document.write(content)
    printWindow.document.close()
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button variant="outline" size="sm">
          <Printer className="h-4 w-4 mr-2" />
          인쇄
        </Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>주문서 인쇄</DialogTitle>
        </DialogHeader>
        <div className="space-y-4">
          <p>주문서를 인쇄하시겠습니까?</p>
          <div className="flex justify-end gap-2">
            <Button variant="outline" onClick={() => setOpen(false)}>
              취소
            </Button>
            <Button onClick={handlePrint}>
              인쇄하기
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  )
} 