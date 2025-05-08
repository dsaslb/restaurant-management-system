import { NextResponse } from "next/server"
import { readFile } from "fs/promises"
import { existsSync } from "fs"
import path from "path"
import { cookies } from "next/headers"
import { verify } from "jsonwebtoken"

const USER_DATA_FILE = path.join(process.cwd(), "data", "users.json")
const JWT_SECRET = process.env.JWT_SECRET || "your-secret-key"

export async function GET() {
  try {
    const token = cookies().get("token")?.value
    if (!token) {
      return NextResponse.json(
        { error: "인증되지 않은 요청입니다" },
        { status: 401 }
      )
    }

    const decoded = verify(token, JWT_SECRET) as { username: string; role: string }
    if (decoded.role !== "admin") {
      return NextResponse.json(
        { error: "권한이 없습니다" },
        { status: 403 }
      )
    }

    if (!existsSync(USER_DATA_FILE)) {
      return NextResponse.json([])
    }

    const data = await readFile(USER_DATA_FILE, "utf-8")
    const users = JSON.parse(data)

    // 비밀번호 제외하고 사용자 정보 반환
    const userList = Object.entries(users).map(([username, user]: [string, any]) => ({
      username,
      role: user.role,
      info: user.info
    }))

    return NextResponse.json(userList)
  } catch (error) {
    console.error("사용자 목록 조회 중 오류 발생:", error)
    return NextResponse.json(
      { error: "사용자 목록 조회 중 오류가 발생했습니다" },
      { status: 500 }
    )
  }
} 