// Add Items functionality with CRUD for existing kits
document.addEventListener('DOMContentLoaded', function() {
    // Icon helper — pulls a glyph from the inline SVG sprite in base.html.
    function icon(name, className) {
        return `<svg class="icon${className ? ' ' + className : ''}" aria-hidden="true"><use href="#${name}"></use></svg>`;
    }

    const userSelect = document.getElementById('user');
    const checkboxes = document.querySelectorAll('.modern-checkbox');
    const quantityInputs = document.querySelectorAll('.quantity-input');
    const detailInputs = document.querySelectorAll('.detail-input, .detail-select, .detail-textarea');
    const submitBtn = document.getElementById('submitBtn');
    const kitTypeSearch = document.getElementById('kitTypeSearch');
    const catalogCount = document.getElementById('catalogCount');
    const catalogNoResults = document.getElementById('catalogNoResults');
    const kitTypeCards = Array.from(document.querySelectorAll('.kit-type-card'));
    const selectionSummary = document.getElementById('selectionSummary');
    
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

    const htmlEscapes = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#39;'
    };

    function escapeHtml(value) {
        return String(value ?? '').replace(/[&<>"']/g, character => htmlEscapes[character]);
    }

    if (kitsListContainer) {
        kitsListContainer.addEventListener('click', function(event) {
            const button = event.target.closest('[data-kit-action]');
            if (!button || !kitsListContainer.contains(button)) return;

            const kitId = Number(button.dataset.kitId);
            if (!Number.isSafeInteger(kitId) || kitId <= 0) return;

            if (button.dataset.kitAction === 'view') viewKit(kitId);
            if (button.dataset.kitAction === 'edit') editKit(kitId);
            if (button.dataset.kitAction === 'delete') deleteKit(kitId);
        });
    }

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
        const selectedCheckboxes = Array.from(checkboxes).filter(cb => cb.checked);
        const itemsSelected = selectedCheckboxes.length > 0;
        const quantitiesValid = Array.from(quantityInputs).every(input => {
            if (input.disabled) return true;
            return input.value === '' || Number(input.value) >= 0;
        });
        const selectedQuantities = selectedCheckboxes.map(checkbox => {
            const input = checkbox.closest('.item-card').querySelector('.quantity-input');
            return Math.max(0, Number(input.value) || 0);
        });
        const totalQuantity = selectedQuantities.reduce((total, quantity) => total + quantity, 0);
        const quantitiesComplete = selectedQuantities.length > 0 && selectedQuantities.every(quantity => quantity > 0);
        const canSubmit = userSelected && itemsSelected && quantitiesComplete && quantitiesValid;

        submitBtn.disabled = !canSubmit;
        if (!userSelected) {
            submitBtn.innerHTML = `${icon('i-plus')}<span>${itemsSelected ? 'Choose a recipient' : 'Choose a recipient to continue'}</span>`;
        } else if (!itemsSelected) {
            submitBtn.innerHTML = `${icon('i-plus')}<span>Select kit types to continue</span>`;
        } else if (!quantitiesComplete) {
            submitBtn.innerHTML = `${icon('i-plus')}<span>Enter a quantity for each type</span>`;
        } else {
            submitBtn.innerHTML = `${icon('i-plus')}<span>Add ${selectedCheckboxes.length} type${selectedCheckboxes.length === 1 ? '' : 's'}</span>`;
        }

        if (selectionSummary) {
            const typeLabel = `${selectedCheckboxes.length} type${selectedCheckboxes.length === 1 ? '' : 's'} selected`;
            selectionSummary.textContent = selectedCheckboxes.length
                ? `${typeLabel} · ${totalQuantity} total ${totalQuantity === 1 ? 'unit' : 'units'}`
                : 'No kit types selected';
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
                // Keep any values if the checkbox is toggled off and back on;
                // disabled fields are not submitted until the item is selected again.
                detailFields.forEach(field => {
                    field.disabled = true;
                });
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

    // Filter the kit catalog without losing any selections already made.
    function filterKitTypes() {
        if (!kitTypeSearch) return;
        const query = kitTypeSearch.value.trim().toLocaleLowerCase();
        let visibleCount = 0;

        kitTypeCards.forEach(card => {
            const checkbox = card.querySelector('.modern-checkbox');
            const searchable = `${card.querySelector('.item-name')?.textContent || ''} ${card.querySelector('.kit-type-code')?.textContent || ''}`.toLocaleLowerCase();
            const matches = !query || searchable.includes(query) || checkbox.checked;
            card.hidden = !matches;
            if (matches) visibleCount += 1;
        });

        if (catalogCount) {
            catalogCount.textContent = query
                ? `${visibleCount} type${visibleCount === 1 ? '' : 's'} shown`
                : `${kitTypeCards.length} type${kitTypeCards.length === 1 ? '' : 's'} available`;
        }
        if (catalogNoResults) catalogNoResults.hidden = visibleCount !== 0 || kitTypeCards.length === 0;
    }

    if (kitTypeSearch) {
        kitTypeSearch.addEventListener('input', filterKitTypes);
        document.addEventListener('keydown', function(event) {
            const target = event.target;
            const isTyping = target && (target.matches('input, textarea, select') || target.isContentEditable);
            if (event.key === '/' && !isTyping && !event.ctrlKey && !event.metaKey && !event.altKey) {
                event.preventDefault();
                kitTypeSearch.focus();
            } else if (event.key === 'Escape' && target === kitTypeSearch) {
                kitTypeSearch.value = '';
                filterKitTypes();
            }
        });
    }
    filterKitTypes();

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

    // Existing-stock tools are only rendered for users who can select a
    // recipient. Guard these optional controls for regular members.
    if (existingKitsSection && selectedUserName && refreshKitsBtn &&
        kitsListContainer && kitsEmptyState && kitSearchInput && kitFilterSelect) {
        userSelect.addEventListener('change', function() {
            const userId = this.value;
            if (userId) {
                loadUserKits(userId);
                const selectedOption = this.options[this.selectedIndex];
                selectedUserName.textContent = selectedOption.text.split(' (')[0];
                existingKitsSection.hidden = false;
            } else {
                existingKitsSection.hidden = true;
            }
        });

        refreshKitsBtn.addEventListener('click', function() {
            const userId = userSelect.value;
            if (userId) loadUserKits(userId);
        });
        kitSearchInput.addEventListener('input', filterKits);
        kitFilterSelect.addEventListener('change', filterKits);

        if (userSelect.value) {
            const selectedOption = userSelect.options[userSelect.selectedIndex];
            selectedUserName.textContent = selectedOption.text.split(' (')[0];
            loadUserKits(userSelect.value);
        }
    }

    // Load user's kits from API
    async function loadUserKits(userId) {
        try {
            kitsListContainer.innerHTML = `
                <div class="loading-kits" role="status">
                    <span class="loading-spinner">Loading existing stock…</span>
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
            kitsListContainer.hidden = true;
            kitsEmptyState.hidden = false;
            return;
        }

        kitsListContainer.hidden = false;
        kitsEmptyState.hidden = true;

        const kitsHTML = kits.map(kit => `
            <div class="kit-item ${!kit.is_active ? 'inactive' : ''}" data-kit-id="${escapeHtml(kit.id)}" data-kit-type="${escapeHtml(kit.kit_type_code)}">
                <div class="kit-info-main">
                    <div class="kit-type-name">
                        ${escapeHtml(kit.kit_type)}
                        ${!kit.is_active ? '<span class="badge badge-secondary">Inactive</span>' : ''}
                    </div>
                    <div class="kit-meta">
                        <div class="kit-meta-item">
                            ${icon('i-boxes')}
                            <span>Qty ${escapeHtml(kit.quantity)}</span>
                        </div>
                        <div class="kit-meta-item">
                            ${icon('i-calendar')}
                            <span>${escapeHtml(formatDate(kit.timestamp))}</span>
                        </div>
                        <div class="kit-meta-item">
                            <span class="condition-badge condition-${escapeHtml(kit.condition)}">${escapeHtml(kit.condition)}</span>
                        </div>
                    </div>
                    ${kit.location || kit.notes || kit.expiration_date ? `
                        <div class="kit-details-preview">
                            ${kit.location ? `<span class="kit-detail-chip">${icon('i-pin')}${escapeHtml(kit.location)}</span>` : ''}
                            ${kit.expiration_date ? `<span class="kit-detail-chip">${icon('i-calendar')}Expires ${escapeHtml(formatDate(kit.expiration_date))}</span>` : ''}
                            ${kit.notes ? `<span class="kit-detail-chip kit-detail-chip--note">${escapeHtml(kit.notes)}</span>` : ''}
                        </div>
                    ` : ''}
                </div>
                <div class="kit-actions">
                    <button type="button" class="kit-action-btn kit-view-btn" data-kit-action="view" data-kit-id="${escapeHtml(kit.id)}" title="View kit details">
                        ${icon('i-eye')}
                        View
                    </button>
                    <button type="button" class="kit-action-btn kit-edit-btn" data-kit-action="edit" data-kit-id="${escapeHtml(kit.id)}" title="Edit kit">
                        ${icon('i-edit')}
                        Edit
                    </button>
                    <button type="button" class="kit-action-btn kit-delete-btn" data-kit-action="delete" data-kit-id="${escapeHtml(kit.id)}" title="Delete kit">
                        ${icon('i-trash')}
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
                    <dl class="detail-list">
                        <div class="detail-row">
                            <dt>Quantity</dt>
                            <dd>${escapeHtml(kit.quantity)}</dd>
                        </div>
                        <div class="detail-row">
                            <dt>Condition</dt>
                            <dd><span class="condition-badge condition-${escapeHtml(kit.condition)}">${escapeHtml(kit.condition)}</span></dd>
                        </div>
                        <div class="detail-row">
                            <dt>Location</dt>
                            <dd>${escapeHtml(kit.location || 'Not recorded')}</dd>
                        </div>
                        <div class="detail-row">
                            <dt>Status</dt>
                            <dd>${kit.is_active ? 'Active' : 'Inactive'}</dd>
                        </div>
                        <div class="detail-row">
                            <dt>Added</dt>
                            <dd>${escapeHtml(formatDate(kit.timestamp))}</dd>
                        </div>
                        <div class="detail-row">
                            <dt>Last updated</dt>
                            <dd>${escapeHtml(formatDate(kit.last_updated))}</dd>
                        </div>
                        ${kit.expiration_date ? `<div class="detail-row"><dt>Expires</dt><dd>${escapeHtml(formatDate(kit.expiration_date))}</dd></div>` : ''}
                        ${kit.notes ? `<div class="detail-row detail-row--stacked"><dt>Notes</dt><dd>${escapeHtml(kit.notes)}</dd></div>` : ''}
                    </dl>
                </div>
            `;
            
            kitEditModalBody.innerHTML = kitDetails;
            document.getElementById('kit-edit-title').textContent = 'Stock item details';
            saveKitChangesBtn.style.display = 'none';
            kitEditModal.hidden = false;
            kitEditModal.style.display = 'flex';
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
                    <div class="edit-grid">
                        <div class="form-group">
                            <label for="editQuantity">Quantity</label>
                            <input type="number" class="form-control" id="editQuantity" name="quantity" min="1" value="${escapeHtml(kit.quantity)}" required>
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
                            <input type="text" class="form-control" id="editLocation" name="location" value="${escapeHtml(kit.location || '')}">
                        </div>
                        <div class="form-group">
                            <label for="editExpirationDate">Expires</label>
                            <input type="date" class="form-control" id="editExpirationDate" name="expiration_date" value="${escapeHtml(kit.expiration_date || '')}">
                        </div>
                    </div>
                    <div class="form-group">
                        <label for="editNotes">Notes</label>
                        <textarea class="form-control" id="editNotes" name="notes" rows="3">${escapeHtml(kit.notes || '')}</textarea>
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
            document.getElementById('kit-edit-title').textContent = 'Edit stock item';
            saveKitChangesBtn.style.display = 'inline-block';
            kitEditModal.hidden = false;
            kitEditModal.style.display = 'flex';
            
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
                kitEditModal.style.display = 'none';
                kitEditModal.hidden = true;
                
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
            
            kitDeleteModal.hidden = false;
            kitDeleteModal.style.display = 'flex';
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
                kitDeleteModal.style.display = 'none';
                kitDeleteModal.hidden = true;
                
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
        showAlert(message, 'success', 'check-circle');
    }

    function showError(message) {
        showAlert(message, 'danger', 'exclamation-triangle');
    }

    function showAlert(message, type, iconName) {
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type}`;
        alertDiv.setAttribute('role', type === 'danger' ? 'alert' : 'status');

        const iconWrap = document.createElement('span');
        iconWrap.className = 'alert-icon';
        iconWrap.innerHTML = icon(iconName === 'exclamation-triangle' ? 'i-alert' : 'i-check');
        const messageNode = document.createElement('span');
        messageNode.className = 'alert-text';
        messageNode.textContent = message;
        const closeButton = document.createElement('button');
        closeButton.type = 'button';
        closeButton.className = 'alert-close';
        closeButton.setAttribute('aria-label', 'Dismiss message');
        closeButton.innerHTML = icon('i-close');
        closeButton.addEventListener('click', () => alertDiv.remove());
        alertDiv.append(iconWrap, messageNode, closeButton);

        const container = document.querySelector('.add-items-container');
        if (!container) {
            console.error('Unable to display alert: add-items container is missing.');
            return;
        }
        container.insertBefore(alertDiv, container.firstChild);

        setTimeout(() => alertDiv.remove(), 6000);
    }

    // Modal close buttons
    document.querySelectorAll('.modal-close').forEach(btn => {
        btn.addEventListener('click', function() {
            const modal = this.closest('.modal');
            if (modal) {
                modal.style.display = 'none';
                modal.hidden = true;
            }
        });
    });
    
    // Close modals when clicking outside
    [kitEditModal, kitDeleteModal].forEach(modal => {
        if (modal) {
            modal.addEventListener('click', function(e) {
                if (e.target === modal) {
                    modal.style.display = 'none';
                    modal.hidden = true;
                }
            });
        }
    });
    
    // Make functions globally available
    window.viewKit = viewKit;
    window.editKit = editKit;
    window.deleteKit = deleteKit;
});
