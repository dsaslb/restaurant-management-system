import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"
import { useToast } from "@/components/ui/use-toast"
import { Toaster } from "@/components/ui/toaster"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
} 