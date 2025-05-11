import { NextResponse } from 'next/server';
import supabase from '@/lib/supabase';

export async function GET(request) {
  const { searchParams } = new URL(request.url);
  const keyword = searchParams.get('q');
  let query = supabase.from('users').select('*');
  if (keyword) {
    query = query.ilike('name', `%${keyword}%`);
  }
  const { data, error } = await query;
  if (error) {
    console.error('직원 데이터 불러오기 오류:', error.message);
    return NextResponse.json({ error: 'DB 오류' }, { status: 500 });
  }
  return NextResponse.json(data);
}

export async function POST(request) {
  const body = await request.json();
  const { data, error } = await supabase.from('users').insert([body]);
  if (error) return NextResponse.json({ error: error.message }, { status: 500 });
  return NextResponse.json(data, { status: 201 });
}

export async function PUT(request) {
  const body = await request.json();
  const { id, ...updateData } = body;
  const { data, error } = await supabase.from('users').update(updateData).eq('id', id);
  if (error) return NextResponse.json({ error: error.message }, { status: 500 });
  return NextResponse.json(data);
}

export async function DELETE(request) {
  const { id } = await request.json();
  const { data, error } = await supabase.from('users').delete().eq('id', id);
  if (error) return NextResponse.json({ error: error.message }, { status: 500 });
  return NextResponse.json(data);
} 