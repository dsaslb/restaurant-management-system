import './globals.css'
import { Toaster } from "@/components/ui/toaster"

export const metadata = {
  title: 'Restaurant ERP',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ko">
      <body>
        {children}
        <Toaster />
      </body>
    </html>
  )
} 