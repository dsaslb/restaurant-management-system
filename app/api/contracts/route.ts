import { NextResponse } from "next/server"
import { promises as fs } from "fs"
import path from "path"
import { PDFDocument } from "pdf-lib"

const CONTRACTS_DIR = path.join(process.cwd(), "contracts")

// PDF 생성 함수
async function createContractPDF(data: {
  username: string
  position: string
  wage: number
  startDate: string
  endDate: string
  signature: string
}) {
  try {
    const pdfDoc = await PDFDocument.create()
    const page = pdfDoc.addPage()
    const { width, height } = page.getSize()

    // 기본 폰트 사용 (외부 폰트 의존성 제거)
    page.drawText("근로계약서", {
      x: width / 2 - 50,
      y: height - 50,
      size: 20,
    })

    page.drawText(`이름: ${data.username}`, {
      x: 50,
      y: height - 100,
      size: 12,
    })

    page.drawText(`직책: ${data.position}`, {
      x: 50,
      y: height - 120,
      size: 12,
    })

    page.drawText(`급여: ${data.wage.toLocaleString()}원`, {
      x: 50,
      y: height - 140,
      size: 12,
    })

    page.drawText(`계약기간: ${data.startDate} ~ ${data.endDate}`, {
      x: 50,
      y: height - 160,
      size: 12,
    })

    page.drawText(`서명: ${data.signature}`, {
      x: 50,
      y: height - 200,
      size: 12,
    })

    return await pdfDoc.save()
  } catch (error) {
    console.error("PDF 생성 중 오류 발생:", error)
    throw new Error("PDF 생성에 실패했습니다")
  }
}

export async function GET() {
  try {
    // contracts 디렉토리가 없으면 생성
    await fs.mkdir(CONTRACTS_DIR, { recursive: true })

    // 계약서 파일 목록 가져오기
    const files = await fs.readdir(CONTRACTS_DIR)
    const contracts = await Promise.all(
      files
        .filter((file) => file.endsWith(".pdf"))
        .map(async (file) => {
          try {
            const filePath = path.join(CONTRACTS_DIR, file)
            const stats = await fs.stat(filePath)
            const [username, date] = file.replace(".pdf", "").split("_")
            
            return {
              id: file,
              username,
              position: "직원", // 실제로는 PDF에서 추출하거나 DB에서 가져와야 함
              wage: 3000000, // 실제로는 PDF에서 추출하거나 DB에서 가져와야 함
              startDate: date,
              endDate: new Date(new Date(date).setFullYear(new Date(date).getFullYear() + 1)).toISOString(),
              status: new Date(date) > new Date() ? "active" : "expired",
              fileUrl: `/api/contracts/${file}`,
            }
          } catch (error) {
            console.error(`파일 처리 중 오류 발생: ${file}`, error)
            return null
          }
        })
    )

    // null 값 필터링
    const validContracts = contracts.filter((contract): contract is NonNullable<typeof contract> => contract !== null)

    return NextResponse.json(validContracts)
  } catch (error) {
    console.error("계약 목록을 가져오는데 실패했습니다:", error)
    return NextResponse.json(
      { error: "계약 목록을 가져오는데 실패했습니다" },
      { status: 500 }
    )
  }
}

export async function POST(request: Request) {
  try {
    const data = await request.json()
    
    // 필수 필드 검증
    const requiredFields = ["username", "position", "wage", "startDate", "endDate", "signature"]
    for (const field of requiredFields) {
      if (!data[field]) {
        return NextResponse.json(
          { error: `${field} 필드가 필요합니다` },
          { status: 400 }
        )
      }
    }

    // PDF 생성
    const pdfBytes = await createContractPDF(data)

    // 파일명 생성 (중복 방지)
    const timestamp = new Date().getTime()
    const fileName = `${data.username}_${data.startDate}_${timestamp}.pdf`
    const filePath = path.join(CONTRACTS_DIR, fileName)

    // PDF 저장
    await fs.writeFile(filePath, pdfBytes)

    return NextResponse.json({
      success: true,
      file: fileName,
    })
  } catch (error) {
    console.error("계약서 생성에 실패했습니다:", error)
    return NextResponse.json(
      { error: "계약서 생성에 실패했습니다" },
      { status: 500 }
    )
  }
} 