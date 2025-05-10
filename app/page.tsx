"use client"

import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { ThemeToggle } from "@/components/theme-toggle"
import { Users, ShoppingCart, DollarSign, Bell } from "lucide-react"
import { motion } from "framer-motion"
import Link from "next/link"

export default function HomePage() {
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

      {/* 메인 대시보드 */}
      <main className="max-w-5xl mx-auto py-10 px-4 space-y-8">
        {/* 통계 카드 */}
        <section className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-6">
          <motion.div whileHover={{ scale: 1.03 }}>
            <Card>
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle>오늘 매출</CardTitle>
                <DollarSign className="text-green-500" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">₩1,250,000</div>
                <CardDescription>전일 대비 +12%</CardDescription>
              </CardContent>
            </Card>
          </motion.div>
          <motion.div whileHover={{ scale: 1.03 }}>
            <Card>
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle>주문 수</CardTitle>
                <ShoppingCart className="text-blue-500" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">87건</div>
                <CardDescription>신규 주문 5건</CardDescription>
              </CardContent>
            </Card>
          </motion.div>
          <motion.div whileHover={{ scale: 1.03 }}>
            <Card>
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle>직원 수</CardTitle>
                <Users className="text-violet-500" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">15명</div>
                <CardDescription>출근 12명</CardDescription>
              </CardContent>
            </Card>
          </motion.div>
          <motion.div whileHover={{ scale: 1.03 }}>
            <Card>
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle>알림</CardTitle>
                <Bell className="text-orange-500" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">3건</div>
                <CardDescription>미확인 알림</CardDescription>
              </CardContent>
            </Card>
          </motion.div>
        </section>

        {/* 빠른 액션/CTA */}
        <section className="flex flex-col md:flex-row gap-4">
          <Button className="flex-1 text-lg py-6" variant="default">+ 새 주문 등록</Button>
          <Button className="flex-1 text-lg py-6" variant="secondary">+ 직원 추가</Button>
        </section>

        {/* 공지/타임라인 예시 */}
        <section className="bg-muted rounded-lg p-6 mt-8">
          <h2 className="text-lg font-semibold mb-2">오늘의 공지</h2>
          <ul className="list-disc pl-5 space-y-1 text-muted-foreground">
            <li>오후 3시~5시 정기 점검 예정</li>
            <li>신규 메뉴 출시 이벤트 진행 중</li>
            <li>직원 출퇴근 기록은 <b>ERP &gt; 직원</b> 메뉴에서 확인하세요</li>
          </ul>
        </section>
      </main>
    </div>
  )
}
