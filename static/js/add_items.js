/* --------------------------------------------------------------------------
   Modal helper
   The kit edit/delete dialogs are opened with a jQuery-style call further down
   this file, but the page does not load jQuery or Bootstrap. This tiny helper
   provides the same `.modal('show' | 'hide')` behaviour using plain DOM APIs.
   -------------------------------------------------------------------------- */
(function () {
    function factory(selector) {
        const element = typeof selector === 'string' ? document.querySelector(selector) : selector;
        return {
            modal(action) {
                if (!element) return this;
                if (action === 'show') {
                    element.style.display = 'flex';
                    element.classList.add('is-open');
                } else if (action === 'hide') {
                    element.style.display = 'none';
                    element.classList.remove('is-open');
                }
                return this;
            }
        };
    }

    window.$ = window.$ || factory;

    document.addEventListener('click', function (event) {
        const closer = event.target.closest('.modal-close');
        if (closer) {
            const modal = closer.closest('.modal');
            if (modal) modal.style.display = 'none';
            return;
        }
        if (event.target.classList && event.target.classList.contains('modal')) {
            event.target.style.display = 'none';
        }
    });

    document.addEventListener('keydown', function (event) {
        if (event.key !== 'Escape') return;
        document.querySelectorAll('.modal').forEach(function (modal) {
            modal.style.display = 'none';
        });
    });
})();

// Add Items functionality with CRUD for existing kits
document.addEventListener('DOMContentLoaded', function() {
    const userSelect = document.getElementById('user');
    const checkboxes = document.querySelectorAll('.modern-checkbox');
    const quantityInputs = document.querySelectorAll('.quantity-input');
    const detailInputs = document.querySelectorAll('.detail-input, .detail-select, .detail-textarea');
    const submitBtn = document.getElementById('submitBtn');
    
    // CRUD functionality elements
    const existingKitsSection = document.getElementById('existingKitsSection');
    const selectedUserName = document.getElementById('selectedUserName');
    const refreshKitsBtn = document.getElementById('refreshKitsBtn');
    const kitsListContainer = document.getElementById('kitsListContainer');
    const kitsEmptyState = document.getElementById('kitsEmptyState');
    const kitSearchInput = document.getElementById('kitSearchInput');
    const kitFilterSelect = document.getElementById('kitFilterSelect');
    
    // Modal elements
    const kitEditModal = document.getElementById('kitEditModal');
    const kitDeleteModal = document.getElementById('kitDeleteModal');
    const kitEditModalBody = document.getElementById('kitEditModalBody');
    const saveKitChangesBtn = document.getElementById('saveKitChangesBtn');
    const confirmKitDeleteBtn = document.getElementById('confirmKitDeleteBtn');
    
    let currentUserKits = [];
    let currentEditingKitId = null;
    let currentDeletingKitId = null;

    // Tape calculation function
    function calculateTapeLength(quantity, tapeWidth) {
        // Convert width from mm to meters for calculation
        const widthInMeters = tapeWidth / 1000;
        // Standard roll length assumption: 33 meters per roll
        const standardRollLength = 33;
        // Calculate total length in meters
        const totalLength = quantity * standardRollLength;
        // Calculate total area in square meters
        const totalArea = totalLength * widthInMeters;
        
        return {
            totalLength: totalLength.toFixed(2),
            totalArea: totalArea.toFixed(4),
            widthInMeters: widthInMeters.toFixed(3)
        };
    }

    // Function to update tape calculation display
    function updateTapeCalculation(itemCard, quantity, kitName) {
        let calcDisplay = itemCard.querySelector('.tape-calculation');
        
        // Check if this is a tape item
        const isTape = kitName.toLowerCase().includes('tape') || kitName.toLowerCase().includes('vhb');
        
        if (isTape && quantity > 0) {
            // Extract tape width from name (e.g., "VHB Boss Tape 18mm" -> 18)
            const widthMatch = kitName.match(/(\d+)mm/);
            const tapeWidth = widthMatch ? parseInt(widthMatch[1]) : 18; // Default to 18mm if not found
            
            const calculation = calculateTapeLength(quantity, tapeWidth);
            
            if (!calcDisplay) {
                calcDisplay = document.createElement('div');
                calcDisplay.className = 'tape-calculation';
                // Insert before the kit-details section
                const kitDetails = itemCard.querySelector('.kit-details');
                if (kitDetails) {
                    kitDetails.parentNode.insertBefore(calcDisplay, kitDetails);
                } else {
                    itemCard.querySelector('.item-quantity').appendChild(calcDisplay);
                }
            }
            
            calcDisplay.innerHTML = `<p>${calculation.totalLength}m</p>`;
            setTimeout(() => calcDisplay.classList.add('show'), 10);
        } else if (calcDisplay) {
            calcDisplay.classList.remove('show');
        }
    }

    function updateFormState() {
        const userSelected = userSelect.value !== '';
        const itemsSelected = Array.from(checkboxes).some(cb => cb.checked);
        const quantitiesValid = Array.from(quantityInputs).every(input => {
            if (input.disabled) return true;
            const value = parseInt(input.value) || 0;
            return value >= 0;
        });

        submitBtn.disabled = !(userSelected && itemsSelected && quantitiesValid);

        if (submitBtn.disabled) {
            submitBtn.innerHTML = '<i class="fa fa-plus"></i><span>Select User & Items</span>';
        } else {
            const selectedCount = Array.from(checkboxes).filter(cb => cb.checked).length;
            submitBtn.innerHTML = `<i class="fa fa-plus"></i><span>Add ${selectedCount} Kit${selectedCount > 1 ? 's' : ''}</span>`;
        }
    }

    // Handle checkbox changes
    checkboxes.forEach(checkbox => {
        checkbox.addEventListener('change', function() {
            const itemCard = this.closest('.item-card');
            const quantityInput = itemCard.querySelector('.quantity-input');
            const kitDetails = itemCard.querySelector('.kit-details');
            const detailFields = itemCard.querySelectorAll('.detail-input, .detail-select, .detail-textarea');
            const itemUnit = itemCard.querySelector('.item-unit');
            const itemName = itemCard.querySelector('.item-name').textContent;

            if (this.checked) {
                itemCard.classList.add('selected');
                quantityInput.disabled = false;
                quantityInput.style.display = 'block'; // Show quantity input when selected
                kitDetails.classList.add('show'); // Use smooth transition
                detailFields.forEach(field => field.disabled = false);
                itemUnit.style.display = 'block'; // Show unit when item is selected
                quantityInput.focus();
                
                // Update tape calculation if quantity has value
                const quantity = parseInt(quantityInput.value) || 0;
                updateTapeCalculation(itemCard, quantity, itemName);
            } else {
                itemCard.classList.remove('selected');
                quantityInput.disabled = true;
                quantityInput.style.display = 'none'; // Hide quantity input when not selected
                kitDetails.classList.remove('show'); // Use smooth transition
                detailFields.forEach(field => {
                    field.disabled = true;
                    field.value = '';
                });
                quantityInput.value = '';
                itemUnit.style.display = 'none'; // Hide unit when item is not selected
                
                // Hide tape calculation
                const calcDisplay = itemCard.querySelector('.tape-calculation');
                if (calcDisplay) {
                    calcDisplay.classList.remove('show');
                }
            }

            updateFormState();
        });
    });

    // Handle quantity input changes with tape calculation
    quantityInputs.forEach(input => {
        input.addEventListener('input', function() {
            const itemCard = this.closest('.item-card');
            const itemName = itemCard.querySelector('.item-name').textContent;
            const quantity = parseInt(this.value) || 0;
            
            // Update tape calculation for tape items
            updateTapeCalculation(itemCard, quantity, itemName);
            
            updateFormState();
        });
    });

    // Handle user selection
    userSelect.addEventListener('change', updateFormState);

    // Initialize form state
    updateFormState();

    // Hide kit details, unit fields, and quantity inputs initially
    document.querySelectorAll('.kit-details').forEach(details => {
        details.classList.remove('show');
    });

    // Hide quantity inputs initially for unselected items
    quantityInputs.forEach(input => {
        const checkbox = input.closest('.item-card').querySelector('.modern-checkbox');
        if (!checkbox.checked) {
            input.style.display = 'none';
        }
    });

    // Form validation for new kit type
    const addKitTypeBtn = document.querySelector('.add-kit-type-btn');
    if (addKitTypeBtn) {
        addKitTypeBtn.addEventListener('click', function(e) {
            const newKitName = document.getElementById('new_kit_name').value.trim();
            const newKitCode = document.getElementById('new_kit_code').value.trim();
            
            if (!newKitName || !newKitCode) {
                e.preventDefault();
                alert('Please provide both kit name and code for the new kit type.');
                return false;
            }
        });
    }

    // ========== CRUD FUNCTIONALITY FOR EXISTING KITS ==========

    // Load user's existing kits when user is selected
    userSelect.addEventListener('change', function() {
        const userId = this.value;
        if (userId) {
            loadUserKits(userId);
            const selectedOption = this.options[this.selectedIndex];
            const userName = selectedOption.text.split(' (')[0]; // Extract username without clock number
            selectedUserName.textContent = userName;
            existingKitsSection.style.display = 'block';
        } else {
            existingKitsSection.style.display = 'none';
        }
    });

    // Refresh kits button
    refreshKitsBtn.addEventListener('click', function() {
        const userId = userSelect.value;
        if (userId) {
            loadUserKits(userId);
        }
    });

    // Search and filter functionality
    kitSearchInput.addEventListener('input', filterKits);
    kitFilterSelect.addEventListener('change', filterKits);

    // Load user's kits from API
    async function loadUserKits(userId) {
        try {
            kitsListContainer.innerHTML = `
                <div class="loading-kits">
                    <i class="fa fa-spinner fa-spin"></i>
                    <span>Loading existing kits...</span>
                </div>
            `;
            
            const response = await fetch(`/get_user_kits/${userId}/`);
            const data = await response.json();
            
            if (data.success) {
                currentUserKits = data.kits;
                renderKitsList(currentUserKits);
            } else {
                showError('Failed to load kits: ' + data.error);
            }
        } catch (error) {
            console.error('Error loading kits:', error);
            showError('Error loading kits. Please try again.');
        }
    }

    // Render kits list
    function renderKitsList(kits) {
        if (kits.length === 0) {
            kitsListContainer.style.display = 'none';
            kitsEmptyState.style.display = 'block';
            return;
        }

        kitsListContainer.style.display = 'block';
        kitsEmptyState.style.display = 'none';

        const kitsHTML = kits.map(kit => `
            <div class="kit-item ${!kit.is_active ? 'inactive' : ''}" data-kit-id="${kit.id}" data-kit-type="${kit.kit_type_code}">
                <div class="kit-info-main">
                    <div class="kit-type-name">
                        ${kit.kit_type}
                        ${!kit.is_active ? '<span class="badge badge-secondary">Inactive</span>' : ''}
                    </div>
                    <div class="kit-meta">
                        <div class="kit-meta-item">
                            <i class="fa fa-cubes"></i>
                            <span>Quantity: ${kit.quantity}</span>
                        </div>
                        <div class="kit-meta-item">
                            <i class="fa fa-calendar"></i>
                            <span>Added: ${formatDate(kit.timestamp)}</span>
                        </div>
                        <div class="kit-meta-item">
                            <span class="condition-badge condition-${kit.condition}">${kit.condition}</span>
                        </div>
                    </div>
                    ${kit.location || kit.notes || kit.expiration_date ? `
                        <div class="kit-details-preview">
                            ${kit.location ? `<div><i class="fa fa-map-marker-alt"></i> ${kit.location}</div>` : ''}
                            ${kit.expiration_date ? `<div><i class="fa fa-calendar-alt"></i> Expires: ${formatDate(kit.expiration_date)}</div>` : ''}
                            ${kit.notes ? `<div><i class="fa fa-sticky-note"></i> ${kit.notes}</div>` : ''}
                        </div>
                    ` : ''}
                </div>
                <div class="kit-actions">
                    <button type="button" class="kit-action-btn kit-view-btn" onclick="viewKit(${kit.id})" title="View kit details">
                        <i class="fa fa-eye"></i>
                        View
                    </button>
                    <button type="button" class="kit-action-btn kit-edit-btn" onclick="editKit(${kit.id})" title="Edit kit">
                        <i class="fa fa-edit"></i>
                        Edit
                    </button>
                    <button type="button" class="kit-action-btn kit-delete-btn" onclick="deleteKit(${kit.id})" title="Delete kit">
                        <i class="fa fa-trash"></i>
                        Delete
                    </button>
                </div>
            </div>
        `).join('');

        kitsListContainer.innerHTML = kitsHTML;
    }

    // Filter kits based on search and filter criteria
    function filterKits() {
        const searchTerm = kitSearchInput.value.toLowerCase();
        const filterType = kitFilterSelect.value;

        const filteredKits = currentUserKits.filter(kit => {
            const matchesSearch = !searchTerm || 
                kit.kit_type.toLowerCase().includes(searchTerm) ||
                (kit.location && kit.location.toLowerCase().includes(searchTerm)) ||
                (kit.notes && kit.notes.toLowerCase().includes(searchTerm));
            
            const matchesFilter = !filterType || kit.kit_type_code === filterType;

            return matchesSearch && matchesFilter;
        });

        renderKitsList(filteredKits);
    }

    // View kit details
    function viewKit(kitId) {
        const kit = currentUserKits.find(k => k.id === kitId);
        if (kit) {
            const kitDetails = `
                <div class="kit-details-modal">
                    <h5>${kit.kit_type}</h5>
                    <div class="row">
                        <div class="col-md-6"><strong>Quantity:</strong> ${kit.quantity}</div>
                        <div class="col-md-6"><strong>Condition:</strong> ${kit.condition}</div>
                    </div>
                    <div class="row">
                        <div class="col-md-6"><strong>Location:</strong> ${kit.location || 'Not specified'}</div>
                        <div class="col-md-6"><strong>Status:</strong> ${kit.is_active ? 'Active' : 'Inactive'}</div>
                    </div>
                    ${kit.expiration_date ? `<div class="row"><div class="col-12"><strong>Expiration Date:</strong> ${formatDate(kit.expiration_date)}</div></div>` : ''}
                    ${kit.notes ? `<div class="row"><div class="col-12"><strong>Notes:</strong> ${kit.notes}</div></div>` : ''}
                    <div class="row">
                        <div class="col-md-6"><strong>Created:</strong> ${formatDate(kit.timestamp)}</div>
                        <div class="col-md-6"><strong>Last Updated:</strong> ${formatDate(kit.last_updated)}</div>
                    </div>
                </div>
            `;
            
            kitEditModalBody.innerHTML = kitDetails;
            saveKitChangesBtn.style.display = 'none';
            $('#kitEditModal').modal('show');
        }
    }

    // Edit kit
    async function editKit(kitId) {
        currentEditingKitId = kitId;
        const kit = currentUserKits.find(k => k.id === kitId);
        
        if (kit) {
            const editForm = `
                <form id="kitEditForm">
                    <div class="form-group">
                        <label for="editKitType">Kit Type</label>
                        <select class="form-control" id="editKitType" name="kit_type_fk" required>
                            <!-- Kit types will be loaded via AJAX -->
                        </select>
                    </div>
                    <div class="form-group">
                        <label for="editQuantity">Quantity</label>
                        <input type="number" class="form-control" id="editQuantity" name="quantity" min="1" value="${kit.quantity}" required>
                    </div>
                    <div class="form-group">
                        <label for="editCondition">Condition</label>
                        <select class="form-control" id="editCondition" name="condition">
                            <option value="new" ${kit.condition === 'new' ? 'selected' : ''}>New</option>
                            <option value="good" ${kit.condition === 'good' ? 'selected' : ''}>Good</option>
                            <option value="fair" ${kit.condition === 'fair' ? 'selected' : ''}>Fair</option>
                            <option value="poor" ${kit.condition === 'poor' ? 'selected' : ''}>Poor</option>
                            <option value="damaged" ${kit.condition === 'damaged' ? 'selected' : ''}>Damaged</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label for="editLocation">Location</label>
                        <input type="text" class="form-control" id="editLocation" name="location" value="${kit.location || ''}">
                    </div>
                    <div class="form-group">
                        <label for="editExpirationDate">Expiration Date</label>
                        <input type="date" class="form-control" id="editExpirationDate" name="expiration_date" value="${kit.expiration_date || ''}">
                    </div>
                    <div class="form-group">
                        <label for="editNotes">Notes</label>
                        <textarea class="form-control" id="editNotes" name="notes" rows="3">${kit.notes || ''}</textarea>
                    </div>
                    <div class="form-group">
                        <div class="form-check">
                            <input class="form-check-input" type="checkbox" id="editIsActive" name="is_active" ${kit.is_active ? 'checked' : ''}>
                            <label class="form-check-label" for="editIsActive">
                                Kit is active
                            </label>
                        </div>
                    </div>
                </form>
            `;
            
            kitEditModalBody.innerHTML = editForm;
            saveKitChangesBtn.style.display = 'inline-block';
            $('#kitEditModal').modal('show');
            
            // Load kit types for the dropdown
            loadKitTypesForEdit(kit.kit_type_code);
        }
    }

    // Load kit types for edit form
    async function loadKitTypesForEdit(selectedKitTypeCode) {
        try {
            // Get kit types from the server
            const response = await fetch('/get_kit_types_for_edit/');
            const data = await response.json();
            
            if (data.success && data.kit_types) {
                const kitTypeSelect = document.getElementById('editKitType');
                kitTypeSelect.innerHTML = '';
                
                data.kit_types.forEach(kitType => {
                    const option = document.createElement('option');
                    option.value = kitType.id;
                    option.textContent = kitType.name;
                    if (kitType.code === selectedKitTypeCode) {
                        option.selected = true;
                    }
                    kitTypeSelect.appendChild(option);
                });
            } else {
                // Fallback to filter dropdown
                const filterSelect = document.getElementById('kitFilterSelect');
                const kitTypeSelect = document.getElementById('editKitType');
                
                if (filterSelect && kitTypeSelect) {
                    kitTypeSelect.innerHTML = '';
                    Array.from(filterSelect.options).forEach(option => {
                        if (option.value) {
                            const optionClone = option.cloneNode(true);
                            if (optionClone.value === selectedKitTypeCode) {
                                optionClone.selected = true;
                            }
                            kitTypeSelect.appendChild(optionClone);
                        }
                    });
                }
            }
        } catch (error) {
            console.error('Error loading kit types:', error);
            // Fallback to filter dropdown
            const filterSelect = document.getElementById('kitFilterSelect');
            const kitTypeSelect = document.getElementById('editKitType');
            
            if (filterSelect && kitTypeSelect) {
                kitTypeSelect.innerHTML = '';
                Array.from(filterSelect.options).forEach(option => {
                    if (option.value) {
                        const optionClone = option.cloneNode(true);
                        if (optionClone.value === selectedKitTypeCode) {
                            optionClone.selected = true;
                        }
                        kitTypeSelect.appendChild(optionClone);
                    }
                });
            }
        }
    }

    // Save kit changes
    saveKitChangesBtn.addEventListener('click', async function() {
        if (!currentEditingKitId) return;

        const formData = new FormData(document.getElementById('kitEditForm'));
        
        try {
            const response = await fetch(`/update_kit/${currentEditingKitId}/`, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
                }
            });

            const data = await response.json();

            if (data.success) {
                // Update the kit in the local array
                const kitIndex = currentUserKits.findIndex(k => k.id === currentEditingKitId);
                if (kitIndex !== -1) {
                    currentUserKits[kitIndex] = { ...currentUserKits[kitIndex], ...data.kit };
                }
                
                // Re-render the kits list
                renderKitsList(currentUserKits);
                
                // Close modal
                $('#kitEditModal').modal('hide');
                
                // Show success message
                showSuccess('Kit updated successfully!');
            } else {
                showError('Failed to update kit: ' + (data.error || 'Unknown error'));
                if (data.errors) {
                    console.error('Validation errors:', data.errors);
                }
            }
        } catch (error) {
            console.error('Error updating kit:', error);
            showError('Error updating kit. Please try again.');
        }
    });

    // Delete kit
    function deleteKit(kitId) {
        currentDeletingKitId = kitId;
        const kit = currentUserKits.find(k => k.id === kitId);
        
        if (kit) {
            document.getElementById('deleteKitName').textContent = kit.kit_type;
            document.getElementById('deleteKitQuantity').textContent = kit.quantity;
            document.getElementById('deleteKitOwner').textContent = selectedUserName.textContent;
            
            $('#kitDeleteModal').modal('show');
        }
    }

    // Confirm kit deletion
    confirmKitDeleteBtn.addEventListener('click', async function() {
        if (!currentDeletingKitId) return;

        try {
            const response = await fetch(`/delete_kit/${currentDeletingKitId}/`, {
                method: 'POST',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
                }
            });

            if (response.ok) {
                // Remove the kit from the local array
                currentUserKits = currentUserKits.filter(k => k.id !== currentDeletingKitId);
                
                // Re-render the kits list
                renderKitsList(currentUserKits);
                
                // Close modal
                $('#kitDeleteModal').modal('hide');
                
                // Show success message
                showSuccess('Kit deleted successfully!');
            } else {
                const errorData = await response.json();
                showError('Failed to delete kit: ' + (errorData.error || 'Unknown error'));
            }
        } catch (error) {
            console.error('Error deleting kit:', error);
            showError('Error deleting kit. Please try again.');
        }
    });

    // Utility functions
    function formatDate(dateString) {
        if (!dateString) return '';
        const date = new Date(dateString);
        return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
    }

    function showSuccess(message) {
        // Create a temporary success message
        const alertDiv = document.createElement('div');
        alertDiv.className = 'alert alert-success alert-dismissible fade show';
        alertDiv.innerHTML = `
            <i class="fa fa-check-circle"></i>
            ${message}
            <button type="button" class="close" data-dismiss="alert">&times;</button>
        `;
        
        // Insert at the top of the container
        const container = document.querySelector('.add-items-container');
        container.insertBefore(alertDiv, container.firstChild);
        
        // Auto-hide after 5 seconds
        setTimeout(() => {
            alertDiv.classList.remove('show');
            setTimeout(() => alertDiv.remove(), 150);
        }, 5000);
    }

    function showError(message) {
        // Create a temporary error message
        const alertDiv = document.createElement('div');
        alertDiv.className = 'alert alert-danger alert-dismissible fade show';
        alertDiv.innerHTML = `
            <i class="fa fa-exclamation-triangle"></i>
            ${message}
            <button type="button" class="close" data-dismiss="alert">&times;</button>
        `;
        
        // Insert at the top of the container
        const container = document.querySelector('.add-items-container');
        container.insertBefore(alertDiv, container.firstChild);
        
        // Auto-hide after 5 seconds
        setTimeout(() => {
            alertDiv.classList.remove('show');
            setTimeout(() => alertDiv.remove(), 150);
        }, 5000);
    }

    // Make functions globally available
    window.viewKit = viewKit;
    window.editKit = editKit;
    window.deleteKit = deleteKit;
});
