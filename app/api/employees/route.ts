import { NextResponse } from "next/server"
import { employeeSchema } from "@/models/employee"

// GET /api/employees
export async function GET() {
  try {
    // TODO: 데이터베이스에서 직원 목록 조회
    const employees = [
      {
        id: "1",
        name: "홍길동",
        position: "매니저",
        email: "hong@example.com",
        phone: "010-1234-5678",
        hireDate: new Date("2022-03-15"),
        status: "active",
        employmentType: "full-time",
        salary: 3500000,
        bankAccount: "신한은행 110-123-456789",
        emergencyContact: "김철수(배우자) 010-9876-5432",
      },
    ]

    return NextResponse.json(employees)
  } catch (error) {
    return NextResponse.json({ error: "직원 목록을 가져오는데 실패했습니다." }, { status: 500 })
  }
}

// POST /api/employees
export async function POST(request: Request) {
  try {
    const body = await request.json()
    const validatedData = employeeSchema.parse(body)

    // TODO: 데이터베이스에 직원 정보 저장

    return NextResponse.json(validatedData, { status: 201 })
  } catch (error) {
    return NextResponse.json({ error: "직원 정보 저장에 실패했습니다." }, { status: 400 })
  }
} 