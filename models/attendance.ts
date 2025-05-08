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