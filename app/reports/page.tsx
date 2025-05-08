"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { format, subDays, startOfDay, endOfDay } from "date-fns"
import { ko } from "date-fns/locale"

interface ReportData {
  totalOrders: number
  totalRevenue: number
  averageOrderValue: number
  topItems: {
    menuId: string
    name: string
    quantity: number
    revenue: number
  }[]
  statusDistribution: {
    status: string
    count: number
  }[]
  hourlyDistribution: {
    hour: number
    count: number
  }[]
}

export default function ReportsPage() {
  const [dateRange, setDateRange] = useState("today")
  const [reportData, setReportData] = useState<ReportData | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchReportData()
  }, [dateRange])

  const fetchReportData = async () => {
    try {
      const startDate = startOfDay(
        dateRange === "today"
          ? new Date()
          : dateRange === "week"
          ? subDays(new Date(), 7)
          : subDays(new Date(), 30)
      )
      const endDate = endOfDay(new Date())

      const response = await fetch(
        `/api/reports?startDate=${startDate.toISOString()}&endDate=${endDate.toISOString()}`
      )
      const data = await response.json()
      setReportData(data)
    } catch (error) {
      console.error("리포트 데이터를 가져오는데 실패했습니다:", error)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return <div>로딩 중...</div>
  }

  if (!reportData) {
    return <div>데이터를 불러올 수 없습니다.</div>
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold">주문 통계</h1>
        <div className="flex items-center gap-4">
          <Select value={dateRange} onValueChange={setDateRange}>
            <SelectTrigger className="w-[180px]">
              <SelectValue placeholder="기간 선택" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="today">오늘</SelectItem>
              <SelectItem value="week">최근 7일</SelectItem>
              <SelectItem value="month">최근 30일</SelectItem>
            </SelectContent>
          </Select>
          <Button variant="outline">인쇄</Button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>총 주문 수</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold">{reportData.totalOrders.toLocaleString()}건</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>총 매출</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold">
              {reportData.totalRevenue.toLocaleString()}원
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>평균 주문 금액</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold">
              {reportData.averageOrderValue.toLocaleString()}원
            </p>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>인기 메뉴</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {reportData.topItems.map((item) => (
                <div key={item.menuId} className="flex items-center justify-between">
                  <div>
                    <p className="font-medium">{item.name}</p>
                    <p className="text-sm text-muted-foreground">
                      {item.quantity.toLocaleString()}개 판매
                    </p>
                  </div>
                  <p className="font-medium">{item.revenue.toLocaleString()}원</p>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>주문 상태 분포</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {reportData.statusDistribution.map((status) => (
                <div key={status.status} className="flex items-center justify-between">
                  <p className="font-medium">{status.status}</p>
                  <p className="text-muted-foreground">
                    {status.count.toLocaleString()}건
                  </p>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>시간대별 주문 분포</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-[300px]">
            <div className="flex h-full items-end gap-2">
              {reportData.hourlyDistribution.map((hour) => (
                <div
                  key={hour.hour}
                  className="flex-1 bg-primary/20 rounded-t"
                  style={{
                    height: `${(hour.count / Math.max(...reportData.hourlyDistribution.map((h) => h.count))) * 100}%`,
                  }}
                >
                  <div className="text-center text-sm text-muted-foreground mt-2">
                    {hour.hour}시
                  </div>
                </div>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
} 