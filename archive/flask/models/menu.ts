import { z } from "zod"

export const menuSchema = z.object({
  id: z.string(),
  name: z.string(),
  description: z.string(),
  price: z.number(),
  category: z.enum(["appetizer", "main", "dessert", "beverage"]),
  image: z.string().optional(),
  isAvailable: z.boolean(),
  ingredients: z.array(z.string()),
  allergens: z.array(z.string()).optional(),
  preparationTime: z.number(), // 분 단위
  calories: z.number().optional(),
})

export type Menu = z.infer<typeof menuSchema> 