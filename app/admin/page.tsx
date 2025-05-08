"use client"

import { useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { toast } from "sonner"

interface User {
  username: string
  role: string
  info: {
    name: string
    address: string
  }
}

export default function AdminPage() {
  const router = useRouter()
  const [users, setUsers] = useState<User[]>([])
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    fetchUsers()
  }, [])

  const fetchUsers = async () => {
    try {
      const response = await fetch("/api/auth/users")
      if (!response.ok) {
        if (response.status === 401) {
          router.push("/login")
          return
        }
        throw new Error("사용자 목록을 불러오는데 실패했습니다")
      }
      const data = await response.json()
      setUsers(data)
    } catch (error) {
      console.error("사용자 목록 조회 실패:", error)
      toast.error("사용자 목록을 불러오는데 실패했습니다")
    } finally {
      setIsLoading(false)
    }
  }

  const handleDeleteUser = async (username: string) => {
    if (!confirm(`${username} 사용자를 삭제하시겠습니까?`)) return

    try {
      const response = await fetch(`/api/auth/users/${username}`, {
        method: "DELETE",
      })

      if (!response.ok) {
        throw new Error("사용자 삭제에 실패했습니다")
      }

      toast.success("사용자가 삭제되었습니다")
      fetchUsers()
    } catch (error) {
      console.error("사용자 삭제 실패:", error)
      toast.error("사용자 삭제에 실패했습니다")
    }
  }

  return (
    <div className="container mx-auto py-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">관리자 페이지</h1>
        <Button onClick={() => router.push("/")}>메인으로</Button>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>사용자 관리</CardTitle>
          <CardDescription>
            시스템에 등록된 사용자 목록입니다
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>사용자 이름</TableHead>
                <TableHead>역할</TableHead>
                <TableHead>이름</TableHead>
                <TableHead>주소</TableHead>
                <TableHead>관리</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {users.map((user) => (
                <TableRow key={user.username}>
                  <TableCell>{user.username}</TableCell>
                  <TableCell>
                    <span
                      className={`px-2 py-1 rounded-full text-xs ${
                        user.role === "admin"
                          ? "bg-purple-100 text-purple-800"
                          : "bg-blue-100 text-blue-800"
                      }`}
                    >
                      {user.role === "admin" ? "관리자" : "직원"}
                    </span>
                  </TableCell>
                  <TableCell>{user.info.name || "-"}</TableCell>
                  <TableCell>{user.info.address || "-"}</TableCell>
                  <TableCell>
                    <Button
                      variant="destructive"
                      size="sm"
                      onClick={() => handleDeleteUser(user.username)}
                    >
                      삭제
                    </Button>
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