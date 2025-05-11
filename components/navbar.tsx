"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { Button } from "@/components/ui/button"
import { ThemeToggle } from "@/components/theme-toggle"

// 메뉴 항목 배열 - 반드시 대괄호로 열고 닫고, 각 항목은 중괄호로 감쌉니다.
const menuItems = [
  { name: "대시보드", href: "/dashboard" },
  { name: "직원 관리", href: "/employees" },
  { name: "계약서", href: "/contracts" },
  { name: "급여", href: "/payroll" },
  { name: "출퇴근", href: "/attendance" },
  { name: "설정", href: "/settings" },
]

export default function Navbar() {
  const pathname = usePathname()

  return (
    <nav className="bg-white dark:bg-gray-900 border-b shadow-sm theme-element-transition" aria-label="메인 메뉴">
      <div className="mx-auto max-w-screen-xl px-4 py-3 flex items-center justify-between">
        {/* 좌측: 로고/타이틀 */}
        <h1 className="text-xl font-bold dark:text-white">매장 ERP</h1>
        {/* 중앙: 메뉴 버튼들 */}
        <ul className="flex gap-2">
          {menuItems.map((item) => {
            const isActive = pathname === item.href
            return (
              <li key={item.href}>
                <Link href={item.href}>
                  <Button
                    variant={isActive ? "default" : "ghost"}
                    className={
                      isActive
                        ? "text-blue-600 dark:text-blue-400 font-bold"
                        : "text-gray-700 dark:text-gray-300"
                    }
                    size="sm"
                  >
                    {item.name}
                  </Button>
                </Link>
              </li>
            )
          })}
        </ul>
        {/* 우측: 테마 토글 버튼 */}
        <div className="ml-4">
          <ThemeToggle />
        </div>
      </div>
    </nav>
  )
} 