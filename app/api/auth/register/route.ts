import { NextResponse } from "next/server"
import { hash } from "bcryptjs"
import { writeFile, readFile, mkdir } from "fs/promises"
import { existsSync } from "fs"
import path from "path"

const USER_DATA_FILE = path.join(process.cwd(), "data", "users.json")

// 사용 가능한 역할 정의
const AVAILABLE_ROLES = {
  STAFF: "staff",        // 일반 직원
  MANAGER: "manager",    // 매장 관리자
  KITCHEN: "kitchen",    // 주방 직원
  WAITER: "waiter"       // 서빙 직원
}

export async function POST(request: Request) {
  try {
    const body = await request.json()
    const { username, password, role = AVAILABLE_ROLES.STAFF } = body

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

    // 역할 유효성 검사
    if (!Object.values(AVAILABLE_ROLES).includes(role)) {
      return NextResponse.json(
        { error: "유효하지 않은 역할입니다" },
        { status: 400 }
      )
    }

    // 비밀번호 해싱
    const hashedPassword = await hash(password, 12)

    // 새 사용자 추가 (승인 대기 상태)
    users[username] = {
      password: hashedPassword,
      role,
      status: "pending", // pending: 승인 대기, active: 승인됨, rejected: 거절됨
      info: {
        name: "",
        address: ""
      },
      createdAt: new Date().toISOString()
    }

    // 사용자 데이터 저장
    await writeFile(USER_DATA_FILE, JSON.stringify(users, null, 2), "utf-8")

    return NextResponse.json({ 
      message: "회원가입이 완료되었습니다. 관리자 승인 후 로그인이 가능합니다." 
    })
  } catch (error) {
    console.error("회원가입 처리 중 오류 발생:", error)
    return NextResponse.json(
      { error: "회원가입 처리 중 오류가 발생했습니다" },
      { status: 500 }
    )
  }
} 