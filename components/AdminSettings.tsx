'use client';
import React, { useEffect, useState, useRef } from 'react';
import { Trash2, Edit2, Save, Filter, Trash } from 'lucide-react';
import { createClient } from '@supabase/supabase-js';
import './globals.css'
import { ReactNode } from 'react'
import { Navbar } from '@/components/layout/navbar'
import { Toaster, toast } from 'sonner'
import { NextResponse } from 'next/server'
import supabase from '@/lib/supabase'
import { BarChart, Bar, XAxis, YAxis, Tooltip } from 'recharts'
import * as XLSX from 'xlsx'
import { useSearchParams, useParams } from 'next/navigation'
import EmployeeList from "@/components/employee-list"
import { Chat } from "@/components/ui/chat"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { Button } from "@/components/ui/button"
import { Phone, Mail, Calendar, Briefcase, Building, Eye } from "lucide-react"
import Link from "next/link"
import { EmployeeCards } from "./employee-cards"
import { EmployeeDetail as EmployeeDetailComponent } from "./employee-detail"
import { Dialog, DialogTrigger } from "./ui/dialog"
import { EmployeeFileUpload } from "./employee-file-upload"
import { AttendanceEditor } from "./attendance-editor"
import { ExcelUpload } from "./excel-upload"
import { AttendanceChart } from "./attendance-chart"
import NotificationList from "./NotificationList"
import { NotificationBell } from "./notification-bell"
import { Employee } from './types'; // Assuming a types file exists for Employee
// import { NotificationListener } from "@/components/notifications/NotificationListener"

const CATEGORIES = [
  { key: 'system', label: '시스템' },
  { key: 'notification', label: '알림' },
  { key: 'security', label: '보안' },
];

const supabaseClient = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
);

export async function uploadPhoto(file: File, userId: string) {
  const filePath = `profile/${userId}_${Date.now()}.jpg`;
  const { data, error } = await supabaseClient.storage
    .from('profile-photos')
    .upload(filePath, file, { cacheControl: '3600', upsert: true });
  if (error) throw error;
  // 업로드 후 public URL 얻기
  const { data: urlData } = supabaseClient.storage.from('profile-photos').getPublicUrl(filePath);
  return urlData.publicUrl;
}

export default function EmployeesPage({ user }: { user: any }) {
  return <EmployeeList user={user} />
}

export function PhotoUpload({ onUpload }: { onUpload: (file: File) => void }) {
  const [preview, setPreview] = useState<string | null>(null);

  function handleChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (file) {
      setPreview(URL.createObjectURL(file));
      onUpload(file);
    }
  }

  return (
    <div className="flex flex-col gap-2">
      <input
        type="file"
        accept="image/*"
        capture="user"
        onChange={handleChange}
        className="border px-2 py-1 rounded"
      />
      {preview && (
        <img src={preview} alt="미리보기" className="w-24 h-24 object-cover rounded" />
      )}
    </div>
  );
}

export function SendNotification({ user, employees }: { user: any, employees: any[] }) {
  const [message, setMessage] = useState('');
  const [target, setTarget] = useState('all');

  async function send() {
    await fetch('/api/notifications', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message,
        target: user.role === 'admin' ? target : user.id,
        sender: user.id,
      }),
    });
    setMessage('');
  }

  return (
    <div className="flex flex-col gap-2">
      {user.role === 'admin' && (
        <select value={target} onChange={e => setTarget(e.target.value)} className="border px-2 py-1 rounded">
          <option value="all">전체 직원</option>
          {employees.map((emp: any) => (
            <option key={emp.id} value={emp.id}>{emp.name}</option>
          ))}
        </select>
      )}
      <input value={message} onChange={e => setMessage(e.target.value)} placeholder="알림 내용" className="border px-2 py-1 rounded" />
      <button onClick={send} className="bg-blue-500 text-white px-3 py-1 rounded">알림 보내기</button>
    </div>
  );
}

export const metadata = {
  title: 'Restaurant ERP',
  description: '외식업 종합 ERP 시스템',
}

// Define the type for user
interface User {
  id: string;
  role: string;
  name: string;
  // Add other properties as needed
}

export function VacationRequest({ user }: { user: User }) {
  const [date, setDate] = useState('')
  const [reason, setReason] = useState('')
  const [message, setMessage] = useState('')
  const [loading, setLoading] = useState(false)
  const [checkMsg, setCheckMsg] = useState('')

  async function handleDateChange(e: React.ChangeEvent<HTMLInputElement>) {
    const newDate = e.target.value
    setDate(newDate)
    if (!newDate) return setCheckMsg('')
    const res = await fetch(`/api/schedule/check?user_id=${user.id}&date=${newDate}`)
    const { ok, reason } = await res.json()
    setCheckMsg(ok ? '신청 가능' : `신청 불가: ${reason}`)
  }

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault()
    setLoading(true)
    setMessage('')
    const res = await fetch('/api/vacations', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ user_id: user.id, date, reason })
    })
    if (res.ok) {
      setMessage('휴무 신청이 완료되었습니다!')
      setDate('')
      setReason('')
      setCheckMsg('')
    } else {
      setMessage('신청 실패: ' + (await res.json()).error)
    }
    setLoading(false)
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-2 max-w-xs">
      <label>
        날짜 선택
        <input type="date" value={date} onChange={handleDateChange} required className="border px-2 py-1 rounded" />
      </label>
      {checkMsg && <div className={checkMsg.startsWith('신청 가능') ? 'text-green-600' : 'text-red-500'}>{checkMsg}</div>}
      <label>
        사유(필수)
        <input type="text" value={reason} onChange={e => setReason(e.target.value)} required className="border px-2 py-1 rounded" />
      </label>
      <button type="submit" className="bg-blue-500 text-white px-3 py-1 rounded" disabled={loading || !date || !reason || !checkMsg.startsWith('신청 가능')}>
        {loading ? '신청 중...' : '휴무 신청'}
      </button>
      {message && <div className="text-green-600">{message}</div>}
    </form>
  );
}

// 두 좌표 간 거리 계산 함수 (Haversine 공식)
function getDistance(lat1: number, lng1: number, lat2: number, lng2: number) {
  const R = 6371e3; // m
  const toRad = (d: number) => d * Math.PI / 180;
  const dLat = toRad(lat2 - lat1);
  const dLng = toRad(lng2 - lng1);
  const a = Math.sin(dLat / 2) ** 2 +
            Math.cos(toRad(lat1)) * Math.cos(toRad(lat2)) *
            Math.sin(dLng / 2) ** 2;
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  return R * c; // meter
}

export async function POST(req: Request) {
  const formData = await req.formData()
  const isCheckIn = formData.get('isCheckIn') === 'true'
  const lat = formData.get('lat')
  const lng = formData.get('lng')
  const photo = formData.get('photo') // Blob

  // Supabase Storage 업로드 예시
  let photoUrl = ''
  if (photo && typeof photo === 'object') {
    const fileName = `attendance/${Date.now()}.jpg`
    const { data, error } = await supabase.storage.from('attendance-photos').upload(fileName, photo, { upsert: true })
    if (!error) {
      const { data: urlData } = supabase.storage.from('attendance-photos').getPublicUrl(fileName)
      photoUrl = urlData?.publicUrl || ''
    }
  }

  // 출근/퇴근 기록에 photoUrl 저장
  await supabase.from('attendance').insert({
    // ...기존 필드
    photo: photoUrl
  })
  // ...
}

export async function GET(req: Request) {
  // 쿼리: ?period=month&user_id=...
  // Supabase에서 group by, count 등으로 통계 집계
  // 예: 월별 출근일수, 지각률, 결근 등
}

navigator.geolocation.getCurrentPosition(async (pos) => {
  const lat = pos.coords.latitude
  const lng = pos.coords.longitude
  await handleCheck(true, lat, lng)
})

export function UnlockUserPage() {
  const [email, setEmail] = useState('')
  const [message, setMessage] = useState('')

  const handleUnlock = async () => {
    const res = await fetch('/api/admin/unlock-user', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email })
    })
    if (res.ok) setMessage('계정 잠금이 해제되었습니다!')
    else setMessage('해제 실패: ' + (await res.json()).error)
  }

  return (
    <div className="max-w-sm mx-auto mt-16 p-6 border rounded shadow">
      <h1 className="text-lg font-bold mb-4">계정 잠금 해제(관리자)</h1>
      <input
        type="email"
        placeholder="직원 이메일"
        value={email}
        onChange={e => setEmail(e.target.value)}
        className="w-full border px-3 py-2 mb-2"
      />
      <button onClick={handleUnlock} className="w-full bg-blue-600 text-white py-2 rounded">
        잠금 해제
      </button>
      {message && <p className="mt-2 text-green-600">{message}</p>}
    </div>
  )
}

export const config = {
  matcher: [
    '/dashboard/:path*',
    '/employees/:path*',
    '/contracts/:path*',
    '/payroll/:path*',
    '/attendance/:path*',
    '/settings/:path*'
  ]
}

type AttendanceRecord = {
  id: string | number;
  check_in?: string;
  check_out?: string;
  location?: string;
  weather?: string;
  reason?: string;
};

export function EmployeeDetail({ id, user }: { id: string; user: User }) {
  const [employee, setEmployee] = useState<any>(null)
  const [attendance, setAttendance] = useState([])
  const [contracts, setContracts] = useState([])
  const [benefits, setBenefits] = useState([])
  const [evaluations, setEvaluations] = useState([])

  const supabase = createClient(process.env.NEXT_PUBLIC_SUPABASE_URL!, process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!)

  useEffect(() => {
    async function fetchEmployee() {
      const { data } = await supabase.from("employees").select("*").eq("id", id).single()
      setEmployee(data)
    }
    fetchEmployee()
  }, [id])

  useEffect(() => {
    async function fetchDetails() {
      const { data: att } = await supabase.from("attendance").select("*").eq("employee_id", id)
      setAttendance(att || [])
      const { data: con } = await supabase.from("contracts").select("*").eq("employee_id", id)
      setContracts(con || [])
      const { data: ben } = await supabase.from("benefits").select("*").eq("employee_id", id)
      setBenefits(ben || [])
      const { data: eva } = await supabase.from("evaluations").select("*").eq("employee_id", id)
      setEvaluations(eva || [])
    }
    fetchDetails()
  }, [id])

  useEffect(() => {
    const channel = supabase
      .channel("notifications")
      .on("postgres_changes", { event: "INSERT", schema: "public", table: "notifications" }, payload => {
        toast.info(`새 알림: ${payload.new.message}`)
      })
      .subscribe()
    return () => { supabase.removeChannel(channel) }
  }, [])

  if (!employee) return <div>로딩 중...</div>

  return (
    <Card className="max-w-lg mx-auto mt-8">
      <CardContent className="p-6">
        <div className="flex items-center gap-4 mb-4">
          <Avatar className="h-16 w-16">
            <AvatarImage src={employee.image || "/placeholder.svg"} alt={employee.name} />
            <AvatarFallback>{employee.name.slice(0, 1)}</AvatarFallback>
          </Avatar>
          <div>
            <h2 className="text-xl font-bold">{employee.name}</h2>
            <Badge variant={employee.status === "active" ? "default" : "secondary"}>
              {employee.status === "active" ? "재직 중" : "퇴사"}
            </Badge>
            <div className="text-sm text-muted-foreground">{employee.position}</div>
          </div>
        </div>
        <div className="space-y-2">
          <div className="flex items-center text-sm">
            <Building className="mr-2 h-4 w-4" />
            <span>{employee.department}</span>
          </div>
          <div className="flex items-center text-sm">
            <Briefcase className="mr-2 h-4 w-4" />
            <span>{employee.contract}</span>
          </div>
          <div className="flex items-center text-sm">
            <Calendar className="mr-2 h-4 w-4" />
            <span>{formatDate(employee.joinDate)}</span>
          </div>
          <div className="flex items-center text-sm">
            <Phone className="mr-2 h-4 w-4" />
            <a href={`tel:${employee.phone}`} className="hover:underline">{employee.phone}</a>
          </div>
          <div className="flex items-center text-sm">
            <Mail className="mr-2 h-4 w-4" />
            <a href={`mailto:${employee.email}`} className="hover:underline">{employee.email}</a>
          </div>
        </div>
        {user?.role === "admin" && (
          <div className="mt-6 flex w-full gap-2">
            <Dialog>
              <DialogTrigger asChild>
                <Button variant="destructive" className="flex-1">
                  <Trash className="mr-2 h-4 w-4" />
                  삭제
                </Button>
              </DialogTrigger>
            </Dialog>
          </div>
        )}
        {user?.role === "admin" && !record.approved && (
          <Button onClick={() => approveRecord(record.id)}>승인</Button>
        )}

        {/* 파일 업로드/다운로드 */}
        <EmployeeFileUpload employeeId={id} />

        {/* 근무기록 등록/수정/삭제 (관리자만) */}
        {user?.role === "admin" && <AttendanceEditor employeeId={id} onSaved={fetchAttendance} />}

        {/* 엑셀 업로드 (관리자만) */}
        {user?.role === "admin" && <ExcelUpload onUploaded={fetchAttendance} />}
      </CardContent>
    </Card>
  )
}

function formatDate(dateString: string): string {
  const date = new Date(dateString)
  return new Intl.DateTimeFormat("ko-KR", { year: "numeric", month: "long", day: "numeric" }).format(date)
}

export default function SomePage({ user }) {
  return <Chat user={user} />
}

export function handleFileChange(e) {
  const file = e.target.files?.[0]
  if (!file) return
  // Supabase Storage 업로드
  const filePath = `chat/${user.id}_${Date.now()}_${file.name}`
  const { data, error } = supabase.storage.from('chat-files').upload(filePath, file)
  if (!error) {
    const { data: urlData } = supabase.storage.from('chat-files').getPublicUrl(filePath)
    // 여기에 파일 업로드 후 처리 로직을 추가해야 합니다
  }
}

// 메시지 삭제
async function handleDelete(id) {
  await supabase.from('messages').update({ deleted: true }).eq('id', id)
}

// 메시지 수정
async function handleEdit(msg) {
  const newText = prompt('수정할 메시지:', msg.text)
  if (newText && newText !== msg.text) {
    await supabase.from('messages').update({ text: newText, edited: true }).eq('id', msg.id)
  }
}

// 파일 업로드
async function handleFileChange(e) {
  const file = e.target.files?.[0]
  if (!file) return
  // Supabase Storage 업로드
  const filePath = `chat/${user.id}_${Date.now()}_${file.name}`
  const { data, error } = await supabase.storage.from('chat-files').upload(filePath, file)
  if (!error) {
    const { data: urlData } = supabase.storage.from('chat-files').getPublicUrl(filePath)
    await supabase.from('messages').insert({
      user_id: user.id,
      user_name: user.name,
      role: user.role,
      text: '', // 파일만 전송
      file_url: urlData.publicUrl,
      channel: 'general'
    })
  }
}

interface Employee {
  id: string
  name: string
  position: string
  department: string
  status: string
  joinDate: string
  contract: string
  phone: string
  email: string
  image: string
}

interface EmployeeCardsData {
  id: string;
  name: string;
  // 필요에 따라 속성 추가
}

export function EmployeeCards({ employees, user }: { employees: Employee[]; user: User }) {
  const [search, setSearch] = useState("")
  const [status, setStatus] = useState("all")

  // 검색/필터 적용
  const filtered = employees.filter(emp =>
    (emp.name.includes(search) || emp.department.includes(search) || emp.position.includes(search)) &&
    (status === "all" || emp.status === status)
  )

  return (
    <>
      {/* 관리자만 보이는 버튼 예시 */}
      {user?.role === "admin" && (
        <div className="mb-2">
          <Button>직원 추가</Button>
        </div>
      )}
      <div className="flex gap-2 mb-4">
        <input
          type="text"
          placeholder="이름/부서/직책 검색"
          value={search}
          onChange={e => setSearch(e.target.value)}
          className="border px-2 py-1 rounded"
        />
        <select value={status} onChange={e => setStatus(e.target.value)} className="border px-2 py-1 rounded">
          <option value="all">전체</option>
          <option value="active">재직 중</option>
          <option value="inactive">퇴사</option>
        </select>
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
        {filtered.length === 0 ? (
          <div className="col-span-full text-center text-gray-400">직원이 없습니다.</div>
        ) : (
          filtered.map((employee) => (
            <Card key={employee.id} className="overflow-hidden">
              <CardContent className="p-0">
                <div className="flex items-center gap-4 border-b p-4">
                  <Avatar className="h-12 w-12">
                    <AvatarImage src={employee.image || "/placeholder.svg"} alt={employee.name} />
                    <AvatarFallback>{employee.name.slice(0, 1)}</AvatarFallback>
                  </Avatar>
                  <div className="flex-1">
                    <div className="flex items-center justify-between">
                      <h3 className="font-semibold">{employee.name}</h3>
                      <Badge variant={employee.status === "active" ? "default" : "secondary"} className="ml-2">
                        {employee.status === "active" ? "재직 중" : "퇴사"}
                      </Badge>
                    </div>
                    <p className="text-sm text-muted-foreground">{employee.position}</p>
                  </div>
                </div>
                <div className="space-y-2 p-4">
                  <div className="flex items-center text-sm">
                    <Building className="mr-2 h-4 w-4 text-muted-foreground" />
                    <span>{employee.department}</span>
                  </div>
                  <div className="flex items-center text-sm">
                    <Briefcase className="mr-2 h-4 w-4 text-muted-foreground" />
                    <span>{employee.contract}</span>
                  </div>
                  <div className="flex items-center text-sm">
                    <Calendar className="mr-2 h-4 w-4 text-muted-foreground" />
                    <span>{formatDate(employee.joinDate)}</span>
                  </div>
                  <div className="flex items-center text-sm">
                    <Phone className="mr-2 h-4 w-4 text-muted-foreground" />
                    <a href={`tel:${employee.phone}`} className="truncate hover:underline">{employee.phone}</a>
                  </div>
                  <div className="flex items-center text-sm">
                    <Mail className="mr-2 h-4 w-4 text-muted-foreground" />
                    <a href={`mailto:${employee.email}`} className="truncate hover:underline">{employee.email}</a>
                  </div>
                </div>
                <div className="border-t p-4">
                  <Link href={`/employees/${employee.id}`} passHref>
                    <Button variant="outline" className="w-full">
                      <Eye className="mr-2 h-4 w-4" />
                      상세 정보
                    </Button>
                  </Link>
                </div>
              </CardContent>
            </Card>
          ))
        )}
      </div>
    </>
  )
}

function formatDate(dateString: string): string {
  const date = new Date(dateString)
  return new Intl.DateTimeFormat("ko-KR", { year: "numeric", month: "long", day: "numeric" }).format(date)
}

// employees는 Supabase 등에서 불러온 직원 배열이어야 합니다.
<EmployeeCards employees={employees} />

export default async function EmployeesPage() {
  const supabase = createClient(process.env.NEXT_PUBLIC_SUPABASE_URL!, process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!)
  const { data: employees } = await supabase.from('employees').select('*')
  return <EmployeeCards employees={employees || []} />
}

export default function EmployeeDetailPage({ params, user }) {
  // ...상세 데이터 패칭 생략...

  return (
    <div>
      <NotificationListener userId={user.id} />
      <EmployeeFileUpload employeeId={params.id} />
      {user?.role === "admin" && <AttendanceEditor employeeId={params.id} />}
      {user?.role === "admin" && <ExcelUpload />}
      <AttendanceChart stats={attendanceStats} />
    </div>
  )
}

function formatDate(dateString: string): string {
  const date = new Date(dateString)
  return new Intl.DateTimeFormat("ko-KR", { year: "numeric", month: "long", day: "numeric" }).format(date)
}

export function EmployeeFileUpload({ employeeId }: { employeeId: string }) {
  const [uploading, setUploading] = useState(false)
  const [fileUrl, setFileUrl] = useState<string | null>(null)
  const [preview, setPreview] = useState<string | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  async function uploadFile(file: File) {
    setUploading(true)
    const filePath = `employee/${employeeId}/${Date.now()}_${file.name}`
    const { error } = await supabase.storage.from("employee-files").upload(filePath, file)
    if (error) {
      toast.error("업로드 실패")
    } else {
      const { data } = supabase.storage.from("employee-files").getPublicUrl(filePath)
      setFileUrl(data.publicUrl)
      toast.success("업로드 성공")
      if (file.type.startsWith("image/")) setPreview(URL.createObjectURL(file))
    }
    setUploading(false)
  }

  function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0]
    if (file) uploadFile(file)
  }

  return (
    <div>
      <input
        type="file"
        ref={fileInputRef}
        onChange={handleFileChange}
        className="hidden"
        accept="image/*,application/pdf"
      />
      <Button onClick={() => fileInputRef.current?.click()} disabled={uploading}>
        파일 업로드
      </Button>
      {preview && <img src={preview} alt="미리보기" className="h-32 mt-2" />}
      {fileUrl && (
        <a href={fileUrl} target="_blank" rel="noopener" className="block mt-2 underline text-blue-600">
          파일 다운로드
        </a>
      )}
    </div>
  )
}

function downloadExcel(data: any[], filename: string) {
  const ws = XLSX.utils.json_to_sheet(data)
  const wb = XLSX.utils.book_new()
  XLSX.utils.book_append_sheet(wb, ws, "Sheet1")
  XLSX.writeFile(wb, filename)
}

// 사용 예시: <Button onClick={() => downloadExcel(attendance, "근무기록.xlsx")}>엑셀 다운로드</Button>

export function AttendanceChart({ stats }) {
  // stats: [{ month: "2024-06", 출근: 20, 지각: 2, 결근: 1 }, ...]
  return (
    <BarChart width={500} height={250} data={stats}>
      <XAxis dataKey="month" />
      <YAxis />
      <Tooltip />
      <Bar dataKey="출근" fill="#60a5fa" />
      <Bar dataKey="지각" fill="#fbbf24" />
      <Bar dataKey="결근" fill="#f87171" />
    </BarChart>
  )
}

export function AttendanceEditor({ employeeId, onSaved }) {
  const [date, setDate] = useState("")
  const [checkIn, setCheckIn] = useState("")
  const [checkOut, setCheckOut] = useState("")
  const [status, setStatus] = useState("정상")

  async function handleSave() {
    const { error } = await supabase.from("attendance").insert({ employee_id: employeeId, date, check_in: checkIn, check_out: checkOut, status })
    if (error) {
      toast.error("저장 실패: " + error.message)
    } else {
      toast.success("저장 완료!")
    }
    onSaved?.()
  }

  return (
    <div className="flex gap-2">
      <input type="date" value={date} onChange={e => setDate(e.target.value)} className="border px-2 py-1 rounded" />
      <input type="time" value={checkIn} onChange={e => setCheckIn(e.target.value)} className="border px-2 py-1 rounded" />
      <input type="time" value={checkOut} onChange={e => setCheckOut(e.target.value)} className="border px-2 py-1 rounded" />
      <select value={status} onChange={e => setStatus(e.target.value)} className="border px-2 py-1 rounded">
        <option value="정상">정상</option>
        <option value="지각">지각</option>
        <option value="결근">결근</option>
      </select>
      <Button onClick={handleSave}>저장</Button>
    </div>
  )
}

// 삭제 예시
async function handleDeleteAttendance(id: string) {
  await supabase.from("attendance").delete().eq("id", id)
}

export function ExcelUpload({ onUploaded }: { onUploaded: () => void }) {
  async function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0]
    if (!file) return
    const data = await file.arrayBuffer()
    const workbook = XLSX.read(data)
    const sheet = workbook.Sheets[workbook.SheetNames[0]]
    const json = XLSX.utils.sheet_to_json(sheet)
    // 예시: 근무기록 대량 등록
    await supabase.from("attendance").insert(json)
    onUploaded?.()
  }

  return (
    <input type="file" accept=".xlsx,.xls" onChange={handleFileChange} />
  )
}

async function markNotificationAsRead(id: string) {
  await supabase.from("notifications").update({ read: true }).eq("id", id)
}

async function deleteAllNotifications(userId: string) {
  await supabase.from("notifications").delete().eq("user_id", userId)
}

function AttendanceStatsChart({ stats }) {
  // stats: [{ month: "2024-06", 출근: 20, 지각: 2, 결근: 1 }, ...]
  return (
    <BarChart width={500} height={250} data={stats}>
      <XAxis dataKey="month" />
      <YAxis />
      <Tooltip />
      <Bar dataKey="출근" fill="#60a5fa" />
      <Bar dataKey="지각" fill="#fbbf24" />
      <Bar dataKey="결근" fill="#f87171" />
    </BarChart>
  )
}

export function AdminSettings({ user }: { user: User }) {
  if (user?.role !== "admin") return <div>권한이 없습니다.</div>
  // 관리자만 볼 수 있는 설정 UI
}

export function NotificationListener({ userId }: { userId: string }) {
  useEffect(() => {
    const channel = supabase
      .channel("notifications")
      .on("postgres_changes", { event: "INSERT", schema: "public", table: "notifications" }, payload => {
        if (payload.new.user_id === userId || payload.new.user_id === "all") {
          toast.info(`새 알림: ${payload.new.message}`)
        }
      })
      .subscribe()
    return () => { supabase.removeChannel(channel) }
  }, [userId])

  return null // UI 필요시 알림 리스트 등 추가
}