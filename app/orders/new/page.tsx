"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
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
import { Menu } from "@/models/menu"

export default function NewOrderPage() {
  const router = useRouter()
  const [menu, setMenu] = useState<Menu[]>([])
  const [selectedItems, setSelectedItems] = useState<{ menuId: string; quantity: number }[]>([])
  const [tableNumber, setTableNumber] = useState("")
  const [paymentMethod, setPaymentMethod] = useState("")

  // TODO: API에서 메뉴 목록 가져오기
  const fetchMenu = async () => {
    try {
      const response = await fetch("/api/menu")
      const data = await response.json()
      setMenu(data)
    } catch (error) {
      console.error("메뉴 목록을 가져오는데 실패했습니다:", error)
    }
  }

  const addItem = (menuId: string) => {
    const existingItem = selectedItems.find((item) => item.menuId === menuId)
    if (existingItem) {
      setSelectedItems(
        selectedItems.map((item) =>
          item.menuId === menuId ? { ...item, quantity: item.quantity + 1 } : item
        )
      )
    } else {
      setSelectedItems([...selectedItems, { menuId, quantity: 1 }])
    }
  }

  const removeItem = (menuId: string) => {
    const existingItem = selectedItems.find((item) => item.menuId === menuId)
    if (existingItem && existingItem.quantity > 1) {
      setSelectedItems(
        selectedItems.map((item) =>
          item.menuId === menuId ? { ...item, quantity: item.quantity - 1 } : item
        )
      )
    } else {
      setSelectedItems(selectedItems.filter((item) => item.menuId !== menuId))
    }
  }

  const calculateTotal = () => {
    return selectedItems.reduce((total, item) => {
      const menuItem = menu.find((m) => m.id === item.menuId)
      return total + (menuItem?.price || 0) * item.quantity
    }, 0)
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    try {
      const response = await fetch("/api/orders", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          tableNumber: parseInt(tableNumber),
          items: selectedItems,
          paymentMethod,
          totalAmount: calculateTotal(),
        }),
      })

      if (response.ok) {
        router.push("/orders")
      }
    } catch (error) {
      console.error("주문 생성에 실패했습니다:", error)
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold">새 주문</h1>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        <Card>
          <CardHeader>
            <CardTitle>주문 정보</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="tableNumber">테이블 번호</Label>
                <Input
                  id="tableNumber"
                  type="number"
                  value={tableNumber}
                  onChange={(e) => setTableNumber(e.target.value)}
                  required
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="paymentMethod">결제 방법</Label>
                <Select value={paymentMethod} onValueChange={setPaymentMethod} required>
                  <SelectTrigger>
                    <SelectValue placeholder="결제 방법 선택" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="cash">현금</SelectItem>
                    <SelectItem value="card">카드</SelectItem>
                    <SelectItem value="mobile">모바일 결제</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>메뉴 선택</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {menu.map((item) => (
                <div key={item.id} className="flex items-center justify-between">
                  <div>
                    <p className="font-medium">{item.name}</p>
                    <p className="text-sm text-muted-foreground">{item.price.toLocaleString()}원</p>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Button
                      type="button"
                      variant="outline"
                      size="sm"
                      onClick={() => removeItem(item.id)}
                    >
                      -
                    </Button>
                    <span>
                      {selectedItems.find((i) => i.menuId === item.id)?.quantity || 0}
                    </span>
                    <Button
                      type="button"
                      variant="outline"
                      size="sm"
                      onClick={() => addItem(item.id)}
                    >
                      +
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>주문 요약</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {selectedItems.map((item) => {
                const menuItem = menu.find((m) => m.id === item.menuId)
                return (
                  <div key={item.menuId} className="flex items-center justify-between">
                    <div>
                      <p className="font-medium">{menuItem?.name}</p>
                      <p className="text-sm text-muted-foreground">
                        {item.quantity}개 × {menuItem?.price.toLocaleString()}원
                      </p>
                    </div>
                    <p className="font-medium">
                      {((menuItem?.price || 0) * item.quantity).toLocaleString()}원
                    </p>
                  </div>
                )
              })}
              <div className="border-t pt-4">
                <div className="flex items-center justify-between">
                  <p className="font-medium">총 금액</p>
                  <p className="font-medium">{calculateTotal().toLocaleString()}원</p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        <div className="flex justify-end space-x-2">
          <Button type="button" variant="outline" onClick={() => router.back()}>
            취소
          </Button>
          <Button type="submit">주문하기</Button>
        </div>
      </form>
    </div>
  )
} 