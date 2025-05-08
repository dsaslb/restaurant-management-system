import { NextResponse } from "next/server"
import type { NextRequest } from "next/server"
import { verify } from "jsonwebtoken"

const JWT_SECRET = process.env.JWT_SECRET || "your-secret-key"

// 보호된 라우트 목록
const protectedRoutes = [
  "/employees",
  "/attendance",
  "/menu",
  "/orders",
  "/contracts",
]

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl

  // 로그인 페이지는 미들웨어를 통과
  if (pathname === "/login") {
    return NextResponse.next()
  }

  // 보호된 라우트인 경우 토큰 확인
  if (protectedRoutes.some(route => pathname.startsWith(route))) {
    const token = request.cookies.get("token")?.value

    if (!token) {
      return NextResponse.redirect(new URL("/login", request.url))
    }

    try {
      verify(token, JWT_SECRET)
      return NextResponse.next()
    } catch (error) {
      return NextResponse.redirect(new URL("/login", request.url))
    }
  }

  return NextResponse.next()
}

export const config = {
  matcher: [
    /*
     * Match all request paths except for the ones starting with:
     * - api (API routes)
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     */
    "/((?!api|_next/static|_next/image|favicon.ico).*)",
  ],
} 