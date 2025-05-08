import { NextResponse } from "next/server"
import { prisma } from "@/lib/prisma"

export async function GET(request: Request) {
  try {
    const { searchParams } = new URL(request.url)
    const startDate = searchParams.get("startDate")
    const endDate = searchParams.get("endDate")

    if (!startDate || !endDate) {
      return NextResponse.json(
        { error: "시작일과 종료일이 필요합니다." },
        { status: 400 }
      )
    }

    // 주문 데이터 조회
    const orders = await prisma.order.findMany({
      where: {
        createdAt: {
          gte: new Date(startDate),
          lte: new Date(endDate),
        },
      },
      include: {
        items: {
          include: {
            menu: true,
          },
        },
      },
    })

    // 총 주문 수
    const totalOrders = orders.length

    // 총 매출
    const totalRevenue = orders.reduce((sum, order) => sum + order.totalAmount, 0)

    // 평균 주문 금액
    const averageOrderValue = totalOrders > 0 ? totalRevenue / totalOrders : 0

    // 인기 메뉴
    const menuStats = new Map()
    orders.forEach((order) => {
      order.items.forEach((item) => {
        const key = item.menuId
        if (!menuStats.has(key)) {
          menuStats.set(key, {
            menuId: key,
            name: item.menu.name,
            quantity: 0,
            revenue: 0,
          })
        }
        const stats = menuStats.get(key)
        stats.quantity += item.quantity
        stats.revenue += item.price * item.quantity
      })
    })

    const topItems = Array.from(menuStats.values())
      .sort((a, b) => b.quantity - a.quantity)
      .slice(0, 5)

    // 주문 상태 분포
    const statusCount = new Map()
    orders.forEach((order) => {
      const status = order.status
      statusCount.set(status, (statusCount.get(status) || 0) + 1)
    })

    const statusDistribution = Array.from(statusCount.entries()).map(
      ([status, count]) => ({
        status,
        count,
      })
    )

    // 시간대별 주문 분포
    const hourlyCount = new Map()
    orders.forEach((order) => {
      const hour = new Date(order.createdAt).getHours()
      hourlyCount.set(hour, (hourlyCount.get(hour) || 0) + 1)
    })

    const hourlyDistribution = Array.from({ length: 24 }, (_, hour) => ({
      hour,
      count: hourlyCount.get(hour) || 0,
    }))

    return NextResponse.json({
      totalOrders,
      totalRevenue,
      averageOrderValue,
      topItems,
      statusDistribution,
      hourlyDistribution,
    })
  } catch (error) {
    console.error("리포트 데이터 조회 중 오류 발생:", error)
    return NextResponse.json(
      { error: "리포트 데이터를 가져오는데 실패했습니다." },
      { status: 500 }
    )
  }
} 