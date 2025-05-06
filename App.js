import React, { useState, useEffect } from 'react';
import { Button, Text, View, StyleSheet, Alert } from 'react-native';
import * as Location from 'expo-location';
import AsyncStorage from '@react-native-async-storage/async-storage';

// 서버 URL 설정 - 실제 컴퓨터 IP로 변경 필요
const SERVER_URL = 'http://192.168.0.1:5000'; // 예: 'http://192.168.0.100:5000'

export default function App() {
  const [location, setLocation] = useState(null);
  const [errorMsg, setErrorMsg] = useState(null);
  const [user, setUser] = useState(null);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    // 사용자 정보 로드
    loadUserData();
  }, []);

  const loadUserData = async () => {
    try {
      const storedUser = await AsyncStorage.getItem('user');
      if (storedUser) {
        setUser(JSON.parse(storedUser));
      } else {
        // 테스트용 사용자 데이터
        const testUser = {
          id: 'staff01',
          name: '홍길동',
          store: '강남점'
        };
        await AsyncStorage.setItem('user', JSON.stringify(testUser));
        setUser(testUser);
      }
    } catch (error) {
      console.error('사용자 정보 로드 실패:', error);
    }
  };

  const handleAttendance = async (action) => {
    if (isLoading) return;
    setIsLoading(true);

    try {
      // 위치 권한 요청
      let { status } = await Location.requestForegroundPermissionsAsync();
      if (status !== 'granted') {
        setErrorMsg('위치 권한이 거부되었습니다.');
        Alert.alert('오류', '위치 권한이 필요합니다.');
        return;
      }

      // 현재 위치 가져오기
      let loc = await Location.getCurrentPositionAsync({
        accuracy: Location.Accuracy.High
      });
      setLocation(loc);

      // 출퇴근 기록 데이터
      const data = {
        id: user.id,
        name: user.name,
        store: user.store,
        action: action,
        latitude: loc.coords.latitude,
        longitude: loc.coords.longitude
      };

      // 서버로 전송
      const response = await fetch(`${SERVER_URL}/attendance`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data)
      });

      if (!response.ok) {
        throw new Error('서버 응답 오류');
      }

      const result = await response.json();
      
      // 성공 메시지 (주소 정보 포함)
      Alert.alert(
        '기록 완료',
        `${action}이 완료되었습니다.\n위치: ${result.address}`,
        [{ text: '확인' }]
      );
    } catch (error) {
      console.error('출퇴근 기록 실패:', error);
      Alert.alert('오류', '서버에 연결할 수 없습니다');
    } finally {
      setIsLoading(false);
    }
  };

  if (!user) {
    return (
      <View style={styles.container}>
        <Text>사용자 정보를 불러오는 중...</Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <Text style={styles.title}>{user.name}님 출퇴근 관리</Text>
      <Text style={styles.subtitle}>매장: {user.store}</Text>
      
      <View style={styles.buttonContainer}>
        <Button 
          title={isLoading ? "처리 중..." : "출근"} 
          onPress={() => handleAttendance("출근")}
          color="#4CAF50"
          disabled={isLoading}
        />
        <View style={styles.buttonSpacer} />
        <Button 
          title={isLoading ? "처리 중..." : "퇴근"} 
          onPress={() => handleAttendance("퇴근")}
          color="#f44336"
          disabled={isLoading}
        />
      </View>

      {errorMsg && (
        <Text style={styles.errorText}>{errorMsg}</Text>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
    backgroundColor: '#f5f5f5',
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    marginBottom: 10,
  },
  subtitle: {
    fontSize: 16,
    color: '#666',
    marginBottom: 30,
  },
  buttonContainer: {
    width: '100%',
    maxWidth: 300,
  },
  buttonSpacer: {
    height: 10,
  },
  errorText: {
    color: 'red',
    marginTop: 20,
  }
}); 