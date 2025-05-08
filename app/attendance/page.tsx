"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Search, Filter, Clock, ArrowUpRight, ArrowDownRight, Calendar, BarChart } from "lucide-react"
import { format } from "date-fns"
import { ko } from "date-fns/locale"

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

export default function AttendancePage() {
  const [date] = useState(new Date())

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

      <div className="flex flex-col md:flex-row gap-4 mb-6">
        <div className="relative flex-1">
          <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
          <Input type="search" placeholder="직원 이름으로 검색..." className="pl-8" />
        </div>
        <Button variant="outline" size="icon">
          <Filter className="h-4 w-4" />
        </Button>
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
          <div className="rounded-md border">
            <div className="grid grid-cols-7 bg-slate-50 p-4 text-sm font-medium">
              <div>직원</div>
              <div>직책</div>
              <div>출근 시간</div>
              <div>퇴근 시간</div>
              <div>근무 시간</div>
              <div>상태</div>
              <div></div>
            </div>
            <div className="divide-y">
              <AttendanceRow
                name="김직원"
                position="매니저"
                checkIn="08:55"
                checkOut="18:05"
                hours="9시간 10분"
                status="complete"
              />
              <AttendanceRow
                name="이직원"
                position="주방장"
                checkIn="08:45"
                checkOut="18:30"
                hours="9시간 45분"
                status="complete"
              />
              <AttendanceRow
                name="박직원"
                position="서빙"
                checkIn="09:15"
                checkOut="-"
                hours="-"
                status="active"
              />
              <AttendanceRow
                name="최직원"
                position="캐셔"
                checkIn="09:30"
                checkOut="-"
                hours="-"
                status="active"
              />
              <AttendanceRow
                name="정직원"
                position="주방 보조"
                checkIn="10:15"
                checkOut="-"
                hours="-"
                status="late"
              />
            </div>
          </div>
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