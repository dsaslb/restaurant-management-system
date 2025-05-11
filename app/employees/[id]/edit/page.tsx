'use client';

import React, { useState, useEffect } from 'react';
import { Card, Form, Input, Select, DatePicker, Button, Upload, message } from 'antd';
import { UploadOutlined } from '@ant-design/icons';
import { useRouter } from 'next/navigation';
import supabase from '@/lib/supabase';
import type { UploadFile } from 'antd/es/upload/interface';
import type { RcFile } from 'antd/es/upload';
import { format, parseISO } from 'date-fns';

const { Option } = Select;

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

export default function EditEmployeePage({ params }: { params: { id: string } }) {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [fileList, setFileList] = useState<UploadFile[]>([]);
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
      if (data) {
        form.setFieldsValue({
          ...data,
          hire_date: parseISO(data.hire_date),
        });
        if (data.profile_image) {
          setFileList([
            {
              uid: '-1',
              name: 'profile_image',
              status: 'done',
              url: data.profile_image,
            },
          ]);
        }
      }
    } catch (error) {
      message.error('직원 정보를 불러오는데 실패했습니다.');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (values: any) => {
    try {
      setLoading(true);

      let profile_image = values.profile_image;
      if (fileList.length > 0 && fileList[0].originFileObj) {
        const file = fileList[0];
        const fileExt = file.name.split('.').pop();
        const fileName = `${Math.random()}.${fileExt}`;
        const filePath = `profile_images/${fileName}`;

        const { error: uploadError } = await supabase.storage
          .from('employees')
          .upload(filePath, file.originFileObj as RcFile);

        if (uploadError) throw uploadError;

        const { data: { publicUrl } } = supabase.storage
          .from('employees')
          .getPublicUrl(filePath);

        profile_image = publicUrl;
      }

      const { error } = await supabase
        .from('employees')
        .update({
          ...values,
          hire_date: format(values.hire_date, 'yyyy-MM-dd'),
          profile_image,
        })
        .eq('id', params.id);

      if (error) throw error;

      message.success('직원 정보가 수정되었습니다.');
      router.push(`/employees/${params.id}`);
    } catch (error) {
      message.error('직원 정보 수정에 실패했습니다.');
    } finally {
      setLoading(false);
    }
  };

  const beforeUpload = (file: RcFile) => {
    const isImage = file.type.startsWith('image/');
    if (!isImage) {
      message.error('이미지 파일만 업로드할 수 있습니다!');
    }
    const isLt2M = file.size / 1024 / 1024 < 2;
    if (!isLt2M) {
      message.error('이미지 크기는 2MB보다 작아야 합니다!');
    }
    return isImage && isLt2M;
  };

  const handleChange = ({ fileList: newFileList }: { fileList: UploadFile[] }) => {
    setFileList(newFileList);
  };

  return (
    <div className="container mx-auto p-4">
      <Card title="직원 정보 수정">
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSubmit}
        >
          <div className="grid grid-cols-2 gap-4">
            <Form.Item
              name="name"
              label="이름"
              rules={[{ required: true, message: '이름을 입력해주세요' }]}
            >
              <Input />
            </Form.Item>

            <Form.Item
              name="position"
              label="직급"
              rules={[{ required: true, message: '직급을 선택해주세요' }]}
            >
              <Select placeholder="직급 선택">
                <Option value="manager">매니저</Option>
                <Option value="chef">셰프</Option>
                <Option value="server">서버</Option>
                <Option value="host">호스트</Option>
              </Select>
            </Form.Item>

            <Form.Item
              name="department"
              label="부서"
              rules={[{ required: true, message: '부서를 선택해주세요' }]}
            >
              <Select placeholder="부서 선택">
                <Option value="kitchen">주방</Option>
                <Option value="service">서비스</Option>
                <Option value="management">경영</Option>
              </Select>
            </Form.Item>

            <Form.Item
              name="email"
              label="이메일"
              rules={[
                { required: true, message: '이메일을 입력해주세요' },
                { type: 'email', message: '올바른 이메일 형식이 아닙니다' },
              ]}
            >
              <Input />
            </Form.Item>

            <Form.Item
              name="phone"
              label="전화번호"
              rules={[{ required: true, message: '전화번호를 입력해주세요' }]}
            >
              <Input />
            </Form.Item>

            <Form.Item
              name="hire_date"
              label="입사일"
              rules={[{ required: true, message: '입사일을 선택해주세요' }]}
            >
              <DatePicker style={{ width: '100%' }} />
            </Form.Item>

            <Form.Item
              name="status"
              label="상태"
              rules={[{ required: true, message: '상태를 선택해주세요' }]}
            >
              <Select>
                <Option value="active">재직중</Option>
                <Option value="inactive">퇴사</Option>
              </Select>
            </Form.Item>

            <Form.Item
              name="profile_image"
              label="프로필 이미지"
              className="col-span-2"
            >
              <Upload
                listType="picture"
                maxCount={1}
                beforeUpload={beforeUpload}
                onChange={handleChange}
                fileList={fileList}
              >
                <Button icon={<UploadOutlined />}>이미지 업로드</Button>
              </Upload>
            </Form.Item>
          </div>

          <Form.Item className="mt-4">
            <Button type="primary" htmlType="submit" loading={loading}>
              수정
            </Button>
          </Form.Item>
        </Form>
      </Card>
    </div>
  );
} 