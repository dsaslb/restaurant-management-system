"use client"

import { useEffect, useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Search, Filter, Clock, ArrowUpRight, ArrowDownRight, Calendar, BarChart } from "lucide-react"
import { format } from "date-fns"
import { ko } from "date-fns/locale"
import { Table, TableHeader, TableRow, TableHead, TableBody, TableCell } from "@/components/ui/table"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogTrigger,
} from "@/components/ui/dialog"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"

interface AttendanceCardProps {
  title: string
  value: string
  description: string
  icon: React.ReactNode
  color: string
}

interface AttendanceRowProps {
  name: string
  position: string
  checkIn: string
  checkOut: string
  hours: string
  status: "complete" | "active" | "late" | "absent"
}

interface Attendance {
  id: string
  employee: string
  checkIn: string
  checkOut: string
  late: boolean
}

interface Employee {
  id: string
  name: string
  position?: string
  avatar?: string
}

export default function AttendancePage() {
  const [date] = useState(new Date())
  const [records, setRecords] = useState<Attendance[]>([])
  const [employees, setEmployees] = useState<Employee[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [search, setSearch] = useState("")
  const [filterLate, setFilterLate] = useState<null | boolean>(null)
  const [selectedRecord, setSelectedRecord] = useState<Attendance | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchAttendance()
    fetchEmployees()
  }, [])

  const fetchAttendance = async () => {
    setIsLoading(true)
    try {
      const response = await fetch("/api/attendance")
      const data = await response.json()
      setRecords(data)
    } catch (error) {
      console.error("출퇴근 기록을 가져오는데 실패했습니다:", error)
    } finally {
      setIsLoading(false)
    }
  }

  const fetchEmployees = async () => {
    try {
      const response = await fetch("/api/employees")
      const data = await response.json()
      setEmployees(data)
    } catch (error) {
      console.error("직원 데이터를 가져오는데 실패했습니다:", error)
    }
  }

  // 검색 및 필터링된 데이터
  const filteredRecords = records.filter((rec) => {
    const matchesSearch =
      rec.employee.includes(search) ||
      rec.id.includes(search)
    const matchesLate =
      filterLate === null ? true : rec.late === filterLate
    return matchesSearch && matchesLate
  })

  // 직원명 → 직원 객체 매칭 함수
  const getEmployeeInfo = (employeeName: string) =>
    employees.find(emp => emp.name === employeeName)

  return (
    <div className="container mx-auto p-4 md:p-6">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-6 gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">출퇴근 관리</h1>
          <p className="text-muted-foreground">직원 출퇴근 기록을 확인하고 관리하세요.</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline">
            <Calendar className="mr-2 h-4 w-4" />
            날짜 선택
          </Button>
          <Button variant="outline">
            <BarChart className="mr-2 h-4 w-4" />
            리포트
          </Button>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4 mb-6">
        <AttendanceCard
          title="출근"
          value="8명"
          description="오늘 출근"
          icon={<ArrowUpRight className="h-4 w-4 text-green-600" />}
          color="green"
        />
        <AttendanceCard
          title="퇴근"
          value="2명"
          description="오늘 퇴근"
          icon={<ArrowDownRight className="h-4 w-4 text-blue-600" />}
          color="blue"
        />
        <AttendanceCard
          title="지각"
          value="1명"
          description="오늘 지각"
          icon={<Clock className="h-4 w-4 text-amber-600" />}
          color="amber"
        />
        <AttendanceCard
          title="결근"
          value="0명"
          description="오늘 결근"
          icon={<Clock className="h-4 w-4 text-red-600" />}
          color="red"
        />
      </div>

      {/* 검색/필터 UI */}
      <div className="flex flex-col md:flex-row gap-4 mb-6 items-center">
        <div className="relative flex-1">
          <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
          <Input
            type="search"
            placeholder="직원 이름, 기록ID로 검색..."
            className="pl-8"
            value={search}
            onChange={e => setSearch(e.target.value)}
          />
        </div>
        <div className="flex gap-2">
          <Button
            variant={filterLate === null ? "default" : "outline"}
            onClick={() => setFilterLate(null)}
          >
            전체
          </Button>
          <Button
            variant={filterLate === false ? "default" : "outline"}
            onClick={() => setFilterLate(false)}
          >
            정상
          </Button>
          <Button
            variant={filterLate === true ? "default" : "outline"}
            onClick={() => setFilterLate(true)}
          >
            지각
          </Button>
        </div>
      </div>

      <Tabs defaultValue="today" className="mb-6">
        <TabsList>
          <TabsTrigger value="today">오늘</TabsTrigger>
          <TabsTrigger value="week">이번 주</TabsTrigger>
          <TabsTrigger value="month">이번 달</TabsTrigger>
          <TabsTrigger value="custom">사용자 지정</TabsTrigger>
        </TabsList>
      </Tabs>

      <Card>
        <CardHeader>
          <CardTitle>출퇴근 기록</CardTitle>
          <CardDescription>
            {format(date, "yyyy년 M월 d일 EEEE", { locale: ko })}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>기록 ID</TableHead>
                <TableHead>직원</TableHead>
                <TableHead>직위</TableHead>
                <TableHead>출근</TableHead>
                <TableHead>퇴근</TableHead>
                <TableHead>지각</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredRecords.map((rec) => {
                const emp = getEmployeeInfo(rec.employee)
                return (
                  <TableRow key={rec.id}>
                    <TableCell>{rec.id}</TableCell>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        <Avatar className="h-8 w-8">
                          <AvatarImage src={emp?.avatar || "/placeholder.svg"} />
                          <AvatarFallback>{emp?.name?.charAt(0) || rec.employee.charAt(0)}</AvatarFallback>
                        </Avatar>
                        <span>{emp ? emp.name : rec.employee}</span>
                      </div>
                    </TableCell>
                    <TableCell>{emp?.position || '-'}</TableCell>
                    <TableCell>{rec.checkIn}</TableCell>
                    <TableCell>{rec.checkOut}</TableCell>
                    <TableCell>
                      <Badge variant={rec.late ? "destructive" : "default"}>
                        {rec.late ? "지각" : "정상"}
                      </Badge>
                    </TableCell>
                  </TableRow>
                )
              })}
            </TableBody>
          </Table>
          {isLoading && <p className="text-center py-4">불러오는 중...</p>}
          {!isLoading && filteredRecords.length === 0 && (
            <p className="text-center py-4 text-gray-500">출퇴근 데이터가 없습니다.</p>
          )}
        </CardContent>
      </Card>
    </div>
  )
}

function AttendanceCard({ title, value, description, icon, color }: AttendanceCardProps) {
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium">{title}</CardTitle>
        <div className={`rounded-full p-2 bg-${color}-50`}>{icon}</div>
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">{value}</div>
        <p className="text-xs text-muted-foreground">{description}</p>
      </CardContent>
    </Card>
  )
}

function AttendanceRow({ name, position, checkIn, checkOut, hours, status }: AttendanceRowProps) {
  const getStatusBadge = () => {
    switch (status) {
      case "complete":
        return <Badge className="bg-green-100 text-green-700 hover:bg-green-100">완료</Badge>
      case "active":
        return <Badge className="bg-blue-100 text-blue-700 hover:bg-blue-100">근무 중</Badge>
      case "late":
        return <Badge className="bg-amber-100 text-amber-700 hover:bg-amber-100">지각</Badge>
      case "absent":
        return <Badge className="bg-red-100 text-red-700 hover:bg-red-100">결근</Badge>
      default:
        return null
    }
  }

  return (
    <div className="grid grid-cols-7 items-center p-4">
      <div className="font-medium">{name}</div>
      <div className="text-sm text-muted-foreground">{position}</div>
      <div className="text-sm">{checkIn}</div>
      <div className="text-sm">{checkOut}</div>
      <div className="text-sm">{hours}</div>
      <div>{getStatusBadge()}</div>
      <div className="text-right">
        <Button variant="ghost" size="sm">
          상세
        </Button>
      </div>
    </div>
  )
} 