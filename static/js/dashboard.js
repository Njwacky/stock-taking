// Global variables for dashboard functionality
let currentParams = {
    user: '',
    search: '',
    sort: 'timestamp',
    order: 'desc',
    page: '1'
};

// Carousel functionality for Why Register section
let currentSlideIndex = 0;
let carouselAutoAdvanceInterval;
let totalSlides = 3; // Total number of slides (each shows 2 cards)
const cardsPerSlide = 2; // Number of cards per slide
const totalCards = 6; // Total number of register cards

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Keep filter controls and pagination in sync with a bookmarked/shared URL.
    const initialParams = new URLSearchParams(window.location.search);
    currentParams.user = initialParams.get('user') || '';
    currentParams.search = initialParams.get('search') || '';
    currentParams.sort = initialParams.get('sort') || 'timestamp';
    currentParams.order = initialParams.get('order') || 'desc';
    currentParams.page = initialParams.get('page') || '1';

    // Initialize selection display
    updateSelection();
    
    // Add event listeners for checkboxes
    const checkboxes = document.querySelectorAll('.kit-checkbox');
    checkboxes.forEach(checkbox => {
        checkbox.addEventListener('change', updateSelection);
    });
    
    // Bind select-all checkbox
    const selectAllCheckbox = document.getElementById('select-all');
    if (selectAllCheckbox) {
        selectAllCheckbox.addEventListener('change', toggleSelectAll);
    }
    
    // Bind filter form to use AJAX instead of full page reload
    const filterForm = document.getElementById('filter-form');
    if (filterForm) {
        filterForm.addEventListener('submit', loadDashboardData);
    }

    // Confirm bulk deletion and prevent an empty submission.
    const bulkDeleteForm = document.getElementById('bulk-delete-form');
    if (bulkDeleteForm) {
        bulkDeleteForm.addEventListener('submit', function(event) {
            const count = document.querySelectorAll('.kit-checkbox:checked').length;
            if (count === 0) {
                event.preventDefault();
                window.alert('Select at least one stock item first.');
                return;
            }
            if (!window.confirm(`Delete ${count} selected stock item(s)? This cannot be undone.`)) {
                event.preventDefault();
            }
        });
    }
    
    // Initialize pie chart if user is authenticated and data exists
    initializePieChart();
    
    // Initialize carousel if it exists on the page
    initializeCarousel();
    
    // Keep pagination working after AJAX replaces its links.
    const paginationContainer = document.getElementById('pagination-container');
    if (paginationContainer) {
        paginationContainer.addEventListener('click', function(event) {
            const link = event.target.closest('.page-link');
            if (!link) {
                return;
            }
            event.preventDefault();
            loadPage(link.dataset.page);
        });
    }

    // Restore the visible controls and table when navigating browser history.
    window.addEventListener('popstate', function(event) {
        const url = event.state && event.state.path
            ? new URL(event.state.path, window.location.origin)
            : new URL(window.location.href);
        const params = new URLSearchParams(url.search);
        currentParams.user = params.get('user') || '';
        currentParams.search = params.get('search') || '';
        currentParams.sort = params.get('sort') || 'timestamp';
        currentParams.order = params.get('order') || 'desc';
        currentParams.page = params.get('page') || '1';
        syncFilterControlsFromParams();
        fetchDashboardData(false);
    });
});

// Initialize carousel functionality
function initializeCarousel() {
    const carouselTrack = document.querySelector('.why-register-cards');
    const dots = document.querySelectorAll('.dot');
    
    if (carouselTrack && dots.length > 0) {
        // Start auto-advance
        startCarouselAutoAdvance();
        
        // Pause auto-advance on hover
        const carouselContainer = document.querySelector('.carousel-container');
        if (carouselContainer) {
            carouselContainer.addEventListener('mouseenter', stopCarouselAutoAdvance);
            carouselContainer.addEventListener('mouseleave', startCarouselAutoAdvance);
        }
    }
}

// Move carousel in specified direction
function moveCarousel(direction) {
    const totalSlides = 3; // Total number of slides
    
    currentSlideIndex += direction;
    
    // Wrap around at the ends
    if (currentSlideIndex >= totalSlides) {
        currentSlideIndex = 0;
    } else if (currentSlideIndex < 0) {
        currentSlideIndex = totalSlides - 1;
    }
    
    updateCarousel();
}

// Go to specific slide
function currentSlide(slideIndex) {
    currentSlideIndex = slideIndex - 1; // Convert to 0-based index
    updateCarousel();
}

// Handle keyboard events for carousel dots
function handleDotKeydown(event, slideIndex) {
    // Check if Enter or Space key was pressed
    if (event.key === 'Enter' || event.key === ' ' || event.key === 'Spacebar') {
        event.preventDefault(); // Prevent default behavior (like scrolling for space)
        currentSlide(slideIndex); // Navigate to the slide
    }
}

// Update carousel position and dots
function updateCarousel() {
    const carouselTrack = document.querySelector('.why-register-cards');
    const dots = document.querySelectorAll('.dot');
    
    if (carouselTrack) {
        // Calculate the translateX value
        const cardWidth = 220; // Card width (200px) + gap (20px)
        const translateX = -(currentSlideIndex * cardWidth * cardsPerSlide);
        carouselTrack.style.transform = `translateX(${translateX}px)`;
    }
    
    // Update active dot
    dots.forEach((dot, index) => {
        dot.classList.remove('active');
        if (index === currentSlideIndex) {
            dot.classList.add('active');
        }
    });
}

// Start auto-advance functionality
function startCarouselAutoAdvance() {
    // Clear any existing interval
    stopCarouselAutoAdvance();
    
    // Set new interval for auto-advance (5 seconds)
    carouselAutoAdvanceInterval = setInterval(() => {
        moveCarousel(1);
    }, 5000);
}

// Stop auto-advance functionality
function stopCarouselAutoAdvance() {
    if (carouselAutoAdvanceInterval) {
        clearInterval(carouselAutoAdvanceInterval);
        carouselAutoAdvanceInterval = null;
    }
}

// Update selection count and show/hide bulk actions
function updateSelection() {
    const checkboxes = document.querySelectorAll('.kit-checkbox');
    const checkedBoxes = document.querySelectorAll('.kit-checkbox:checked');
    const count = checkedBoxes.length;
    
    // Update both sticky and regular bulk action counters
    const stickyCountElement = document.getElementById('sticky-selected-count');
    const regularCountElement = document.getElementById('selected-count');
    
    if (stickyCountElement) {
        stickyCountElement.textContent = count;
    }
    
    if (regularCountElement) {
        regularCountElement.textContent = count;
    }
    
    // Show/hide bulk action bars based on selection
    const stickyBulkActionsBar = document.getElementById('sticky-bulk-actions-bar');
    const regularBulkActionsBar = document.getElementById('bulk-actions-bar');
    
    if (count > 0) {
        if (stickyBulkActionsBar) {
            stickyBulkActionsBar.style.display = 'flex';
        }
        if (regularBulkActionsBar) {
            regularBulkActionsBar.style.display = 'flex';
        }
    } else {
        if (stickyBulkActionsBar) {
            stickyBulkActionsBar.style.display = 'none';
        }
        if (regularBulkActionsBar) {
            regularBulkActionsBar.style.display = 'none';
        }
    }
    
    // Update select-all checkbox state
    const selectAllCheckbox = document.getElementById('select-all');
    if (selectAllCheckbox) {
        if (count === 0) {
            selectAllCheckbox.indeterminate = false;
            selectAllCheckbox.checked = false;
        } else if (count === checkboxes.length) {
            selectAllCheckbox.indeterminate = false;
            selectAllCheckbox.checked = true;
        } else {
            selectAllCheckbox.indeterminate = true;
        }
    }
}

// Toggle select all checkboxes
function toggleSelectAll() {
    const selectAllCheckbox = document.getElementById('select-all');
    const checkboxes = document.querySelectorAll('.kit-checkbox');
    
    checkboxes.forEach(checkbox => {
        checkbox.checked = selectAllCheckbox.checked;
    });
    
    updateSelection();
}

// Clear selection and hide bulk actions
function clearSelection() {
    const checkboxes = document.querySelectorAll('.kit-checkbox');
    const selectAllCheckbox = document.getElementById('select-all');
    
    checkboxes.forEach(checkbox => {
        checkbox.checked = false;
    });
    
    if (selectAllCheckbox) {
        selectAllCheckbox.checked = false;
        selectAllCheckbox.indeterminate = false;
    }
    
    updateSelection();
}

// Submit bulk delete form
function submitBulkDelete() {
    const form = document.getElementById('bulk-delete-form');
    const checkedBoxes = document.querySelectorAll('.kit-checkbox:checked');
    
    if (checkedBoxes.length === 0) {
        alert('Please select at least one kit to delete.');
        return;
    }
    
    if (confirm(`Are you sure you want to delete ${checkedBoxes.length} selected kit(s)?`)) {
        form.submit();
    }
}

// Load dashboard data with AJAX
function loadDashboardData(event) {
    if (event) {
        event.preventDefault();
    }
    
    const form = document.getElementById('filter-form');
    const formData = new FormData(form);
    
    // Update every control before fetching so search, sort, order and user
    // filters work together and remain reflected in the URL.
    currentParams.user = formData.get('user') || '';
    currentParams.search = formData.get('search') || '';
    currentParams.sort = formData.get('sort') || 'timestamp';
    currentParams.order = formData.get('order') || 'desc';
    currentParams.page = '1';
    
    fetchDashboardData();
}

// Load sorted data
function loadSortData(sortBy, currentOrder) {
    currentParams.sort = sortBy;
    currentParams.order = currentOrder === 'desc' ? 'asc' : 'desc';
    currentParams.page = '1';
    
    fetchDashboardData();
}

// Load specific page
function loadPage(pageNumber) {
    currentParams.page = pageNumber.toString();
    fetchDashboardData();
}

function syncFilterControlsFromParams() {
    const form = document.getElementById('filter-form');
    if (!form) {
        return;
    }
    ['user', 'search', 'sort', 'order'].forEach(name => {
        const control = form.elements.namedItem(name);
        if (control) {
            control.value = currentParams[name] || (name === 'sort' ? 'timestamp' : name === 'order' ? 'desc' : '');
        }
    });
}

// Fetch dashboard data via AJAX. History restoration fetches without adding a
// second history entry so the browser's Back and Forward buttons keep working.
function fetchDashboardData(pushHistory = true) {
    const queryString = new URLSearchParams(currentParams).toString();
    const url = `${window.location.pathname}?${queryString}`;
    
    // Show loading indicator
    showLoading();
    
    // Update browser history for a new user action only.
    if (pushHistory) {
        history.pushState({ path: url }, '', url);
    }
    
    // Make AJAX request to fetch new data
    fetch(url, {
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'Accept': 'application/json'
        }
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            // Update the table content
            updateTableContent(data.table_html);
            
            // Update pagination
            updatePagination(data.pagination_html);
            
            // Update pie chart if data exists
            if (data.kit_stats) {
                updatePieChart(data.kit_stats);
            }
            
            // Update selection management
            updateSelection();
        } else {
            // If there's an error, fall back to full page reload
            window.location.href = url;
        }
    })
    .catch(error => {
        console.error('AJAX request failed:', error);
        // Fall back to full page reload on error
        window.location.href = url;
    })
    .finally(() => {
        hideLoading();
    });
}

// Show loading indicator
function showLoading() {
    // Create loading overlay if it doesn't exist
    if (!document.getElementById('loading-overlay')) {
        const loadingOverlay = document.createElement('div');
        loadingOverlay.id = 'loading-overlay';
        loadingOverlay.setAttribute('role', 'status');
        loadingOverlay.setAttribute('aria-live', 'polite');
        loadingOverlay.innerHTML = `
            <div class="loading-spinner">
                <i class="fa fa-spinner fa-spin" aria-hidden="true"></i>
                <span>Loading stock items…</span>
            </div>
        `;
        document.body.appendChild(loadingOverlay);
    }
    document.getElementById('loading-overlay').style.display = 'flex';
}

// Hide loading indicator
function hideLoading() {
    const loadingOverlay = document.getElementById('loading-overlay');
    if (loadingOverlay) {
        loadingOverlay.style.display = 'none';
    }
}

// Update table content with new HTML
function updateTableContent(tableHTML) {
    const tableContainer = document.getElementById('table-container');
    if (tableContainer && tableHTML) {
        tableContainer.innerHTML = tableHTML;
        
        // Re-attach event listeners to new checkboxes
        const checkboxes = document.querySelectorAll('.kit-checkbox');
        checkboxes.forEach(checkbox => {
            checkbox.addEventListener('change', updateSelection);
        });
        
        // Re-attach event listener to select-all checkbox
        const selectAllCheckbox = document.getElementById('select-all');
        if (selectAllCheckbox) {
            selectAllCheckbox.addEventListener('change', toggleSelectAll);
        }
    }
}

// Update pagination with new HTML. The container uses delegated click handling,
// so links continue to work even after their markup is replaced.
function updatePagination(paginationHTML) {
    const paginationContainer = document.getElementById('pagination-container');
    if (paginationContainer) {
        paginationContainer.innerHTML = paginationHTML || '';
    }
}

// Update pie chart with new data
function updatePieChart(kitStatsData) {
    const chartDataElement = document.getElementById('kitStatsData');
    if (chartDataElement && kitStatsData) {
        // Update the hidden JSON data
        chartDataElement.textContent = JSON.stringify(kitStatsData);
        
        // Re-initialize the pie chart
        const chartCanvas = document.getElementById('kitsPieChart');
        if (chartCanvas) {
            // Destroy existing chart instance if it exists
            const existingChart = Chart.getChart(chartCanvas);
            if (existingChart) {
                existingChart.destroy();
            }
            
            // Re-initialize the chart
            initializePieChart();
        }
    }
}

// Initialize pie chart for most received kits
function initializePieChart() {
    const chartCanvas = document.getElementById('kitsPieChart');
    const chartDataElement = document.getElementById('kitStatsData');
    
    if (!chartCanvas || !chartDataElement) {
        return;
    }
    
    try {
        // Parse the JSON data from the hidden div
        const chartData = JSON.parse(chartDataElement.textContent);
        
        if (!chartData || chartData.length === 0) {
            // Hide the chart section if no data
            const statsContainer = document.querySelector('.dashboard-stats');
            if (statsContainer) {
                statsContainer.style.display = 'none';
            }
            return;
        }
        
        // Prepare data for Chart.js
        const labels = chartData.map(item => item.kit_type || 'Unknown');
        const data = chartData.map(item => item.total_quantity || 0);
        
        // Generate colors for the pie chart
        const colors = [
            '#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', 
            '#9966FF', '#FF9F40', '#FF6384', '#C9CBCF',
            '#4BC0C0', '#FF6384', '#36A2EB', '#FFCE56'
        ];
        
        const backgroundColors = data.map((_, index) => colors[index % colors.length]);
        
        // Create the pie chart
        const ctx = chartCanvas.getContext('2d');
        new Chart(ctx, {
            type: 'pie',
            data: {
                labels: labels,
                datasets: [{
                    data: data,
                    backgroundColor: backgroundColors,
                    borderColor: '#ffffff',
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false // Hide the built-in Chart.js legend with round dots
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const label = context.label || '';
                                const value = context.parsed || 0;
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const percentage = ((value / total) * 100).toFixed(1);
                                return `${label}: ${value} (${percentage}%)`;
                            }
                        }
                    }
                }
            }
        });
        
        // Generate custom legend if needed
        generateChartLegend(chartData, colors);
        
    } catch (error) {
        console.error('Error initializing pie chart:', error);
        // Hide the chart section if there's an error
        const statsContainer = document.querySelector('.dashboard-stats');
        if (statsContainer) {
            statsContainer.style.display = 'none';
        }
    }
}

// Generate an accessible legend without inserting kit type names as HTML.
function generateChartLegend(chartData, colors) {
    const legendContainer = document.getElementById('chartLegend');
    if (!legendContainer || !chartData || chartData.length === 0) {
        return;
    }

    const total = chartData.reduce((sum, item) => sum + (Number(item.total_quantity) || 0), 0);
    const list = document.createElement('div');
    list.className = 'chart-legend-container';
    list.setAttribute('role', 'list');

    chartData.forEach((item, index) => {
        const quantity = Number(item.total_quantity) || 0;
        const userCount = Number(item.user_count) || 0;
        const percentage = total > 0 ? ((quantity / total) * 100).toFixed(1) : '0.0';
        const color = colors[index % colors.length];

        const legendItem = document.createElement('div');
        legendItem.className = 'legend-item';
        legendItem.setAttribute('role', 'listitem');

        const swatch = document.createElement('div');
        swatch.className = 'legend-color';
        swatch.style.backgroundColor = color;
        swatch.setAttribute('aria-hidden', 'true');

        const info = document.createElement('div');
        info.className = 'legend-info';

        const label = document.createElement('div');
        label.className = 'legend-label';
        label.textContent = item.kit_type || 'Unknown';

        const stats = document.createElement('div');
        stats.className = 'legend-stats';
        const unitLabel = quantity === 1 ? 'unit' : 'units';
        const userLabel = userCount === 1 ? 'user' : 'users';
        stats.textContent = `${quantity.toLocaleString()} ${unitLabel} (${percentage}%) · ${userCount.toLocaleString()} ${userLabel}`;

        info.append(label, stats);
        legendItem.append(swatch, info);
        list.appendChild(legendItem);
    });

    legendContainer.replaceChildren(list);
}
