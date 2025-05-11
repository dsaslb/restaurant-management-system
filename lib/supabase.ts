import { createClient } from '@supabase/supabase-js'

// .env.local에 저장한 환경변수에서 URL과 anon key를 읽어옵니다.
const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,      // Supabase 프로젝트 URL
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!  // Supabase anon key
)

export default supabase 