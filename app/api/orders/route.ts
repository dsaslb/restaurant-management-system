import { NextResponse } from "next/server"
import { orderSchema } from "@/models/order"

// GET /api/orders
export async function GET(request: Request) {
  try {
    const { searchParams } = new URL(request.url)
    const status = searchParams.get("status")
    const date = searchParams.get("date")

    // TODO: 데이터베이스에서 주문 목록 조회
    const orders = [
      {
        id: "1",
        tableNumber: 1,
        items: [
          {
            menuId: "1",
            quantity: 2,
            price: 15000,
            notes: "덜 맵게",
          },
        ],
        status: "pending",
        totalAmount: 30000,
        paymentMethod: "card",
        paymentStatus: "pending",
        createdAt: new Date(),
        updatedAt: new Date(),
        servedBy: "1",
      },
    ]

    return NextResponse.json(orders)
  } catch (error) {
    return NextResponse.json({ error: "주문 목록을 가져오는데 실패했습니다." }, { status: 500 })
  }
}

// POST /api/orders
export async function POST(request: Request) {
  try {
    const body = await request.json()
    const validatedData = orderSchema.parse(body)

    // TODO: 데이터베이스에 주문 정보 저장

    return NextResponse.json(validatedData, { status: 201 })
  } catch (error) {
    return NextResponse.json({ error: "주문 정보 저장에 실패했습니다." }, { status: 400 })
  }
} 