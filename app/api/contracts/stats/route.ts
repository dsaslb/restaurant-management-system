import { NextResponse } from "next/server"
import { promises as fs } from "fs"
import path from "path"

const CONTRACTS_DIR = path.join(process.cwd(), "contracts")

export async function GET() {
  try {
    // contracts 디렉토리가 없으면 생성
    await fs.mkdir(CONTRACTS_DIR, { recursive: true })

    // 계약서 파일 목록 가져오기
    const files = await fs.readdir(CONTRACTS_DIR)
    const contracts = files.filter((file) => file.endsWith(".pdf"))

    // 현재 날짜
    const now = new Date()
    const thirtyDaysLater = new Date(now)
    thirtyDaysLater.setDate(now.getDate() + 30)

    // 통계 계산
    const stats = {
      totalContracts: contracts.length,
      activeContracts: 0,
      expiringContracts: 0,
    }

    for (const file of contracts) {
      const [_, date] = file.replace(".pdf", "").split("_")
      const contractDate = new Date(date)
      const endDate = new Date(contractDate)
      endDate.setFullYear(contractDate.getFullYear() + 1)

      if (endDate > now) {
        stats.activeContracts++
      }

      if (endDate > now && endDate <= thirtyDaysLater) {
        stats.expiringContracts++
      }
    }

    return NextResponse.json(stats)
  } catch (error) {
    console.error("통계를 가져오는데 실패했습니다:", error)
    return NextResponse.json(
      { error: "통계를 가져오는데 실패했습니다" },
      { status: 500 }
    )
  }
} 