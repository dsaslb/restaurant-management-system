"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { FileText, Download, Plus } from "lucide-react"
import { toast } from "sonner"
import { BulkImport } from "./bulk-import"

interface Contract {
  id: string
  username: string
  position: string
  wage: number
  startDate: string
  endDate: string
  status: "active" | "expired" | "renewed"
  fileUrl: string
}

interface ContractFormData {
  username: string
  position: string
  wage: string
  startDate: string
  endDate: string
  signature: string
}

export default function ContractsPage() {
  const [contracts, setContracts] = useState<Contract[]>([])
  const [stats, setStats] = useState({
    totalContracts: 0,
    activeContracts: 0,
    expiringContracts: 0,
  })
  const [isLoading, setIsLoading] = useState(false)
  const [isDialogOpen, setIsDialogOpen] = useState(false)

  // const form = useForm<ContractFormData>({
  //   defaultValues: {
  //     username: "",
  //     position: "",
  //     wage: "",
  //     startDate: format(new Date(), "yyyy-MM-dd"),
  //     endDate: format(new Date(new Date().setFullYear(new Date().getFullYear() + 1)), "yyyy-MM-dd"),
  //     signature: "",
  //   },
  // })

  useEffect(() => {
    fetchContracts()
    fetchStats()
  }, [])

  const fetchContracts = async () => {
    try {
      setIsLoading(true)
      const response = await fetch("/api/contracts")
      if (!response.ok) throw new Error("계약 목록을 불러오는데 실패했습니다")
      const data = await response.json()
      setContracts(data)
    } catch (error) {
      console.error("계약 목록을 불러오는데 실패했습니다:", error)
      toast.error("계약 목록을 불러오는데 실패했습니다")
    } finally {
      setIsLoading(false)
    }
  }

  const fetchStats = async () => {
    try {
      const response = await fetch("/api/contracts/stats")
      if (!response.ok) throw new Error("통계를 불러오는데 실패했습니다")
      const data = await response.json()
      setStats(data)
    } catch (error) {
      console.error("통계를 불러오는데 실패했습니다:", error)
      toast.error("통계를 불러오는데 실패했습니다")
    }
  }

  const handleDownload = async (fileUrl: string) => {
    try {
      const response = await fetch(fileUrl)
      if (!response.ok) throw new Error("파일 다운로드에 실패했습니다")
      const blob = await response.blob()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement("a")
      a.href = url
      a.download = fileUrl.split("/").pop() || "contract.pdf"
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
    } catch (error) {
      console.error("파일 다운로드에 실패했습니다:", error)
      toast.error("파일 다운로드에 실패했습니다")
    }
  }

  // const onSubmit = async (data: ContractFormData) => {
  //   try {
  //     setIsLoading(true)
  //     const response = await fetch("/api/contracts", {
  //       method: "POST",
  //       headers: {
  //         "Content-Type": "application/json",
  //       },
  //       body: JSON.stringify({
  //         ...data,
  //         wage: parseInt(data.wage.replace(/,/g, "")),
  //       }),
  //     })

  //     if (!response.ok) throw new Error("계약서 생성에 실패했습니다")

  //     toast.success("계약서가 생성되었습니다")
  //     setIsDialogOpen(false)
  //     form.reset()
  //     fetchContracts()
  //     fetchStats()
  //   } catch (error) {
  //     console.error("계약서 생성에 실패했습니다:", error)
  //     toast.error("계약서 생성에 실패했습니다")
  //   } finally {
  //     setIsLoading(false)
  //   }
  // }

  return (
    <div className="container mx-auto py-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">계약 관리</h1>
        <div className="flex items-center gap-2">
          <BulkImport />
          <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
            <DialogTrigger asChild>
              <Button>
                <Plus className="h-4 w-4 mr-2" />
                새 계약
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>새 계약서 작성</DialogTitle>
                <DialogDescription>
                  새로운 근로계약서를 작성합니다.
                </DialogDescription>
              </DialogHeader>
              {/* <Form {...form}>
                <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
                  <FormField
                    control={form.control}
                    name="username"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>직원명</FormLabel>
                        <FormControl>
                          <Input {...field} />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                  <FormField
                    control={form.control}
                    name="position"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>직책</FormLabel>
                        <FormControl>
                          <Input {...field} />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                  <FormField
                    control={form.control}
                    name="wage"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>급여</FormLabel>
                        <FormControl>
                          <Input
                            {...field}
                            type="text"
                            onChange={(e) => {
                              const value = e.target.value.replace(/[^0-9]/g, "")
                              field.onChange(
                                value ? parseInt(value).toLocaleString() : ""
                              )
                            }}
                          />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                  <FormField
                    control={form.control}
                    name="startDate"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>시작일</FormLabel>
                        <FormControl>
                          <Input type="date" {...field} />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                  <FormField
                    control={form.control}
                    name="endDate"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>종료일</FormLabel>
                        <FormControl>
                          <Input type="date" {...field} />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                  <FormField
                    control={form.control}
                    name="signature"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>서명</FormLabel>
                        <FormControl>
                          <Input {...field} />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                  <Button type="submit" className="w-full" disabled={isLoading}>
                    {isLoading ? "생성 중..." : "계약서 생성"}
                  </Button>
                </form>
              </Form> */}
            </DialogContent>
          </Dialog>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-3 mb-6">
        <Card>
          <CardHeader>
            <CardTitle>전체 계약</CardTitle>
            <CardDescription>총 계약서 수</CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold">{stats.totalContracts}</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>활성 계약</CardTitle>
            <CardDescription>현재 유효한 계약</CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold">{stats.activeContracts}</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>만료 예정</CardTitle>
            <CardDescription>30일 이내 만료</CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold">{stats.expiringContracts}</p>
          </CardContent>
        </Card>
      </div>

      <div className="rounded-md border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>직원명</TableHead>
              <TableHead>직책</TableHead>
              <TableHead>급여</TableHead>
              <TableHead>시작일</TableHead>
              <TableHead>종료일</TableHead>
              <TableHead>상태</TableHead>
              <TableHead>계약서</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {contracts.map((contract) => (
              <TableRow key={contract.id}>
                <TableCell>{contract.username}</TableCell>
                <TableCell>{contract.position}</TableCell>
                <TableCell>{contract.wage.toLocaleString()}원</TableCell>
                <TableCell>
                  {format(new Date(contract.startDate), "yyyy년 MM월 dd일", {
                    locale: ko,
                  })}
                </TableCell>
                <TableCell>
                  {format(new Date(contract.endDate), "yyyy년 MM월 dd일", {
                    locale: ko,
                  })}
                </TableCell>
                <TableCell>
                  <span
                    className={`px-2 py-1 rounded-full text-xs ${
                      contract.status === "active"
                        ? "bg-green-100 text-green-800"
                        : contract.status === "expired"
                        ? "bg-red-100 text-red-800"
                        : "bg-blue-100 text-blue-800"
                    }`}
                  >
                    {contract.status === "active"
                      ? "활성"
                      : contract.status === "expired"
                      ? "만료"
                      : "갱신"}
                  </span>
                </TableCell>
                <TableCell>
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => handleDownload(contract.fileUrl)}
                  >
                    <Download className="h-4 w-4" />
                  </Button>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    </div>
  )
} 