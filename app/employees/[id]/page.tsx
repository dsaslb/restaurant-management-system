'use client';

import React, { useState, useEffect } from 'react';
import { Card, Descriptions, Button, Space, Tabs, message, Avatar } from 'antd';
import { UserOutlined, EditOutlined } from '@ant-design/icons';
import { useRouter } from 'next/navigation';
import supabase from '@/lib/supabase';

interface Employee {
  id: string;
  name: string;
  position: string;
  department: string;
  email: string;
  phone: string;
  hire_date: string;
  status: 'active' | 'inactive';
  profile_image?: string;
}

export default function EmployeeDetailPage({ params }: { params: { id: string } }) {
  const [employee, setEmployee] = useState<Employee | null>(null);
  const [loading, setLoading] = useState(false);
  const router = useRouter();

  useEffect(() => {
    fetchEmployee();
  }, [params.id]);

  const fetchEmployee = async () => {
    try {
      setLoading(true);
      const { data, error } = await supabase
        .from('employees')
        .select('*')
        .eq('id', params.id)
        .single();

      if (error) throw error;
      if (data) setEmployee(data);
    } catch (error) {
      message.error('직원 정보를 불러오는데 실패했습니다.');
    } finally {
      setLoading(false);
    }
  };

  const items = [
    {
      key: 'attendance',
      label: '근태 관리',
      children: (
        <iframe
          src={`/employees/${params.id}/attendance`}
          className="w-full h-[800px] border-0"
        />
      ),
    },
    {
      key: 'leave',
      label: '휴가 관리',
      children: (
        <iframe
          src={`/employees/${params.id}/leave`}
          className="w-full h-[800px] border-0"
        />
      ),
    },
    {
      key: 'salary',
      label: '급여 관리',
      children: (
        <iframe
          src={`/employees/${params.id}/salary`}
          className="w-full h-[800px] border-0"
        />
      ),
    },
  ];

  if (!employee) {
    return <div>로딩 중...</div>;
  }

  return (
    <div className="container mx-auto p-4">
      <Card
        title={
          <div className="flex items-center space-x-4">
            <Avatar
              size={64}
              src={employee.profile_image}
              icon={<UserOutlined />}
            />
            <div>
              <h1 className="text-2xl font-bold">{employee.name}</h1>
              <p className="text-gray-600">
                {employee.position} | {employee.department}
              </p>
            </div>
          </div>
        }
        extra={
          <Space>
            <Button
              icon={<EditOutlined />}
              onClick={() => router.push(`/employees/${params.id}/edit`)}
            >
              정보 수정
            </Button>
          </Space>
        }
      >
        <Descriptions bordered>
          <Descriptions.Item label="이메일" span={3}>
            {employee.email}
          </Descriptions.Item>
          <Descriptions.Item label="전화번호" span={3}>
            {employee.phone}
          </Descriptions.Item>
          <Descriptions.Item label="입사일" span={3}>
            {employee.hire_date}
          </Descriptions.Item>
          <Descriptions.Item label="상태" span={3}>
            <span
              style={{
                color: employee.status === 'active' ? 'green' : 'red',
              }}
            >
              {employee.status === 'active' ? '재직중' : '퇴사'}
            </span>
          </Descriptions.Item>
        </Descriptions>
      </Card>

      <Card className="mt-4">
        <Tabs items={items} />
      </Card>
    </div>
  );
} 