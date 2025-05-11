'use client';

import React, { useState, useEffect } from 'react';
import { Card, Calendar, Badge, Modal, Form, TimePicker, Select, Button, message } from 'antd';
import { PlusOutlined } from '@ant-design/icons';
import { format, parseISO } from 'date-fns';
import supabase from '@/lib/supabase';

const { Option } = Select;

interface Schedule {
  id: string;
  date: string;
  start_time: string;
  end_time: string;
  type: 'regular' | 'overtime' | 'holiday';
  status: 'scheduled' | 'completed' | 'absent';
}

export default function EmployeeSchedulePage({ params }: { params: { id: string } }) {
  const [schedules, setSchedules] = useState<Schedule[]>([]);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [selectedDate, setSelectedDate] = useState<any>(null);
  const [form] = Form.useForm();

  useEffect(() => {
    fetchSchedules();
  }, [params.id]);

  const fetchSchedules = async () => {
    try {
      setLoading(true);
      const { data, error } = await supabase
        .from('schedules')
        .select('*')
        .eq('employee_id', params.id)
        .order('date');

      if (error) throw error;
      if (data) setSchedules(data);
    } catch (error) {
      message.error('일정을 불러오는데 실패했습니다.');
    } finally {
      setLoading(false);
    }
  };

  const handleDateSelect = (date: any) => {
    setSelectedDate(date);
    setModalVisible(true);
  };

  const handleScheduleSubmit = async (values: any) => {
    try {
      setLoading(true);
      const { error } = await supabase
        .from('schedules')
        .insert({
          employee_id: params.id,
          date: selectedDate ? format(selectedDate.toDate(), 'yyyy-MM-dd') : '',
          start_time: format(values.start_time.toDate(), 'HH:mm'),
          end_time: format(values.end_time.toDate(), 'HH:mm'),
          type: values.type,
          status: 'scheduled',
        });

      if (error) throw error;
      message.success('일정이 등록되었습니다.');
      setModalVisible(false);
      form.resetFields();
      fetchSchedules();
    } catch (error) {
      message.error('일정 등록에 실패했습니다.');
    } finally {
      setLoading(false);
    }
  };

  const dateCellRender = (date: any) => {
    const daySchedules = schedules.filter(
      schedule => schedule.date === format(date.toDate(), 'yyyy-MM-dd')
    );

    return (
      <ul className="events">
        {daySchedules.map(schedule => (
          <li key={schedule.id}>
            <Badge
              status={
                schedule.type === 'regular'
                  ? 'success'
                  : schedule.type === 'overtime'
                  ? 'warning'
                  : 'error'
              }
              text={`${schedule.start_time} - ${schedule.end_time}`}
            />
          </li>
        ))}
      </ul>
    );
  };

  return (
    <div className="container mx-auto p-4">
      <Card
        title="근무 일정"
        extra={
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => setModalVisible(true)}
          >
            일정 추가
          </Button>
        }
      >
        <Calendar
          dateCellRender={dateCellRender}
          onSelect={handleDateSelect}
          loading={loading}
        />
      </Card>

      <Modal
        title="근무 일정 등록"
        open={modalVisible}
        onCancel={() => setModalVisible(false)}
        footer={null}
      >
        <Form form={form} onFinish={handleScheduleSubmit} layout="vertical">
          <Form.Item
            name="type"
            label="근무 유형"
            rules={[{ required: true, message: '근무 유형을 선택해주세요' }]}
          >
            <Select placeholder="근무 유형 선택">
              <Option value="regular">정규 근무</Option>
              <Option value="overtime">초과 근무</Option>
              <Option value="holiday">휴일 근무</Option>
            </Select>
          </Form.Item>

          <Form.Item
            name="start_time"
            label="시작 시간"
            rules={[{ required: true, message: '시작 시간을 선택해주세요' }]}
          >
            <TimePicker format="HH:mm" />
          </Form.Item>

          <Form.Item
            name="end_time"
            label="종료 시간"
            rules={[{ required: true, message: '종료 시간을 선택해주세요' }]}
          >
            <TimePicker format="HH:mm" />
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