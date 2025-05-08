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
import { Calendar } from "@/components/ui/calendar"
import { Badge } from "@/components/ui/badge"
import { Attendance } from "@/models/attendance"
import { format } from "date-fns"
import { ko } from "date-fns/locale"

export default function AttendancePage() {
  const [attendance, setAttendance] = useState<Attendance[]>([])
  const [selectedDate, setSelectedDate] = useState<Date>(new Date())

  // TODO: API에서 출퇴근 기록 가져오기
  const fetchAttendance = async () => {
    try {
      const response = await fetch(`/api/attendance?date=${selectedDate.toISOString()}`)
      const data = await response.json()
      setAttendance(data)
    } catch (error) {
      console.error("출퇴근 기록을 가져오는데 실패했습니다:", error)
    }
  }

  const getStatusBadge = (status: string) => {
    const statusConfig = {
      onTime: { label: "정상 출근", className: "bg-green-100 text-green-800" },
      late: { label: "지각", className: "bg-orange-100 text-orange-800" },
      earlyLeave: { label: "조퇴", className: "bg-yellow-100 text-yellow-800" },
      absent: { label: "결근", className: "bg-red-100 text-red-800" },
      vacation: { label: "휴가", className: "bg-blue-100 text-blue-800" },
    }

    const config = statusConfig[status as keyof typeof statusConfig]
    return (
      <Badge variant="outline" className={config.className}>
        {config.label}
      </Badge>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold">출퇴근 관리</h1>
        <Button>출퇴근 기록 추가</Button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card className="md:col-span-2">
          <CardHeader>
            <CardTitle>출퇴근 기록</CardTitle>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>직원</TableHead>
                  <TableHead>날짜</TableHead>
                  <TableHead>출근 시간</TableHead>
                  <TableHead>퇴근 시간</TableHead>
                  <TableHead>근무 시간</TableHead>
                  <TableHead>상태</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {attendance.map((record) => (
                  <TableRow key={record.id}>
                    <TableCell>{record.employeeId}</TableCell>
                    <TableCell>
                      {format(record.date, "yyyy-MM-dd", { locale: ko })}
                    </TableCell>
                    <TableCell>
                      {format(record.checkIn, "HH:mm", { locale: ko })}
                    </TableCell>
                    <TableCell>
                      {record.checkOut
                        ? format(record.checkOut, "HH:mm", { locale: ko })
                        : "-"}
                    </TableCell>
                    <TableCell>
                      {record.workHours ? `${record.workHours}시간` : "-"}
                    </TableCell>
                    <TableCell>{getStatusBadge(record.status)}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>달력</CardTitle>
          </CardHeader>
          <CardContent>
            <Calendar
              mode="single"
              selected={selectedDate}
              onSelect={(date) => date && setSelectedDate(date)}
              locale={ko}
            />
          </CardContent>
        </Card>
      </div>
    </div>
  )
} 