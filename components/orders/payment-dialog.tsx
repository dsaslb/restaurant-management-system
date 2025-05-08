"use client"

import { useState } from "react"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { CreditCard, Wallet } from "lucide-react"

interface PaymentDialogProps {
  orderId: string
  totalAmount: number
  onPaymentComplete: () => void
}

export function PaymentDialog({ orderId, totalAmount, onPaymentComplete }: PaymentDialogProps) {
  const [open, setOpen] = useState(false)
  const [loading, setLoading] = useState(false)
  const [paymentMethod, setPaymentMethod] = useState("card")
  const [cardNumber, setCardNumber] = useState("")
  const [cardExpiry, setCardExpiry] = useState("")
  const [cardCVC, setCardCVC] = useState("")

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)

    try {
      const response = await fetch(`/api/orders/${orderId}/payment`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          paymentMethod,
          cardNumber: paymentMethod === "card" ? cardNumber : undefined,
          cardExpiry: paymentMethod === "card" ? cardExpiry : undefined,
          cardCVC: paymentMethod === "card" ? cardCVC : undefined,
        }),
      })

      if (!response.ok) {
        throw new Error("결제 처리에 실패했습니다.")
      }

      onPaymentComplete()
      setOpen(false)
    } catch (error) {
      console.error("결제 처리 중 오류 발생:", error)
      alert("결제 처리에 실패했습니다. 다시 시도해주세요.")
    } finally {
      setLoading(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button>
          <CreditCard className="h-4 w-4 mr-2" />
          결제하기
        </Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>결제 처리</DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <Label>결제 금액</Label>
            <p className="text-2xl font-bold">{totalAmount.toLocaleString()}원</p>
          </div>

          <div className="space-y-2">
            <Label>결제 방법</Label>
            <Select value={paymentMethod} onValueChange={setPaymentMethod}>
              <SelectTrigger>
                <SelectValue placeholder="결제 방법 선택" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="card">
                  <div className="flex items-center">
                    <CreditCard className="h-4 w-4 mr-2" />
                    신용카드
                  </div>
                </SelectItem>
                <SelectItem value="cash">
                  <div className="flex items-center">
                    <Wallet className="h-4 w-4 mr-2" />
                    현금
                  </div>
                </SelectItem>
              </SelectContent>
            </Select>
          </div>

          {paymentMethod === "card" && (
            <div className="space-y-4">
              <div className="space-y-2">
                <Label>카드 번호</Label>
                <Input
                  type="text"
                  placeholder="1234 5678 9012 3456"
                  value={cardNumber}
                  onChange={(e) => setCardNumber(e.target.value)}
                  maxLength={19}
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>유효기간</Label>
                  <Input
                    type="text"
                    placeholder="MM/YY"
                    value={cardExpiry}
                    onChange={(e) => setCardExpiry(e.target.value)}
                    maxLength={5}
                  />
                </div>

                <div className="space-y-2">
                  <Label>CVC</Label>
                  <Input
                    type="text"
                    placeholder="123"
                    value={cardCVC}
                    onChange={(e) => setCardCVC(e.target.value)}
                    maxLength={3}
                  />
                </div>
              </div>
            </div>
          )}

          <div className="flex justify-end gap-2">
            <Button type="button" variant="outline" onClick={() => setOpen(false)}>
              취소
            </Button>
            <Button type="submit" disabled={loading}>
              {loading ? "처리 중..." : "결제하기"}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  )
} 