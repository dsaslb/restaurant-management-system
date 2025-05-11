import { NextResponse } from "next/server"
import { promises as fs } from "fs"
import path from "path"
import { PDFDocument } from "pdf-lib"
import supabase from '@/lib/supabase'

const CONTRACTS_DIR = path.join(process.cwd(), "contracts")

// PDF 생성 함수
async function createContractPDF(data: {
  username: string
  position: string
  wage: number
  startDate: string
  endDate: string
  signature: string
}) {
  try {
    const pdfDoc = await PDFDocument.create()
    const page = pdfDoc.addPage()
    const { width, height } = page.getSize()

    // 기본 폰트 사용 (외부 폰트 의존성 제거)
    page.drawText("근로계약서", {
      x: width / 2 - 50,
      y: height - 50,
      size: 20,
    })

    page.drawText(`이름: ${data.username}`, {
      x: 50,
      y: height - 100,
      size: 12,
    })

    page.drawText(`직책: ${data.position}`, {
      x: 50,
      y: height - 120,
      size: 12,
    })

    page.drawText(`급여: ${data.wage.toLocaleString()}원`, {
      x: 50,
      y: height - 140,
      size: 12,
    })

    page.drawText(`계약기간: ${data.startDate} ~ ${data.endDate}`, {
      x: 50,
      y: height - 160,
      size: 12,
    })

    page.drawText(`서명: ${data.signature}`, {
      x: 50,
      y: height - 200,
      size: 12,
    })

    return await pdfDoc.save()
  } catch (error) {
    console.error("PDF 생성 중 오류 발생:", error)
    throw new Error("PDF 생성에 실패했습니다")
  }
}

export async function GET(request) {
  const { searchParams } = new URL(request.url);
  const keyword = searchParams.get('q');
  let query = supabase.from('contracts').select('*');
  if (keyword) {
    query = query.ilike('username', `%${keyword}%`);
  }
  const { data, error } = await query;
  if (error) {
    console.error('계약 데이터 불러오기 오류:', error.message);
    return NextResponse.json({ error: 'DB 오류' }, { status: 500 });
  }
  return NextResponse.json(data);
}

export async function POST(request) {
  const body = await request.json();
  const { data, error } = await supabase.from('contracts').insert([body]);
  if (error) return NextResponse.json({ error: error.message }, { status: 500 });
  return NextResponse.json(data, { status: 201 });
}

export async function PUT(request) {
  const body = await request.json();
  const { id, ...updateData } = body;
  const { data, error } = await supabase.from('contracts').update(updateData).eq('id', id);
  if (error) return NextResponse.json({ error: error.message }, { status: 500 });
  return NextResponse.json(data);
}

export async function DELETE(request) {
  const { id } = await request.json();
  const { data, error } = await supabase.from('contracts').delete().eq('id', id);
  if (error) return NextResponse.json({ error: error.message }, { status: 500 });
  return NextResponse.json(data);
} 