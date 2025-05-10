"use client"

import { useState } from "react"
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Table, TableHeader, TableRow, TableHead, TableBody, TableCell } from "@/components/ui/table"
import { Input } from "@/components/ui/input"
import { Plus, Search } from "lucide-react"

const dummyInventory = [
  { id: "1", name: "쌀", category: "식자재", quantity: 20, status: "정상" },
  { id: "2", name: "계란", category: "식자재", quantity: 5, status: "부족" },
]

export default function InventoryPage() {
  const [search, setSearch] = useState("")
  const filtered = dummyInventory.filter(i =>
    i.name.includes(search) || i.category.includes(search) || i.status.includes(search)
  )
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold">재고 관리</h1>
        <Button>
          <Plus className="mr-2 h-4 w-4" />
          재고 추가
        </Button>
      </div>
      <Card>
        <CardHeader>
          <CardTitle>재고 목록</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="mb-4">
            <div className="relative">
              <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="재고 검색..."
                className="pl-8"
                value={search}
                onChange={e => setSearch(e.target.value)}
              />
            </div>
          </div>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>재고 ID</TableHead>
                <TableHead>이름</TableHead>
                <TableHead>카테고리</TableHead>
                <TableHead>수량</TableHead>
                <TableHead>상태</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filtered.map(item => (
                <TableRow key={item.id}>
                  <TableCell>{item.id}</TableCell>
                  <TableCell>{item.name}</TableCell>
                  <TableCell>{item.category}</TableCell>
                  <TableCell>{item.quantity}</TableCell>
                  <TableCell>{item.status}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  )
} 