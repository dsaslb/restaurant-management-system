import { NextResponse } from "next/server"
import { compare } from "bcryptjs"
import { readFile } from "fs/promises"
import { existsSync } from "fs"
import path from "path"
import { sign } from "jsonwebtoken"
import { cookies } from "next/headers"

const USER_DATA_FILE = path.join(process.cwd(), "data", "users.json")
const JWT_SECRET = process.env.JWT_SECRET || "your-secret-key"

export async function POST(request: Request) {
  try {
    const body = await request.json()
    const { username, password } = body

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
        { error: "아이디 또는 비밀번호가 올바르지 않습니다" },
        { status: 401 }
      )
    }

    const user = users[username]

    // 승인 상태 확인
    if (user.status !== "active") {
      return NextResponse.json(
        { error: "승인 대기 중인 계정입니다. 관리자 승인 후 로그인이 가능합니다." },
        { status: 401 }
      )
    }

    const isValid = await compare(password, user.password)
    if (!isValid) {
      return NextResponse.json(
        { error: "아이디 또는 비밀번호가 올바르지 않습니다" },
        { status: 401 }
      )
    }

    const role = user.role || "staff"
    const token = sign(
      { username, role },
      JWT_SECRET,
      { expiresIn: "2h" }
    )

    cookies().set("token", token, {
      httpOnly: true,
      secure: process.env.NODE_ENV === "production",
      sameSite: "strict",
      maxAge: 2 * 60 * 60 // 2시간
    })

    return NextResponse.json({ success: true, role })
  } catch (error) {
    console.error("로그인 처리 중 오류 발생:", error)
    return NextResponse.json(
      { error: "로그인 처리 중 오류가 발생했습니다" },
      { status: 500 }
    )
  }
} 