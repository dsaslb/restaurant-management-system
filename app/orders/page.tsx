"use client"

import { useState } from "react"
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Table, TableHeader, TableRow, TableHead, TableBody, TableCell } from "@/components/ui/table"
import { Input } from "@/components/ui/input"
import { Plus, Search } from "lucide-react"
import { Badge } from "@/components/ui/badge"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { MoreHorizontal } from "lucide-react"

const dummyOrders = [
  { id: "1", tableNumber: 3, status: "served", totalAmount: 45000, createdAt: "2024-05-10" },
  { id: "2", tableNumber: 1, status: "pending", totalAmount: 32000, createdAt: "2024-05-10" },
]

export default function OrdersPage() {
  const [search, setSearch] = useState("")
  const filtered = dummyOrders.filter(o =>
    o.id.includes(search) || String(o.tableNumber).includes(search) || o.status.includes(search)
  )
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold">주문 관리</h1>
        <Button>
          <Plus className="mr-2 h-4 w-4" />
          주문 추가
        </Button>
      </div>
      <Card>
        <CardHeader>
          <CardTitle>주문 목록</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="mb-4">
            <div className="relative">
              <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="주문 검색..."
                className="pl-8"
                value={search}
                onChange={e => setSearch(e.target.value)}
              />
            </div>
          </div>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>주문 ID</TableHead>
                <TableHead>테이블 번호</TableHead>
                <TableHead>상태</TableHead>
                <TableHead>총액</TableHead>
                <TableHead>주문일</TableHead>
                <TableHead>액션</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filtered.map(order => (
                <TableRow key={order.id}>
                  <TableCell>{order.id}</TableCell>
                  <TableCell>{order.tableNumber}</TableCell>
                  <TableCell>
                    <Badge variant={order.status === "served" ? "default" : "outline"}>
                      {order.status === "served" ? "서빙 완료" : order.status === "pending" ? "대기 중" : order.status}
                    </Badge>
                  </TableCell>
                  <TableCell>{order.totalAmount.toLocaleString()}원</TableCell>
                  <TableCell>{order.createdAt}</TableCell>
                  <TableCell>
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button variant="ghost" size="icon">
                          <MoreHorizontal className="h-4 w-4" />
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                        <DropdownMenuItem>수정</DropdownMenuItem>
                        <DropdownMenuItem className="text-red-600">삭제</DropdownMenuItem>
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  )
} 