import { NextResponse } from "next/server"
import { attendanceSchema } from "@/models/attendance"

// GET /api/attendance
export async function GET(request: Request) {
  try {
    const { searchParams } = new URL(request.url)
    const employeeId = searchParams.get("employeeId")
    const date = searchParams.get("date")

    // TODO: 데이터베이스에서 출퇴근 기록 조회
    const attendance = [
      {
        id: "1",
        employeeId: "1",
        date: new Date("2024-03-15"),
        checkIn: new Date("2024-03-15T09:00:00"),
        checkOut: new Date("2024-03-15T18:00:00"),
        status: "onTime",
        workHours: 9,
      },
    ]

    return NextResponse.json(attendance)
  } catch (error) {
    return NextResponse.json({ error: "출퇴근 기록을 가져오는데 실패했습니다." }, { status: 500 })
  }
}

// POST /api/attendance
export async function POST(request: Request) {
  try {
    const body = await request.json()
    const validatedData = attendanceSchema.parse(body)

    // TODO: 데이터베이스에 출퇴근 기록 저장

    return NextResponse.json(validatedData, { status: 201 })
  } catch (error) {
    return NextResponse.json({ error: "출퇴근 기록 저장에 실패했습니다." }, { status: 400 })
  }
} 