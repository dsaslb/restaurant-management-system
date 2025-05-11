"use client"

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import supabase from "@/lib/supabase"
import { toast } from "sonner"
import Link from "next/link"

const MAX_FAIL = 5

export default function LoginPage() {
  const router = useRouter()
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [showPw, setShowPw] = useState(false)
  const [failCount, setFailCount] = useState(0)
  const [locked, setLocked] = useState(false)

  // 자동 로그인(세션 유지)
  useEffect(() => {
    supabase.auth.getUser().then(({ data }) => {
      if (data?.user) {
        if (data.user.user_metadata?.role === "admin") {
          router.push("/dashboard")
        } else {
          router.push("/attendance")
        }
      }
    })
    // 로그인 실패 횟수 로드
    const fail = Number(localStorage.getItem('loginFail') || '0')
    setFailCount(fail)
  }, [router])

  const handleLogin = async () => {
    setLoading(true)
    setError(null)
    const { data, error } = await supabase.auth.signInWithPassword({ email, password })
    setLoading(false)
    if (error) {
      const nextFail = failCount + 1
      setFailCount(nextFail)
      localStorage.setItem('loginFail', String(nextFail))
      return setError(`로그인 실패! (${nextFail}/${MAX_FAIL}) - 이메일 또는 비밀번호를 확인하세요.`)
    }
    // 로그인 성공 시 실패 횟수 초기화
    localStorage.removeItem('loginFail')
    setFailCount(0)
    toast.success("로그인 성공!")
    const user = data?.user
    if (user?.user_metadata?.role === "admin") {
      router.push("/dashboard")
    } else {
      router.push("/attendance")
    }
  }

  // 소셜 로그인 예시(구글, 카카오, 네이버)
  const handleSocial = async (provider: 'google' | 'kakao' | 'naver') => {
    setLoading(true)
    const { error } = await supabase.auth.signInWithOAuth({ provider })
    setLoading(false)
    if (error) setError(error.message)
  }

  return (
    <div className="container flex items-center justify-center min-h-screen py-12">
      <div className="max-w-sm mx-auto mt-16 p-6 border rounded shadow">
        <h1 className="text-lg font-bold mb-4">로그인</h1>
        {error && <p className="text-red-500 mb-2">{error}</p>}
        <label htmlFor="email" className="block text-sm font-medium mb-1">이메일</label>
        <input
          id="email"
          type="email"
          aria-label="이메일"
          placeholder="이메일"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          className="w-full border px-3 py-2 mb-2 rounded"
          autoComplete="username"
          required
        />
        <label htmlFor="password" className="block text-sm font-medium mb-1">비밀번호</label>
        <div className="relative mb-4">
          <input
            id="password"
            type={showPw ? "text" : "password"}
            aria-label="비밀번호"
            placeholder="비밀번호"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="w-full border px-3 py-2 pr-10 rounded"
            autoComplete="current-password"
            required
          />
          <button
            type="button"
            aria-label={showPw ? "비밀번호 숨기기" : "비밀번호 보이기"}
            onClick={() => setShowPw((v) => !v)}
            className="absolute right-2 top-1/2 -translate-y-1/2 text-xs text-gray-500"
          >
            {showPw ? "숨기기" : "보이기"}
          </button>
        </div>
        <button
          onClick={handleLogin}
          className="w-full bg-blue-600 text-white py-2 rounded mb-2 disabled:opacity-60"
          disabled={loading}
        >
          {loading ? "로그인 중..." : "로그인"}
        </button>
        <button
          onClick={() => handleSocial('google')}
          className="w-full bg-red-500 text-white py-2 rounded mb-2 disabled:opacity-60"
          disabled={loading}
          type="button"
        >
          Google로 로그인
        </button>
        <button
          onClick={() => handleSocial('kakao')}
          className="w-full bg-yellow-400 text-black py-2 rounded mb-2 disabled:opacity-60"
          disabled={loading}
          type="button"
        >
          Kakao로 로그인
        </button>
        <button
          onClick={() => handleSocial('naver')}
          className="w-full bg-green-500 text-white py-2 rounded mb-2 disabled:opacity-60"
          disabled={loading}
          type="button"
        >
          Naver로 로그인
        </button>
        <div className="flex justify-between text-sm mt-2">
          <Link href="/signup" className="text-blue-500 underline">회원가입</Link>
          <Link href="/forgot" className="text-blue-500 underline">비밀번호 찾기</Link>
        </div>
      </div>
    </div>
  )
} 