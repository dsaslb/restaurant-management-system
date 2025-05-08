import { NextApiRequest } from "next"
import { initSocket, NextApiResponseWithSocket } from "@/lib/socket"

export default function handler(req: NextApiRequest, res: NextApiResponseWithSocket) {
  if (req.method !== "GET") {
    res.status(405).json({ error: "Method not allowed" })
    return
  }

  initSocket(res)
  res.status(200).json({ message: "Socket server initialized" })
} 