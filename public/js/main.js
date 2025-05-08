// API 엔드포인트
const API_ENDPOINTS = {
    employees: '/api/employees',
    inventory: '/api/inventory',
    orders: '/api/orders'
};

// 통계 데이터 가져오기
async function fetchStats() {
    try {
        // 직원 수 가져오기
        const employeeResponse = await fetch(API_ENDPOINTS.employees);
        const employeeData = await employeeResponse.json();
        document.getElementById('employee-count').textContent = employeeData.length;

        // 부족 재고 가져오기
        const inventoryResponse = await fetch(API_ENDPOINTS.inventory);
        const inventoryData = await inventoryResponse.json();
        const lowStock = inventoryData.filter(item => item.current_quantity < item.min_quantity);
        document.getElementById('low-stock-count').textContent = lowStock.length;

        // 대기 중인 발주 가져오기
        const ordersResponse = await fetch(API_ENDPOINTS.orders);
        const ordersData = await ordersResponse.json();
        const pendingOrders = ordersData.filter(order => order.status === 'pending');
        document.getElementById('pending-orders').textContent = pendingOrders.length;
    } catch (error) {
        console.error('데이터를 가져오는 중 오류가 발생했습니다:', error);
    }
}

// 페이지 로드 시 통계 데이터 가져오기
document.addEventListener('DOMContentLoaded', fetchStats);

// 네비게이션 메뉴 활성화
function setActiveNav() {
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('nav a');
    
    navLinks.forEach(link => {
        if (link.getAttribute('href') === currentPath) {
            link.style.color = '#3498db';
            link.style.fontWeight = 'bold';
        }
    });
}

// 페이지 로드 시 네비게이션 메뉴 활성화
document.addEventListener('DOMContentLoaded', setActiveNav); 