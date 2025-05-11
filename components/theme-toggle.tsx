"use client"

import { useEffect, useState } from "react"
import { motion } from "framer-motion"
import { Moon, Sun } from "lucide-react"
import { useTheme } from "next-themes"

import { Button } from "@/components/ui/button"
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "@/components/ui/dropdown-menu"

export function ThemeToggle() {
  const { setTheme, theme, resolvedTheme } = useTheme()
  const [mounted, setMounted] = useState(false)
  const [isAnimating, setIsAnimating] = useState(false)

  // 컴포넌트가 마운트되었는지 확인
  useEffect(() => {
    setMounted(true)
  }, [])

  // 테마 변경 핸들러
  const handleThemeChange = (newTheme: string) => {
    setIsAnimating(true)
    setTimeout(() => {
      setTheme(newTheme)
      setTimeout(() => {
        setIsAnimating(false)
      }, 1000)
    }, 100)
  }

  // 아이콘 애니메이션 변형
  const iconVariants = {
    initial: { scale: 0.6, rotate: 0 },
    animate: { scale: 1, rotate: 360, transition: { duration: 0.5, ease: "easeInOut" } },
    exit: { scale: 0.6, rotate: 0, transition: { duration: 0.3 } },
  }

  if (!mounted) {
    return (
      <Button variant="outline" size="icon" className="relative h-8 w-8 rounded-full">
        <span className="sr-only">테마 변경</span>
      </Button>
    )
  }

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button
          variant="outline"
          size="icon"
          className={`relative h-8 w-8 rounded-full overflow-hidden ${isAnimating ? "theme-toggle-icon-animate" : ""}`}
        >
          {resolvedTheme === "dark" ? (
            <motion.div
              className="absolute inset-0 flex items-center justify-center moon-icon"
              initial="initial"
              animate="animate"
              exit="exit"
              variants={iconVariants}
              key="moon"
            >
              <Moon className="h-4 w-4" />
            </motion.div>
          ) : (
            <motion.div
              className="absolute inset-0 flex items-center justify-center sun-icon"
              initial="initial"
              animate="animate"
              exit="exit"
              variants={iconVariants}
              key="sun"
            >
              <Sun className="h-4 w-4" />
            </motion.div>
          )}
          <span className="sr-only">테마 변경</span>
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="theme-element-transition">
        <DropdownMenuItem
          onClick={() => handleThemeChange("light")}
          className="theme-element-transition flex items-center gap-2"
        >
          <Sun className="h-4 w-4" />
          <span>라이트 모드</span>
        </DropdownMenuItem>
        <DropdownMenuItem
          onClick={() => handleThemeChange("dark")}
          className="theme-element-transition flex items-center gap-2"
        >
          <Moon className="h-4 w-4" />
          <span>다크 모드</span>
        </DropdownMenuItem>
        <DropdownMenuItem
          onClick={() => handleThemeChange("system")}
          className="theme-element-transition flex items-center gap-2"
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            width="16"
            height="16"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
            className="h-4 w-4"
          >
            <rect x="2" y="3" width="20" height="14" rx="2" />
            <line x1="8" x2="16" y1="21" y2="21" />
            <line x1="12" x2="12" y1="17" y2="21" />
          </svg>
          <span>시스템 설정</span>
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  )
} 