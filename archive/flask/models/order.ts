import { z } from "zod"

export const orderItemSchema = z.object({
  menuId: z.string(),
  quantity: z.number(),
  price: z.number(),
  notes: z.string().optional(),
})

export const orderSchema = z.object({
  id: z.string(),
  tableNumber: z.number(),
  items: z.array(orderItemSchema),
  status: z.enum(["pending", "preparing", "ready", "served", "completed", "cancelled"]),
  totalAmount: z.number(),
  paymentMethod: z.enum(["cash", "card", "mobile"]).optional(),
  paymentStatus: z.enum(["pending", "paid", "refunded"]),
  createdAt: z.date(),
  updatedAt: z.date(),
  servedBy: z.string(), // employeeId
  notes: z.string().optional(),
})

export type Order = z.infer<typeof orderSchema>
export type OrderItem = z.infer<typeof orderItemSchema> 