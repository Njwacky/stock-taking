# Universal Inventory Calculator - Architecture Documentation

## Overview

The Universal Inventory Calculator is a sophisticated drag-and-drop calculation system integrated into your Django stock management application. It enables users to build complex inventory formulas with unit conversions, supporting scenarios like:

- "I have 100 units, each uses 350mm of tape, and tape rolls are 33m — how many rolls do I need?"
- Material coverage calculations with overlap considerations
- Liquid mixing ratios
- Kit assembly component calculations

## Architecture Components

### Frontend (Client-Side)

#### 1. Core JavaScript Module (`static/js/inventory-calculator.js`)
- **Class**: `InventoryCalculator`
- **Features**:
  - Drag-and-drop formula building
  - Unit conversion system
  - Template management
  - Calculation history
  - Local storage persistence
  - Form integration

#### 2. UI Components (`stockT/templates/inventory_calculator.html`)
- **Drag Zones**: Variables, Operators, Formula Builder, Results
- **Sidebar**: Templates, Elements, Functions
- **Controls**: Calculate, Clear, Save Template, Close

#### 3. Styling (`static/css/inventory-calculator.css`)
- **Responsive Design**: Mobile-first approach
- **Visual Feedback**: Hover states, drag indicators
- **Accessibility**: High contrast, reduced motion support

### Backend (Server-Side)

#### 1. Calculator API (`stockT/api_calculator.py`)
- **UnitConverter Class**: Handles unit conversions across categories
- **FormulaEvaluator Class**: Safe mathematical expression evaluation
- **Security**: Sandboxed evaluation with allowed functions only

#### 2. API Endpoints (`stockT/urls.py`)
```
/api/calculator/calculate/    # Calculate expressions
/api/calculator/convert/      # Convert units
/api/calculator/validate/     # Validate formula syntax
/api/calculator/rates/        # Get conversion rates
/api/calculator/batch/        # Batch calculations
```

## Key Features

### 1. Drag-and-Drop Interface
- **Visual Formula Building**: Drag variables, operators, and functions
- **Smart Zones**: Organized areas for different element types
- **Real-time Validation**: Immediate feedback on formula syntax

### 2. Unit Conversion System
**Supported Categories**:
- **Length**: mm, cm, m, km, in, ft, yd
- **Volume**: ml, l, kl, gal, oz
- **Area**: mm², cm², m², km², in², ft²
- **Weight**: g, kg, t, oz, lb
- **Inventory**: pieces, rolls, boxes, kits, bottles, units

### 3. Template System
**Built-in Templates**:
- **Tape Roll Calculator**: `(units * tape_per_unit) / roll_length`
- **Material Coverage**: `(area * (1 + overlap/100)) / material_width`
- **Liquid Mixing**: Component ratio calculations
- **Kit Assembly**: Spare percentage calculations

### 4. Form Integration
- **Smart Field Mapping**: Automatically applies results to appropriate form fields
- **Context Awareness**: Understands tape vs. piece vs. liquid units
- **One-Click Application**: Direct integration with add items form

## Technical Implementation

### Frontend Architecture

```javascript
class InventoryCalculator {
    constructor() {
        this.formula = [];
        this.variables = new Map();
        this.units = new Map();
        this.templates = new Map();
        this.history = [];
    }
    
    // Core methods
    setupDragZones()      // Initialize drag-drop zones
    evaluateExpression()     // Calculate results
    convertUnits()         // Handle unit conversions
    applyToForm()         // Integration with forms
}
```

### Backend Architecture

```python
class UnitConverter:
    CONVERSION_RATES = {
        'length': {'mm': 0.001, 'cm': 0.01, 'm': 1, ...},
        'volume': {'ml': 0.001, 'l': 1, 'kl': 1000, ...},
        # ... other categories
    }
    
    @classmethod
    def convert(cls, value, from_unit, to_unit, category):
        # Safe unit conversion logic

class FormulaEvaluator:
    ALLOWED_FUNCTIONS = {'round': round, 'ceil': ..., 'floor': ...}
    
    @classmethod
    def evaluate(cls, expression, variables):
        # Safe expression evaluation
```

## Integration Points

### 1. Add Items Page
- **Location**: `/add_items/`
- **Integration**: Calculator modal embedded in page
- **Data Flow**: Calculator results → Form fields

### 2. Template System
- **Storage**: LocalStorage for persistence
- **Sharing**: Templates saved per user session
- **Pre-built**: Industry-specific templates included

### 3. Unit System
- **Extensible**: Easy to add new units
- **Categorized**: Logical grouping of measurement types
- **Precise**: Decimal-based calculations for accuracy

## Usage Examples

### Example 1: Tape Roll Calculation
1. **Drag**: "units" variable → Set value: 100
2. **Drag**: "*" operator
3. **Drag**: "tape_per_unit" variable → Set value: 350mm
4. **Drag**: "/" operator
5. **Drag**: "roll_length" variable → Set value: 33m
6. **Calculate**: Result: 1.06 rolls

### Example 2: Material Coverage
1. **Template**: Select "Material Coverage"
2. **Variables**: 
   - Area: 50m²
   - Material Width: 1.2m
   - Overlap: 10%
3. **Calculate**: Result: 45.83m of material needed

### Example 3: Liquid Mixing
1. **Template**: Select "Liquid Mixing"
2. **Variables**:
   - Total Volume: 10l
   - Ratio A: 30%
   - Ratio B: 70%
3. **Calculate**: 
   - Component A: 3l
   - Component B: 7l

## Security Considerations

### Frontend
- **Input Validation**: Client-side validation before API calls
- **XSS Prevention**: Safe DOM manipulation
- **CSRF Protection**: Django CSRF tokens used

### Backend
- **Expression Sandboxing**: Only allowed functions and operators
- **Input Sanitization**: Regex-based validation
- **Error Handling**: Graceful failure with informative messages

## Performance Optimizations

### Frontend
- **Lazy Loading**: Templates loaded on demand
- **Debounced Calculations**: Prevent excessive API calls
- **Local Storage**: Cache frequently used calculations

### Backend
- **Decimal Precision**: Avoid floating-point errors
- **Efficient Conversions**: Pre-calculated conversion rates
- **Batch Processing**: Handle multiple calculations efficiently

## Extensibility

### Adding New Units
```python
# In UnitConverter.CONVERSION_RATES
'new_category': {
    'unit1': Decimal('1.0'),
    'unit2': Decimal('0.5'),
    # ...
}
```

### Adding New Templates
```javascript
// In InventoryCalculator.initializeTemplates()
this.templates.set('new_template', {
    name: 'Custom Template',
    description: 'Description',
    variables: ['var1', 'var2'],
    formula: '(var1 + var2) * factor',
    units: { var1: 'm', var2: 'kg', result: 'units' }
});
```

### Adding New Functions
```python
# In FormulaEvaluator.ALLOWED_FUNCTIONS
'new_function': lambda x: custom_logic(x),
```

## Mobile Responsiveness

### Breakpoints
- **Desktop**: > 768px - Full sidebar and grid layout
- **Tablet**: 480px-768px - Collapsed sidebar, single column
- **Mobile**: < 480px - Hidden sidebar, stacked layout

### Touch Support
- **Touch Events**: Proper touch event handling
- **Gesture Support**: Swipe gestures for navigation
- **Large Targets**: Touch-friendly button sizes

## Browser Compatibility

### Supported Browsers
- **Chrome**: 80+ (recommended)
- **Firefox**: 75+ (recommended)
- **Safari**: 13+ (iOS), 11+ (macOS)
- **Edge**: 80+ (Chromium-based)

### Fallbacks
- **Drag & Drop**: Click-based fallback for older browsers
- **Local Storage**: Session storage fallback
- **ES6 Features**: Polyfills for older browsers

## Testing Strategy

### Frontend Tests
- **Unit Tests**: Individual method testing
- **Integration Tests**: Full workflow testing
- **UI Tests**: Visual regression testing

### Backend Tests
- **API Tests**: Endpoint validation
- **Calculation Tests**: Accuracy verification
- **Security Tests**: Input validation testing

## Deployment Considerations

### Static Files
- **Versioning**: Cache-busting with timestamps
- **Compression**: Minified CSS/JS for production
- **CDN**: Optional CDN deployment for static assets

### Database
- **No Database Required**: Stateless calculator design
- **Optional Persistence**: User templates could be stored in DB
- **Scalability**: Horizontal scaling friendly

## Future Enhancements

### Planned Features
1. **Advanced Unit Algebra**: Proper unit manipulation (m² → m × m)
2. **Visual Formula Builder**: Graphical formula representation
3. **Export/Import**: Template sharing between users
4. **Mobile App**: Native mobile application
5. **API Integration**: Connect to external inventory systems

### Performance Improvements
1. **Web Workers**: Background calculations
2. **Service Workers**: Offline functionality
3. **Caching**: Redis-based calculation caching
4. **CDN**: Global content delivery

## Support and Maintenance

### Documentation
- **Inline Help**: Contextual tooltips and guides
- **Video Tutorials**: Step-by-step video guides
- **FAQ Section**: Common questions and answers

### Monitoring
- **Error Tracking**: Client-side error reporting
- **Usage Analytics**: Feature usage statistics
- **Performance Metrics**: Response time monitoring

---

This architecture provides a robust, scalable, and user-friendly inventory calculation system that integrates seamlessly with your existing Django stock management application.
