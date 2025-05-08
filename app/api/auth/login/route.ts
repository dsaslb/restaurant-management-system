import { NextResponse } from "next/server"
import { sign } from "jsonwebtoken"
import { cookies } from "next/headers"

const JWT_SECRET = process.env.JWT_SECRET || "your-secret-key"

export async function POST(request: Request) {
  try {
    const body = await request.json()
    const { username, password } = body

    // TODO: 실제 데이터베이스에서 사용자 확인
    // 현재는 임시로 하드코딩된 사용자 정보 사용
    const users = {
      "admin": {
        password: "admin123", // 실제로는 해시된 비밀번호를 사용해야 합니다
        role: "admin"
      }
    }

    const user = users[username]
    if (!user || user.password !== password) {
      return NextResponse.json(
        { error: "잘못된 사용자 이름 또는 비밀번호입니다" },
        { status: 401 }
      )
    }

    // JWT 토큰 생성
    const token = sign(
      { username, role: user.role },
      JWT_SECRET,
      { expiresIn: "2h" }
    )

    // 쿠키에 토큰 저장
    cookies().set("token", token, {
      httpOnly: true,
      secure: process.env.NODE_ENV === "production",
      sameSite: "strict",
      maxAge: 2 * 60 * 60 // 2시간
    })

    return NextResponse.json({ success: true })
  } catch (error) {
    console.error("로그인 처리 중 오류 발생:", error)
    return NextResponse.json(
      { error: "로그인 처리 중 오류가 발생했습니다" },
      { status: 500 }
    )
  }
} 