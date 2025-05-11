import { NextResponse } from 'next/server';
import supabase from '@/lib/supabase';

export async function GET() {
  const { data, error } = await supabase.from('restaurant_system').select('*');
  if (error) {
    console.error('레스토랑 시스템 데이터 불러오기 오류:', error.message);
    return NextResponse.json({ error: 'DB 오류' }, { status: 500 });
  }
  return NextResponse.json(data);
}

export async function POST(request: Request) {
  const body = await request.json();
  const { data, error } = await supabase.from('restaurant_system').insert([body]);
  if (error) return NextResponse.json({ error: error.message }, { status: 500 });
  return NextResponse.json(data, { status: 201 });
} 