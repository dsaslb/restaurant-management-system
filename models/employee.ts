import { z } from "zod"

export const employeeSchema = z.object({
  id: z.string(),
  name: z.string(),
  position: z.string(),
  email: z.string().email(),
  phone: z.string(),
  hireDate: z.date(),
  status: z.enum(["active", "vacation", "leave", "resigned"]),
  employmentType: z.enum(["full-time", "part-time", "contract"]),
  salary: z.number(),
  bankAccount: z.string(),
  emergencyContact: z.string(),
  notes: z.string().optional(),
})

export type Employee = z.infer<typeof employeeSchema> 