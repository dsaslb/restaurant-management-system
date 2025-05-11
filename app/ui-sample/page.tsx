"use client"

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { Skeleton } from "@/components/ui/skeleton"
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "@/components/ui/dropdown-menu"
import { ThemeToggle } from "@/components/theme-toggle"

export default function UiSamplePage() {
  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 p-8 space-y-8">
      <h1 className="text-2xl font-bold mb-4 dark:text-white">shadcn UI 샘플 모음</h1>

      {/* 버튼 예시 */}
      <section>
        <h2 className="text-xl font-semibold mb-2 dark:text-white">Button (버튼)</h2>
        <div className="flex gap-4 flex-wrap">
          <Button>기본 버튼</Button>
          <Button variant="outline">아웃라인 버튼</Button>
          <Button variant="destructive">위험(삭제) 버튼</Button>
          <Button disabled>비활성화</Button>
        </div>
      </section>

      {/* 배지 예시 */}
      <section>
        <h2 className="text-xl font-semibold mb-2 dark:text-white">Badge (배지)</h2>
        <div className="flex gap-2 flex-wrap">
          <Badge>기본 배지</Badge>
          <Badge variant="outline">아웃라인 배지</Badge>
        </div>
      </section>

      {/* 카드 예시 */}
      <section>
        <h2 className="text-xl font-semibold mb-2 dark:text-white">Card (카드)</h2>
        <Card className="max-w-xs">
          <CardHeader>
            <CardTitle>카드 제목</CardTitle>
          </CardHeader>
          <CardContent>
            <p>이곳에 카드 내용을 입력할 수 있습니다.</p>
            <Button className="mt-4 w-full">카드 내 버튼</Button>
          </CardContent>
        </Card>
      </section>

      {/* 프로그레스 바 예시 */}
      <section>
        <h2 className="text-xl font-semibold mb-2 dark:text-white">Progress (프로그레스 바)</h2>
        <Progress value={60} className="w-1/2" />
      </section>

      {/* 탭 예시 */}
      <section>
        <h2 className="text-xl font-semibold mb-2 dark:text-white">Tabs (탭)</h2>
        <Tabs defaultValue="first" className="w-[300px]">
          <TabsList>
            <TabsTrigger value="first">첫 번째</TabsTrigger>
            <TabsTrigger value="second">두 번째</TabsTrigger>
          </TabsList>
          <TabsContent value="first">첫 번째 탭 내용</TabsContent>
          <TabsContent value="second">두 번째 탭 내용</TabsContent>
        </Tabs>
      </section>

      {/* 아바타 예시 */}
      <section>
        <h2 className="text-xl font-semibold mb-2 dark:text-white">Avatar (아바타)</h2>
        <div className="flex gap-4 items-center">
          <Avatar>
            <AvatarImage src="/placeholder.svg" />
            <AvatarFallback>홍길동</AvatarFallback>
          </Avatar>
          <Avatar>
            <AvatarFallback>JS</AvatarFallback>
          </Avatar>
        </div>
      </section>

      {/* 스켈레톤(로딩) 예시 */}
      <section>
        <h2 className="text-xl font-semibold mb-2 dark:text-white">Skeleton (로딩)</h2>
        <div className="flex gap-4">
          <Skeleton className="h-8 w-32" />
          <Skeleton className="h-8 w-8 rounded-full" />
        </div>
      </section>

      {/* 드롭다운 메뉴 예시 */}
      <section>
        <h2 className="text-xl font-semibold mb-2 dark:text-white">DropdownMenu (드롭다운 메뉴)</h2>
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button>메뉴 열기</Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent>
            <DropdownMenuItem>메뉴 1</DropdownMenuItem>
            <DropdownMenuItem>메뉴 2</DropdownMenuItem>
            <DropdownMenuItem>메뉴 3</DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </section>

      {/* 테마 토글 예시 */}
      <section>
        <h2 className="text-xl font-semibold mb-2 dark:text-white">ThemeToggle (테마 토글)</h2>
        <ThemeToggle />
      </section>
    </div>
  )
} 