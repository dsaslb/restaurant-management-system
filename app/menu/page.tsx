"use client"

import { useState } from "react"
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
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { Menu } from "@/models/menu"
import { Plus, Search } from "lucide-react"
import Image from "next/image"

export default function MenuPage() {
  const [menu, setMenu] = useState<Menu[]>([])
  const [searchQuery, setSearchQuery] = useState("")
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null)

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

  const categories = [
    { value: "appetizer", label: "에피타이저" },
    { value: "main", label: "메인" },
    { value: "dessert", label: "디저트" },
    { value: "beverage", label: "음료" },
  ]

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold">메뉴 관리</h1>
        <Button>
          <Plus className="mr-2 h-4 w-4" />
          메뉴 추가
        </Button>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>메뉴 목록</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="flex items-center gap-4">
              <div className="relative flex-1">
                <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="메뉴 검색..."
                  className="pl-8"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                />
              </div>
              <div className="flex gap-2">
                {categories.map((category) => (
                  <Button
                    key={category.value}
                    variant={selectedCategory === category.value ? "default" : "outline"}
                    onClick={() => setSelectedCategory(category.value)}
                  >
                    {category.label}
                  </Button>
                ))}
              </div>
            </div>

            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>이미지</TableHead>
                  <TableHead>이름</TableHead>
                  <TableHead>설명</TableHead>
                  <TableHead>가격</TableHead>
                  <TableHead>카테고리</TableHead>
                  <TableHead>준비 시간</TableHead>
                  <TableHead>상태</TableHead>
                  <TableHead>액션</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {menu.map((item) => (
                  <TableRow key={item.id}>
                    <TableCell>
                      {item.image && (
                        <Image
                          src={item.image}
                          alt={item.name}
                          width={50}
                          height={50}
                          className="rounded-md object-cover"
                        />
                      )}
                    </TableCell>
                    <TableCell>{item.name}</TableCell>
                    <TableCell>{item.description}</TableCell>
                    <TableCell>{item.price.toLocaleString()}원</TableCell>
                    <TableCell>
                      {categories.find((c) => c.value === item.category)?.label}
                    </TableCell>
                    <TableCell>{item.preparationTime}분</TableCell>
                    <TableCell>
                      <Badge
                        variant="outline"
                        className={
                          item.isAvailable
                            ? "bg-green-100 text-green-800"
                            : "bg-red-100 text-red-800"
                        }
                      >
                        {item.isAvailable ? "판매 중" : "품절"}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <Button variant="ghost" size="sm">
                        수정
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