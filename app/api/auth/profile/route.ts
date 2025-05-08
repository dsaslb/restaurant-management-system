import { NextResponse } from "next/server"
import { writeFile, readFile } from "fs/promises"
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

    const decoded = verify(token, JWT_SECRET) as { username: string }
    const username = decoded.username

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

    const { password, ...userInfo } = users[username]
    return NextResponse.json(userInfo)
  } catch (error) {
    console.error("프로필 조회 중 오류 발생:", error)
    return NextResponse.json(
      { error: "프로필 조회 중 오류가 발생했습니다" },
      { status: 500 }
    )
  }
}

export async function PUT(request: Request) {
  try {
    const body = await request.json()
    const { name, address } = body

    const token = cookies().get("token")?.value
    if (!token) {
      return NextResponse.json(
        { error: "인증되지 않은 요청입니다" },
        { status: 401 }
      )
    }

    const decoded = verify(token, JWT_SECRET) as { username: string }
    const username = decoded.username

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

    // 프로필 정보 업데이트
    users[username].info = {
      name: name || users[username].info.name,
      address: address || users[username].info.address
    }

    await writeFile(USER_DATA_FILE, JSON.stringify(users, null, 2), "utf-8")

    return NextResponse.json({ message: "프로필이 업데이트되었습니다" })
  } catch (error) {
    console.error("프로필 업데이트 중 오류 발생:", error)
    return NextResponse.json(
      { error: "프로필 업데이트 중 오류가 발생했습니다" },
      { status: 500 }
    )
  }
} 