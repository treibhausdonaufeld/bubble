# Categories and Items System Documentation

This document explains the dynamic category fields system in bubble, including conditional field dependencies, dynamic filtering, and display configuration.

## Overview

The categories and items system allows different types of items (Sachen, Events, Services, etc.) to have their own custom fields defined at the category level. This provides flexibility without requiring separate models for each content type. The system now includes dynamic filtering and display configuration per category.

## Architecture

### Data Models

#### ItemCategory (`bubble/categories/models.py`)
- **Hierarchical Structure**: Categories can have parent categories for unlimited nesting
- **Root Categories**: Define content types (e.g., Sachen, Events) with unique URL slugs
- **custom_fields**: JSONField containing the schema for dynamic fields
- **filters**: ArrayField listing field names to display as filters (NEW)
- **sort_by**: ArrayField listing field names available for sorting (NEW)
- **upper_tag**: CharField specifying which custom field to display in item card upper badge (NEW)
- **lower_tag**: CharField specifying which custom field to display in item card lower badge (NEW)

#### Item (`bubble/items/models.py`)
- **Single Model**: All content types use the same Item model
- **category**: ForeignKey to ItemCategory
- **custom_fields**: JSONField storing actual field values
- **Removed Fields**: The following fields have been moved to custom_fields:
  - `price`, `th_payment`, `display_contact`, `item_type`, `profile_img_frame`, `profile_img_frame_alt`

### Custom Fields Schema

The `custom_fields` in ItemCategory defines the structure of dynamic fields:

```json
{
  "field_name": {
    "type": "text|textarea|number|choice|datetime",
    "label": "Display Label",
    "required": true|false,
    "default": "default_value",          // Default value if field is not filled
    "choices": ["option1", "option2"],  // For choice fields
    "depending": "other_field_name",     // Conditional dependency
    "depending_values": ["value1", "value2"]  // Array of values that trigger display
  }
}
```

Note: For backward compatibility, `depending_value` (singular) is still supported but `depending_values` (plural, array) is preferred.

### Field Types

1. **text**: Single-line text input
2. **textarea**: Multi-line text input
3. **number**: Integer input
4. **choice**: Dropdown selection
   - Simple format: `["Option 1", "Option 2"]`
   - Key-value format: `[{"key": "db_value", "value": "Display Value"}]`
5. **datetime**: Date and time picker

### Default Values

The `default` attribute provides a fallback value when:
- A new item is created and the field is not filled
- An existing item is saved without the field value
- The field is hidden due to conditional logic

This prevents `null` values in the database and ensures consistent data.

Examples:
```json
{
  "condition": {
    "type": "choice",
    "label": "Zustand",
    "choices": ["new", "used", "defective"],
    "default": "used"  // Default to "used" if not specified
  },
  "quantity": {
    "type": "number",
    "label": "Anzahl",
    "default": 1  // Default to 1 if not specified
  },
  "description": {
    "type": "textarea",
    "label": "Beschreibung",
    "default": ""  // Default to empty string instead of null
  }
}
```

## Conditional Fields (NEW)

### Definition

Conditional fields appear/hide based on the value of another field. You can now specify multiple trigger values:

```json
{
  "device_type": {
    "type": "choice",
    "label": "Device Type",
    "choices": ["laptop", "smartphone", "tablet", "desktop"],
    "required": true
  },
  "screen_size": {
    "type": "choice",
    "label": "Screen Size",
    "choices": ["13\"", "15\"", "17\"", "21\"", "24\"", "27\""],
    "required": false,
    "depending": "device_type",
    "depending_values": ["laptop", "desktop"]  // Shows for both laptop AND desktop
  },
  "mobile_carrier": {
    "type": "choice",
    "label": "Mobile Carrier",
    "choices": ["AT&T", "Verizon", "T-Mobile"],
    "required": false,
    "depending": "device_type",
    "depending_values": ["smartphone", "tablet"]  // Shows for smartphone OR tablet
  }
}
```

In this example:
- "screen_size" appears when "device_type" is either "laptop" OR "desktop"
- "mobile_carrier" appears when "device_type" is either "smartphone" OR "tablet"

### Implementation Details

1. **Form Generation**: The `ItemForm` adds data attributes to conditional fields:
   - `data-depending`: The field this depends on
   - `data-depending-values`: JSON array of values that trigger display (or `data-depending-value` for single value)
   - CSS class `conditional-field` for JavaScript targeting

2. **JavaScript Logic**: Located in `item_form.html`:
   - Monitors changes on dependent fields
   - Shows/hides conditional fields
   - Handles required field validation
   - Clears hidden field values

3. **Validation**: 
   - Required attributes are removed when fields are hidden
   - Values are cleared to prevent invalid data submission
   - Required attributes are restored when fields become visible

## Data Flow

### Creating an Item

1. User navigates to `/sachen/create/`
2. View identifies root category from URL
3. Form generates fields from category's `custom_fields`
4. JavaScript handles conditional field visibility
5. On save, values stored in item's `custom_fields`

### Field Value Storage

Values are stored with both the value and label:

```json
{
  "size": {
    "value": "M",
    "label": "Größe"
  },
  "condition": {
    "value": "new",
    "label": "Zustand"
  }
}
```

## Dynamic Filtering and Display Configuration (NEW)

### Filter Configuration

The `filters` array in ItemCategory controls which fields appear as filters in the item list:

```python
# In ItemCategory model
filters = ['brand', 'condition', 'price_range']  # These fields will show as filters
```

### Sort Configuration

The `sort_by` array controls which fields can be used for sorting:

```python
# In ItemCategory model
sort_by = ['price', 'date_listed', 'condition']  # These fields get sort options
```

Sort options are automatically generated with both ascending (↑) and descending (↓) options for custom fields.

### Display Tag Configuration

Control what information appears on item cards:

```python
# In ItemCategory model
upper_tag = 'item_type'  # Shows this field value in the upper badge
lower_tag = 'price'      # Shows this field value in the lower badge
```

### Filter Display Logic

1. **Category Filter**: Only shown if the root category has subcategories
2. **Search Filter**: Always shown
3. **Custom Filters**: Based on the `filters` array (implementation pending)
4. **Sort Options**: Always shown with:
   - Default options: Newest first, Oldest first, Name A-Z, Name Z-A
   - Custom options: Based on `sort_by` array with ↑/↓ for each field

## Examples

### Electronics Category Configuration

```python
# ItemCategory setup
{
    "name": "Electronics",
    "url_slug": "electronics",
    "custom_fields": {
        "device_type": {
            "type": "choice",
            "label": "Gerätetyp",
            "choices": [
                {"key": "laptop", "value": "Laptop"},
                {"key": "smartphone", "value": "Smartphone"}
            ],
            "required": True
        },
        "brand": {
            "type": "choice",
            "label": "Marke",
            "choices": ["Apple", "Samsung", "Dell", "HP"],
            "required": True
        },
        "condition": {
            "type": "choice",
            "label": "Zustand",
            "choices": [
                {"key": "new", "value": "Neu"},
                {"key": "used", "value": "Gebraucht"},
                {"key": "defective", "value": "Defekt"}
            ],
            "required": True,
            "default": "used"  # Default to "Gebraucht" if not specified
        },
        "price": {
            "type": "number",
            "label": "Preis",
            "required": False,
            "default": 0  # Default to 0 if not specified
        },
        # Laptop/Desktop fields
        "ram": {
            "type": "choice",
            "label": "RAM",
            "choices": ["8GB", "16GB", "32GB", "64GB"],
            "depending": "device_type",
            "depending_values": ["laptop", "desktop"]
        },
        # Mobile device fields
        "storage": {
            "type": "choice",
            "label": "Speicher",
            "choices": ["64GB", "128GB", "256GB", "512GB", "1TB"],
            "depending": "device_type",
            "depending_values": ["smartphone", "tablet"]
        }
    },
    "filters": ["brand", "device_type", "condition"],
    "sort_by": ["price", "condition"],
    "upper_tag": "condition",
    "lower_tag": "price"
}
```

### Clothing Category Configuration

```python
# ItemCategory setup
{
    "name": "Clothing",
    "url_slug": "clothing",
    "custom_fields": {
        "clothing_type": {
            "type": "choice",
            "label": "Art",
            "choices": [
                {"key": "shirt", "value": "Oberteil"},
                {"key": "pants", "value": "Hose"},
                {"key": "shoes", "value": "Schuhe"}
            ],
            "required": True
        },
        "size": {
            "type": "choice",
            "label": "Größe",
            "choices": ["XS", "S", "M", "L", "XL", "XXL"],
            "required": True
        },
        "color": {
            "type": "choice",
            "label": "Farbe",
            "choices": ["Schwarz", "Weiß", "Blau", "Rot", "Grün"],
            "required": False
        },
        "material": {
            "type": "choice",
            "label": "Material",
            "choices": ["Baumwolle", "Polyester", "Wolle", "Leder"],
            "required": False
        },
        "shoe_size": {
            "type": "number",
            "label": "Schuhgröße",
            "depending": "clothing_type",
            "depending_values": ["shoes"]  // Using array format for consistency
        }
    },
    "filters": ["clothing_type", "size", "color", "material"],
    "sort_by": ["size"],
    "upper_tag": "clothing_type",
    "lower_tag": "size"
}
```

## Management Commands

### Setup Example Categories
```bash
just manage setup_conditional_fields_example
```

This creates example categories with conditional fields for testing.

### Setup Initial Categories
```bash
just manage setup_categories
```

Creates the standard category structure for a Wohnprojekt.

## Best Practices

1. **Field Naming**: Use descriptive, lowercase field names with underscores
2. **Labels**: Always provide German labels for user-facing text
3. **Required Fields**: Only mark fields as required if they're essential
4. **Conditional Logic**: 
   - Keep dependencies simple (one level deep)
   - Ensure dependent fields have sensible defaults
   - Test all combinations thoroughly

5. **Choice Values**: 
   - Use key-value format for choices that need translation
   - Keys should be stable (don't change in database)
   - Values can be updated for display

## Technical Implementation Details

### Template Tags

A custom template filter `get_item` is used to access dictionary values in templates:

```python
# bubble/items/templatetags/item_extras.py
@register.filter
def get_item(dictionary, key):
    """Get an item from a dictionary using a dynamic key."""
    if dictionary and key:
        return dictionary.get(key)
    return None
```

Used in templates like: `{{ item.custom_fields|get_item:field_name|get_item:"value" }}`

### View Implementation

The `ItemListView` handles dynamic sorting:

```python
# Check if this is a custom field sort
if sort.startswith("custom_"):
    field_name = sort.replace("custom_", "").replace("_asc", "").replace("_desc", "")
    if field_name in root_category.sort_by:
        if sort.endswith("_desc"):
            queryset = queryset.order_by(f"-custom_fields__{field_name}__value")
        else:
            queryset = queryset.order_by(f"custom_fields__{field_name}__value")
```

### Field Migration

When migrating from hardcoded fields to custom fields:

1. Create data migration to copy values to custom_fields JSON
2. Update all references in forms, views, and templates
3. Remove fields from model
4. Run migration to drop database columns

## Extending the System

### Adding New Field Types

1. Add the type handling in `ItemForm._create_dynamic_field()`
2. Add appropriate widget and validation
3. Update JavaScript if special handling needed

### Implementing Dynamic Filters

To complete the filter implementation:

1. Update `ItemFilterForm` to dynamically add fields based on category.filters
2. Create filter widgets for different field types (choice, range, text)
3. Update `ItemListView.get_queryset()` to handle custom field filtering
4. Add filter UI components to item_list.html

### Future Enhancement: Complex Dependencies

The current implementation supports single field dependencies with multiple OR values. Future enhancements could include:

1. **Multiple Field Dependencies (AND logic)**:
```json
{
  "depending": ["field1", "field2"],
  "depending_logic": "AND",
  "depending_values": [["value1"], ["value2"]]  // field1=value1 AND field2=value2
}
```

2. **Complex Boolean Logic**:
```json
{
  "depending_expression": "(device_type == 'laptop' OR device_type == 'desktop') AND brand == 'Apple'"
}
```

These would require updating both Python and JavaScript logic.

### Dynamic Field Updates via AJAX

For real-time category field updates without page reload:
1. Create an API endpoint to fetch category fields
2. Update JavaScript to load fields dynamically
3. Handle form state preservation

## Troubleshooting

### Fields Not Showing
- Check browser console for JavaScript errors
- Verify field names in `depending` match exactly
- Ensure `depending_value` matches the choice key, not display value

### Validation Issues
- Hidden required fields should have validation disabled
- Check that conditional fields clear values when hidden
- Verify form processes all custom fields correctly
- When using `depending_values`, ensure it's an array even for single values

### Performance
- Large numbers of conditional fields may slow form rendering
- Consider lazy loading for complex forms
- Cache category schemas if needed