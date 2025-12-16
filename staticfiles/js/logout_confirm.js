// Logout confirmation functionality
document.addEventListener('DOMContentLoaded', function() {
    const logoutBtn = document.querySelector('.logout-confirm-btn');
    const cancelBtn = document.querySelector('.cancel-logout-btn');
    
    // Add hover effects
    if (logoutBtn) {
        logoutBtn.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-2px)';
        });
        
        logoutBtn.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0)';
        });
    }
    
    if (cancelBtn) {
        cancelBtn.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-2px)';
        });
        
        cancelBtn.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0)';
        });
    }
});
