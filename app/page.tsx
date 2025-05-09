"use client"

import type React from "react"

import { useEffect, useRef } from "react"
import Image from "next/image"
import Link from "next/link"
import { motion, useAnimation, useInView } from "framer-motion"
import {
  ArrowRight,
  Award,
  ChefHat,
  Clock,
  FileText,
  Gift,
  Globe,
  Headphones,
  Layers,
  Sparkles,
  Star,
  Users,
  Zap,
} from "lucide-react"

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"

export default function Home() {
  return (
    <div className="bg-blue-500 text-white p-4 rounded-lg shadow-lg text-center mt-10">
      홈페이지입니다! (Tailwind 적용 테스트)
    </div>
  );
}
