import React, { useState, useEffect } from 'react';
import { Card, Input, Button, Space, Table, Tag, message } from 'antd';
import { SearchOutlined, PlusOutlined } from '@ant-design/icons';
import { useRouter } from 'next/router';
import supabase from '@/lib/supabase';

const { Search } = Input;

interface Employee {
  id: number;
  name: string;
  position: string;
  department: string;
  status: 'active' | 'inactive';
}

const EmployeeList: React.FC = () => {
  const [employees, setEmployees] = useState<Employee[]>([]);
  const [loading, setLoading] = useState(false);
  const [searchText, setSearchText] = useState('');
  const router = useRouter();

  const columns = [
    {
      title: '이름',
      dataIndex: 'name',
      key: 'name',
      render: (text: string, record: Employee) => (
        <a onClick={() => router.push(`/employees/${record.id}`)}>{text}</a>
      ),
    },
    {
      title: '직책',
      dataIndex: 'position',
      key: 'position',
    },
    {
      title: '부서',
      dataIndex: 'department',
      key: 'department',
    },
    {
      title: '상태',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => (
        <Tag color={status === 'active' ? 'green' : 'red'}>
          {status === 'active' ? '재직중' : '퇴사'}
        </Tag>
      ),
    },
  ];

  const filteredEmployees = employees.filter(employee =>
    Object.values(employee).some(value =>
      value.toString().toLowerCase().includes(searchText.toLowerCase())
    )
  );

  return (
    <Card title="직원 목록" className="shadow-md">
      <Space direction="vertical" size="middle" style={{ width: '100%' }}>
        <Space>
          <Search
            placeholder="직원 검색"
            allowClear
            enterButton={<SearchOutlined />}
            onSearch={value => setSearchText(value)}
            style={{ width: 300 }}
          />
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => router.push('/employees/new')}
          >
            직원 추가
          </Button>
        </Space>
        <Table
          columns={columns}
          dataSource={filteredEmployees}
          loading={loading}
          rowKey="id"
          pagination={{
            pageSize: 10,
            showSizeChanger: true,
            showTotal: total => `총 ${total}명의 직원`,
          }}
        />
      </Space>
    </Card>
  );
};

export default EmployeeList; 