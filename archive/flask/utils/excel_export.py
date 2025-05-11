import pandas as pd
from io import BytesIO
from datetime import datetime

def export_stock_usage_to_excel(transactions):
    """재고 사용 내역을 엑셀 파일로 내보내기"""
    try:
        # 데이터프레임 생성
        data = []
        for trans in transactions:
            data.append({
                '날짜': trans.created_at.strftime('%Y-%m-%d %H:%M'),
                '식자재': trans.ingredient.name,
                '사용량': abs(trans.quantity),
                '단위': trans.ingredient.unit,
                '요청자': trans.created_by_user.name,
                '메모': trans.notes or '',
                '상태': {
                    'pending': '승인 대기',
                    'approved': '승인됨',
                    'rejected': '거절됨'
                }.get(trans.status, trans.status),
                '처리일시': trans.approved_at.strftime('%Y-%m-%d %H:%M') if trans.approved_at else '',
                '거절사유': trans.rejection_reason or ''
            })
            
        df = pd.DataFrame(data)
        
        # 엑셀 파일 생성
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, sheet_name='재고사용내역', index=False)
            
            # 워크시트 가져오기
            worksheet = writer.sheets['재고사용내역']
            
            # 열 너비 조정
            worksheet.set_column('A:A', 20)  # 날짜
            worksheet.set_column('B:B', 20)  # 식자재
            worksheet.set_column('C:C', 15)  # 사용량
            worksheet.set_column('D:D', 10)  # 단위
            worksheet.set_column('E:E', 15)  # 요청자
            worksheet.set_column('F:F', 30)  # 메모
            worksheet.set_column('G:G', 15)  # 상태
            worksheet.set_column('H:H', 20)  # 처리일시
            worksheet.set_column('I:I', 30)  # 거절사유
            
        output.seek(0)
        return output
        
    except Exception as e:
        print(f"엑셀 파일 생성 중 오류 발생: {str(e)}")
        return None 