'use client';
import { useEffect, useState } from 'react';
import { Bell, CheckCircle2, Trash2, MailOpen, Search } from 'lucide-react';

function formatDate(dateStr: string) {
  const d = new Date(dateStr);
  return d.toLocaleString('ko-KR', { year: '2-digit', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' });
}

export default function NotificationList() {
  const [notifications, setNotifications] = useState([]);
  const [search, setSearch] = useState('');
  const [sort, setSort] = useState<'desc'|'asc'>('desc');
  const [filter, setFilter] = useState<'all'|'read'|'unread'>('all');

  useEffect(() => {
    fetchNotifications();
  }, []);

  async function fetchNotifications() {
    const res = await fetch('/api/notifications');
    const data = await res.json();
    setNotifications(data);
  }

  async function markAsRead(id?: number) {
    await fetch('/api/notifications', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(id ? { id } : { all: true }),
    });
    fetchNotifications();
  }

  async function deleteNotification(id?: number) {
    await fetch('/api/notifications', {
      method: 'DELETE',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(id ? { id } : { all: true }),
    });
    fetchNotifications();
  }

  // 검색, 정렬, 필터 적용
  const filtered = notifications
    .filter((n: any) => {
      if (filter === 'read') return n.is_read;
      if (filter === 'unread') return !n.is_read;
      return true;
    })
    .filter((n: any) => {
      if (!search) return true;
      return (
        n.type?.toLowerCase().includes(search.toLowerCase()) ||
        n.message?.toLowerCase().includes(search.toLowerCase())
      );
    })
    .sort((a: any, b: any) => {
      if (sort === 'desc') return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
      return new Date(a.created_at).getTime() - new Date(b.created_at).getTime();
    });

  return (
    <div className="p-4 border rounded bg-white mt-4 max-w-lg mx-auto shadow">
      <div className="flex items-center mb-2 gap-2">
        <Bell className="text-blue-500" />
        <h2 className="font-bold text-lg">알림 내역</h2>
        <div className="ml-auto flex gap-2">
          <button onClick={() => markAsRead()} className="bg-blue-500 text-white px-2 py-1 rounded text-sm flex items-center gap-1">
            <CheckCircle2 size={16} /> 전체 읽음
          </button>
          <button onClick={() => deleteNotification()} className="bg-red-500 text-white px-2 py-1 rounded text-sm flex items-center gap-1">
            <Trash2 size={16} /> 전체 삭제
          </button>
        </div>
      </div>
      {/* 검색, 정렬, 필터 UI */}
      <div className="flex gap-2 mb-2 items-center">
        <div className="relative flex-1">
          <input
            value={search}
            onChange={e => setSearch(e.target.value)}
            placeholder="검색 (종류, 내용)"
            className="border px-2 py-1 rounded w-full pl-8"
          />
          <Search size={16} className="absolute left-2 top-2 text-gray-400" />
        </div>
        <select value={sort} onChange={e => setSort(e.target.value as 'desc'|'asc')} className="border px-2 py-1 rounded">
          <option value="desc">최신순</option>
          <option value="asc">오래된순</option>
        </select>
        <select value={filter} onChange={e => setFilter(e.target.value as 'all'|'read'|'unread')} className="border px-2 py-1 rounded">
          <option value="all">전체</option>
          <option value="unread">안읽음</option>
          <option value="read">읽음</option>
        </select>
      </div>
      <ul className="max-h-72 overflow-y-auto space-y-2">
        {filtered.length === 0 && (
          <li className="text-gray-400 text-center py-8">알림이 없습니다.</li>
        )}
        {filtered.map((n: any) => (
          <li
            key={n.id}
            className={`flex items-center gap-2 p-3 rounded border ${n.is_read ? 'bg-gray-100 text-gray-400' : 'bg-blue-50 border-blue-200'} shadow-sm`}
          >
            <span className="flex-shrink-0">
              {n.is_read ? <MailOpen size={20} className="text-gray-400" /> : <Bell size={20} className="text-blue-500" />}
            </span>
            <div className="flex-1">
              <div className="font-semibold">{n.type}</div>
              <div className="text-sm">{n.message}</div>
              <div className="text-xs text-gray-400">{formatDate(n.created_at)}</div>
            </div>
            {!n.is_read && (
              <button onClick={() => markAsRead(n.id)} className="text-blue-500 underline text-xs">읽음</button>
            )}
            <button onClick={() => deleteNotification(n.id)} className="text-red-400 underline text-xs">삭제</button>
          </li>
        ))}
      </ul>
    </div>
  );
} 