// Simple Calculator
let currentInput = '0';
let previousInput = '';
let operation = null;
let resetScreen = false;

const calculator = document.getElementById('popup-calculator');
const calcDisplay = document.getElementById('calc-input');
const calcResult = document.getElementById('calc-result');
const calcToggleBtn = document.getElementById('calculatorToggle');
const closeBtn = document.getElementById('closeCalculator');

// Initialize calculator
document.addEventListener('DOMContentLoaded', () => {
    // Hide calculator by default
    calculator.style.display = 'none';
    
    // Toggle calculator visibility
    if (calcToggleBtn) {
        calcToggleBtn.addEventListener('click', toggleCalculator);
    }
    
    // Close button
    if (closeBtn) {
        closeBtn.addEventListener('click', toggleCalculator);
    }
    
    // Number buttons
    document.querySelectorAll('.calc-number').forEach(button => {
        button.addEventListener('click', () => appendNumber(button.textContent.trim()));
    });
    
    // Operator buttons
    document.querySelectorAll('.calc-operator').forEach(button => {
        button.addEventListener('click', () => setOperation(button.textContent.trim()));
    });
    
    // Clear buttons
    document.querySelectorAll('.calc-clear').forEach(button => {
        if (button.textContent.trim() === 'C') {
            button.addEventListener('click', clearAll);
        } else if (button.textContent.trim() === 'CE') {
            button.addEventListener('click', clearEntry);
        }
    });
    
    // Initialize display
    updateDisplay();
    
    // Keyboard support
    document.addEventListener('keydown', handleKeyboardInput);
});

// Toggle calculator visibility
function toggleCalculator() {
    if (calculator.style.display === 'block') {
        calculator.style.display = 'none';
        calcToggleBtn.style.display = 'block';
        document.removeEventListener('click', handleOutsideClick);
    } else {
        calculator.style.display = 'block';
        calcToggleBtn.style.display = 'none';
        calcDisplay.focus();
        // Add click outside handler
        setTimeout(() => document.addEventListener('click', handleOutsideClick), 0);
    }
}

// Close calculator when clicking outside
function handleOutsideClick(e) {
    if (!calculator.contains(e.target) && !calcToggleBtn.contains(e.target)) {
        toggleCalculator();
    }
}

// Update the calculator display
function updateDisplay() {
    calcDisplay.value = currentInput;
}

// Append a number to the current input
function appendNumber(number) {
    if (currentInput === '0' || resetScreen) {
        currentInput = number;
        resetScreen = false;
    } else {
        currentInput += number;
    }
    updateDisplay();
}

// Set the operation
function setOperation(op) {
    if (operation !== null) calculate();
    previousInput = currentInput;
    operation = op;
    resetScreen = true;
    updateDisplay();
}

// Perform the calculation
function calculate() {
    if (operation === null || resetScreen) return;
    
    let result;
    const prev = parseFloat(previousInput);
    const current = parseFloat(currentInput);
    
    if (isNaN(prev) || isNaN(current)) return;
    
    try {
        switch (operation) {
            case '+':
                result = prev + current;
                break;
            case '-':
                result = prev - current;
                break;
            case '×':
                result = prev * current;
                break;
            case '÷':
                result = prev / current;
                break;
            default:
                return;
        }
        
        // Handle decimal places
        result = Math.round(result * 1000000) / 1000000; // Limit to 6 decimal places
        
        currentInput = result.toString();
        operation = null;
        previousInput = '';
        resetScreen = true;
        
        // Show result in the result display
        calcResult.textContent = `= ${result}`;
        updateDisplay();
    } catch (error) {
        currentInput = 'Error';
        updateDisplay();
    }
}

// Clear all inputs
function clearAll() {
    currentInput = '0';
    previousInput = '';
    operation = null;
    calcResult.textContent = '';
    updateDisplay();
}

// Clear the last entry
function clearEntry() {
    if (currentInput.length === 1) {
        currentInput = '0';
    } else {
        currentInput = currentInput.slice(0, -1);
    }
    updateDisplay();
}

// Handle keyboard input
function handleKeyboardInput(e) {
    if (calculator.style.display !== 'block') return;
    
    if (/[0-9.]/.test(e.key)) {
        e.preventDefault();
        appendNumber(e.key);
    } else if (['+', '-', '*', '/'].includes(e.key)) {
        e.preventDefault();
        setOperation(e.key === '*' ? '×' : e.key === '/' ? '÷' : e.key);
    } else if (e.key === 'Enter' || e.key === '=') {
        e.preventDefault();
        calculate();
    } else if (e.key === 'Escape') {
        e.preventDefault();
        clearAll();
    } else if (e.key === 'Backspace') {
        e.preventDefault();
        clearEntry();
    } else if (e.key.toLowerCase() === 'c') {
        e.preventDefault();
        clearAll();
    }
}

// Simple VHB calculation
function updateVHB(qtyId, meterId) {
    const rolls = document.getElementById(qtyId)?.value;
    if (rolls) {
        const meters = rolls * 33;
        const meterElement = document.getElementById(meterId);
        if (meterElement) {
            meterElement.textContent = `${meters}m`;
        }
    }
}
// Make calculator draggable
function makeCalculatorDraggable() {
    const calc = document.getElementById('popup-calculator');
    const calcHandle = document.querySelector('.calc-drag-handle');
    
    if (!calc || !calcHandle) return;
    
    let isDragging = false;
    let currentX;
    let currentY;
    let initialX;
    let initialY;
    let xOffset = 0;
    let yOffset = 0;

    calcHandle.addEventListener('mousedown', dragStart);
    document.addEventListener('mousemove', drag);
    document.addEventListener('mouseup', dragEnd);

    function dragStart(e) {
        initialX = e.clientX - xOffset;
        initialY = e.clientY - yOffset;

        if (e.target === calcHandle) {
            isDragging = true;
            calc.classList.add('dragging');
        }
    }

    function drag(e) {
        if (isDragging) {
            e.preventDefault();
            currentX = e.clientX - initialX;
            currentY = e.clientY - initialY;

            xOffset = currentX;
            yOffset = currentY;

            const calcRect = calc.getBoundingClientRect();
            const minLeft = 0;
            const minTop = 0;
            const maxLeft = window.innerWidth - calcRect.width;
            const maxTop = window.innerHeight - calcRect.height;
            
            let newLeft = Math.max(minLeft, Math.min(currentX, maxLeft));
            let newTop = Math.max(minTop, Math.min(currentY, maxTop));
            
            calc.style.left = newLeft + 'px';
            calc.style.top = newTop + 'px';
            calc.style.right = '';
            calc.style.bottom = '';
            calc.style.position = 'fixed';
        }
    }

    function dragEnd(e) {
        initialX = currentX;
        initialY = currentY;
        isDragging = false;
        calc.classList.remove('dragging');
    }
}

// Initialize draggable calculator
document.addEventListener('DOMContentLoaded', function() {
    makeCalculatorDraggable();
});

// Attach checkbox change event listeners for kit quantity fields
document.addEventListener('DOMContentLoaded', function() {
    ['feets','vhb_18','vhb_12','vhb_7','pi_strips','rivnut_8','rivnut_6','rivnut_5','rivnut_4'].forEach(function(kit){
        var cb = document.getElementById(kit+'_cb');
        var qty = document.getElementById(kit+'_qty');
        if (cb && qty) {
            var parent = cb.closest ? cb.closest('.form-group') : cb.parentNode;
            cb.addEventListener('change',function(){
                qty.style.display = this.checked ? 'block' : 'none';
                if (parent) {
                    if (this.checked) {
                        parent.classList.add('active-qty');
                    } else {
                        parent.classList.remove('active-qty');
                    }
                }
            });
            // Set initial state
            qty.style.display = cb.checked ? 'block' : 'none';
            if (parent) {
                if (cb.checked) {
                    parent.classList.add('active-qty');
                } else {
                    parent.classList.remove('active-qty');
                }
            }
        }
    });
});
