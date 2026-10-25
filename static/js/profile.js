// Profile functionality
// Set print date when page loads
document.addEventListener('DOMContentLoaded', function() {
    const now = new Date();
    const printDate = now.toLocaleDateString() + ' ' + now.toLocaleTimeString();
    document.body.setAttribute('data-print-date', printDate);
});

// Print functionality
function printProfile() {
    window.print();
}

// PDF Download functionality
async function downloadPDF() {
    try {
        console.log('PDF download started');
        
        // Check if required libraries are loaded
        if (typeof html2canvas === 'undefined') {
            console.error('html2canvas not loaded');
            showNotification('PDF library not loaded. Please refresh the page.', 'error');
            return;
        }
        
        if (typeof window.jspdf === 'undefined') {
            console.error('jsPDF not loaded');
            showNotification('PDF library not loaded. Please refresh the page.', 'error');
            return;
        }
        
        // Show loading state
        const downloadBtn = document.querySelector('.download-btn');
        if (!downloadBtn) {
            console.error('Download button not found');
            showNotification('Download button not found.', 'error');
            return;
        }
        
        const originalText = downloadBtn.innerHTML;
        downloadBtn.innerHTML = '<svg class="icon" aria-hidden="true"><use href="#i-refresh"></use></svg> Generating...';
        downloadBtn.disabled = true;

        // Get the profile container
        const profileContainer = document.querySelector('.profile-container');
        if (!profileContainer) {
            console.error('Profile container not found');
            showNotification('Profile content not found.', 'error');
            return;
        }
        
        console.log('Profile container found:', profileContainer);
        
        // Create a clone of the profile container for PDF generation
        const clone = profileContainer.cloneNode(true);
        
        // Remove interactive elements from clone
        const actionsDiv = clone.querySelector('.profile-actions');
        if (actionsDiv) {
            actionsDiv.remove();
        }
        
        // Style the clone for PDF
        clone.style.width = '800px';
        clone.style.padding = '20px';
        clone.style.backgroundColor = 'white';
        clone.style.boxShadow = 'none';
        clone.style.position = 'absolute';
        clone.style.left = '-9999px';
        clone.style.top = '0';
        
        // Append clone to body temporarily
        document.body.appendChild(clone);
        
        // Configure html2canvas options
        const canvas = await html2canvas(clone, {
            scale: 2,
            useCORS: true,
            logging: false,
            backgroundColor: '#ffffff',
            windowWidth: 800
        });
        
        // Remove the clone
        document.body.removeChild(clone);
        
        // Create PDF
        const { jsPDF } = window.jspdf;
        const pdf = new jsPDF('p', 'mm', 'a4');
        
        const imgWidth = 210; // A4 width in mm
        const pageHeight = 295; // A4 height in mm
        const imgHeight = (canvas.height * imgWidth) / canvas.width;
        let heightLeft = imgHeight;
        let position = 0;
        
        // Add image to PDF
        pdf.addImage(canvas.toDataURL('image/png'), 'PNG', 0, position, imgWidth, imgHeight);
        heightLeft -= pageHeight;
        
        // Add additional pages if content is long
        while (heightLeft >= 0) {
            position = heightLeft - imgHeight;
            pdf.addPage();
            pdf.addImage(canvas.toDataURL('image/png'), 'PNG', 0, position, imgWidth, imgHeight);
            heightLeft -= pageHeight;
        }
        
        // Generate filename
        const username = document.querySelector('.profile-title')?.textContent?.trim() || 'user';
        const date = new Date().toISOString().split('T')[0];
        const filename = `${username}_profile_${date}.pdf`;
        
        // Save PDF
        pdf.save(filename);
        
        // Show success message
        showNotification('PDF downloaded successfully!', 'success');
        
    } catch (error) {
        console.error('Error generating PDF:', error);
        showNotification('Error generating PDF: ' + error.message, 'error');
    } finally {
        // Restore button state
        const downloadBtn = document.querySelector('.download-btn');
        if (downloadBtn) {
            downloadBtn.innerHTML = '<svg class="icon" aria-hidden="true"><use href="#i-download"></use></svg> Download PDF';
            downloadBtn.disabled = false;
        }
    }
}

// Show notification message
function showNotification(message, type = 'info') {
    // Remove any existing notifications
    const existingNotifications = document.querySelectorAll('.pdf-notification');
    existingNotifications.forEach(notification => notification.remove());
    
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `alert alert-${type} pdf-notification`;
    notification.style.position = 'fixed';
    notification.style.top = '20px';
    notification.style.right = '20px';
    notification.style.zIndex = '9999';
    notification.style.maxWidth = '400px';
    const iconName = type === 'success' ? 'i-check' : (type === 'error' ? 'i-alert' : 'i-help');
    notification.innerHTML = `
        <span class="alert-icon" aria-hidden="true"><svg class="icon"><use href="#${iconName}"></use></svg></span>
        <span class="alert-text">${message}</span>
        <button type="button" class="alert-close" aria-label="Dismiss message" onclick="this.closest('.pdf-notification').remove()">
            <svg class="icon" aria-hidden="true"><use href="#i-close"></use></svg>
        </button>
    `;
    
    document.body.appendChild(notification);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (notification.parentElement) {
            notification.remove();
        }
    }, 5000);
}

// Add print-specific CSS
const printStyles = `
@media print {
    body * {
        visibility: hidden;
    }
    .profile-container, .profile-container * {
        visibility: visible;
    }
    .profile-container {
        position: absolute;
        left: 0;
        top: 0;
        width: 100%;
        box-shadow: none;
        margin: 0;
        padding: 20px;
    }
    .print-btn, .download-btn {
        display: none !important;
    }
    .profile-header {
        border-bottom: 2px solid #000;
    }
    .kit-card {
        break-inside: avoid;
        page-break-inside: avoid;
    }
    .kits-grid {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 15px;
    }
    .profile-content {
        grid-template-columns: 1fr 1fr;
        gap: 30px;
    }
}
`;

// Add print styles to head
const styleSheet = document.createElement('style');
styleSheet.textContent = printStyles;
document.head.appendChild(styleSheet);
