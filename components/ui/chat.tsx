import { useEffect, useRef, useState } from 'react'
import supabase from '@/lib/supabase'
import { toast } from 'sonner'

// 실시간 채팅 컴포넌트 (Supabase 연동, 관리자/직원 구분, 알림)
export function Chat({ user }: { user: any }) {
  const [messages, setMessages] = useState<any[]>([])
  const [input, setInput] = useState('')
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const userId = user?.id
  const userName = user?.user_metadata?.name || user?.email || '익명'
  const role = user?.user_metadata?.role || '직원'

  // 메시지 불러오기 + 실시간 구독
  useEffect(() => {
    let subscription: any
    async function fetchAndSubscribe() {
      // 1. 기존 메시지 불러오기
      const { data } = await supabase.from('messages').select('*').order('created_at', { ascending: true })
      if (data) setMessages(data)
      // 2. 실시간 구독
      subscription = supabase
        .channel('messages')
        .on('postgres_changes', { event: 'INSERT', schema: 'public', table: 'messages' }, payload => {
          setMessages(prev => [...prev, payload.new])
          if (payload.new.user_id !== userId) {
            toast.info(`${payload.new.user_name}님의 새 메시지: ${payload.new.text}`)
          }
        })
        .subscribe()
    }
    fetchAndSubscribe()
    return () => {
      if (subscription) supabase.removeChannel(subscription)
    }
  }, [userId])

  // 스크롤 항상 아래로
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // 메시지 전송
  async function sendMessage() {
    if (!input.trim()) return
    await supabase.from('messages').insert({
      user_id: userId,
      user_name: userName,
      role,
      text: input
    })
    setInput('')
  }

  // 엔터로 전송
  function handleKeyDown(e: React.KeyboardEvent<HTMLInputElement>) {
    if (e.key === 'Enter') sendMessage()
  }

  return (
    <div className="max-w-md mx-auto border rounded shadow bg-white dark:bg-gray-900 flex flex-col h-96">
      <div className="flex-1 overflow-y-auto p-4 space-y-2">
        {messages.map((msg, i) => (
          <div key={msg.id || i} className={msg.user_id === userId ? 'text-right' : 'text-left'}>
            <span className={
              'inline-block px-3 py-2 rounded text-sm ' +
              (msg.user_id === userId
                ? 'bg-blue-100 dark:bg-blue-800'
                : msg.role === 'admin'
                  ? 'bg-yellow-100 dark:bg-yellow-800'
                  : 'bg-gray-100 dark:bg-gray-800')
            }>
              <b>{msg.user_name}({msg.role === 'admin' ? '관리자' : '직원'})</b>: {msg.text}
            </span>
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>
      <div className="p-2 border-t flex gap-2">
        <input
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="메시지 입력..."
          className="border px-2 py-1 rounded flex-1"
        />
        <button onClick={sendMessage} className="bg-blue-500 text-white px-3 py-1 rounded">전송</button>
      </div>
    </div>
  )
} 