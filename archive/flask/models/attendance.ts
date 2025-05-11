import { z } from "zod"

export const attendanceSchema = z.object({
  id: z.string(),
  employeeId: z.string(),
  date: z.date(),
  checkIn: z.date(),
  checkOut: z.date().optional(),
  status: z.enum(["onTime", "late", "earlyLeave", "absent", "vacation"]),
  workHours: z.number().optional(),
  note: z.string().optional(),
})

export type Attendance = z.infer<typeof attendanceSchema>

export interface AttendanceStats {
  totalDays: number
  presentDays: number
  absentDays: number
  lateDays: number
  earlyDays: number
  averageWorkHours: number
}

export interface AttendanceFilter {
  userId?: string
  startDate?: string
  endDate?: string
  status?: Attendance['status']
} 