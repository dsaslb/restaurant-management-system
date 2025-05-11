'use client';

import React, { useState, useEffect } from 'react';
import { Card, Table, Button, Space, Modal, Form, DatePicker, TimePicker, Select, message, Calendar, Badge } from 'antd';
import { PlusOutlined } from '@ant-design/icons';
import { format, parseISO } from 'date-fns';
import supabase from '@/lib/supabase';

const { Option } = Select;

interface Attendance {
  id: string;
  date: string;
  check_in: string;
  check_out: string;
  status: 'normal' | 'late' | 'early' | 'absent';
  note?: string;
}

interface AttendanceSummary {
  total_days: number;
  present_days: number;
  late_days: number;
  early_days: number;
  absent_days: number;
}

export default function EmployeeAttendancePage({ params }: { params: { id: string } }) {
  const [attendances, setAttendances] = useState<Attendance[]>([]);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [summary, setSummary] = useState<AttendanceSummary>({
    total_days: 0,
    present_days: 0,
    late_days: 0,
    early_days: 0,
    absent_days: 0,
  });
  const [form] = Form.useForm();

  useEffect(() => {
    fetchAttendances();
    calculateSummary();
  }, [params.id]);

  const fetchAttendances = async () => {
    try {
      setLoading(true);
      const { data, error } = await supabase
        .from('attendances')
        .select('*')
        .eq('employee_id', params.id)
        .order('date', { ascending: false });

      if (error) throw error;
      if (data) setAttendances(data);
    } catch (error) {
      message.error('근태 정보를 불러오는데 실패했습니다.');
    } finally {
      setLoading(false);
    }
  };

  const calculateSummary = () => {
    const summary = attendances.reduce(
      (acc, attendance) => {
        acc.total_days++;
        switch (attendance.status) {
          case 'normal':
            acc.present_days++;
            break;
          case 'late':
            acc.late_days++;
            break;
          case 'early':
            acc.early_days++;
            break;
          case 'absent':
            acc.absent_days++;
            break;
        }
        return acc;
      },
      {
        total_days: 0,
        present_days: 0,
        late_days: 0,
        early_days: 0,
        absent_days: 0,
      }
    );
    setSummary(summary);
  };

  const handleAttendanceSubmit = async (values: any) => {
    try {
      setLoading(true);
      const { error } = await supabase
        .from('attendances')
        .insert({
          employee_id: params.id,
          date: format(values.date.toDate(), 'yyyy-MM-dd'),
          check_in: format(values.check_in.toDate(), 'HH:mm:ss'),
          check_out: format(values.check_out.toDate(), 'HH:mm:ss'),
          status: values.status,
          note: values.note,
        });

      if (error) throw error;
      message.success('근태 정보가 등록되었습니다.');
      setModalVisible(false);
      form.resetFields();
      fetchAttendances();
      calculateSummary();
    } catch (error) {
      message.error('근태 정보 등록에 실패했습니다.');
    } finally {
      setLoading(false);
    }
  };

  const getListData = (value: any) => {
    const date = format(value.toDate(), 'yyyy-MM-dd');
    const attendance = attendances.find(a => a.date === date);
    if (!attendance) return [];

    const statusColors = {
      normal: 'green',
      late: 'orange',
      early: 'blue',
      absent: 'red',
    };

    const statusText = {
      normal: '정상',
      late: '지각',
      early: '조퇴',
      absent: '결근',
    };

    return [
      {
        type: statusColors[attendance.status as keyof typeof statusColors],
        content: statusText[attendance.status as keyof typeof statusText],
      },
    ];
  };

  const dateCellRender = (value: any) => {
    const listData = getListData(value);
    return (
      <ul className="events">
        {listData.map((item, index) => (
          <li key={index}>
            <Badge status={item.type as any} text={item.content} />
          </li>
        ))}
      </ul>
    );
  };

  const columns = [
    {
      title: '날짜',
      dataIndex: 'date',
      key: 'date',
    },
    {
      title: '출근 시간',
      dataIndex: 'check_in',
      key: 'check_in',
    },
    {
      title: '퇴근 시간',
      dataIndex: 'check_out',
      key: 'check_out',
    },
    {
      title: '상태',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => {
        const statusColors = {
          normal: 'green',
          late: 'orange',
          early: 'blue',
          absent: 'red',
        };
        const statusText = {
          normal: '정상',
          late: '지각',
          early: '조퇴',
          absent: '결근',
        };
        return (
          <span style={{ color: statusColors[status as keyof typeof statusColors] }}>
            {statusText[status as keyof typeof statusText]}
          </span>
        );
      },
    },
    {
      title: '비고',
      dataIndex: 'note',
      key: 'note',
      ellipsis: true,
    },
  ];

  return (
    <div className="container mx-auto p-4">
      <Card title="근태 현황" className="mb-4">
        <div className="grid grid-cols-5 gap-4">
          <div className="text-center">
            <div className="text-lg font-semibold">총 근무일</div>
            <div className="text-2xl">{summary.total_days}일</div>
          </div>
          <div className="text-center">
            <div className="text-lg font-semibold text-green-600">정상 출근</div>
            <div className="text-2xl">{summary.present_days}일</div>
          </div>
          <div className="text-center">
            <div className="text-lg font-semibold text-orange-600">지각</div>
            <div className="text-2xl">{summary.late_days}일</div>
          </div>
          <div className="text-center">
            <div className="text-lg font-semibold text-blue-600">조퇴</div>
            <div className="text-2xl">{summary.early_days}일</div>
          </div>
          <div className="text-center">
            <div className="text-lg font-semibold text-red-600">결근</div>
            <div className="text-2xl">{summary.absent_days}일</div>
          </div>
        </div>
      </Card>

      <div className="grid grid-cols-2 gap-4">
        <Card
          title="근태 캘린더"
          className="mb-4"
        >
          <Calendar dateCellRender={dateCellRender} />
        </Card>

        <Card
          title="근태 기록"
          extra={
            <Button
              type="primary"
              icon={<PlusOutlined />}
              onClick={() => setModalVisible(true)}
            >
              근태 등록
            </Button>
          }
        >
          <Table
            columns={columns}
            dataSource={attendances}
            loading={loading}
            rowKey="id"
            pagination={{
              pageSize: 10,
              showSizeChanger: true,
              showTotal: total => `총 ${total}건의 근태 기록`,
            }}
          />
        </Card>
      </div>

      <Modal
        title="근태 등록"
        open={modalVisible}
        onCancel={() => setModalVisible(false)}
        footer={null}
      >
        <Form form={form} onFinish={handleAttendanceSubmit} layout="vertical">
          <Form.Item
            name="date"
            label="날짜"
            rules={[{ required: true, message: '날짜를 선택해주세요' }]}
          >
            <DatePicker style={{ width: '100%' }} />
          </Form.Item>

          <Form.Item
            name="check_in"
            label="출근 시간"
            rules={[{ required: true, message: '출근 시간을 입력해주세요' }]}
          >
            <TimePicker format="HH:mm" style={{ width: '100%' }} />
          </Form.Item>

          <Form.Item
            name="check_out"
            label="퇴근 시간"
            rules={[{ required: true, message: '퇴근 시간을 입력해주세요' }]}
          >
            <TimePicker format="HH:mm" style={{ width: '100%' }} />
          </Form.Item>

          <Form.Item
            name="status"
            label="상태"
            rules={[{ required: true, message: '상태를 선택해주세요' }]}
          >
            <Select placeholder="상태 선택">
              <Option value="normal">정상</Option>
              <Option value="late">지각</Option>
              <Option value="early">조퇴</Option>
              <Option value="absent">결근</Option>
            </Select>
          </Form.Item>

          <Form.Item
            name="note"
            label="비고"
          >
            <Select.TextArea rows={4} placeholder="비고를 입력해주세요" />
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