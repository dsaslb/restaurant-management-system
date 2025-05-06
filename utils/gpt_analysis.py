import openai
import os
from dotenv import load_dotenv
import logging
from datetime import datetime, timedelta
from sqlalchemy import func

# 환경 변수 로드
load_dotenv()

# 로깅 설정
logger = logging.getLogger(__name__)

def analyze_feedback(feedback_list):
    """피드백 분석 및 요약"""
    try:
        # OpenAI API 키 설정
        openai.api_key = os.getenv('OPENAI_API_KEY')
        if not openai.api_key:
            raise ValueError("OpenAI API 키가 설정되지 않았습니다.")

        # 피드백 텍스트 생성
        text = "\n".join([f"- {f.rating}점: {f.comment}" for f in feedback_list])
        
        # 프롬프트 생성
        prompt = f"""
다음은 음식점 직원 근무 피드백입니다:

{text}

이 피드백을 분석하고 다음 형식으로 요약해 주세요:

1. 전체 요약
- 평균 평점
- 주요 키워드
- 전반적인 분위기

2. 긍정적인 피드백
- 자주 언급된 장점
- 특별히 칭찬받은 부분

3. 개선이 필요한 부분
- 자주 지적된 문제점
- 개선 제안

4. 관리자 제안
- 직원 교육 방향
- 운영 개선 방안
"""
        # GPT API 호출
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}]
        )
        
        return {
            'status': 'success',
            'analysis': response.choices[0].message['content']
        }

    except Exception as e:
        logger.error(f"피드백 분석 중 오류 발생: {str(e)}")
        return {
            'status': 'error',
            'message': f'피드백 분석 중 오류가 발생했습니다: {str(e)}'
        }

def analyze_contract_text(contract_text):
    """계약서 분석 및 요약"""
    try:
        # OpenAI API 키 설정
        openai.api_key = os.getenv('OPENAI_API_KEY')
        if not openai.api_key:
            raise ValueError("OpenAI API 키가 설정되지 않았습니다.")

        # 프롬프트 생성
        prompt = f"""
다음은 직원과의 근로 계약서입니다. 주요 내용을 요약해 주세요:

1. 근무 조건
- 근무 기간
- 근무 시간
- 근무 형태 (정규직/계약직/파트타임)
- 근무 장소

2. 급여 조건
- 기본급
- 수당 종류
- 지급일
- 연봉/시급 정보

3. 주의 사항
- 근무 규칙
- 휴가 규정
- 복장 규정
- 기타 주의사항

4. 관리자 유의사항
- 법적 요구사항 준수 여부
- 특이사항
- 리스크 요소

계약서:
{contract_text}
"""
        # GPT API 호출
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}]
        )
        
        return {
            'status': 'success',
            'analysis': response.choices[0].message['content']
        }

    except Exception as e:
        logger.error(f"계약서 분석 중 오류 발생: {str(e)}")
        return {
            'status': 'error',
            'message': f'계약서 분석 중 오류가 발생했습니다: {str(e)}'
        }

def analyze_lateness(attendance_logs):
    """지각 기록 분석 및 개선 제안"""
    try:
        # OpenAI API 키 설정
        openai.api_key = os.getenv('OPENAI_API_KEY')
        if not openai.api_key:
            raise ValueError("OpenAI API 키가 설정되지 않았습니다.")

        # 지각 기록 텍스트 생성
        records = []
        for log in attendance_logs:
            # 지각 시간 계산 (분 단위)
            scheduled_time = datetime.combine(datetime.today(), log.schedule.start_time)
            actual_time = log.clock_in
            lateness_minutes = (actual_time - scheduled_time).total_seconds() / 60
            
            if lateness_minutes >= 10:  # 10분 이상 지각인 경우만 포함
                records.append(
                    f"- {log.user.name} ({log.user_id}): "
                    f"예정 {log.schedule.start_time.strftime('%H:%M')} → "
                    f"실제 {log.clock_in.strftime('%H:%M')} "
                    f"(지각 {int(lateness_minutes)}분)"
                )

        if not records:
            return {
                'status': 'success',
                'analysis': '지각 기록이 없습니다.'
            }

        # 프롬프트 생성
        prompt = f"""
다음은 직원들의 지각 기록입니다 (예정 시간 → 실제 출근 시간):

{chr(10).join(records)}

이 데이터를 분석하고 다음 형식으로 요약해 주세요:

1. 지각 현황 요약
- 총 지각 건수
- 가장 자주 지각하는 직원
- 평균 지각 시간
- 지각 패턴 (요일별, 시간대별)

2. 지각 원인 분석
- 개인별 주요 원인
- 공통적인 원인
- 외부 요인

3. 개선 제안
- 개인별 맞춤형 제안
- 전반적인 개선 방안
- 관리자 조치사항

4. 모범 사례
- 지각이 적은 직원의 특징
- 효과적인 출근 관리 방법
"""
        # GPT API 호출
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}]
        )
        
        return {
            'status': 'success',
            'analysis': response.choices[0].message['content']
        }

    except Exception as e:
        logger.error(f"지각 기록 분석 중 오류 발생: {str(e)}")
        return {
            'status': 'error',
            'message': f'지각 기록 분석 중 오류가 발생했습니다: {str(e)}'
        }

def generate_store_report(data_summary):
    """매장 운영 리포트 자동 생성"""
    try:
        # OpenAI API 키 설정
        openai.api_key = os.getenv('OPENAI_API_KEY')
        if not openai.api_key:
            raise ValueError("OpenAI API 키가 설정되지 않았습니다.")

        # 프롬프트 생성
        prompt = f"""
다음은 매장의 한 달간 운영 데이터 요약입니다:

{data_summary}

이 데이터를 바탕으로 상세한 운영 리포트를 작성해 주세요. 다음 형식으로 작성해 주세요:

1. 인건비 및 근무 현황
- 총 인건비 및 월별 추이
- 주당 평균 근무 시간
- 직원별 근무 시간 분포
- 시간대별 근무 밀도

2. 인력 관리 현황
- 계약 만료 예정 직원 수
- 신규/퇴사 직원 현황
- 직원 만족도 점수
- 주요 피드백 요약

3. 재고 및 운영 현황
- 재고 부족 품목
- 재고 회전율
- 인기 메뉴/품목
- 손실률 및 개선점

4. 서비스 품질 평가
- 고객 피드백 분석
- 직원 서비스 평가
- 주요 칭찬/불만 사항
- 서비스 개선 필요 항목

5. AI 분석 및 개선 제안
- 운영 효율성 분석
- 인력 배치 최적화 방안
- 비용 절감 방안
- 서비스 품질 향상 방안

6. 관리자 권장사항
- 우선 개선 필요 항목
- 단기/중기/장기 목표
- 예산 계획 제안
- 교육/훈련 필요 사항

각 섹션은 구체적인 수치와 함께 작성해 주세요.
"""
        # GPT API 호출
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}]
        )
        
        return {
            'status': 'success',
            'report': response.choices[0].message['content']
        }

    except Exception as e:
        logger.error(f"매장 리포트 생성 중 오류 발생: {str(e)}")
        return {
            'status': 'error',
            'message': f'매장 리포트 생성 중 오류가 발생했습니다: {str(e)}'
        } 