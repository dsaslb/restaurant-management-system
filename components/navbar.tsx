"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import { OrderNotification } from "@/components/orders/notification"

const routes = [
  {
    href: "/employees",
    label: "직원 관리",
  },
  {
    href: "/attendance",
    label: "근태 관리",
  },
  {
    href: "/menu",
    label: "메뉴 관리",
  },
  {
    href: "/orders",
    label: "주문 관리",
  },
  {
    href: "/contracts",
    label: "계약 관리",
  },
]

export function Navbar() {
  const pathname = usePathname()

  return (
    <div className="border-b">
      <div className="flex h-16 items-center px-4">
        <nav className="flex items-center space-x-4 lg:space-x-6 mx-6">
          {routes.map((route) => (
            <Link
              key={route.href}
              href={route.href}
              className={cn(
                "text-sm font-medium transition-colors hover:text-primary",
                pathname === route.href
                  ? "text-black dark:text-white"
                  : "text-muted-foreground"
              )}
            >
              {route.label}
            </Link>
          ))}
        </nav>
        <div className="ml-auto flex items-center space-x-4">
          <OrderNotification />
        </div>
      </div>
    </div>
  )
} 