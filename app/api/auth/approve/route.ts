import { NextResponse } from "next/server"
import { readFile, writeFile } from "fs/promises"
import { existsSync } from "fs"
import path from "path"
import { cookies } from "next/headers"
import { verify } from "jsonwebtoken"

const USER_DATA_FILE = path.join(process.cwd(), "data", "users.json")
const JWT_SECRET = process.env.JWT_SECRET || "your-secret-key"

export async function POST(request: Request) {
  try {
    // 관리자 권한 확인
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

    const body = await request.json()
    const { username, action } = body // action: "approve" or "reject"

    if (!existsSync(USER_DATA_FILE)) {
      return NextResponse.json(
        { error: "사용자 데이터를 찾을 수 없습니다" },
        { status: 404 }
      )
    }

    const data = await readFile(USER_DATA_FILE, "utf-8")
    const users = JSON.parse(data)

    if (!users[username]) {
      return NextResponse.json(
        { error: "사용자를 찾을 수 없습니다" },
        { status: 404 }
      )
    }

    // 승인/거절 처리
    if (action === "approve") {
      users[username].status = "active"
    } else if (action === "reject") {
      users[username].status = "rejected"
    } else {
      return NextResponse.json(
        { error: "잘못된 요청입니다" },
        { status: 400 }
      )
    }

    // 변경사항 저장
    await writeFile(USER_DATA_FILE, JSON.stringify(users, null, 2), "utf-8")

    return NextResponse.json({ 
      message: action === "approve" ? "사용자가 승인되었습니다" : "사용자가 거절되었습니다" 
    })
  } catch (error) {
    console.error("승인 처리 중 오류 발생:", error)
    return NextResponse.json(
      { error: "승인 처리 중 오류가 발생했습니다" },
      { status: 500 }
    )
  }
} 