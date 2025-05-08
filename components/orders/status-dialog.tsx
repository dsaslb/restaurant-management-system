"use client"

import { useState } from "react"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"

interface StatusDialogProps {
  orderId: string
  currentStatus: string
  onStatusChange: (status: string) => Promise<void>
}

const statuses = [
  { value: "pending", label: "대기 중" },
  { value: "preparing", label: "준비 중" },
  { value: "ready", label: "준비 완료" },
  { value: "served", label: "서빙 완료" },
  { value: "completed", label: "완료" },
  { value: "cancelled", label: "취소" },
]

export function StatusDialog({ orderId, currentStatus, onStatusChange }: StatusDialogProps) {
  const [open, setOpen] = useState(false)
  const [status, setStatus] = useState(currentStatus)
  const [loading, setLoading] = useState(false)

  const handleSubmit = async () => {
    setLoading(true)
    try {
      await onStatusChange(status)
      setOpen(false)
    } catch (error) {
      console.error("상태 변경에 실패했습니다:", error)
    } finally {
      setLoading(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button>상태 변경</Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>주문 상태 변경</DialogTitle>
        </DialogHeader>
        <div className="space-y-4 py-4">
          <div className="space-y-2">
            <p className="text-sm text-muted-foreground">새로운 상태를 선택하세요</p>
            <Select value={status} onValueChange={setStatus}>
              <SelectTrigger>
                <SelectValue placeholder="상태 선택" />
              </SelectTrigger>
              <SelectContent>
                {statuses.map((status) => (
                  <SelectItem key={status.value} value={status.value}>
                    {status.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="flex justify-end space-x-2">
            <Button variant="outline" onClick={() => setOpen(false)}>
              취소
            </Button>
            <Button onClick={handleSubmit} disabled={loading}>
              {loading ? "변경 중..." : "변경"}
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  )
} 