import { NextResponse } from "next/server"
import { hash, compare } from "bcryptjs"
import { writeFile, readFile } from "fs/promises"
import { existsSync } from "fs"
import path from "path"
import { cookies } from "next/headers"
import { verify } from "jsonwebtoken"

const USER_DATA_FILE = path.join(process.cwd(), "data", "users.json")
const JWT_SECRET = process.env.JWT_SECRET || "your-secret-key"

export async function POST(request: Request) {
  try {
    const body = await request.json()
    const { oldPassword, newPassword } = body

    // 토큰에서 사용자 정보 가져오기
    const token = cookies().get("token")?.value
    if (!token) {
      return NextResponse.json(
        { error: "인증되지 않은 요청입니다" },
        { status: 401 }
      )
    }

    const decoded = verify(token, JWT_SECRET) as { username: string }
    const username = decoded.username

    // 사용자 데이터 로드
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

    // 기존 비밀번호 확인
    const isValid = await compare(oldPassword, users[username].password)
    if (!isValid) {
      return NextResponse.json(
        { error: "기존 비밀번호가 올바르지 않습니다" },
        { status: 401 }
      )
    }

    // 새 비밀번호 해싱 및 저장
    users[username].password = await hash(newPassword, 12)
    await writeFile(USER_DATA_FILE, JSON.stringify(users, null, 2), "utf-8")

    return NextResponse.json({ message: "비밀번호가 변경되었습니다" })
  } catch (error) {
    console.error("비밀번호 변경 중 오류 발생:", error)
    return NextResponse.json(
      { error: "비밀번호 변경 중 오류가 발생했습니다" },
      { status: 500 }
    )
  }
} 