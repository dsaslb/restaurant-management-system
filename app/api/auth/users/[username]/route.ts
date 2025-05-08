import { NextResponse } from "next/server"
import { readFile, writeFile } from "fs/promises"
import { existsSync } from "fs"
import path from "path"
import { cookies } from "next/headers"
import { verify } from "jsonwebtoken"

const USER_DATA_FILE = path.join(process.cwd(), "data", "users.json")
const JWT_SECRET = process.env.JWT_SECRET || "your-secret-key"

export async function DELETE(
  request: Request,
  { params }: { params: { username: string } }
) {
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
      return NextResponse.json(
        { error: "사용자 데이터를 찾을 수 없습니다" },
        { status: 404 }
      )
    }

    const data = await readFile(USER_DATA_FILE, "utf-8")
    const users = JSON.parse(data)

    if (!users[params.username]) {
      return NextResponse.json(
        { error: "사용자를 찾을 수 없습니다" },
        { status: 404 }
      )
    }

    // 자기 자신은 삭제할 수 없음
    if (params.username === decoded.username) {
      return NextResponse.json(
        { error: "자기 자신은 삭제할 수 없습니다" },
        { status: 400 }
      )
    }

    // 사용자 삭제
    delete users[params.username]
    await writeFile(USER_DATA_FILE, JSON.stringify(users, null, 2), "utf-8")

    return NextResponse.json({ message: "사용자가 삭제되었습니다" })
  } catch (error) {
    console.error("사용자 삭제 중 오류 발생:", error)
    return NextResponse.json(
      { error: "사용자 삭제 중 오류가 발생했습니다" },
      { status: 500 }
    )
  }
} 