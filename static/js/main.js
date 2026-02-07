// Simple Attendance System JavaScript

document.addEventListener('DOMContentLoaded', function() {
    initProgressBars();
    initFileUpload();
    initNotifications();
});

// Animate progress bars
function initProgressBars() {
    const bars = document.querySelectorAll('.progress-fill');
    bars.forEach(bar => {
        const width = bar.style.width;
        bar.style.width = '0%';
        setTimeout(() => bar.style.width = width, 100);
    });
}

// File upload handling
function initFileUpload() {
    const fileInput = document.getElementById('file');
    const fileName = document.getElementById('fileName');
    
    if (fileInput && fileName) {
        fileInput.addEventListener('change', function(e) {
            const file = e.target.files[0];
            fileName.textContent = file ? file.name : 'No file chosen';
            fileName.style.color = file ? '#667eea' : '#666';
        });
    }
}

// Auto-dismiss notifications
function initNotifications() {
    document.querySelectorAll('.alert').forEach(alert => {
        setTimeout(() => {
            alert.style.opacity = '0';
            setTimeout(() => alert.remove(), 300);
        }, 5000);
    });
}
