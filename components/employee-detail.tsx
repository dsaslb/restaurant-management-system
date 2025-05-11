"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { Button } from "@/components/ui/button"
import { Edit, User } from "lucide-react"
import { useRouter } from "next/navigation"

interface Employee {
  id: string
  name: string
  position: string
  department: string
  email: string
  phone: string
  hire_date: string
  status: 'active' | 'inactive'
  profile_image?: string
}

interface EmployeeDetailProps {
  employee: Employee
}

export function EmployeeDetail({ employee }: EmployeeDetailProps) {
  const router = useRouter()

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <div className="flex items-center space-x-4">
            <Avatar className="h-16 w-16">
              <AvatarImage src={employee.profile_image || "/placeholder.svg"} alt={employee.name} />
              <AvatarFallback>{employee.name.slice(0, 1)}</AvatarFallback>
            </Avatar>
            <div>
              <CardTitle className="text-2xl font-bold">{employee.name}</CardTitle>
              <p className="text-sm text-muted-foreground">
                {employee.position} | {employee.department}
              </p>
            </div>
          </div>
          <Button onClick={() => router.push(`/employees/${employee.id}/edit`)}>
            <Edit className="mr-2 h-4 w-4" />
            정보 수정
          </Button>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-1">
              <p className="text-sm font-medium text-muted-foreground">이메일</p>
              <p>{employee.email}</p>
            </div>
            <div className="space-y-1">
              <p className="text-sm font-medium text-muted-foreground">전화번호</p>
              <p>{employee.phone}</p>
            </div>
            <div className="space-y-1">
              <p className="text-sm font-medium text-muted-foreground">입사일</p>
              <p>{formatDate(employee.hire_date)}</p>
            </div>
            <div className="space-y-1">
              <p className="text-sm font-medium text-muted-foreground">상태</p>
              <p className={employee.status === 'active' ? 'text-green-600' : 'text-red-600'}>
                {employee.status === 'active' ? '재직중' : '퇴사'}
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <Tabs defaultValue="attendance">
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="attendance">근태 관리</TabsTrigger>
            <TabsTrigger value="leave">휴가 관리</TabsTrigger>
            <TabsTrigger value="salary">급여 관리</TabsTrigger>
          </TabsList>
          <TabsContent value="attendance" className="h-[600px]">
            <iframe
              src={`/employees/${employee.id}/attendance`}
              className="w-full h-full border-0"
            />
          </TabsContent>
          <TabsContent value="leave" className="h-[600px]">
            <iframe
              src={`/employees/${employee.id}/leave`}
              className="w-full h-full border-0"
            />
          </TabsContent>
          <TabsContent value="salary" className="h-[600px]">
            <iframe
              src={`/employees/${employee.id}/salary`}
              className="w-full h-full border-0"
            />
          </TabsContent>
        </Tabs>
      </Card>
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