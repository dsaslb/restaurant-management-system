import { NextResponse } from 'next/server';
import supabase from '@/lib/supabase';

// 알림 목록 조회
export async function GET() {
  const { data, error } = await supabase.from('notifications').select('*').order('created_at', { ascending: false });
  if (error) return NextResponse.json({ error: error.message }, { status: 500 });
  return NextResponse.json(data);
}

// 알림 생성
export async function POST(request: Request) {
  const body = await request.json();
  const { data, error } = await supabase.from('notifications').insert([body]);
  if (error) return NextResponse.json({ error: error.message }, { status: 500 });
  return NextResponse.json(data, { status: 201 });
}

// 알림 읽음 처리 (단일/전체)
export async function PUT(request: Request) {
  const { id, all } = await request.json();
  let query = supabase.from('notifications').update({ is_read: true });
  if (!all) query = query.eq('id', id);
  const { data, error } = await query;
  if (error) return NextResponse.json({ error: error.message }, { status: 500 });
  return NextResponse.json(data);
}

// 알림 삭제 (단일/전체)
export async function DELETE(request: Request) {
  const { id, all } = await request.json();
  let query = supabase.from('notifications').delete();
  if (!all) query = query.eq('id', id);
  const { data, error } = await query;
  if (error) return NextResponse.json({ error: error.message }, { status: 500 });
  return NextResponse.json(data);
} 