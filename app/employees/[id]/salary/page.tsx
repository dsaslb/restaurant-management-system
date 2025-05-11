'use client';

import React, { useState, useEffect } from 'react';
import { Card, Table, Button, Space, Modal, Form, Input, InputNumber, Select, message } from 'antd';
import { PlusOutlined, DownloadOutlined } from '@ant-design/icons';
import * as XLSX from 'xlsx';
import supabase from '@/lib/supabase';

const { Option } = Select;

interface Salary {
  id: string;
  year: number;
  month: number;
  base_salary: number;
  overtime_pay: number;
  bonus: number;
  deductions: number;
  net_salary: number;
  payment_date: string;
  status: 'pending' | 'paid';
}

export default function EmployeeSalaryPage({ params }: { params: { id: string } }) {
  const [salaries, setSalaries] = useState<Salary[]>([]);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [form] = Form.useForm();

  useEffect(() => {
    fetchSalaries();
  }, [params.id]);

  const fetchSalaries = async () => {
    try {
      setLoading(true);
      const { data, error } = await supabase
        .from('salaries')
        .select('*')
        .eq('employee_id', params.id)
        .order('year', { ascending: false })
        .order('month', { ascending: false });

      if (error) throw error;
      if (data) setSalaries(data);
    } catch (error) {
      message.error('급여 정보를 불러오는데 실패했습니다.');
    } finally {
      setLoading(false);
    }
  };

  const handleSalarySubmit = async (values: any) => {
    try {
      setLoading(true);
      const netSalary = values.base_salary + values.overtime_pay + values.bonus - values.deductions;
      
      const { error } = await supabase
        .from('salaries')
        .insert({
          employee_id: params.id,
          year: values.year,
          month: values.month,
          base_salary: values.base_salary,
          overtime_pay: values.overtime_pay,
          bonus: values.bonus,
          deductions: values.deductions,
          net_salary: netSalary,
          payment_date: values.payment_date,
          status: 'pending',
        });

      if (error) throw error;
      message.success('급여 정보가 등록되었습니다.');
      setModalVisible(false);
      form.resetFields();
      fetchSalaries();
    } catch (error) {
      message.error('급여 정보 등록에 실패했습니다.');
    } finally {
      setLoading(false);
    }
  };

  const exportToExcel = () => {
    const worksheet = XLSX.utils.json_to_sheet(salaries);
    const workbook = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(workbook, worksheet, '급여 내역');
    XLSX.writeFile(workbook, '급여내역.xlsx');
    message.success('엑셀 파일이 다운로드되었습니다.');
  };

  const columns = [
    {
      title: '년도',
      dataIndex: 'year',
      key: 'year',
    },
    {
      title: '월',
      dataIndex: 'month',
      key: 'month',
    },
    {
      title: '기본급',
      dataIndex: 'base_salary',
      key: 'base_salary',
      render: (value: number) => value.toLocaleString() + '원',
    },
    {
      title: '초과수당',
      dataIndex: 'overtime_pay',
      key: 'overtime_pay',
      render: (value: number) => value.toLocaleString() + '원',
    },
    {
      title: '상여금',
      dataIndex: 'bonus',
      key: 'bonus',
      render: (value: number) => value.toLocaleString() + '원',
    },
    {
      title: '공제액',
      dataIndex: 'deductions',
      key: 'deductions',
      render: (value: number) => value.toLocaleString() + '원',
    },
    {
      title: '실지급액',
      dataIndex: 'net_salary',
      key: 'net_salary',
      render: (value: number) => value.toLocaleString() + '원',
    },
    {
      title: '지급일',
      dataIndex: 'payment_date',
      key: 'payment_date',
    },
    {
      title: '상태',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => (
        <span style={{ color: status === 'paid' ? 'green' : 'orange' }}>
          {status === 'paid' ? '지급완료' : '대기중'}
        </span>
      ),
    },
  ];

  return (
    <div className="container mx-auto p-4">
      <Card
        title="급여 정보"
        extra={
          <Space>
            <Button
              icon={<DownloadOutlined />}
              onClick={exportToExcel}
            >
              엑셀 다운로드
            </Button>
            <Button
              type="primary"
              icon={<PlusOutlined />}
              onClick={() => setModalVisible(true)}
            >
              급여 등록
            </Button>
          </Space>
        }
      >
        <Table
          columns={columns}
          dataSource={salaries}
          loading={loading}
          rowKey="id"
          pagination={{
            pageSize: 12,
            showSizeChanger: true,
            showTotal: total => `총 ${total}건의 급여 내역`,
          }}
        />
      </Card>

      <Modal
        title="급여 정보 등록"
        open={modalVisible}
        onCancel={() => setModalVisible(false)}
        footer={null}
      >
        <Form form={form} onFinish={handleSalarySubmit} layout="vertical">
          <Form.Item
            name="year"
            label="년도"
            rules={[{ required: true, message: '년도를 입력해주세요' }]}
          >
            <InputNumber min={2000} max={2100} style={{ width: '100%' }} />
          </Form.Item>

          <Form.Item
            name="month"
            label="월"
            rules={[{ required: true, message: '월을 선택해주세요' }]}
          >
            <Select placeholder="월 선택">
              {Array.from({ length: 12 }, (_, i) => (
                <Option key={i + 1} value={i + 1}>
                  {i + 1}월
                </Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item
            name="base_salary"
            label="기본급"
            rules={[{ required: true, message: '기본급을 입력해주세요' }]}
          >
            <InputNumber
              min={0}
              step={100000}
              style={{ width: '100%' }}
              formatter={value => `${value}`.replace(/\B(?=(\d{3})+(?!\d))/g, ',')}
              parser={value => value!.replace(/\$\s?|(,*)/g, '')}
            />
          </Form.Item>

          <Form.Item
            name="overtime_pay"
            label="초과수당"
            initialValue={0}
          >
            <InputNumber
              min={0}
              step={10000}
              style={{ width: '100%' }}
              formatter={value => `${value}`.replace(/\B(?=(\d{3})+(?!\d))/g, ',')}
              parser={value => value!.replace(/\$\s?|(,*)/g, '')}
            />
          </Form.Item>

          <Form.Item
            name="bonus"
            label="상여금"
            initialValue={0}
          >
            <InputNumber
              min={0}
              step={100000}
              style={{ width: '100%' }}
              formatter={value => `${value}`.replace(/\B(?=(\d{3})+(?!\d))/g, ',')}
              parser={value => value!.replace(/\$\s?|(,*)/g, '')}
            />
          </Form.Item>

          <Form.Item
            name="deductions"
            label="공제액"
            initialValue={0}
          >
            <InputNumber
              min={0}
              step={10000}
              style={{ width: '100%' }}
              formatter={value => `${value}`.replace(/\B(?=(\d{3})+(?!\d))/g, ',')}
              parser={value => value!.replace(/\$\s?|(,*)/g, '')}
            />
          </Form.Item>

          <Form.Item
            name="payment_date"
            label="지급일"
            rules={[{ required: true, message: '지급일을 입력해주세요' }]}
          >
            <Input type="date" />
          </Form.Item>

          <Form.Item>
            <Button type="primary" htmlType="submit" loading={loading}>
              등록
            </Button>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
} 