import { NextResponse } from "next/server"
import { prisma } from "@/lib/prisma"

export async function POST(
  request: Request,
  { params }: { params: { id: string } }
) {
  try {
    const { paymentMethod, cardNumber, cardExpiry, cardCVC } = await request.json()

    // 주문 조회
    const order = await prisma.order.findUnique({
      where: { id: params.id },
    })

    if (!order) {
      return NextResponse.json(
        { error: "주문을 찾을 수 없습니다." },
        { status: 404 }
      )
    }

    if (order.paymentStatus === "paid") {
      return NextResponse.json(
        { error: "이미 결제가 완료된 주문입니다." },
        { status: 400 }
      )
    }

    // 결제 처리 로직
    // 실제 구현에서는 PG사 연동이 필요합니다.
    const paymentResult = {
      success: true,
      transactionId: `TXN_${Date.now()}`,
      paymentMethod,
      amount: order.totalAmount,
      timestamp: new Date(),
    }

    // 주문 상태 업데이트
    const updatedOrder = await prisma.order.update({
      where: { id: params.id },
      data: {
        paymentStatus: "paid",
        paymentMethod,
        paymentDetails: paymentResult,
      },
    })

    return NextResponse.json(updatedOrder)
  } catch (error) {
    console.error("결제 처리 중 오류 발생:", error)
    return NextResponse.json(
      { error: "결제 처리에 실패했습니다." },
      { status: 500 }
    )
  }
} 