import React from 'react';
import { Card, CardContent } from './ui/card';
import { Avatar, AvatarFallback, AvatarImage } from './ui/avatar';
import { Badge } from './ui/badge';
import { Eye } from 'lucide-react';
import Link from 'next/link';

interface Employee {
  id: string;
  name: string;
  position: string;
  department: string;
  status: string;
  joinDate: string;
  contract: string;
  phone: string;
  email: string;
  image: string;
}

interface EmployeeCardsProps {
  employees: Employee[];
  user: any;
}

export function EmployeeCards({ employees, user }: EmployeeCardsProps) {
  const [search, setSearch] = React.useState("");
  const [status, setStatus] = React.useState("all");

  const filtered = employees.filter(emp =>
    (emp.name.includes(search) || emp.department.includes(search) || emp.position.includes(search)) &&
    (status === "all" || emp.status === status)
  );

  return (
    <>
      {user?.role === "admin" && (
        <div className="mb-2">
          <button>직원 추가</button>
        </div>
      )}
      <div className="flex gap-2 mb-4">
        <input
          type="text"
          placeholder="이름/부서/직책 검색"
          value={search}
          onChange={e => setSearch(e.target.value)}
          className="border px-2 py-1 rounded"
        />
        <select value={status} onChange={e => setStatus(e.target.value)} className="border px-2 py-1 rounded">
          <option value="all">전체</option>
          <option value="active">재직 중</option>
          <option value="inactive">퇴사</option>
        </select>
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
        {filtered.length === 0 ? (
          <div className="col-span-full text-center text-gray-400">직원이 없습니다.</div>
        ) : (
          filtered.map((employee) => (
            <Card key={employee.id} className="overflow-hidden">
              <CardContent className="p-0">
                <div className="flex items-center gap-4 border-b p-4">
                  <Avatar className="h-12 w-12">
                    <AvatarImage src={employee.image || "/placeholder.svg"} alt={employee.name} />
                    <AvatarFallback>{employee.name.slice(0, 1)}</AvatarFallback>
                  </Avatar>
                  <div className="flex-1">
                    <div className="flex items-center justify-between">
                      <h3 className="font-semibold">{employee.name}</h3>
                      <Badge variant={employee.status === "active" ? "default" : "secondary"} className="ml-2">
                        {employee.status === "active" ? "재직 중" : "퇴사"}
                      </Badge>
                    </div>
                    <p className="text-sm text-muted-foreground">{employee.position}</p>
                  </div>
                </div>
                <div className="space-y-2 p-4">
                  <div className="flex items-center text-sm">
                    <span>{employee.department}</span>
                  </div>
                  <div className="flex items-center text-sm">
                    <span>{employee.contract}</span>
                  </div>
                  <div className="flex items-center text-sm">
                    <span>{employee.joinDate}</span>
                  </div>
                  <div className="flex items-center text-sm">
                    <a href={`tel:${employee.phone}`} className="truncate hover:underline">{employee.phone}</a>
                  </div>
                  <div className="flex items-center text-sm">
                    <a href={`mailto:${employee.email}`} className="truncate hover:underline">{employee.email}</a>
                  </div>
                </div>
                <div className="border-t p-4">
                  <Link href={`/employees/${employee.id}`} passHref>
                    <button className="w-full">
                      <Eye className="mr-2 h-4 w-4" />
                      상세 정보
                    </button>
                  </Link>
                </div>
              </CardContent>
            </Card>
          ))
        )}
      </div>
    </>
  );
}

export default EmployeeCards; 