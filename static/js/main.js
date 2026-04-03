// AttendanceX Main JavaScript

document.addEventListener('DOMContentLoaded', function() {
    initSidebar();
    initClock();
    initTheme();
});

function initTheme() {
    const themeToggle = document.getElementById('themeToggle');
    if (themeToggle) {
        themeToggle.addEventListener('click', function() {
            const currentTheme = document.documentElement.getAttribute('data-theme');
            const newTheme = currentTheme === 'light' ? 'dark' : 'light';
            
            document.documentElement.setAttribute('data-theme', newTheme);
            localStorage.setItem('theme', newTheme);
        });
    }
}

function initSidebar() {
    const sidebar = document.getElementById('sidebar');
    const mainContent = document.getElementById('mainContent');
    const sidebarToggle = document.getElementById('sidebarToggle');
    let backdrop = document.getElementById('sidebarBackdrop');

    if (!backdrop) {
        backdrop = document.createElement('div');
        backdrop.id = 'sidebarBackdrop';
        backdrop.className = 'sidebar-backdrop';
        document.body.appendChild(backdrop);
    }

    const openSidebar = () => {
        sidebar.classList.add('open');
        backdrop.classList.add('open');
    };

    const closeSidebar = () => {
        sidebar.classList.remove('open');
        backdrop.classList.remove('open');
    };

    if (sidebarToggle) {
        sidebarToggle.addEventListener('click', function() {
            if (window.innerWidth <= 768) {
                if (sidebar.classList.contains('open')) {
                    closeSidebar();
                } else {
                    openSidebar();
                }
            } else {
                sidebar.classList.toggle('collapsed');
                mainContent.classList.toggle('expanded');
            }
        });
    }

    backdrop.addEventListener('click', closeSidebar);

    window.addEventListener('resize', function() {
        if (window.innerWidth > 768) {
            closeSidebar();
            sidebar.classList.remove('collapsed');
            mainContent.classList.remove('expanded');
        }
    });
}

function initClock() {
    const timeDisplay = document.getElementById('currentTime');
    if (timeDisplay) {
        updateClock();
        setInterval(updateClock, 1000);
    }
}

function updateClock() {
    const now = new Date();
    const options = {
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        hour12: false
    };
    const timeString = now.toLocaleTimeString('en-US', options);
    const dateString = now.toLocaleDateString('en-US', {
        weekday: 'short',
        month: 'short',
        day: 'numeric',
        year: 'numeric'
    });

    if (document.getElementById('currentTime')) {
        document.getElementById('currentTime').textContent = `${dateString} | ${timeString}`;
    }
}

// API Helper
async function apiRequest(url, method = 'GET', data = null) {
    const options = {
        method,
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        }
    };

    if (data) {
        options.body = JSON.stringify(data);
    }

    try {
        const response = await fetch(url, options);
        const json = await response.json();

        if (!response.ok) {
            throw new Error(json.error || 'Request failed');
        }

        return json;
    } catch (error) {
        throw error;
    }
}

// Cookie helper for CSRF
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Toast notification
function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast-notification toast-${type}`;
    toast.innerHTML = `
        <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-circle' : 'info-circle'}"></i>
        <span>${message}</span>
    `;

    const styles = `
        .toast-notification {
            position: fixed;
            bottom: 30px;
            right: 30px;
            padding: 16px 24px;
            background: var(--glass-bg);
            backdrop-filter: blur(20px);
            border: 1px solid var(--glass-border);
            border-radius: 12px;
            display: flex;
            align-items: center;
            gap: 12px;
            animation: slideIn 0.3s ease;
            z-index: 3000;
        }
        .toast-success { border-color: var(--accent-green); }
        .toast-error { border-color: var(--accent-red); }
        .toast-info { border-color: var(--accent-cyan); }
        .toast-success i { color: var(--accent-green); }
        .toast-error i { color: var(--accent-red); }
        .toast-info i { color: var(--accent-cyan); }
        @keyframes slideIn {
            from { transform: translateX(100%); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
        }
    `;

    if (!document.querySelector('#toast-styles')) {
        const styleSheet = document.createElement('style');
        styleSheet.id = 'toast-styles';
        styleSheet.textContent = styles;
        document.head.appendChild(styleSheet);
    }

    document.body.appendChild(toast);

    setTimeout(() => {
        toast.style.animation = 'slideIn 0.3s ease reverse';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// Format time helper
function formatTime(dateString) {
    if (!dateString) return '-';
    const date = new Date(dateString);
    return date.toLocaleTimeString('en-US', {
        hour: '2-digit',
        minute: '2-digit',
        hour12: false
    });
}

// Format date helper
function formatDate(dateString) {
    if (!dateString) return '-';
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    });
}
