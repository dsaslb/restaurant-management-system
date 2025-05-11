"use client";
import type React from "react";
import { useEffect, useState } from "react";
import Image from "next/image";
import Link from "next/link";
import { motion } from "framer-motion";
import {
  BarChart3,
  Bell,
  Calendar,
  ChefHat,
  Clock,
  FileText,
  Gift,
  Home,
  Lightbulb,
  Menu,
  MessageSquare,
  Settings,
  Sparkles,
  TrendingUp,
  User,
  Users,
  X,
  ShoppingCart,
  DollarSign,
  Box,
} from "lucide-react";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ThemeToggle } from "@/components/theme-toggle";

export default function Dashboard() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [currentTime, setCurrentTime] = useState(new Date());
  const [mounted, setMounted] = useState(false);

  // 컴포넌트가 마운트되었는지 확인
  useEffect(() => {
    setMounted(true);
  }, []);

  // 현재 시간 업데이트
  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentTime(new Date());
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  // 현재 시간 포맷
  const formattedTime = currentTime.toLocaleTimeString("ko-KR", {
    hour: "2-digit",
    minute: "2-digit",
  });

  // 현재 날짜 포맷
  const formattedDate = currentTime.toLocaleDateString("ko-KR", {
    year: "numeric",
    month: "long",
    day: "numeric",
    weekday: "long",
  });

  // 인사말 생성
  const getGreeting = () => {
    const hour = currentTime.getHours();
    if (hour < 12) return "좋은 아침이에요";
    if (hour < 18) return "좋은 오후에요";
    return "좋은 저녁이에요";
  };

  return (
    <div className="max-w-5xl mx-auto py-10 px-4 space-y-8">
      <h1 className="text-3xl font-bold mb-6">대시보드</h1>
      <section className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-6">
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
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle>재고</CardTitle>
            <Box className="text-orange-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">32종</div>
            <CardDescription>부족 2종</CardDescription>
          </CardContent>
        </Card>
      </section>
      <section className="flex flex-col md:flex-row gap-4 mt-8">
        <Button className="flex-1 text-lg py-6" variant="default">+ 새 주문 등록</Button>
        <Button className="flex-1 text-lg py-6" variant="secondary">+ 직원 추가</Button>
      </section>
      <section className="bg-muted rounded-lg p-6 mt-8">
        <h2 className="text-lg font-semibold mb-2">오늘의 공지</h2>
        <ul className="list-disc pl-5 space-y-1 text-muted-foreground">
          <li>오후 3시~5시 정기 점검 예정</li>
          <li>신규 메뉴 출시 이벤트 진행 중</li>
          <li>직원 출퇴근 기록은 <b>ERP > 직원</b> 메뉴에서 확인하세요</li>
        </ul>
      </section>
    </div>
  );
}

// ... (아래에 전체 대시보드 코드 붙여넣기)

// (생략) 위에서 주신 Dashboard 컴포넌트 전체 코드와 하단의 데이터, SidebarItem, StatsCard 함수 등 모두 포함 