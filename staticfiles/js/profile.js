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
        downloadBtn.innerHTML = '<i class="fa fa-spinner fa-spin"></i> Generating...';
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
        
        // Remove buttons from the clone (they don't need to be in PDF)
        const buttons = clone.querySelectorAll('.print-btn, .download-btn');
        buttons.forEach(button => button.remove());
        
        // Add PDF-specific styling
        clone.style.width = '210mm'; // A4 width
        clone.style.margin = '0';
        clone.style.padding = '20mm';
        clone.style.boxShadow = 'none';
        clone.style.background = 'white';
        
        // Create a temporary container for rendering
        const tempContainer = document.createElement('div');
        tempContainer.style.position = 'absolute';
        tempContainer.style.left = '-9999px';
        tempContainer.style.top = '0';
        tempContainer.style.width = '210mm';
        tempContainer.style.background = 'white';
        tempContainer.appendChild(clone);
        
        document.body.appendChild(tempContainer);
        
        console.log('Temporary container created');
        
        // Wait a bit for any dynamic content to load
        await new Promise(resolve => setTimeout(resolve, 1000));
        
        // Generate canvas from HTML
        console.log('Starting html2canvas...');
        const canvas = await html2canvas(clone, {
            scale: 2, // Higher resolution
            useCORS: true,
            allowTaint: true,
            backgroundColor: '#ffffff',
            width: clone.offsetWidth,
            height: clone.offsetHeight,
            logging: true
        });
        
        console.log('Canvas generated:', canvas);
        
        // Remove temporary container
        document.body.removeChild(tempContainer);
        
        // Create PDF
        const { jsPDF } = window.jspdf;
        const pdf = new jsPDF('p', 'mm', 'a4');
        
        const imgData = canvas.toDataURL('image/png');
        const imgWidth = 210; // A4 width in mm
        const pageHeight = 295; // A4 height in mm
        const imgHeight = (canvas.height * imgWidth) / canvas.width;
        let heightLeft = imgHeight;
        
        let position = 0;
        
        // Add first page
        pdf.addImage(imgData, 'PNG', 0, position, imgWidth, imgHeight);
        heightLeft -= pageHeight;
        
        // Add additional pages if needed
        while (heightLeft >= 0) {
            position = heightLeft - imgHeight;
            pdf.addPage();
            pdf.addImage(imgData, 'PNG', 0, position, imgWidth, imgHeight);
            heightLeft -= pageHeight;
        }
        
        // Get profile username for filename - use the current logged-in user if available
        let profileTitle = 'profile';
        try {
            const titleElement = document.querySelector('.profile-title');
            if (titleElement) {
                profileTitle = titleElement.textContent.trim();
            }
            // If it's "My Profile", try to get the actual username
            if (profileTitle === 'My Profile') {
                const usernameElement = document.querySelector('.info-value');
                if (usernameElement && usernameElement.textContent.trim()) {
                    profileTitle = usernameElement.textContent.trim() + '_profile';
                }
            }
        } catch (e) {
            console.log('Could not get profile title, using default');
        }
        
        const sanitizedTitle = profileTitle.replace(/[^a-z0-9]/gi, '_').toLowerCase();
        const timestamp = new Date().toISOString().slice(0, 19).replace(/:/g, '-');
        const filename = `${sanitizedTitle}_${timestamp}.pdf`;
        
        console.log('Saving PDF with filename:', filename);
        
        // Save the PDF
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
            downloadBtn.innerHTML = '<i class="fa fa-download"></i> Download PDF';
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
    notification.innerHTML = `
        <i class="fa fa-${type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-triangle' : 'info-circle'}"></i>
        ${message}
        <button type="button" class="close" onclick="this.parentElement.remove()">
            <span>&times;</span>
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
