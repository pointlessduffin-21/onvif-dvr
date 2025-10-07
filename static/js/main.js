// Main JavaScript for ONVIF Viewer

// Utility Functions
function showAlert(message, type = 'info') {
    const alertHtml = `
        <div class="alert alert-${type} alert-dismissible fade show" role="alert">
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;
    
    const container = $('.container-fluid').first();
    container.prepend(alertHtml);
    
    // Auto dismiss after 5 seconds
    setTimeout(() => {
        $('.alert').fadeOut(300, function() {
            $(this).remove();
        });
    }, 5000);
}

function showLoading() {
    const loadingHtml = `
        <div class="position-fixed top-50 start-50 translate-middle" id="loadingSpinner" style="z-index: 9999;">
            <div class="spinner-border text-primary" role="status" style="width: 3rem; height: 3rem;">
                <span class="visually-hidden">Loading...</span>
            </div>
        </div>
    `;
    $('body').append(loadingHtml);
}

function hideLoading() {
    $('#loadingSpinner').remove();
}

// Format date/time
function formatDateTime(dateString) {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    return date.toLocaleString();
}

// Format duration in seconds to human readable
function formatDuration(seconds) {
    if (!seconds) return 'N/A';
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    
    if (hours > 0) {
        return `${hours}h ${minutes}m ${secs}s`;
    } else if (minutes > 0) {
        return `${minutes}m ${secs}s`;
    } else {
        return `${secs}s`;
    }
}

// Format file size
function formatFileSize(bytes) {
    if (!bytes || bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i];
}

// API Error Handler
function handleApiError(xhr, defaultMessage = 'An error occurred') {
    let errorMessage = defaultMessage;
    
    if (xhr.responseJSON && xhr.responseJSON.error) {
        errorMessage = xhr.responseJSON.error;
    } else if (xhr.statusText) {
        errorMessage = xhr.statusText;
    }
    
    showAlert(errorMessage, 'danger');
    console.error('API Error:', xhr);
}

// Confirm Dialog
function confirmAction(message, callback) {
    if (confirm(message)) {
        callback();
    }
}

// Update Active Navigation Link
function updateActiveNav() {
    const currentPath = window.location.pathname;
    $('.navbar-nav .nav-link').removeClass('active');
    
    $('.navbar-nav .nav-link').each(function() {
        const href = $(this).attr('href');
        if (href === currentPath || (currentPath.startsWith(href) && href !== '/')) {
            $(this).addClass('active');
        }
    });
}

// Initialize tooltips
function initTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

// Initialize popovers
function initPopovers() {
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
}

// WebSocket Connection for Real-time Updates
class ONVIFWebSocket {
    constructor(url) {
        this.url = url;
        this.ws = null;
        this.reconnectInterval = 5000;
        this.handlers = {};
    }
    
    connect() {
        try {
            this.ws = new WebSocket(this.url);
            
            this.ws.onopen = () => {
                console.log('WebSocket connected');
            };
            
            this.ws.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    if (this.handlers[data.type]) {
                        this.handlers[data.type](data);
                    }
                } catch (e) {
                    console.error('WebSocket message error:', e);
                }
            };
            
            this.ws.onclose = () => {
                console.log('WebSocket disconnected, reconnecting...');
                setTimeout(() => this.connect(), this.reconnectInterval);
            };
            
            this.ws.onerror = (error) => {
                console.error('WebSocket error:', error);
            };
        } catch (e) {
            console.error('WebSocket connection error:', e);
        }
    }
    
    on(type, handler) {
        this.handlers[type] = handler;
    }
    
    send(type, data) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify({ type, data }));
        }
    }
    
    disconnect() {
        if (this.ws) {
            this.ws.close();
        }
    }
}

// Camera Status Checker
class CameraStatusChecker {
    constructor(interval = 30000) {
        this.interval = interval;
        this.timerId = null;
    }
    
    start(callback) {
        this.timerId = setInterval(callback, this.interval);
    }
    
    stop() {
        if (this.timerId) {
            clearInterval(this.timerId);
            this.timerId = null;
        }
    }
}

// Local Storage Utilities
const Storage = {
    set: function(key, value) {
        try {
            localStorage.setItem(key, JSON.stringify(value));
        } catch (e) {
            console.error('LocalStorage set error:', e);
        }
    },
    
    get: function(key) {
        try {
            const item = localStorage.getItem(key);
            return item ? JSON.parse(item) : null;
        } catch (e) {
            console.error('LocalStorage get error:', e);
            return null;
        }
    },
    
    remove: function(key) {
        try {
            localStorage.removeItem(key);
        } catch (e) {
            console.error('LocalStorage remove error:', e);
        }
    },
    
    clear: function() {
        try {
            localStorage.clear();
        } catch (e) {
            console.error('LocalStorage clear error:', e);
        }
    }
};

// Initialize on document ready
$(document).ready(function() {
    updateActiveNav();
    initTooltips();
    initPopovers();
    
    // Add CSRF token to all AJAX requests if available
    $.ajaxSetup({
        beforeSend: function(xhr, settings) {
            if (!/^(GET|HEAD|OPTIONS|TRACE)$/i.test(settings.type)) {
                const csrfToken = $('meta[name="csrf-token"]').attr('content');
                if (csrfToken) {
                    xhr.setRequestHeader('X-CSRFToken', csrfToken);
                }
            }
        }
    });
    
    // Handle AJAX errors globally
    $(document).ajaxError(function(event, xhr, settings, error) {
        if (xhr.status === 401) {
            showAlert('Session expired. Please refresh the page.', 'warning');
        } else if (xhr.status === 500) {
            showAlert('Server error occurred. Please try again later.', 'danger');
        }
    });
});

// Export utilities for use in other scripts
window.ONVIFUtils = {
    showAlert,
    showLoading,
    hideLoading,
    formatDateTime,
    formatDuration,
    formatFileSize,
    handleApiError,
    confirmAction,
    Storage,
    ONVIFWebSocket,
    CameraStatusChecker
};
