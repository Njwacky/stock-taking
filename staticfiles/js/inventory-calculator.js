/**
 * Universal Inventory Calculator with Drag & Drop Interface
 * Handles complex unit conversions and dynamic formula building
 */

class InventoryCalculator {
    constructor() {
        this.formula = [];
        this.variables = new Map();
        this.units = new Map();
        this.templates = new Map();
        this.history = [];
        this.isDragging = false;
        this.draggedElement = null;
        this.currentMode = 'inventory'; // 'inventory' or 'standard'
        
        // Standard calculator properties
        this.currentValue = '0';
        this.previousValue = null;
        this.operation = null;
        this.waitingForOperand = false;
        this.memory = 0;
        this.calculationHistory = [];
        
        this.initializeUnits();
        this.initializeTemplates();
        this.setupEventListeners();
        this.loadFromStorage();
        this.setupStandardCalculator();
    }

    // Initialize unit conversion system
    initializeUnits() {
        // Base units and their conversion factors to meters/liters
        this.units.set('length', {
            'mm': 0.001,
            'cm': 0.01,
            'm': 1,
            'km': 1000,
            'in': 0.0254,
            'ft': 0.3048,
            'yd': 0.9144
        });

        this.units.set('volume', {
            'ml': 0.001,
            'l': 1,
            'kl': 1000,
            'gal': 3.78541,
            'oz': 0.0295735
        });

        this.units.set('area', {
            'mm²': 0.000001,
            'cm²': 0.0001,
            'm²': 1,
            'km²': 1000000,
            'in²': 0.00064516,
            'ft²': 0.092903
        });

        this.units.set('weight', {
            'g': 0.001,
            'kg': 1,
            't': 1000,
            'oz': 0.0283495,
            'lb': 0.453592
        });

        // Specialized units for inventory
        this.units.set('inventory', {
            'pieces': 1,
            'rolls': 1,
            'boxes': 1,
            'kits': 1,
            'bottles': 1,
            'units': 1
        });
    }

    // Initialize common formula templates
    initializeTemplates() {
        this.templates.set('tape_calculation', {
            name: 'Tape Roll Calculator',
            description: 'Calculate rolls needed for units with tape requirements',
            variables: ['units', 'tape_per_unit', 'roll_length'],
            formula: '(units * tape_per_unit) / roll_length',
            units: { units: 'pieces', tape_per_unit: 'm', roll_length: 'm', result: 'rolls' },
            example: {
                units: 100,
                tape_per_unit: 0.5,
                roll_length: 25
            }
        });

        this.templates.set('material_coverage', {
            name: 'Material Coverage',
            description: 'Calculate material needed for area',
            variables: ['area', 'material_width', 'overlap'],
            formula: '(area * (1 + overlap/100)) / material_width',
            units: { area: 'm²', material_width: 'm', overlap: '%', result: 'm' }
        });

        this.templates.set('liquid_mixing', {
            name: 'Liquid Mixing Ratio',
            description: 'Calculate quantities for mixing liquids',
            variables: ['total_volume', 'ratio_a', 'ratio_b'],
            formula: {
                component_a: 'total_volume * ratio_a / (ratio_a + ratio_b)',
                component_b: 'total_volume * ratio_b / (ratio_a + ratio_b)'
            },
            units: { total_volume: 'l', ratio_a: '%', ratio_b: '%', component_a: 'l', component_b: 'l' }
        });

        this.templates.set('kit_assembly', {
            name: 'Kit Assembly Calculator',
            description: 'Calculate components needed for kits',
            variables: ['kit_quantity', 'components_per_kit', 'spare_percentage'],
            formula: 'kit_quantity * components_per_kit * (1 + spare_percentage/100)',
            units: { kit_quantity: 'kits', components_per_kit: 'pieces', spare_percentage: '%', result: 'pieces' }
        });
    }

    // Setup event listeners for drag and drop
    setupEventListeners() {
        // Initialize drag zones
        this.setupDragZones();
        
        // Setup calculator controls
        this.setupControls();
        
        // Setup template selector
        this.setupTemplateSelector();
    }

    setupDragZones() {
        const variablesZone = document.getElementById('calc-variables-zone');
        const operatorsZone = document.getElementById('calc-operators-zone');
        const formulaZone = document.getElementById('calc-formula-zone');
        const resultsZone = document.getElementById('calc-results-zone');

        if (variablesZone) {
            this.makeZoneDropTarget(variablesZone, 'variable');
        }
        if (operatorsZone) {
            this.makeZoneDropTarget(operatorsZone, 'operator');
        }
        if (formulaZone) {
            this.makeZoneDropTarget(formulaZone, 'formula');
        }
        if (resultsZone) {
            this.makeZoneDropTarget(resultsZone, 'result');
        }
    }

    makeZoneDropTarget(zone, type) {
        zone.addEventListener('dragover', (e) => {
            e.preventDefault();
            zone.classList.add('drag-over');
        });

        zone.addEventListener('dragleave', (e) => {
            if (e.target === zone) {
                zone.classList.remove('drag-over');
            }
        });

        zone.addEventListener('drop', (e) => {
            e.preventDefault();
            zone.classList.remove('drag-over');
            
            const data = JSON.parse(e.dataTransfer.getData('text/plain'));
            this.handleDrop(data, zone, type);
        });
    }

    handleDrop(data, zone, type) {
        const element = this.createFormulaElement(data, type);
        zone.appendChild(element);
        this.updateFormula();
        this.saveToStorage();
    }

    createFormulaElement(data, type) {
        const element = document.createElement('div');
        element.className = `formula-element formula-${data.type}`;
        element.draggable = true;
        element.dataset.type = data.type;
        element.dataset.value = data.value;

        // Add content based on type
        switch (data.type) {
            case 'variable':
                element.innerHTML = `
                    <div class="element-content">
                        <i class="fa fa-cube"></i>
                        <span class="variable-name">${data.name}</span>
                        <input type="number" class="variable-input" placeholder="0" step="any">
                        <select class="variable-unit">
                            ${this.getUnitOptions(data.unitType)}
                        </select>
                    </div>
                    <button class="remove-element" onclick="this.parentElement.remove()">&times;</button>
                `;
                break;
            
            case 'operator':
                element.innerHTML = `
                    <div class="element-content">
                        <span class="operator-symbol">${data.symbol}</span>
                    </div>
                    <button class="remove-element" onclick="this.parentElement.remove()">&times;</button>
                `;
                break;
            
            case 'function':
                element.innerHTML = `
                    <div class="element-content">
                        <span class="function-name">${data.name}()</span>
                    </div>
                    <button class="remove-element" onclick="this.parentElement.remove()">&times;</button>
                `;
                break;
        }

        // Make draggable
        element.addEventListener('dragstart', (e) => {
            this.isDragging = true;
            this.draggedElement = element;
            e.dataTransfer.effectAllowed = 'move';
            e.dataTransfer.setData('text/plain', JSON.stringify(data));
            element.classList.add('dragging');
        });

        element.addEventListener('dragend', (e) => {
            this.isDragging = false;
            this.draggedElement = null;
            element.classList.remove('dragging');
        });

        return element;
    }

    getUnitOptions(unitType) {
        const units = this.units.get(unitType) || {};
        return Object.entries(units).map(([unit, factor]) => 
            `<option value="${unit}">${unit}</option>`
        ).join('');
    }

    setupControls() {
        // Mode toggle button
        const modeToggleBtn = document.getElementById('calc-mode-toggle');
        if (modeToggleBtn) {
            modeToggleBtn.addEventListener('click', () => {
                this.toggleCalculatorMode();
            });
        }

        // Formula display clear button
        const formulaDisplayClear = document.getElementById('formula-display-clear');
        if (formulaDisplayClear) {
            formulaDisplayClear.addEventListener('click', () => {
                const formulaDisplayContent = document.getElementById('formula-display-content');
                if (formulaDisplayContent) {
                    formulaDisplayContent.innerHTML = `
                        <div class="empty-state">
                            <i class="fa fa-edit"></i>
                            <p>Build your formula below</p>
                        </div>
                    `;
                }
            });
        }

        // Tour button
        const tourBtn = document.getElementById('calc-tour-btn');
        if (tourBtn) {
            tourBtn.addEventListener('click', () => {
                if (window.calculatorTour) {
                    window.calculatorTour.start();
                }
            });
        }

        // Template selector
        const templateSelect = document.getElementById('calc-template-select');
        if (templateSelect) {
            templateSelect.addEventListener('change', (e) => {
                this.loadTemplate(e.target.value);
            });
        }

        // Calculate button
        const calculateBtn = document.getElementById('calc-calculate-btn');
        if (calculateBtn) {
            calculateBtn.addEventListener('click', () => {
                if (this.currentMode === 'inventory') {
                    this.calculate();
                } else {
                    this.standardCalculate();
                }
            });
        }

        // Clear button
        const clearBtn = document.getElementById('calc-clear-btn');
        if (clearBtn) {
            clearBtn.addEventListener('click', () => {
                if (this.currentMode === 'inventory') {
                    this.clearFormula();
                } else {
                    this.standardClear();
                }
            });
        }

        // Save template button
        const saveTemplateBtn = document.getElementById('calc-save-template-btn');
        if (saveTemplateBtn) {
            saveTemplateBtn.addEventListener('click', () => {
                this.saveAsTemplate();
            });
        }
    }

    setupTemplateSelector() {
        const templateSelect = document.getElementById('calc-template-select');
        if (templateSelect) {
            // Add default templates
            this.templates.forEach((template, key) => {
                const option = document.createElement('option');
                option.value = key;
                option.textContent = template.name;
                templateSelect.appendChild(option);
            });
        }
    }

    loadTemplate(templateKey) {
        const template = this.templates.get(templateKey);
        if (!template) return;

        this.clearFormula();
        
        // Load template variables
        if (template.variables) {
            template.variables.forEach(variable => {
                const variableData = {
                    type: 'variable',
                    name: variable,
                    value: variable,
                    unitType: this.inferUnitType(variable, template.units)
                };
                this.addVariableToFormula(variableData);
            });
        }

        // Load template formula
        if (template.formula) {
            this.parseAndLoadFormula(template.formula);
        }

        // Set example values if available
        if (template.example) {
            setTimeout(() => {
                Object.entries(template.example).forEach(([varName, value]) => {
                    const element = document.querySelector(`[data-value="${varName}"]`);
                    if (element) {
                        const input = element.querySelector('.variable-input');
                        const unit = element.querySelector('.variable-unit');
                        if (input) input.value = value;
                        if (unit && template.units[varName]) {
                            unit.value = template.units[varName];
                        }
                    }
                });
                this.updateFormula();
            }, 200);
        }
    }

    inferUnitType(variable, unitMap) {
        const unit = unitMap[variable];
        if (!unit) return 'inventory';

        for (const [category, units] of this.units.entries()) {
            if (units[unit]) return category;
        }
        return 'inventory';
    }

    addVariableToFormula(variableData) {
        const variablesZone = document.getElementById('calc-variables-zone');
        if (variablesZone) {
            const element = this.createFormulaElement(variableData, 'variable');
            variablesZone.appendChild(element);
        }
    }

    parseAndLoadFormula(formula) {
        // This is a simplified parser - in production, use a proper expression parser
        const operatorsZone = document.getElementById('calc-operators-zone');
        if (operatorsZone && typeof formula === 'string') {
            // Extract operators from formula string
            const operators = formula.match(/[+\-*/()]/g) || [];
            operators.forEach(op => {
                const operatorData = {
                    type: 'operator',
                    symbol: op,
                    value: op
                };
                const element = this.createFormulaElement(operatorData, 'operator');
                operatorsZone.appendChild(element);
            });
        }
    }

    updateFormula() {
        // Collect all formula elements and build expression
        const formulaElements = document.querySelectorAll('.formula-element');
        const expression = [];
        
        formulaElements.forEach(element => {
            const type = element.dataset.type;
            const value = element.dataset.value;
            
            if (type === 'variable') {
                const input = element.querySelector('.variable-input');
                const unit = element.querySelector('.variable-unit');
                const variableName = element.querySelector('.variable-name').textContent;
                
                const numericValue = parseFloat(input.value) || 0;
                this.variables.set(variableName, {
                    value: numericValue,
                    unit: unit.value,
                    element: element
                });
                
                // Use the actual numeric value, not the variable name
                expression.push(numericValue.toString());
            } else if (type === 'operator') {
                expression.push(value);
            } else if (type === 'function') {
                expression.push(value);
            }
        });
        
        this.formula = expression;
        
        // Update formula display
        this.updateFormulaDisplay();
    }

    calculate() {
        this.updateFormula();
        
        try {
            // Convert units and calculate
            const result = this.evaluateExpression();
            this.displayResult(result);
            this.addToHistory(result);
        } catch (error) {
            this.displayError(error.message);
        }
    }

    evaluateExpression() {
        // Simple expression evaluator - in production, use a proper math expression parser
        const expression = this.formula.join(' ');
        
        // If the expression already contains only numbers and operators, evaluate directly
        let evalExpression = expression.trim();
        
        // Check if expression contains variable names that need replacement
        const hasVariables = /[a-zA-Z]/.test(evalExpression);
        
        if (hasVariables) {
            // Replace variable names with values
            this.variables.forEach((variable, name) => {
                // Replace variable names in the expression with their actual values
                const regex = new RegExp(`\\b${name}\\b`, 'g');
                evalExpression = evalExpression.replace(regex, variable.value || 0);
            });
        }
        
        // Clean up the expression - remove any remaining text and ensure valid math
        evalExpression = evalExpression.replace(/[^0-9+\-*/().\s]/g, '');
        
        // Check if expression is valid (not empty and contains valid math)
        if (!evalExpression.trim()) {
            throw new Error('Invalid expression: Please build a valid formula with numbers and operators');
        }
        
        // Additional validation for basic math structure
        if (!/^[\d+\-*/().\s]+$/.test(evalExpression.trim())) {
            throw new Error('Invalid expression: Please build a valid formula with numbers and operators');
        }
        
        // Safe evaluation using Function constructor
        try {
            const result = new Function('return ' + evalExpression)();
            if (isNaN(result) || !isFinite(result)) {
                throw new Error('Invalid result: Calculation produced an invalid number');
            }
            return {
                value: result,
                expression: expression,
                unit: this.getResultUnit()
            };
        } catch (error) {
            throw new Error('Invalid expression: ' + error.message);
        }
    }

    getResultUnit() {
        // Simplified unit inference - in production, implement proper unit algebra
        const variables = Array.from(this.variables.values());
        if (variables.length === 0) return 'units';
        
        // For now, return the unit of the first variable
        return variables[0].unit || 'units';
    }

    displayResult(result) {
        const resultsZone = document.getElementById('calc-results-zone');
        if (!resultsZone) return;

        const resultElement = document.createElement('div');
        resultElement.className = 'calculation-result';
        resultElement.innerHTML = `
            <div class="result-header">
                <h4>Calculation Result</h4>
                <button class="copy-result" onclick="navigator.clipboard.writeText('${result.value}')">
                    <i class="fa fa-copy"></i> Copy
                </button>
            </div>
            <div class="result-content">
                <div class="result-value">${this.formatNumber(result.value)}</div>
                <div class="result-unit">${result.unit}</div>
                <div class="result-expression">${result.expression}</div>
            </div>
            <div class="result-actions">
                <button class="apply-to-form" onclick="inventoryCalculator.applyToForm(${result.value}, '${result.unit}')">
                    <i class="fa fa-plus"></i> Apply to Form
                </button>
            </div>
        `;

        // Clear previous results and add new one
        resultsZone.innerHTML = '';
        resultsZone.appendChild(resultElement);
    }

    displayError(message) {
        const resultsZone = document.getElementById('calc-results-zone');
        if (!resultsZone) return;

        const errorElement = document.createElement('div');
        errorElement.className = 'calculation-error';
        errorElement.innerHTML = `
            <div class="error-header">
                <h4>Calculation Error</h4>
            </div>
            <div class="error-content">
                <i class="fa fa-exclamation-triangle"></i>
                <span>${message}</span>
            </div>
        `;

        resultsZone.innerHTML = '';
        resultsZone.appendChild(errorElement);
    }

    formatNumber(value) {
        if (isNaN(value)) return '0';
        
        // Format with appropriate precision
        if (Number.isInteger(value)) {
            return value.toLocaleString();
        } else {
            return value.toLocaleString(undefined, { maximumFractionDigits: 4 });
        }
    }

    addToHistory(result) {
        const historyEntry = {
            timestamp: new Date().toISOString(),
            result: result,
            formula: this.formula.join(' '),
            variables: Object.fromEntries(this.variables)
        };

        this.history.unshift(historyEntry);
        if (this.history.length > 10) {
            this.history = this.history.slice(0, 10);
        }

        this.updateHistoryDisplay();
        this.saveToStorage();
    }

    updateHistoryDisplay() {
        const historyContainer = document.getElementById('calc-history');
        if (!historyContainer) return;

        historyContainer.innerHTML = '';
        
        this.history.forEach((entry, index) => {
            const historyItem = document.createElement('div');
            historyItem.className = 'history-item';
            historyItem.innerHTML = `
                <div class="history-header">
                    <span class="history-time">${new Date(entry.timestamp).toLocaleString()}</span>
                    <button class="history-load" onclick="inventoryCalculator.loadFromHistory(${index})">
                        <i class="fa fa-redo"></i> Load
                    </button>
                </div>
                <div class="history-content">
                    <div class="history-result">${this.formatNumber(entry.result.value)} ${entry.result.unit}</div>
                    <div class="history-formula">${entry.formula}</div>
                </div>
            `;
            historyContainer.appendChild(historyItem);
        });
    }

    loadFromHistory(index) {
        const entry = this.history[index];
        if (!entry) return;

        // Clear current formula
        this.clearFormula();

        // Restore variables
        Object.entries(entry.variables).forEach(([name, variable]) => {
            const variableData = {
                type: 'variable',
                name: name,
                value: name,
                unitType: this.inferUnitTypeFromUnit(variable.unit)
            };
            this.addVariableToFormula(variableData);
            
            // Set the value after element is created
            setTimeout(() => {
                const element = document.querySelector(`[data-value="${name}"]`);
                if (element) {
                    const input = element.querySelector('.variable-input');
                    const unit = element.querySelector('.variable-unit');
                    if (input) input.value = variable.value;
                    if (unit) unit.value = variable.unit;
                }
            }, 100);
        });

        // Restore formula
        this.parseAndLoadFormula(entry.formula);
    }

    inferUnitTypeFromUnit(unit) {
        for (const [category, units] of this.units.entries()) {
            if (units[unit]) return category;
        }
        return 'inventory';
    }

    applyToForm(value, unit) {
        // Find the most appropriate quantity field in the add items form
        const quantityInputs = document.querySelectorAll('input[name$="_qty"]');
        
        if (quantityInputs.length > 0) {
            // If multiple inputs, try to find the best match based on unit
            let targetInput = null;
            
            if (unit.includes('roll')) {
                targetInput = Array.from(quantityInputs).find(input => 
                    input.name.toLowerCase().includes('vhb') || 
                    input.name.toLowerCase().includes('tape')
                );
            } else if (unit.includes('piece')) {
                targetInput = Array.from(quantityInputs).find(input => 
                    input.name.toLowerCase().includes('feet') || 
                    input.name.toLowerCase().includes('rivnut')
                );
            }
            
            // If no specific match, use the first visible input
            if (!targetInput) {
                targetInput = Array.from(quantityInputs).find(input => 
                    input.offsetParent !== null
                );
            }
            
            if (targetInput) {
                targetInput.value = Math.round(value);
                targetInput.focus();
                
                // Show success message
                this.showSuccessMessage(`Applied ${this.formatNumber(value)} ${unit} to form`);
                
                // Scroll to the input
                targetInput.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }
        }
    }

    showSuccessMessage(message) {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'calc-success-message';
        messageDiv.innerHTML = `
            <i class="fa fa-check-circle"></i>
            <span>${message}</span>
        `;
        
        document.body.appendChild(messageDiv);
        
        // Position near the calculator
        const calculator = document.getElementById('inventory-calculator');
        if (calculator) {
            const rect = calculator.getBoundingClientRect();
            messageDiv.style.top = rect.top + 'px';
            messageDiv.style.left = (rect.right + 10) + 'px';
        }
        
        // Auto-remove after 3 seconds
        setTimeout(() => {
            if (messageDiv.parentNode) {
                messageDiv.parentNode.removeChild(messageDiv);
            }
        }, 3000);
    }

    clearFormula() {
        const zones = [
            'calc-variables-zone',
            'calc-operators-zone', 
            'calc-formula-zone',
            'calc-results-zone'
        ];
        
        zones.forEach(zoneId => {
            const zone = document.getElementById(zoneId);
            if (zone) {
                zone.innerHTML = '';
            }
        });
        
        this.variables.clear();
        this.formula = [];
        this.saveToStorage();
    }

    saveAsTemplate() {
        const templateName = prompt('Enter template name:');
        if (!templateName) return;

        const template = {
            name: templateName,
            description: prompt('Enter template description:') || '',
            variables: Array.from(this.variables.keys()),
            formula: this.formula.join(' '),
            units: {}
        };

        // Collect units for each variable
        this.variables.forEach((variable, name) => {
            template.units[name] = variable.unit;
        });

        const templateKey = 'custom_' + Date.now();
        this.templates.set(templateKey, template);
        
        // Add to template selector
        const templateSelect = document.getElementById('calc-template-select');
        if (templateSelect) {
            const option = document.createElement('option');
            option.value = templateKey;
            option.textContent = template.name;
            templateSelect.appendChild(option);
        }

        this.saveToStorage();
        this.showSuccessMessage(`Template "${templateName}" saved successfully!`);
    }

    updateFormulaDisplay() {
        const formulaDisplayContent = document.getElementById('formula-display-content');
        if (formulaDisplayContent) {
            if (this.formula.length > 0) {
                // Build a readable formula display
                let readableFormula = '';
                let inBrackets = false;
                let bracketCount = 0;
                
                this.formula.forEach((token, index) => {
                    if (token === '(') {
                        readableFormula += token;
                        inBrackets = true;
                        bracketCount++;
                    } else if (token === ')') {
                        readableFormula += token;
                        inBrackets = false;
                        bracketCount--;
                    } else if (inBrackets && bracketCount > 0) {
                        // Add operator inside brackets
                        readableFormula += ` ${token} `;
                    } else {
                        // Add operator outside brackets with spacing
                        if (index > 0 && ['+', '-', '*', '/'].includes(token)) {
                            readableFormula += ` ${token} `;
                        } else {
                            readableFormula += token;
                        }
                    }
                });
                
                formulaDisplayContent.innerHTML = `
                    <div class="formula-display-text">
                        ${readableFormula}
                    </div>
                    <div class="formula-display-example">
                        <small>Example: (100 × 0.5) ÷ 25 = 2</small>
                    </div>
                `;
            } else {
                formulaDisplayContent.innerHTML = `
                    <div class="empty-state">
                        <i class="fa fa-edit"></i>
                        <p>Build your formula below</p>
                    </div>
                `;
            }
        }
    }

    saveToStorage() {
        const data = {
            formula: this.formula,
            variables: Object.fromEntries(this.variables),
            history: this.history,
            calculationHistory: this.calculationHistory,
            templates: Array.from(this.templates.entries())
        };
        
        localStorage.setItem('inventoryCalculator', JSON.stringify(data));
    }

    // Standard Calculator Methods
    setupStandardCalculator() {
        // Setup standard calculator button event listeners
        const calcButtons = document.querySelectorAll('.calc-btn');
        calcButtons.forEach(button => {
            button.addEventListener('click', (e) => {
                const action = e.target.dataset.action;
                const number = e.target.dataset.number;
                
                if (number !== undefined) {
                    this.inputNumber(number);
                } else if (action) {
                    this.handleCalculatorAction(action);
                }
            });
        });

        // Keyboard support
        document.addEventListener('keydown', (e) => {
            if (this.currentMode === 'standard') {
                this.handleKeyPress(e);
            }
        });
    }

    toggleCalculatorMode() {
        const inventoryMain = document.querySelector('.calc-main');
        const standardMain = document.getElementById('standard-calculator');
        const modeIcon = document.getElementById('calc-mode-icon');
        const modeTitle = document.getElementById('calc-mode-title');
        const modeText = document.getElementById('calc-mode-text');
        const saveTemplateBtn = document.getElementById('calc-save-template-btn');
        const tourBtn = document.getElementById('calc-tour-btn');

        if (this.currentMode === 'inventory') {
            // Switch to standard mode
            this.currentMode = 'standard';
            if (inventoryMain) inventoryMain.style.display = 'none';
            if (standardMain) standardMain.style.display = 'block';
            if (modeIcon) modeIcon.className = 'fa fa-calculator';
            if (modeTitle) modeTitle.textContent = 'Standard Calculator';
            if (modeText) modeText.textContent = 'Inventory Calc';
            if (saveTemplateBtn) saveTemplateBtn.style.display = 'none';
            if (tourBtn) tourBtn.style.display = 'none';
            
            // Update display
            this.updateStandardDisplay();
        } else {
            // Switch to inventory mode
            this.currentMode = 'inventory';
            if (inventoryMain) inventoryMain.style.display = 'flex';
            if (standardMain) standardMain.style.display = 'none';
            if (modeIcon) modeIcon.className = 'fa fa-calculator';
            if (modeTitle) modeTitle.textContent = 'Universal Inventory Calculator';
            if (modeText) modeText.textContent = 'Standard Calc';
            if (saveTemplateBtn) saveTemplateBtn.style.display = 'flex';
            if (tourBtn) tourBtn.style.display = 'flex';
        }
    }

    inputNumber(num) {
        if (this.waitingForOperand) {
            this.currentValue = '0';
            this.waitingForOperand = false;
        }

        if (this.currentValue === '0') {
            this.currentValue = num;
        } else {
            this.currentValue += num;
        }

        this.updateStandardDisplay();
    }

    handleCalculatorAction(action) {
        switch (action) {
            case 'clear':
                this.standardClear();
                break;
            case 'ce':
                this.currentValue = '0';
                this.updateStandardDisplay();
                break;
            case 'backspace':
                if (this.currentValue.length > 1) {
                    this.currentValue = this.currentValue.slice(0, -1);
                } else {
                    this.currentValue = '0';
                }
                this.updateStandardDisplay();
                break;
            case 'decimal':
                this.inputDecimal();
                break;
            case 'equals':
                this.performOperation();
                break;
            case 'negate':
                this.negate();
                break;
            case 'percent':
                this.percentage();
                break;
            case 'sqrt':
                this.squareRoot();
                break;
            case 'square':
                this.square();
                break;
            case 'reciprocal':
                this.reciprocal();
                break;
            case 'memory-clear':
                this.memory = 0;
                break;
            case 'memory-recall':
                this.currentValue = this.memory.toString();
                this.updateStandardDisplay();
                break;
            case 'memory-add':
                this.memory += parseFloat(this.currentValue);
                break;
            case 'memory-subtract':
                this.memory -= parseFloat(this.currentValue);
                break;
            case 'memory-store':
                this.memory = parseFloat(this.currentValue);
                break;
            default:
                // Handle basic operations
                if (['add', 'subtract', 'multiply', 'divide'].includes(action)) {
                    this.setOperation(action);
                }
                break;
        }
    }

    inputDecimal() {
        if (this.waitingForOperand) {
            this.currentValue = '0';
            this.waitingForOperand = false;
        }

        if (!this.currentValue.includes('.')) {
            this.currentValue += '.';
            this.updateStandardDisplay();
        }
    }

    setOperation(nextOperation) {
        const inputValue = parseFloat(this.currentValue);

        if (this.previousValue === null) {
            this.previousValue = inputValue;
        } else if (this.operation) {
            const currentValue = this.previousValue || 0;
            const newValue = this.performCalculation(currentValue, inputValue, this.operation);
            
            this.currentValue = newValue.toString();
            this.previousValue = newValue;
            this.updateStandardDisplay();
        }

        this.waitingForOperand = true;
        this.operation = nextOperation;
    }

    performOperation() {
        if (this.operation && this.previousValue !== null) {
            const inputValue = parseFloat(this.currentValue);
            const result = this.performCalculation(this.previousValue, inputValue, this.operation);
            
            // Add to calculation history
            this.addToStandardHistory(this.previousValue, this.operation, inputValue, result);
            
            this.currentValue = result.toString();
            this.previousValue = null;
            this.operation = null;
            this.waitingForOperand = true;
            this.updateStandardDisplay();
        }
    }

    performCalculation(firstOperand, secondOperand, operation) {
        switch (operation) {
            case 'add':
                return firstOperand + secondOperand;
            case 'subtract':
                return firstOperand - secondOperand;
            case 'multiply':
                return firstOperand * secondOperand;
            case 'divide':
                return secondOperand !== 0 ? firstOperand / secondOperand : 0;
            default:
                return secondOperand;
        }
    }

    negate() {
        const value = parseFloat(this.currentValue);
        this.currentValue = (-value).toString();
        this.updateStandardDisplay();
    }

    percentage() {
        const value = parseFloat(this.currentValue);
        this.currentValue = (value / 100).toString();
        this.updateStandardDisplay();
    }

    squareRoot() {
        const value = parseFloat(this.currentValue);
        if (value >= 0) {
            this.currentValue = Math.sqrt(value).toString();
            this.updateStandardDisplay();
        }
    }

    square() {
        const value = parseFloat(this.currentValue);
        this.currentValue = (value * value).toString();
        this.updateStandardDisplay();
    }

    reciprocal() {
        const value = parseFloat(this.currentValue);
        if (value !== 0) {
            this.currentValue = (1 / value).toString();
            this.updateStandardDisplay();
        }
    }

    standardClear() {
        this.currentValue = '0';
        this.previousValue = null;
        this.operation = null;
        this.waitingForOperand = false;
        this.updateStandardDisplay();
    }

    updateStandardDisplay() {
        const display = document.getElementById('calc-current-input');
        const historyDisplay = document.getElementById('calc-history-display');
        
        if (display) {
            display.textContent = this.formatStandardNumber(this.currentValue);
        }
        
        if (historyDisplay) {
            let historyText = '';
            if (this.previousValue !== null && this.operation) {
                const operationSymbol = this.getOperationSymbol(this.operation);
                historyText = `${this.formatStandardNumber(this.previousValue.toString())} ${operationSymbol}`;
            }
            historyDisplay.textContent = historyText;
        }
    }

    formatStandardNumber(value) {
        const num = parseFloat(value);
        if (isNaN(num)) return '0';
        
        // Remove trailing zeros after decimal
        if (value.includes('.')) {
            return parseFloat(num.toFixed(8)).toString();
        }
        return num.toString();
    }

    getOperationSymbol(operation) {
        const symbols = {
            'add': '+',
            'subtract': '−',
            'multiply': '×',
            'divide': '÷'
        };
        return symbols[operation] || '';
    }

    standardCalculate() {
        this.performOperation();
    }

    addToStandardHistory(firstOperand, operation, secondOperand, result) {
        const operationSymbol = this.getOperationSymbol(operation);
        const historyEntry = {
            timestamp: new Date().toISOString(),
            expression: `${this.formatStandardNumber(firstOperand.toString())} ${operationSymbol} ${this.formatStandardNumber(secondOperand.toString())}`,
            result: result
        };

        this.calculationHistory.unshift(historyEntry);
        if (this.calculationHistory.length > 10) {
            this.calculationHistory = this.calculationHistory.slice(0, 10);
        }

        // Update inventory calculator history display if available
        this.updateStandardHistoryDisplay();
        this.saveToStorage();
    }

    updateStandardHistoryDisplay() {
        const historyContainer = document.getElementById('calc-history');
        if (!historyContainer || this.currentMode !== 'inventory') return;

        historyContainer.innerHTML = '';
        
        this.calculationHistory.forEach((entry, index) => {
            const historyItem = document.createElement('div');
            historyItem.className = 'history-item';
            historyItem.innerHTML = `
                <div class="history-header">
                    <span class="history-time">${new Date(entry.timestamp).toLocaleString()}</span>
                    <button class="history-load" onclick="inventoryCalculator.loadFromStandardHistory(${index})">
                        <i class="fa fa-redo"></i> Load
                    </button>
                </div>
                <div class="history-content">
                    <div class="history-result">${this.formatStandardNumber(entry.result.toString())}</div>
                    <div class="history-formula">${entry.expression}</div>
                </div>
            `;
            historyContainer.appendChild(historyItem);
        });
    }

    loadFromStandardHistory(index) {
        const entry = this.calculationHistory[index];
        if (!entry) return;

        this.currentValue = entry.result.toString();
        this.previousValue = null;
        this.operation = null;
        this.waitingForOperand = false;
        this.updateStandardDisplay();
    }

    handleKeyPress(event) {
        const key = event.key;
        
        // Prevent default for calculator keys
        if (['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '.', '+', '-', '*', '/', '=', 'Enter', 'Escape', 'Backspace'].includes(key)) {
            event.preventDefault();
        }

        // Handle number keys
        if (key >= '0' && key <= '9') {
            this.inputNumber(key);
        }
        // Handle decimal
        else if (key === '.') {
            this.inputDecimal();
        }
        // Handle operations
        else if (key === '+') {
            this.setOperation('add');
        } else if (key === '-') {
            this.setOperation('subtract');
        } else if (key === '*') {
            this.setOperation('multiply');
        } else if (key === '/') {
            this.setOperation('divide');
        }
        // Handle equals
        else if (key === '=' || key === 'Enter') {
            this.performOperation();
        }
        // Handle clear
        else if (key === 'Escape') {
            this.standardClear();
        }
        // Handle backspace
        else if (key === 'Backspace') {
            if (this.currentValue.length > 1) {
                this.currentValue = this.currentValue.slice(0, -1);
            } else {
                this.currentValue = '0';
            }
            this.updateStandardDisplay();
        }
    }

    loadFromStorage() {
        try {
            const data = localStorage.getItem('inventoryCalculator');
            if (data) {
                const parsed = JSON.parse(data);
                
                if (parsed.variables) {
                    this.variables = new Map(Object.entries(parsed.variables));
                }
                
                if (parsed.history) {
                    this.history = parsed.history;
                    this.updateHistoryDisplay();
                }
                
                if (parsed.calculationHistory) {
                    this.calculationHistory = parsed.calculationHistory;
                    this.updateStandardHistoryDisplay();
                }
                
                if (parsed.templates) {
                    this.templates = new Map(parsed.templates);
                }
            }
        } catch (error) {
            console.warn('Failed to load calculator data from storage:', error);
        }
    }
}

// Guided Tour Class
class CalculatorGuidedTour {
    constructor(calculator) {
        this.calculator = calculator;
        this.currentStep = 0;
        this.isActive = false;
        this.tourOverlay = null;
        this.highlightElement = null;
        this.tooltip = null;
        
        this.steps = [
            {
                element: '.calc-title',
                title: 'Welcome to the Universal Inventory Calculator!',
                content: 'This powerful tool helps you calculate inventory needs with drag-and-drop simplicity. Let me show you how it works!',
                position: 'bottom'
            },
            {
                element: '.calc-sidebar',
                title: 'Building Blocks',
                content: 'Here you\'ll find all the building blocks for your calculations: variables, operators, and functions. Drag these from the sidebar to the workspace.',
                position: 'right'
            },
            {
                element: '#calc-variables-zone',
                title: 'Variables Zone',
                content: 'Drop variables here to define the values you want to work with. Each variable can have a value and unit.',
                position: 'top'
            },
            {
                element: '#calc-operators-zone',
                title: 'Operators Zone',
                content: 'Place mathematical operators here to build your formula. You can add, subtract, multiply, and divide.',
                position: 'top'
            },
            {
                element: '#calc-formula-zone',
                title: 'Formula Builder',
                content: 'This is where you assemble your complete formula by combining variables and operators.',
                position: 'top'
            },
            {
                element: '#calc-results-zone',
                title: 'Results Display',
                content: 'Your calculation results will appear here. You can copy results or apply them directly to your inventory forms.',
                position: 'top'
            },
            {
                element: '#calc-template-select',
                title: 'Quick Start Templates',
                content: 'Use pre-built templates for common calculations like tape roll calculations, material coverage, and more!',
                position: 'left'
            },
            {
                element: '.draggable-item[data-name="roll_length"]',
                title: 'Example: Roll Length Variable',
                content: 'Let\'s try a practical example! This "Roll Length" variable is perfect for calculating tape requirements. Drag it to the Variables zone.',
                position: 'right'
            },
            {
                element: '.draggable-item[data-name="tape_per_unit"]',
                title: 'Example: Tape per Unit',
                content: 'This variable represents how much tape each unit needs. Drag this to the Variables zone as well.',
                position: 'right'
            },
            {
                element: '.draggable-item[data-name="units"]',
                title: 'Example: Units Variable',
                content: 'Finally, drag the "Units" variable to represent how many items you need to process.',
                position: 'right'
            },
            {
                element: '.draggable-item[data-value="*"]',
                title: 'Add Operators',
                content: 'Now drag the multiplication operator (*) to the Operators zone to multiply units by tape per unit.',
                position: 'right'
            },
            {
                element: '.draggable-item[data-value="/"]',
                title: 'Division Operator',
                content: 'Add the division operator (/) to divide by roll length and get the number of rolls needed.',
                position: 'right'
            },
            {
                element: '#calc-calculate-btn',
                title: 'Calculate Your Result',
                content: 'Once you\'ve built your formula and entered values, click Calculate to see the result!',
                position: 'top'
            },
            {
                element: '#calc-clear-btn',
                title: 'Start Fresh',
                content: 'Use the Clear button to reset everything and start a new calculation.',
                position: 'top'
            },
            {
                element: '#calc-save-template-btn',
                title: 'Save Your Work',
                content: 'Created a useful formula? Save it as a template for future use!',
                position: 'top'
            }
        ];
    }

    start() {
        if (this.isActive) return;
        
        this.isActive = true;
        this.currentStep = 0;
        this.createOverlay();
        this.showStep(0);
        
        // Store tour state
        localStorage.setItem('calculatorTourCompleted', 'false');
    }

    createOverlay() {
        // Create overlay
        this.tourOverlay = document.createElement('div');
        this.tourOverlay.className = 'tour-overlay';
        this.tourOverlay.innerHTML = `
            <div class="tour-backdrop"></div>
            <div class="tour-highlight"></div>
            <div class="tour-tooltip">
                <div class="tour-header">
                    <h3 class="tour-title"></h3>
                    <button class="tour-close">&times;</button>
                </div>
                <div class="tour-content"></div>
                <div class="tour-footer">
                    <button class="tour-prev">Previous</button>
                    <div class="tour-progress"></div>
                    <button class="tour-next">Next</button>
                    <button class="tour-finish" style="display: none;">Finish Tour</button>
                </div>
            </div>
        `;
        
        document.body.appendChild(this.tourOverlay);
        
        // Setup event listeners
        this.tourOverlay.querySelector('.tour-close').addEventListener('click', () => this.end());
        this.tourOverlay.querySelector('.tour-prev').addEventListener('click', () => this.previousStep());
        this.tourOverlay.querySelector('.tour-next').addEventListener('click', () => this.nextStep());
        this.tourOverlay.querySelector('.tour-finish').addEventListener('click', () => this.end());
        
        // Close on escape
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.isActive) {
                this.end();
            }
        });
    }

    showStep(stepIndex) {
        if (stepIndex < 0 || stepIndex >= this.steps.length) return;
        
        const step = this.steps[stepIndex];
        const element = document.querySelector(step.element);
        
        if (!element) {
            console.warn(`Tour element not found: ${step.element}`);
            this.nextStep();
            return;
        }
        
        // Update highlight
        this.highlightElement = this.tourOverlay.querySelector('.tour-highlight');
        const rect = element.getBoundingClientRect();
        this.highlightElement.style.cssText = `
            position: fixed;
            top: ${rect.top - 5}px;
            left: ${rect.left - 5}px;
            width: ${rect.width + 10}px;
            height: ${rect.height + 10}px;
            border: 3px solid #3498db;
            border-radius: 8px;
            box-shadow: 0 0 0 9999px rgba(0, 0, 0, 0.7);
            z-index: 10001;
            transition: all 0.3s ease;
        `;
        
        // Update tooltip
        this.tooltip = this.tourOverlay.querySelector('.tour-tooltip');
        this.tooltip.querySelector('.tour-title').textContent = step.title;
        this.tooltip.querySelector('.tour-content').textContent = step.content;
        
        // Position tooltip
        this.positionTooltip(element, step.position);
        
        // Update progress
        this.tourOverlay.querySelector('.tour-progress').textContent = `${stepIndex + 1} / ${this.steps.length}`;
        
        // Update buttons
        const prevBtn = this.tourOverlay.querySelector('.tour-prev');
        const nextBtn = this.tourOverlay.querySelector('.tour-next');
        const finishBtn = this.tourOverlay.querySelector('.tour-finish');
        
        prevBtn.style.display = stepIndex === 0 ? 'none' : 'inline-block';
        nextBtn.style.display = stepIndex === this.steps.length - 1 ? 'none' : 'inline-block';
        finishBtn.style.display = stepIndex === this.steps.length - 1 ? 'inline-block' : 'none';
        
        // Scroll element into view if needed
        element.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }

    positionTooltip(element, position) {
        const rect = element.getBoundingClientRect();
        const tooltip = this.tooltip;
        const tooltipRect = tooltip.getBoundingClientRect();
        
        let top, left;
        
        switch (position) {
            case 'top':
                top = rect.top - tooltipRect.height - 20;
                left = rect.left + (rect.width - tooltipRect.width) / 2;
                break;
            case 'bottom':
                top = rect.bottom + 20;
                left = rect.left + (rect.width - tooltipRect.width) / 2;
                break;
            case 'left':
                top = rect.top + (rect.height - tooltipRect.height) / 2;
                left = rect.left - tooltipRect.width - 20;
                break;
            case 'right':
                top = rect.top + (rect.height - tooltipRect.height) / 2;
                left = rect.right + 20;
                break;
            default:
                top = rect.bottom + 20;
                left = rect.left + (rect.width - tooltipRect.width) / 2;
        }
        
        // Ensure tooltip stays within viewport
        top = Math.max(10, Math.min(top, window.innerHeight - tooltipRect.height - 10));
        left = Math.max(10, Math.min(left, window.innerWidth - tooltipRect.width - 10));
        
        tooltip.style.cssText = `
            position: fixed;
            top: ${top}px;
            left: ${left}px;
            z-index: 10002;
            max-width: 400px;
        `;
    }

    nextStep() {
        if (this.currentStep < this.steps.length - 1) {
            this.currentStep++;
            this.showStep(this.currentStep);
        }
    }

    previousStep() {
        if (this.currentStep > 0) {
            this.currentStep--;
            this.showStep(this.currentStep);
        }
    }

    end() {
        this.isActive = false;
        if (this.tourOverlay) {
            this.tourOverlay.remove();
            this.tourOverlay = null;
        }
        
        // Mark tour as completed
        localStorage.setItem('calculatorTourCompleted', 'true');
        
        // Show completion message
        this.calculator.showSuccessMessage('Tour completed! You\'re ready to use the calculator.');
    }

    checkFirstTime() {
        const completed = localStorage.getItem('calculatorTourCompleted');
        if (completed !== 'true') {
            // Auto-start tour for first-time users
            setTimeout(() => {
                this.start();
            }, 1000);
        }
    }
}

// Initialize the calculator when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    window.inventoryCalculator = new InventoryCalculator();
    
    // Initialize guided tour
    window.calculatorTour = new CalculatorGuidedTour(window.inventoryCalculator);
    
    // Check if this is first time using calculator
    window.calculatorTour.checkFirstTime();
});
