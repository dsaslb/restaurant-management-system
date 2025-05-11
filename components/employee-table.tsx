"use client"

import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "@/components/ui/dropdown-menu"
import { Button } from "@/components/ui/button"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { Badge } from "@/components/ui/badge"
import { MoreHorizontal, FileText, Edit, Trash, Eye } from "lucide-react"
import Link from "next/link"
import { useRouter } from "next/navigation"

interface Employee {
  id: string
  name: string
  position: string
  department: string
  status: 'active' | 'inactive'
  hire_date: string
  contract: string
  phone: string
  email: string
  profile_image?: string
}

interface EmployeeTableProps {
  employees: Employee[]
}

export function EmployeeTable({ employees }: EmployeeTableProps) {
  const router = useRouter()

  const handleDelete = async (id: string) => {
    if (window.confirm('정말로 이 직원을 삭제하시겠습니까?')) {
      try {
        const { error } = await supabase
          .from('employees')
          .delete()
          .eq('id', id)

        if (error) throw error
        window.location.reload()
      } catch (error) {
        console.error('직원 삭제에 실패했습니다:', error)
      }
    }
  }

  return (
    <div className="rounded-md border">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead className="w-[50px]"></TableHead>
            <TableHead>이름</TableHead>
            <TableHead>직책</TableHead>
            <TableHead>부서</TableHead>
            <TableHead>상태</TableHead>
            <TableHead>입사일</TableHead>
            <TableHead>계약형태</TableHead>
            <TableHead className="text-right">관리</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {employees.map((employee) => (
            <TableRow key={employee.id}>
              <TableCell>
                <Avatar className="h-8 w-8">
                  <AvatarImage src={employee.profile_image || "/placeholder.svg"} alt={employee.name} />
                  <AvatarFallback>{employee.name.slice(0, 1)}</AvatarFallback>
                </Avatar>
              </TableCell>
              <TableCell className="font-medium">{employee.name}</TableCell>
              <TableCell>{employee.position}</TableCell>
              <TableCell>{employee.department}</TableCell>
              <TableCell>
                <Badge variant={employee.status === "active" ? "default" : "secondary"}>
                  {employee.status === "active" ? "재직 중" : "퇴사"}
                </Badge>
              </TableCell>
              <TableCell>{formatDate(employee.hire_date)}</TableCell>
              <TableCell>{employee.contract}</TableCell>
              <TableCell className="text-right">
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button variant="ghost" size="icon">
                      <MoreHorizontal className="h-4 w-4" />
                      <span className="sr-only">메뉴 열기</span>
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end">
                    <Link href={`/employees/${employee.id}`} passHref>
                      <DropdownMenuItem>
                        <Eye className="mr-2 h-4 w-4" />
                        상세 정보
                      </DropdownMenuItem>
                    </Link>
                    <DropdownMenuItem>
                      <FileText className="mr-2 h-4 w-4" />
                      계약서 보기
                    </DropdownMenuItem>
                    <DropdownMenuItem onClick={() => router.push(`/employees/${employee.id}/edit`)}>
                      <Edit className="mr-2 h-4 w-4" />
                      정보 수정
                    </DropdownMenuItem>
                    <DropdownMenuItem 
                      className="text-destructive"
                      onClick={() => handleDelete(employee.id)}
                    >
                      <Trash className="mr-2 h-4 w-4" />
                      삭제
                    </DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  )
}

function formatDate(dateString: string): string {
  const date = new Date(dateString)
  return new Intl.DateTimeFormat("ko-KR", { 
    year: "numeric", 
    month: "long", 
    day: "numeric" 
  }).format(date)
} 