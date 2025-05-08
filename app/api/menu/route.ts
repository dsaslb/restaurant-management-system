import { NextResponse } from "next/server"
import { menuSchema } from "@/models/menu"

// GET /api/menu
export async function GET(request: Request) {
  try {
    const { searchParams } = new URL(request.url)
    const category = searchParams.get("category")

    // TODO: 데이터베이스에서 메뉴 목록 조회
    const menu = [
      {
        id: "1",
        name: "불고기",
        description: "한국의 전통 불고기",
        price: 15000,
        category: "main",
        image: "/images/bulgogi.jpg",
        isAvailable: true,
        ingredients: ["소고기", "양파", "당근", "대파"],
        preparationTime: 15,
        calories: 450,
      },
    ]

    return NextResponse.json(menu)
  } catch (error) {
    return NextResponse.json({ error: "메뉴 목록을 가져오는데 실패했습니다." }, { status: 500 })
  }
}

// POST /api/menu
export async function POST(request: Request) {
  try {
    const body = await request.json()
    const validatedData = menuSchema.parse(body)

    // TODO: 데이터베이스에 메뉴 정보 저장

    return NextResponse.json(validatedData, { status: 201 })
  } catch (error) {
    return NextResponse.json({ error: "메뉴 정보 저장에 실패했습니다." }, { status: 400 })
  }
} 