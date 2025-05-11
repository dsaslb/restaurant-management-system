import requests
from typing import Dict, List, Optional
import logging
from datetime import datetime
from models.inventory import Inventory
from database import db

logger = logging.getLogger(__name__)

class PriceComparator:
    """가격 비교 클래스"""
    
    def __init__(self, api_key: str):
        """
        Args:
            api_key (str): 가격 비교 API 키
        """
        self.api_key = api_key
        self.base_url = "https://api.price-comparison.com/v1"  # 예시 URL
    
    def get_market_prices(self, product_name: str) -> List[Dict]:
        """
        시장 가격을 조회합니다.
        
        Args:
            product_name (str): 제품명
            
        Returns:
            List[Dict]: 시장 가격 목록
        """
        try:
            # API 요청
            headers = {"Authorization": f"Bearer {self.api_key}"}
            params = {"product": product_name}
            
            response = requests.get(
                f"{self.base_url}/prices",
                headers=headers,
                params=params
            )
            response.raise_for_status()
            
            return response.json()['prices']
            
        except Exception as e:
            logger.error(f"시장 가격 조회 중 오류 발생: {str(e)}")
            raise
    
    def compare_prices(self, inventory_id: int) -> Dict:
        """
        현재 가격과 시장 가격을 비교합니다.
        
        Args:
            inventory_id (int): 재고 ID
            
        Returns:
            Dict: 가격 비교 결과
        """
        try:
            # 재고 정보 조회
            inventory = Inventory.query.get_or_404(inventory_id)
            
            # 시장 가격 조회
            market_prices = self.get_market_prices(inventory.name)
            
            # 가격 비교
            current_price = inventory.price
            avg_market_price = sum(p['price'] for p in market_prices) / len(market_prices)
            min_market_price = min(p['price'] for p in market_prices)
            max_market_price = max(p['price'] for p in market_prices)
            
            price_diff = current_price - avg_market_price
            price_diff_percent = (price_diff / avg_market_price) * 100
            
            return {
                'current_price': current_price,
                'market_prices': market_prices,
                'avg_market_price': avg_market_price,
                'min_market_price': min_market_price,
                'max_market_price': max_market_price,
                'price_difference': price_diff,
                'price_difference_percent': price_diff_percent,
                'recommendation': self._get_price_recommendation(price_diff_percent)
            }
            
        except Exception as e:
            logger.error(f"가격 비교 중 오류 발생: {str(e)}")
            raise
    
    def _get_price_recommendation(self, price_diff_percent: float) -> str:
        """
        가격 차이에 따른 추천 사항을 반환합니다.
        
        Args:
            price_diff_percent (float): 가격 차이 비율
            
        Returns:
            str: 추천 사항
        """
        if price_diff_percent > 20:
            return "현재 가격이 시장 평균보다 20% 이상 높습니다. 가격 조정을 고려해보세요."
        elif price_diff_percent < -20:
            return "현재 가격이 시장 평균보다 20% 이상 낮습니다. 수익성을 확인해보세요."
        else:
            return "현재 가격이 시장 평균과 비슷한 수준입니다."
    
    def update_prices(self) -> None:
        """
        모든 재고의 가격을 시장 가격과 비교하고 업데이트합니다.
        """
        try:
            inventories = Inventory.query.all()
            
            for inventory in inventories:
                try:
                    comparison = self.compare_prices(inventory.id)
                    
                    # 가격 차이가 20% 이상인 경우 알림
                    if abs(comparison['price_difference_percent']) >= 20:
                        logger.warning(
                            f"가격 차이 발견: {inventory.name} "
                            f"(현재: {comparison['current_price']}, "
                            f"시장평균: {comparison['avg_market_price']})"
                        )
                        
                        # 가격 업데이트 로그
                        inventory.price_history.append({
                            'date': datetime.utcnow(),
                            'old_price': inventory.price,
                            'new_price': comparison['avg_market_price'],
                            'reason': '시장 가격 조정'
                        })
                        
                        # 가격 업데이트
                        inventory.price = comparison['avg_market_price']
                        db.session.commit()
                        
                except Exception as e:
                    logger.error(f"재고 {inventory.name}의 가격 업데이트 중 오류 발생: {str(e)}")
                    continue
                    
        except Exception as e:
            logger.error(f"가격 업데이트 중 오류 발생: {str(e)}")
            raise 