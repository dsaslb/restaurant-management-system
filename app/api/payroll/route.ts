import { NextResponse } from 'next/server';
import supabase from '@/lib/supabase';

// 급여 데이터 조회 (고급 필터, 관리자 인증 예시)
export async function GET(request: Request) {
  const authHeader = request.headers.get('authorization');
  if (!authHeader) {
    return NextResponse.json({ error: '인증 필요' }, { status: 401 });
  }
  const token = authHeader.replace('Bearer ', '');
  // 토큰 검증
  const { data: { user }, error } = await supabase.auth.getUser(token);
  if (error || !user) {
    return NextResponse.json({ error: '유효하지 않은 토큰' }, { status: 401 });
  }
  // 관리자 권한 체크 (예: user.role === 'admin')
  if (user.role !== 'admin') {
    return NextResponse.json({ error: '관리자 권한 필요' }, { status: 403 });
  }
  const { searchParams } = new URL(request.url);
  const name = searchParams.get('name');
  const min = searchParams.get('min');
  const max = searchParams.get('max');
  const from = searchParams.get('from');
  const to = searchParams.get('to');
  let query = supabase.from('payroll_with_user').select('*');
  if (name) query = query.ilike('user_name', `%${name}%`);
  if (min) query = query.gte('amount', min);
  if (max) query = query.lte('amount', max);
  if (from) query = query.gte('pay_date', from);
  if (to) query = query.lte('pay_date', to);
  const { data, error: queryError } = await query;
  if (queryError) return NextResponse.json({ error: queryError.message }, { status: 500 });
  return NextResponse.json(data);
}

// 급여 데이터 추가
export async function POST(request: Request) {
  const authHeader = request.headers.get('authorization');
  if (!authHeader) return NextResponse.json({ error: '인증 필요' }, { status: 401 });
  const token = authHeader.replace('Bearer ', '');
  const { data: { user }, error } = await supabase.auth.getUser(token);
  if (error || !user || user.user_metadata.role !== 'admin') {
    return NextResponse.json({ error: '관리자 권한 필요' }, { status: 403 });
  }
  const body = await request.json();
  const { data, error: insertError } = await supabase.from('payroll').insert([body]);
  if (insertError) return NextResponse.json({ error: insertError.message }, { status: 500 });
  return NextResponse.json(data, { status: 201 });
}

// 급여 데이터 수정
export async function PUT(request: Request) {
  const body = await request.json();
  const { id, ...updateData } = body;
  const { data, error } = await supabase.from('payroll').update(updateData).eq('id', id);
  if (error) return NextResponse.json({ error: error.message }, { status: 500 });
  return NextResponse.json(data);
}

// 급여 데이터 삭제
export async function DELETE(request: Request) {
  const { id } = await request.json();
  const { data, error } = await supabase.from('payroll').delete().eq('id', id);
  if (error) return NextResponse.json({ error: error.message }, { status: 500 });
  return NextResponse.json(data);
}