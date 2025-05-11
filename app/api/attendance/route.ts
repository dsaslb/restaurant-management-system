import { NextResponse } from "next/server"
import { attendanceSchema } from "@/models/attendance"
import supabase from '@/lib/supabase'

// GET /api/attendance
export async function GET() {
  const { data, error } = await supabase.from('attendance').select('*')
  if (error) {
    console.error('출퇴근 기록 불러오기 오류:', error.message)
    return NextResponse.json({ error: 'DB 오류' }, { status: 500 })
  }
  return NextResponse.json(data)
}

// POST /api/attendance
export async function POST(request: Request) {
  const body = await request.json()
  const { data, error } = await supabase.from('attendance').insert([body])
  if (error) return NextResponse.json({ error: error.message }, { status: 500 })
  return NextResponse.json(data, { status: 201 })
} 