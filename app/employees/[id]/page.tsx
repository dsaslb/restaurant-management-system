"use client"

import type React from "react"
import Link from "next/link"
import { motion } from "framer-motion"
import {
  ArrowLeft,
  Calendar,
  ChevronRight,
  Clock,
  FileText,
  Gift,
  Mail,
  MapPin,
  Phone,
  User,
  Users,
} from "lucide-react"

import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Progress } from "@/components/ui/progress"
import { Separator } from "@/components/ui/separator"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"

export default function EmployeeDetailPage({ params }: { params: { id: string } }) {
  // 실제 구현에서는 params.id를 사용하여 API에서 직원 정보를 가져옵니다
  // 여기서는 예시 데이터를 사용합니다
  const employee = {
    id: params.id,
    name: "김지수",
    position: "매니저",
    email: "jisoo.kim@example.com",
    phone: "010-1234-5678",
    hireDate: "2022-03-15",
    status: "active",
    employmentType: "정규직",
    address: "서울시 강남구 테헤란로 123",
    birthDate: "1990-05-15",
    emergencyContact: "김철수(배우자) 010-9876-5432",
    bankAccount: "신한은행 110-123-456789",
    salary: "월 3,500,000원",
    notes: "성실하고 책임감이 강함. 직원 교육에 탁월한 능력을 보임.",
    avatar: "/placeholder.svg?height=100&width=100",
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white shadow-sm border-b">
        <div className="container mx-auto px-4 py-4 flex items-center">
          <Link
            href="/employees"
            className="flex items-center gap-2 text-gray-600 hover:text-blue-600 transition-colors"
          >
            <ArrowLeft className="h-5 w-5" />
            <span>직원 목록으로 돌아가기</span>
          </Link>
        </div>
      </header>

      <main className="container mx-auto px-4 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* 직원 프로필 카드 */}
          <Card>
            <CardContent className="pt-6">
              <div className="flex flex-col items-center text-center">
                <motion.div
                  initial={{ scale: 0.8, opacity: 0 }}
                  animate={{ scale: 1, opacity: 1 }}
                  transition={{ duration: 0.5 }}
                >
                  <Avatar className="h-32 w-32 mb-4">
                    <AvatarImage src={employee.avatar || "/placeholder.svg"} />
                    <AvatarFallback className="text-3xl">{employee.name.charAt(0)}</AvatarFallback>
                  </Avatar>
                </motion.div>
                <h2 className="text-2xl font-bold">{employee.name}</h2>
                <p className="text-gray-500 mb-2">{employee.position}</p>
                <EmployeeStatusBadge status="active" className="mb-4" />

                <div className="w-full space-y-4 mt-6">
                  <ContactItem icon={Phone} label="연락처" value={employee.phone} />
                  <ContactItem icon={Mail} label="이메일" value={employee.email} />
                  <ContactItem icon={MapPin} label="주소" value={employee.address} />
                  <ContactItem icon={Calendar} label="생년월일" value={employee.birthDate} />
                </div>
              </div>
            </CardContent>
            <CardFooter>
              <Button className="w-full">직원 정보 수정</Button>
            </CardFooter>
          </Card>

          {/* 직원 상세 정보 */}
          <div className="lg:col-span-2">
            <Tabs defaultValue="overview">
              <TabsList className="mb-4">
                <TabsTrigger value="overview">개요</TabsTrigger>
                <TabsTrigger value="employment">고용 정보</TabsTrigger>
                <TabsTrigger value="attendance">출퇴근 기록</TabsTrigger>
                <TabsTrigger value="welfare">복지 혜택</TabsTrigger>
              </TabsList>

              <TabsContent value="overview">
                <Card className="mb-6">
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <User className="h-5 w-5 text-blue-500" />
                      직원 정보 요약
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      <InfoCard
                        title="근무 정보"
                        icon={<Clock className="h-5 w-5 text-blue-500" />}
                        items={[
                          { label: "입사일", value: employee.hireDate },
                          { label: "근속 기간", value: "2년 2개월" },
                          { label: "고용 형태", value: employee.employmentType },
                          { label: "근무 시간", value: "09:00 - 18:00 (주 5일)" },
                        ]}
                      />
                      <InfoCard
                        title="급여 정보"
                        icon={<Gift className="h-5 w-5 text-green-500" />}
                        items={[
                          { label: "급여", value: employee.salary },
                          { label: "계좌 정보", value: employee.bankAccount },
                          { label: "다음 급여일", value: "2025-05-25" },
                          { label: "세금 정보", value: "소득세 3.3%" },
                        ]}
                      />
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <FileText className="h-5 w-5 text-blue-500" />
                      메모 및 특이사항
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p className="text-gray-700">{employee.notes}</p>
                    <Separator className="my-4" />
                    <div>
                      <h4 className="font-medium mb-2">비상 연락처</h4>
                      <p className="text-gray-700">{employee.emergencyContact}</p>
                    </div>
                  </CardContent>
                </Card>
              </TabsContent>

              <TabsContent value="employment">
                <Card className="mb-6">
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <FileText className="h-5 w-5 text-blue-500" />
                      계약 정보
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-6">
                      <div>
                        <h3 className="text-lg font-medium mb-2">현재 계약</h3>
                        <div className="rounded-lg border p-4">
                          <div className="flex justify-between mb-2">
                            <div>
                              <span className="font-medium">정규직 계약</span>
                              <p className="text-sm text-gray-500">무기한</p>
                            </div>
                            <Badge variant="outline" className="bg-green-100 text-green-800">
                              활성
                            </Badge>
                          </div>
                          <div className="space-y-2 mt-4">
                            <div className="flex justify-between text-sm">
                              <span className="text-gray-500">시작일</span>
                              <span>2022-03-15</span>
                            </div>
                            <div className="flex justify-between text-sm">
                              <span className="text-gray-500">종료일</span>
                              <span>무기한</span>
                            </div>
                            <div className="flex justify-between text-sm">
                              <span className="text-gray-500">서명일</span>
                              <span>2022-03-10</span>
                            </div>
                          </div>
                          <div className="mt-4">
                            <Button variant="outline" size="sm" className="w-full">
                              계약서 보기
                            </Button>
                          </div>
                        </div>
                      </div>

                      <div>
                        <h3 className="text-lg font-medium mb-2">계약 이력</h3>
                        <div className="space-y-4">
                          <div className="flex items-center gap-4 p-3 rounded-lg border">
                            <div className="w-2 h-full min-h-[40px] rounded-full bg-gray-200" />
                            <div className="flex-1">
                              <div className="flex justify-between">
                                <h4 className="font-medium">수습 계약</h4>
                                <span className="text-sm text-gray-500">2022-03-15 ~ 2022-06-14</span>
                              </div>
                              <p className="text-sm text-gray-600">3개월 수습 기간</p>
                            </div>
                            <Button variant="ghost" size="sm">
                              <ChevronRight className="h-4 w-4" />
                            </Button>
                          </div>
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <Users className="h-5 w-5 text-blue-500" />
                      직무 및 평가
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-6">
                      <div>
                        <h3 className="text-lg font-medium mb-2">직무 설명</h3>
                        <p className="text-gray-700">
                          매장 운영 총괄 관리, 직원 교육 및 관리, 고객 응대, 매출 관리, 재고 관리 등의 업무를
                          담당합니다.
                        </p>
                      </div>

                      <div>
                        <h3 className="text-lg font-medium mb-2">최근 평가</h3>
                        <div className="space-y-4">
                          <div>
                            <div className="flex justify-between mb-1">
                              <span className="text-sm font-medium">업무 성과</span>
                              <span className="text-sm text-gray-500">90%</span>
                            </div>
                            <Progress value={90} className="h-2" />
                          </div>
                          <div>
                            <div className="flex justify-between mb-1">
                              <span className="text-sm font-medium">팀워크</span>
                              <span className="text-sm text-gray-500">85%</span>
                            </div>
                            <Progress value={85} className="h-2" />
                          </div>
                          <div>
                            <div className="flex justify-between mb-1">
                              <span className="text-sm font-medium">고객 응대</span>
                              <span className="text-sm text-gray-500">95%</span>
                            </div>
                            <Progress value={95} className="h-2" />
                          </div>
                          <div>
                            <div className="flex justify-between mb-1">
                              <span className="text-sm font-medium">리더십</span>
                              <span className="text-sm text-gray-500">80%</span>
                            </div>
                            <Progress value={80} className="h-2" />
                          </div>
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </TabsContent>

              <TabsContent value="attendance">
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <Clock className="h-5 w-5 text-blue-500" />
                      출퇴근 기록
                    </CardTitle>
                    <CardDescription>최근 30일간의 출퇴근 기록입니다.</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      {attendanceRecords.map((record, index) => (
                        <motion.div
                          key={index}
                          initial={{ opacity: 0, y: 10 }}
                          animate={{ opacity: 1, y: 0 }}
                          transition={{ delay: index * 0.05 }}
                          className="flex items-start gap-3 p-3 rounded-lg border hover:bg-gray-50"
                        >
                          <div className={`w-2 h-full min-h-[40px] rounded-full ${record.statusColor}`} />
                          <div className="flex-1">
                            <div className="flex justify-between">
                              <h4 className="font-medium">{record.date}</h4>
                              <AttendanceBadge status={record.status} />
                            </div>
                            <div className="flex justify-between mt-1">
                              <p className="text-sm text-gray-600">
                                출근: {record.checkIn} / 퇴근: {record.checkOut}
                              </p>
                              <p className="text-sm font-medium">{record.workHours}</p>
                            </div>
                            {record.note && <p className="text-sm text-gray-500 mt-1 italic">{record.note}</p>}
                          </div>
                        </motion.div>
                      ))}
                    </div>
                  </CardContent>
                  <CardFooter>
                    <Button variant="outline" className="w-full">
                      모든 출퇴근 기록 보기
                    </Button>
                  </CardFooter>
                </Card>
              </TabsContent>

              <TabsContent value="welfare">
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <Gift className="h-5 w-5 text-blue-500" />
                      복지 혜택
                    </CardTitle>
                    <CardDescription>직원에게 제공되는 복지 혜택 정보입니다.</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-6">
                      <div>
                        <h3 className="text-lg font-medium mb-3">예정된 복지 혜택</h3>
                        <div className="space-y-4">
                          {upcomingBenefits.map((benefit, index) => (
                            <motion.div
                              key={index}
                              initial={{ opacity: 0, x: 20 }}
                              animate={{ opacity: 1, x: 0 }}
                              transition={{ delay: index * 0.1 }}
                              className="p-3 rounded-lg border hover:bg-gray-50"
                            >
                              <div className="flex items-center gap-3 mb-2">
                                <div className={`p-2 rounded-full ${benefit.bgColor}`}>
                                  <span className="text-xl">{benefit.emoji}</span>
                                </div>
                                <div>
                                  <p className="font-medium">{benefit.title}</p>
                                  <p className="text-sm text-gray-500">{benefit.date}</p>
                                </div>
                              </div>
                              <p className="text-sm text-gray-700">{benefit.description}</p>
                            </motion.div>
                          ))}
                        </div>
                      </div>

                      <div>
                        <h3 className="text-lg font-medium mb-3">복지 혜택 이력</h3>
                        <div className="space-y-4">
                          {benefitHistory.map((benefit, index) => (
                            <motion.div
                              key={index}
                              initial={{ opacity: 0, x: 20 }}
                              animate={{ opacity: 1, x: 0 }}
                              transition={{ delay: index * 0.1 }}
                              className="p-3 rounded-lg border hover:bg-gray-50"
                            >
                              <div className="flex items-center gap-3 mb-2">
                                <div className={`p-2 rounded-full ${benefit.bgColor}`}>
                                  <span className="text-xl">{benefit.emoji}</span>
                                </div>
                                <div>
                                  <p className="font-medium">{benefit.title}</p>
                                  <p className="text-sm text-gray-500">{benefit.date}</p>
                                </div>
                              </div>
                              <p className="text-sm text-gray-700">{benefit.description}</p>
                            </motion.div>
                          ))}
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </TabsContent>
            </Tabs>
          </div>
        </div>
      </main>
    </div>
  )
}

// 직원 상태 배지 컴포넌트
function EmployeeStatusBadge({ status, className = "" }: { status: string; className?: string }) {
  const statusConfig = {
    active: { label: "재직 중", className: "bg-green-100 text-green-800 hover:bg-green-200" },
    vacation: { label: "휴가 중", className: "bg-blue-100 text-blue-800 hover:bg-blue-200" },
    leave: { label: "휴직 중", className: "bg-orange-100 text-orange-800 hover:bg-orange-200" },
    resigned: { label: "퇴사", className: "bg-gray-100 text-gray-800 hover:bg-gray-200" },
  }

  const config = statusConfig[status as keyof typeof statusConfig] || statusConfig.active

  return (
    <Badge variant="outline" className={`${config.className} ${className}`}>
      {config.label}
    </Badge>
  )
}

// 출퇴근 상태 배지 컴포넌트
function AttendanceBadge({ status }: { status: string }) {
  const statusConfig = {
    onTime: { label: "정상 출근", className: "bg-green-100 text-green-800" },
    late: { label: "지각", className: "bg-orange-100 text-orange-800" },
    earlyLeave: { label: "조퇴", className: "bg-yellow-100 text-yellow-800" },
    absent: { label: "결근", className: "bg-red-100 text-red-800" },
    vacation: { label: "휴가", className: "bg-blue-100 text-blue-800" },
  }

  const config = statusConfig[status as keyof typeof statusConfig]

  return (
    <Badge variant="outline" className={config.className}>
      {config.label}
    </Badge>
  )
}

// 연락처 아이템 컴포넌트
function ContactItem({ icon: Icon, label, value }: { icon: any; label: string; value: string }) {
  return (
    <div className="flex items-center gap-3">
      <div className="bg-blue-50 p-2 rounded-full">
        <Icon className="h-4 w-4 text-blue-500" />
      </div>
      <div className="flex-1 text-left">
        <p className="text-xs text-gray-500">{label}</p>
        <p className="text-sm font-medium">{value}</p>
      </div>
    </div>
  )
}

// 정보 카드 컴포넌트
function InfoCard({
  title,
  icon,
  items,
}: {
  title: string
  icon: React.ReactNode
  items: { label: string; value: string }[]
}) {
  return (
    <div className="rounded-lg border p-4">
      <div className="flex items-center gap-2 mb-4">
        {icon}
        <h3 className="font-medium">{title}</h3>
      </div>
      <div className="space-y-3">
        {items.map((item, index) => (
          <div key={index} className="flex justify-between text-sm">
            <span className="text-gray-500">{item.label}</span>
            <span className="font-medium">{item.value}</span>
          </div>
        ))}
      </div>
    </div>
  )
}

// 출퇴근 기록 예시 데이터
const attendanceRecords = [
  {
    date: "2025-05-08 (목)",
    checkIn: "08:55",
    checkOut: "18:05",
    workHours: "9시간 10분",
    status: "onTime",
    statusColor: "bg-green-500",
  },
  {
    date: "2025-05-07 (수)",
    checkIn: "09:10",
    checkOut: "18:15",
    workHours: "9시간 5분",
    status: "late",
    statusColor: "bg-orange-500",
    note: "교통 체증으로 인한 지각",
  },
  {
    date: "2025-05-06 (화)",
    checkIn: "08:50",
    checkOut: "18:00",
    workHours: "9시간 10분",
    status: "onTime",
    statusColor: "bg-green-500",
  },
  {
    date: "2025-05-05 (월)",
    checkIn: "-",
    checkOut: "-",
    workHours: "-",
    status: "vacation",
    statusColor: "bg-blue-500",
    note: "연차 휴가",
  },
  {
    date: "2025-05-04 (일)",
    checkIn: "-",
    checkOut: "-",
    workHours: "-",
    status: "absent",
    statusColor: "bg-gray-500",
    note: "휴무일",
  },
]

// 예정된 복지 혜택 예시 데이터
const upcomingBenefits = [
  {
    title: "생일 축하 선물",
    date: "2025-05-15",
    description: "생일 축하 케이크와 상품권 10만원이 지급됩니다.",
    emoji: "🎂",
    bgColor: "bg-purple-100",
  },
  {
    title: "분기 성과급",
    date: "2025-06-15",
    description: "2분기 성과에 따른 인센티브가 지급됩니다.",
    emoji: "💰",
    bgColor: "bg-green-100",
  },
]

// 복지 혜택 이력 예시 데이터
const benefitHistory = [
  {
    title: "명절 선물",
    date: "2025-02-10",
    description: "설날 명절 선물 세트와 상품권 5만원이 지급되었습니다.",
    emoji: "🎁",
    bgColor: "bg-red-100",
  },
  {
    title: "근속 1주년 기념",
    date: "2023-03-15",
    description: "근속 1주년 기념 상품권 20만원이 지급되었습니다.",
    emoji: "🏆",
    bgColor: "bg-blue-100",
  },
  {
    title: "건강검진",
    date: "2024-11-20",
    description: "연간 건강검진 지원이 제공되었습니다.",
    emoji: "🏥",
    bgColor: "bg-green-100",
  },
] 