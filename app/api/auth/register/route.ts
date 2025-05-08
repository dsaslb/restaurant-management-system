import { NextResponse } from "next/server"
import { hash } from "bcryptjs"
import { writeFile, readFile, mkdir } from "fs/promises"
import { existsSync } from "fs"
import path from "path"

const USER_DATA_FILE = path.join(process.cwd(), "data", "users.json")

export async function POST(request: Request) {
  try {
    const body = await request.json()
    const { username, password, role = "staff" } = body

    // 데이터 디렉토리 생성
    await mkdir(path.join(process.cwd(), "data"), { recursive: true })

    // 기존 사용자 데이터 로드
    let users: Record<string, any> = {}
    if (existsSync(USER_DATA_FILE)) {
      const data = await readFile(USER_DATA_FILE, "utf-8")
      users = JSON.parse(data)
    }

    // 사용자 중복 확인
    if (users[username]) {
      return NextResponse.json(
        { error: "이미 존재하는 사용자입니다" },
        { status: 409 }
      )
    }

    // 비밀번호 해싱
    const hashedPassword = await hash(password, 12)

    // 새 사용자 추가
    users[username] = {
      password: hashedPassword,
      role,
      info: {
        name: "",
        address: ""
      }
    }

    // 사용자 데이터 저장
    await writeFile(USER_DATA_FILE, JSON.stringify(users, null, 2), "utf-8")

    return NextResponse.json({ message: "회원가입이 완료되었습니다" })
  } catch (error) {
    console.error("회원가입 처리 중 오류 발생:", error)
    return NextResponse.json(
      { error: "회원가입 처리 중 오류가 발생했습니다" },
      { status: 500 }
    )
  }
} 