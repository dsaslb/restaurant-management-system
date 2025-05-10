import { toast as sonnerToast } from "sonner"

export function useToast() {
  // 간단한 toast 래퍼
  return {
    toast: (options: { title: string; description?: string; action?: React.ReactNode }) => {
      sonnerToast(options.title, {
        description: options.description,
        action: options.action,
      })
    },
  }
} 