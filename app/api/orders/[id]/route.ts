import { NextResponse } from "next/server"
import { orderSchema } from "@/models/order"

export async function GET(
  request: Request,
  { params }: { params: { id: string } }
) {
  try {
    // TODO: 데이터베이스에서 주문 정보 가져오기
    const order = {
      id: params.id,
      tableNumber: 1,
      items: [
        {
          menuId: "1",
          quantity: 2,
          price: 15000,
        },
      ],
      status: "pending",
      totalAmount: 30000,
      paymentMethod: "card",
      paymentStatus: "pending",
      createdAt: new Date(),
      updatedAt: new Date(),
      servedBy: "1",
    }

    return NextResponse.json(order)
  } catch (error) {
    return NextResponse.json(
      { error: "주문 정보를 가져오는데 실패했습니다." },
      { status: 500 }
    )
  }
}

export async function PATCH(
  request: Request,
  { params }: { params: { id: string } }
) {
  try {
    const body = await request.json()
    const { status } = body

    // TODO: 데이터베이스에서 주문 상태 업데이트하기
    const order = {
      id: params.id,
      tableNumber: 1,
      items: [
        {
          menuId: "1",
          quantity: 2,
          price: 15000,
        },
      ],
      status,
      totalAmount: 30000,
      paymentMethod: "card",
      paymentStatus: "pending",
      createdAt: new Date(),
      updatedAt: new Date(),
      servedBy: "1",
    }

    return NextResponse.json(order)
  } catch (error) {
    return NextResponse.json(
      { error: "주문 상태를 업데이트하는데 실패했습니다." },
      { status: 500 }
    )
  }
} 