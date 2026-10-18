// Floating Comment Button Functionality
document.addEventListener('DOMContentLoaded', function() {
    const floatingBtn = document.getElementById('floatingCommentBtn');
    const floatingPanel = document.getElementById('floatingCommentPanel');
    const closeBtn = document.getElementById('floatingPanelClose');
    const tabs = document.querySelectorAll('.floating-tab');
    const tabContents = document.querySelectorAll('.floating-tab-content');

    // Toggle panel visibility
    if (floatingBtn && floatingPanel) {
        floatingBtn.addEventListener('click', function(e) {
            e.stopPropagation();
            floatingPanel.classList.toggle('active');
            
            // Add a small delay to allow the panel to be fully displayed before focusing
            if (floatingPanel.classList.contains('active')) {
                setTimeout(() => {
                    const activeTab = document.querySelector('.floating-tab.active');
                    if (activeTab) {
                        const tabId = activeTab.getAttribute('data-tab') + 'Tab';
                        const activeContent = document.getElementById(tabId);
                        if (activeContent) {
                            const firstInput = activeContent.querySelector('input, textarea, select');
                            if (firstInput) firstInput.focus();
                        }
                    }
                }, 50);
            }
        });
    }

    // Close panel
    if (closeBtn && floatingPanel) {
        closeBtn.addEventListener('click', function(e) {
            e.stopPropagation();
            floatingPanel.classList.remove('active');
        });
    }

    // Close panel when clicking outside
    document.addEventListener('click', function(e) {
        if (floatingPanel && !floatingPanel.contains(e.target) && e.target !== floatingBtn) {
            floatingPanel.classList.remove('active');
        }
    });

    // Tab switching
    tabs.forEach(tab => {
        tab.addEventListener('click', function(e) {
            e.preventDefault();
            
            // Remove active class from all tabs and contents
            tabs.forEach(t => t.classList.remove('active'));
            tabContents.forEach(c => c.classList.remove('active'));
            
            // Add active class to clicked tab and corresponding content
            this.classList.add('active');
            const tabId = this.getAttribute('data-tab') + 'Tab';
            const content = document.getElementById(tabId);
            if (content) {
                content.classList.add('active');
                // Focus first input in the active tab
                const firstInput = content.querySelector('input, textarea, select');
                if (firstInput) firstInput.focus();
            }
        });
    });

    // Handle form submission
    const commentForm = document.getElementById('floatingCommentForm');
    if (commentForm) {
        commentForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const formData = new FormData(this);
            const submitButton = this.querySelector('button[type="submit"]');
            const originalButtonText = submitButton.innerHTML;
            
            // Show loading state
            submitButton.disabled = true;
            submitButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Sending...';
            
            fetch(this.action, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': formData.get('csrfmiddlewaretoken')
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Show success message
                    const successMsg = document.createElement('div');
                    successMsg.className = 'alert alert-success mt-3';
                    successMsg.textContent = data.message || 'Thank you for your feedback!';
                    this.insertBefore(successMsg, this.firstChild);
                    
                    // Reset form
                    this.reset();
                    
                    // Remove success message after 5 seconds
                    setTimeout(() => {
                        successMsg.remove();
                    }, 5000);
                    
                    // If on the "My Feedback" tab, refresh the list
                    const myCommentsTab = document.querySelector('.floating-tab[data-tab="myComments"]');
                    if (myCommentsTab && myCommentsTab.classList.contains('active')) {
                        loadMyComments();
                    }
                } else {
                    // Show error message
                    const errorMsg = document.createElement('div');
                    errorMsg.className = 'alert alert-danger mt-3';
                    errorMsg.textContent = data.message || 'An error occurred. Please try again.';
                    this.insertBefore(errorMsg, this.firstChild);
                    
                    // Remove error message after 5 seconds
                    setTimeout(() => {
                        errorMsg.remove();
                    }, 5000);
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('An error occurred. Please try again.');
            })
            .finally(() => {
                // Reset button state
                submitButton.disabled = false;
                submitButton.innerHTML = originalButtonText;
            });
        });
    }

    // Load user's comments for the "My Feedback" tab
    function loadMyComments() {
        const myCommentsTab = document.getElementById('myCommentsTab');
        if (!myCommentsTab) return;
        
        fetch('/comments/my-comments-json/')
            .then(response => response.json())
            .then(comments => {
                const container = myCommentsTab.querySelector('#userCommentsList');
                if (!container) return;
                
                if (comments.length === 0) {
                    container.innerHTML = '<p class="text-muted">You have not submitted any feedback yet.</p>';
                    return;
                }
                
                container.innerHTML = comments.map(comment => `
                    <div class="comment-item">
                        <div class="comment-header">
                            <strong>${comment.category_display || 'General'}</strong>
                            <span class="text-muted">${new Date(comment.created_at).toLocaleDateString()}</span>
                        </div>
                        <div class="comment-content">${comment.content}</div>
                        ${comment.admin_response ? `
                            <div class="admin-response">
                                <strong>Admin Response:</strong>
                                <p>${comment.admin_response}</p>
                            </div>
                        ` : ''}
                    </div>
                `).join('');
            })
            .catch(error => {
                console.error('Error loading comments:', error);
                const container = myCommentsTab.querySelector('#userCommentsList');
                if (container) {
                    container.innerHTML = '<p class="text-danger">Error loading your feedback. Please try again later.</p>';
                }
            });
    }

    // Load comments when the "My Feedback" tab is clicked
    const myCommentsTabBtn = document.querySelector('.floating-tab[data-tab="myComments"]');
    if (myCommentsTabBtn) {
        myCommentsTabBtn.addEventListener('click', loadMyComments);
    }
});
