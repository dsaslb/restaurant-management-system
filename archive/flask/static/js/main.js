// 전역 설정
const API_BASE_URL = '/api';

// 공통 유틸리티 함수
const formatDate = (dateString) => {
    if (!dateString) return '';
    const date = new Date(dateString);
    return date.toLocaleDateString('ko-KR', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
    });
};

// API 요청 헬퍼 함수
const apiRequest = async (endpoint, options = {}) => {
    try {
        const response = await fetch(`${API_BASE_URL}${endpoint}`, {
            ...options,
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            }
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.detail || data.error || '요청 처리 중 오류가 발생했습니다.');
        }
        
        return data;
    } catch (error) {
        console.error('API 요청 오류:', error);
        throw error;
    }
};

// 알림 표시 함수
const showNotification = (message, type = 'info') => {
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.textContent = message;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.remove();
    }, 3000);
};

// 페이지 로드 시 실행
document.addEventListener('DOMContentLoaded', () => {
    // CSRF 토큰 설정
    const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content;
    if (csrfToken) {
        window.csrfToken = csrfToken;
    }
    
    // 알림 메시지 표시
    const flashMessage = document.querySelector('.flash-message');
    if (flashMessage) {
        showNotification(flashMessage.textContent, flashMessage.dataset.type);
    }

    // 플래시 메시지 자동 숨김
    const flashMessages = document.querySelectorAll('.alert');
    flashMessages.forEach(function(message) {
        setTimeout(function() {
            message.style.opacity = '0';
            setTimeout(function() {
                message.remove();
            }, 500);
        }, 3000);
    });

    // 테이블 정렬 기능
    const sortableTables = document.querySelectorAll('.table-sortable');
    sortableTables.forEach(function(table) {
        const headers = table.querySelectorAll('th');
        headers.forEach(function(header) {
            header.addEventListener('click', function() {
                const index = Array.from(header.parentElement.children).indexOf(header);
                sortTable(table, index);
            });
        });
    });
});

// 테이블 정렬 함수
function sortTable(table, column) {
    const tbody = table.querySelector('tbody');
    const rows = Array.from(tbody.querySelectorAll('tr'));
    const isNumeric = !isNaN(rows[0].children[column].textContent);

    rows.sort((a, b) => {
        const aValue = a.children[column].textContent;
        const bValue = b.children[column].textContent;

        if (isNumeric) {
            return parseFloat(aValue) - parseFloat(bValue);
        } else {
            return aValue.localeCompare(bValue, 'ko');
        }
    });

    rows.forEach(row => tbody.appendChild(row));
}

// 폼 유효성 검사
function validateForm(formId) {
    const form = document.getElementById(formId);
    if (!form) return true;

    const requiredFields = form.querySelectorAll('[required]');
    let isValid = true;

    requiredFields.forEach(function(field) {
        if (!field.value.trim()) {
            field.classList.add('is-invalid');
            isValid = false;
        } else {
            field.classList.remove('is-invalid');
        }
    });

    return isValid;
}

// 숫자 포맷팅
function formatNumber(number) {
    return new Intl.NumberFormat('ko-KR').format(number);
} 