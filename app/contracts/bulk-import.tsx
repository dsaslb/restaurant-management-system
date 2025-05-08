"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import { Download, Upload } from "lucide-react"
import { toast } from "sonner"

export function BulkImport() {
  const [isDialogOpen, setIsDialogOpen] = useState(false)
  const [isLoading, setIsLoading] = useState(false)

  const downloadTemplate = () => {
    // CSV 템플릿 헤더
    const headers = [
      "직원명",
      "직책",
      "급여",
      "시작일",
      "종료일",
      "서명",
    ].join(",")

    // 예시 데이터
    const example = [
      "홍길동",
      "서버",
      "3000000",
      "2024-05-01",
      "2025-05-01",
      "홍길동",
    ].join(",")

    // CSV 내용 생성
    const csvContent = `${headers}\n${example}`

    // CSV 파일 다운로드
    const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" })
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement("a")
    a.href = url
    a.download = "계약서_일괄등록_템플릿.csv"
    document.body.appendChild(a)
    a.click()
    window.URL.revokeObjectURL(url)
    document.body.removeChild(a)
  }

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) return

    try {
      setIsLoading(true)
      // TODO: 파일 업로드 및 처리 로직 구현
      // 현재는 연결하지 않고 준비만 해둡니다
      toast.info("일괄 등록 기능은 아직 준비 중입니다.")
    } catch (error) {
      console.error("파일 업로드 실패:", error)
      toast.error("파일 업로드에 실패했습니다")
    } finally {
      setIsLoading(false)
      setIsDialogOpen(false)
    }
  }

  return (
    <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
      <DialogTrigger asChild>
        <Button variant="outline">
          <Upload className="h-4 w-4 mr-2" />
          일괄 등록
        </Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>계약서 일괄 등록</DialogTitle>
          <DialogDescription>
            CSV 파일을 통해 여러 계약서를 한 번에 등록할 수 있습니다.
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-4">
          <div className="flex items-center justify-between p-4 border rounded-lg">
            <div>
              <h3 className="font-medium">템플릿 다운로드</h3>
              <p className="text-sm text-muted-foreground">
                CSV 파일 형식의 템플릿을 다운로드합니다.
              </p>
            </div>
            <Button variant="outline" onClick={downloadTemplate}>
              <Download className="h-4 w-4 mr-2" />
              템플릿 다운로드
            </Button>
          </div>
          <div className="p-4 border rounded-lg">
            <h3 className="font-medium mb-2">파일 업로드</h3>
            <p className="text-sm text-muted-foreground mb-4">
              작성한 CSV 파일을 업로드하여 계약서를 일괄 등록합니다.
            </p>
            <div className="flex items-center gap-4">
              <input
                type="file"
                accept=".csv"
                onChange={handleFileUpload}
                className="hidden"
                id="csv-upload"
              />
              <label
                htmlFor="csv-upload"
                className="flex-1 cursor-pointer"
              >
                <div className="flex items-center justify-center w-full h-32 border-2 border-dashed rounded-lg hover:bg-accent">
                  <div className="text-center">
                    <Upload className="h-8 w-8 mx-auto mb-2 text-muted-foreground" />
                    <p className="text-sm text-muted-foreground">
                      CSV 파일을 여기에 끌어다 놓거나 클릭하여 선택하세요
                    </p>
                  </div>
                </div>
              </label>
            </div>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  )
} 