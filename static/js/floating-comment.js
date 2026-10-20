// Floating Comment Button Functionality
document.addEventListener('DOMContentLoaded', function() {
    const floatingBtn = document.getElementById('floatingCommentBtn');
    const floatingPanel = document.getElementById('floatingCommentPanel');
    const closeBtn = document.getElementById('floatingPanelClose');
    const tabs = document.querySelectorAll('.floating-tab');
    const tabContents = document.querySelectorAll('.floating-tab-content');

    function setPanelOpen(open, restoreFocus = false) {
        if (!floatingPanel || !floatingBtn) return;
        floatingPanel.classList.toggle('active', open);
        floatingPanel.setAttribute('aria-hidden', open ? 'false' : 'true');
        floatingBtn.setAttribute('aria-expanded', open ? 'true' : 'false');
        if (open) {
            const activeContent = floatingPanel.querySelector('.floating-tab-content.active');
            const activeTab = floatingPanel.querySelector('.floating-tab[aria-selected="true"]');
            const firstInput = activeContent && activeContent.querySelector('input, textarea, select');
            const focusTarget = firstInput || activeTab;
            if (focusTarget) setTimeout(() => focusTarget.focus(), 50);
        } else if (restoreFocus) {
            floatingBtn.focus();
        }
    }

    // Toggle the feedback panel and announce its expanded state.
    if (floatingBtn && floatingPanel) {
        floatingBtn.addEventListener('click', function(e) {
            e.stopPropagation();
            setPanelOpen(!floatingPanel.classList.contains('active'));
        });
    }

    if (closeBtn && floatingPanel) {
        closeBtn.addEventListener('click', function(e) {
            e.stopPropagation();
            setPanelOpen(false, true);
        });
    }

    // Dismiss the panel with Escape or a click outside it.
    document.addEventListener('click', function(e) {
        if (floatingPanel && floatingPanel.classList.contains('active') &&
            !floatingPanel.contains(e.target) && e.target !== floatingBtn) {
            setPanelOpen(false);
        }
    });
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && floatingPanel && floatingPanel.classList.contains('active')) {
            setPanelOpen(false, true);
        }
    });

    function activateTab(tab) {
        tabs.forEach(item => {
            const selected = item === tab;
            item.classList.toggle('active', selected);
            item.setAttribute('aria-selected', selected ? 'true' : 'false');
            item.tabIndex = selected ? 0 : -1;
        });
        tabContents.forEach(content => {
            const selected = content.id === tab.getAttribute('aria-controls');
            content.classList.toggle('active', selected);
            content.hidden = !selected;
        });

        const content = document.getElementById(tab.getAttribute('aria-controls'));
        const firstInput = content && content.querySelector('input, textarea, select');
        if (firstInput) firstInput.focus();
    }

    // Keep the tab controls keyboard-operable with the standard arrow keys.
    tabs.forEach((tab, index) => {
        tab.addEventListener('click', function() {
            activateTab(this);
        });
        tab.addEventListener('keydown', function(e) {
            if (!['ArrowLeft', 'ArrowRight', 'Home', 'End'].includes(e.key)) return;
            e.preventDefault();
            let nextIndex = index;
            if (e.key === 'ArrowRight') nextIndex = (index + 1) % tabs.length;
            if (e.key === 'ArrowLeft') nextIndex = (index - 1 + tabs.length) % tabs.length;
            if (e.key === 'Home') nextIndex = 0;
            if (e.key === 'End') nextIndex = tabs.length - 1;
            tabs[nextIndex].focus();
            activateTab(tabs[nextIndex]);
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
            submitButton.innerHTML = '<span class="loading-spinner">Sending…</span>';
            
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
                
                container.replaceChildren();
                if (!Array.isArray(comments) || comments.length === 0) {
                    const emptyMessage = document.createElement('p');
                    emptyMessage.className = 'text-muted';
                    emptyMessage.textContent = 'You have not submitted any feedback yet.';
                    container.appendChild(emptyMessage);
                    return;
                }

                comments.forEach(comment => {
                    const item = document.createElement('article');
                    item.className = 'comment-item';

                    const header = document.createElement('div');
                    header.className = 'comment-header';
                    const subject = document.createElement('strong');
                    subject.textContent = comment.subject || comment.category_display || 'Feedback';
                    const date = document.createElement('span');
                    date.className = 'text-muted';
                    const timestamp = new Date(comment.created_at);
                    date.textContent = Number.isNaN(timestamp.getTime()) ? '' : timestamp.toLocaleDateString();
                    header.append(subject, date);

                    const category = document.createElement('p');
                    category.className = 'text-muted';
                    category.textContent = comment.category_display || 'General';
                    const content = document.createElement('p');
                    content.className = 'comment-content';
                    content.textContent = comment.content || '';
                    item.append(header, category, content);

                    if (comment.admin_response) {
                        const response = document.createElement('div');
                        response.className = 'admin-response';
                        const responseTitle = document.createElement('strong');
                        responseTitle.textContent = 'Admin response';
                        const responseText = document.createElement('p');
                        responseText.textContent = comment.admin_response;
                        response.append(responseTitle, responseText);
                        item.appendChild(response);
                    }
                    container.appendChild(item);
                });
            })
            .catch(error => {
                console.error('Error loading comments:', error);
                const container = myCommentsTab.querySelector('#userCommentsList');
                if (container) {
                    const errorMessage = document.createElement('p');
                    errorMessage.className = 'text-danger';
                    errorMessage.textContent = 'Error loading your feedback. Please try again later.';
                    container.replaceChildren(errorMessage);
                }
            });
    }

    // Load comments when the "My Feedback" tab is clicked
    const myCommentsTabBtn = document.querySelector('.floating-tab[data-tab="myComments"]');
    if (myCommentsTabBtn) {
        myCommentsTabBtn.addEventListener('click', loadMyComments);
    }
});
