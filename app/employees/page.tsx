"use client"

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import supabase from "@/lib/supabase"
import { toast } from "sonner"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { Badge } from "@/components/ui/badge"
import { ThemeToggle } from "@/components/theme-toggle"

export default function EmployeesPage() {
  const router = useRouter()
  const [employees, setEmployees] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState("")
  const [department, setDepartment] = useState("all")
  const [position, setPosition] = useState("all")

  useEffect(() => {
    fetchEmployees()
  }, [])

  const fetchEmployees = async () => {
    try {
      setLoading(true)
      const { data, error } = await supabase
        .from('employees')
        .select('*')
        .order('name')

      if (error) throw error
      setEmployees(data || [])
    } catch (error) {
      toast.error('직원 목록을 불러오는데 실패했습니다.')
    } finally {
      setLoading(false)
    }
  }

  const filteredEmployees = employees.filter(emp => {
    const matchesSearch = emp.name.toLowerCase().includes(search.toLowerCase()) ||
                         emp.email.toLowerCase().includes(search.toLowerCase())
    const matchesDepartment = department === 'all' || emp.department === department
    const matchesPosition = position === 'all' || emp.position === position
    return matchesSearch && matchesDepartment && matchesPosition
  })

  return (
    <div className="min-h-screen bg-background text-foreground">
      {/* 상단 네비게이션 */}
      <header className="flex items-center justify-between px-8 py-4 border-b">
        <div className="flex items-center gap-2 text-xl font-bold">
          <span role="img" aria-label="restaurant">🍽️</span> Restaurant ERP
        </div>
        <nav className="flex items-center gap-4">
          <Link href="/dashboard" passHref legacyBehavior><a><Button variant="ghost">대시보드</Button></a></Link>
          <Link href="/employees" passHref legacyBehavior><a><Button variant="ghost">직원</Button></a></Link>
          <Link href="/orders" passHref legacyBehavior><a><Button variant="ghost">주문</Button></a></Link>
          <Link href="/inventory" passHref legacyBehavior><a><Button variant="ghost">재고</Button></a></Link>
          <ThemeToggle />
        </nav>
      </header>

      <main className="max-w-7xl mx-auto py-10 px-4">
        <div className="flex justify-between items-center mb-8">
          <h1 className="text-3xl font-bold">직원 관리</h1>
          <Link href="/employees/new" passHref legacyBehavior>
            <a><Button>+ 직원 추가</Button></a>
          </Link>
        </div>

        {/* 검색 및 필터 */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
          <Input
            placeholder="이름 또는 이메일로 검색"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
          <Select value={department} onValueChange={setDepartment}>
            <SelectTrigger>
              <SelectValue placeholder="부서 선택" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">전체 부서</SelectItem>
              <SelectItem value="kitchen">주방</SelectItem>
              <SelectItem value="service">서비스</SelectItem>
              <SelectItem value="management">경영</SelectItem>
            </SelectContent>
          </Select>
          <Select value={position} onValueChange={setPosition}>
            <SelectTrigger>
              <SelectValue placeholder="직급 선택" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">전체 직급</SelectItem>
              <SelectItem value="manager">매니저</SelectItem>
              <SelectItem value="chef">주방장</SelectItem>
              <SelectItem value="staff">직원</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {/* 직원 목록 */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {loading ? (
            <div>로딩 중...</div>
          ) : filteredEmployees.length === 0 ? (
            <div>검색 결과가 없습니다.</div>
          ) : (
            filteredEmployees.map((employee) => (
              <Link href={`/employees/${employee.id}`} key={employee.id} passHref legacyBehavior>
                <a>
                  <Card className="hover:shadow-lg transition-shadow">
                    <CardHeader className="flex flex-row items-center gap-4">
                      <Avatar className="h-12 w-12">
                        <AvatarImage src={employee.profile_image} alt={employee.name} />
                        <AvatarFallback>{employee.name[0]}</AvatarFallback>
                      </Avatar>
                      <div>
                        <CardTitle className="text-lg">{employee.name}</CardTitle>
                        <div className="text-sm text-muted-foreground">{employee.email}</div>
                      </div>
                    </CardHeader>
                    <CardContent>
                      <div className="flex flex-wrap gap-2">
                        <Badge variant="secondary">{employee.department}</Badge>
                        <Badge variant="outline">{employee.position}</Badge>
                      </div>
                    </CardContent>
                  </Card>
                </a>
              </Link>
            ))
          )}
        </div>
      </main>
    </div>
  )
} 