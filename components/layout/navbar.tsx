"use client";
import Link from "next/link"
import { usePathname } from "next/navigation"
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import {
  Users,
  Clock,
  Utensils,
  ShoppingCart,
  Settings,
} from "lucide-react"

const navItems = [
  { href: "/employees", label: "직원 관리", icon: Users },
  { href: "/attendance", label: "출퇴근 관리", icon: Clock },
  { href: "/menu", label: "메뉴 관리", icon: Utensils },
  { href: "/orders", label: "주문 관리", icon: ShoppingCart },
  { href: "/settings", label: "설정", icon: Settings },
]

export function Navbar() {
  const pathname = usePathname()

  return (
    <nav className="border-b">
      <div className="container mx-auto px-4">
        <div className="flex h-16 items-center justify-between">
          <div className="flex items-center">
            <Link href="/" className="text-xl font-bold">
              레스토랑 관리
            </Link>
          </div>
          <div className="flex items-center space-x-4">
            {navItems.map((item) => {
              const Icon = item.icon
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={cn(
                    "flex items-center space-x-2 px-3 py-2 text-sm font-medium rounded-md transition-colors",
                    pathname === item.href
                      ? "bg-primary text-primary-foreground"
                      : "hover:bg-muted"
                  )}
                >
                  <Icon className="h-4 w-4" />
                  <span>{item.label}</span>
                </Link>
              )
            })}
          </div>
        </div>
      </div>
    </nav>
  )
} 


