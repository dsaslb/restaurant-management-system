'use client';

import React, { useState, useEffect } from 'react';
import { Card, Table, Button, Space, Modal, Form, DatePicker, Select, Input, message, Progress } from 'antd';
import { PlusOutlined } from '@ant-design/icons';
import type { RangePickerProps } from 'antd/es/date-picker';
import { format, parseISO, differenceInDays, isBefore, startOfDay } from 'date-fns';
import supabase from '@/lib/supabase';

const { RangePicker } = DatePicker;
const { Option } = Select;
const { TextArea } = Input;

interface Leave {
  id: string;
  start_date: string;
  end_date: string;
  type: 'annual' | 'sick' | 'personal' | 'other';
  reason: string;
  status: 'pending' | 'approved' | 'rejected';
  approved_by?: string;
  approved_at?: string;
}

interface LeaveBalance {
  total: number;
  used: number;
  remaining: number;
}

export default function EmployeeLeavePage({ params }: { params: { id: string } }) {
  const [leaves, setLeaves] = useState<Leave[]>([]);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [leaveBalance, setLeaveBalance] = useState<LeaveBalance>({
    total: 15,
    used: 0,
    remaining: 15,
  });
  const [form] = Form.useForm();

  useEffect(() => {
    fetchLeaves();
    calculateLeaveBalance();
  }, [params.id]);

  const fetchLeaves = async () => {
    try {
      setLoading(true);
      const { data, error } = await supabase
        .from('leaves')
        .select('*')
        .eq('employee_id', params.id)
        .order('start_date', { ascending: false });

      if (error) throw error;
      if (data) setLeaves(data);
    } catch (error) {
      message.error('휴가 정보를 불러오는데 실패했습니다.');
    } finally {
      setLoading(false);
    }
  };

  const calculateLeaveBalance = async () => {
    try {
      const { data, error } = await supabase
        .from('leaves')
        .select('*')
        .eq('employee_id', params.id)
        .eq('type', 'annual')
        .eq('status', 'approved');

      if (error) throw error;
      if (data) {
        const used = data.reduce((sum, leave) => {
          const start = parseISO(leave.start_date);
          const end = parseISO(leave.end_date);
          return sum + differenceInDays(end, start) + 1;
        }, 0);

        setLeaveBalance({
          total: 15,
          used,
          remaining: 15 - used,
        });
      }
    } catch (error) {
      console.error('휴가 잔여일 계산에 실패했습니다:', error);
    }
  };

  const handleLeaveSubmit = async (values: any) => {
    try {
      setLoading(true);
      const { error } = await supabase
        .from('leaves')
        .insert({
          employee_id: params.id,
          start_date: format(values.dates[0].toDate(), 'yyyy-MM-dd'),
          end_date: format(values.dates[1].toDate(), 'yyyy-MM-dd'),
          type: values.type,
          reason: values.reason,
          status: 'pending',
        });

      if (error) throw error;
      message.success('휴가 신청이 등록되었습니다.');
      setModalVisible(false);
      form.resetFields();
      fetchLeaves();
      calculateLeaveBalance();
    } catch (error) {
      message.error('휴가 신청에 실패했습니다.');
    } finally {
      setLoading(false);
    }
  };

  const disabledDate = (current: any) => {
    return current && isBefore(current.toDate(), startOfDay(new Date()));
  };

  const columns = [
    {
      title: '시작일',
      dataIndex: 'start_date',
      key: 'start_date',
    },
    {
      title: '종료일',
      dataIndex: 'end_date',
      key: 'end_date',
    },
    {
      title: '휴가 유형',
      dataIndex: 'type',
      key: 'type',
      render: (type: string) => {
        const types = {
          annual: '연차',
          sick: '병가',
          personal: '개인휴가',
          other: '기타',
        };
        return types[type as keyof typeof types];
      },
    },
    {
      title: '사유',
      dataIndex: 'reason',
      key: 'reason',
      ellipsis: true,
    },
    {
      title: '상태',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => {
        const statusColors = {
          pending: 'orange',
          approved: 'green',
          rejected: 'red',
        };
        const statusText = {
          pending: '대기중',
          approved: '승인',
          rejected: '거절',
        };
        return (
          <span style={{ color: statusColors[status as keyof typeof statusColors] }}>
            {statusText[status as keyof typeof statusText]}
          </span>
        );
      },
    },
    {
      title: '승인자',
      dataIndex: 'approved_by',
      key: 'approved_by',
    },
    {
      title: '승인일',
      dataIndex: 'approved_at',
      key: 'approved_at',
    },
  ];

  return (
    <div className="container mx-auto p-4">
      <Card title="휴가 관리" className="mb-4">
        <div className="mb-4">
          <h3 className="text-lg font-semibold mb-2">연차 현황</h3>
          <Progress
            percent={Math.round((leaveBalance.used / leaveBalance.total) * 100)}
            format={() => `${leaveBalance.used}일 / ${leaveBalance.total}일`}
          />
          <div className="mt-2 text-gray-600">
            잔여 연차: {leaveBalance.remaining}일
          </div>
        </div>
      </Card>

      <Card
        title="휴가 신청 내역"
        extra={
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => setModalVisible(true)}
          >
            휴가 신청
          </Button>
        }
      >
        <Table
          columns={columns}
          dataSource={leaves}
          loading={loading}
          rowKey="id"
          pagination={{
            pageSize: 10,
            showSizeChanger: true,
            showTotal: total => `총 ${total}건의 휴가 신청`,
          }}
        />
      </Card>

      <Modal
        title="휴가 신청"
        open={modalVisible}
        onCancel={() => setModalVisible(false)}
        footer={null}
      >
        <Form form={form} onFinish={handleLeaveSubmit} layout="vertical">
          <Form.Item
            name="dates"
            label="휴가 기간"
            rules={[{ required: true, message: '휴가 기간을 선택해주세요' }]}
          >
            <RangePicker
              style={{ width: '100%' }}
              disabledDate={disabledDate}
            />
          </Form.Item>

          <Form.Item
            name="type"
            label="휴가 유형"
            rules={[{ required: true, message: '휴가 유형을 선택해주세요' }]}
          >
            <Select placeholder="휴가 유형 선택">
              <Option value="annual">연차</Option>
              <Option value="sick">병가</Option>
              <Option value="personal">개인휴가</Option>
              <Option value="other">기타</Option>
            </Select>
          </Form.Item>

          <Form.Item
            name="reason"
            label="휴가 사유"
            rules={[{ required: true, message: '휴가 사유를 입력해주세요' }]}
          >
            <TextArea rows={4} placeholder="휴가 사유를 입력해주세요" />
          </Form.Item>

          <Form.Item>
            <Button type="primary" htmlType="submit" loading={loading}>
              신청
            </Button>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
} 