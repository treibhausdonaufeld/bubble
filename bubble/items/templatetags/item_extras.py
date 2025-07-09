from django import template

register = template.Library()


@register.filter
def get_item(dictionary, key):
    """Get an item from a dictionary using a dynamic key."""
    if dictionary and key:
        return dictionary.get(key)
    return None


@register.filter
def hierarchy_without_root(category):
    """Get category hierarchy without the root category."""
    if not category:
        return ""

    # If this is a root category, just return its name
    if not category.parent_category:
        return category.name

    # Get the full hierarchy
    full_hierarchy = category.get_hierarchy()

    # Split by the separator and remove the first part (root category)
    parts = full_hierarchy.split(" > ")
    if len(parts) > 1:
        return " > ".join(parts[1:])

    # Fallback to just the category name
    return category.name


@register.filter
def get_badge_color(value):
    """Get a consistent color for a given value from a palette of 50 colors."""
    if not value:
        return "#6c757d"  # Default gray

    # 50 visually distinct colors using HSL color space
    # Colors are generated to be vibrant and distinguishable
    colors = [
        "#FF6B6B",
        "#4ECDC4",
        "#45B7D1",
        "#FFA07A",
        "#98D8C8",
        "#F7DC6F",
        "#BB8FCE",
        "#85C1E9",
        "#F8B500",
        "#6C5CE7",
        "#FD79A8",
        "#74B9FF",
        "#A29BFE",
        "#FF7675",
        "#FDCB6E",
        "#6C5B7B",
        "#F8B195",
        "#F67280",
        "#C06C84",
        "#355C7D",
        "#2ECC71",
        "#E74C3C",
        "#3498DB",
        "#9B59B6",
        "#F39C12",
        "#1ABC9C",
        "#34495E",
        "#16A085",
        "#27AE60",
        "#2980B9",
        "#8E44AD",
        "#2C3E50",
        "#E67E22",
        "#95A5A6",
        "#D35400",
        "#7F8C8D",
        "#C0392B",
        "#BDC3C7",
        "#00CEC9",
        "#FABADA",
        "#74B49B",
        "#A8D8EA",
        "#AA96DA",
        "#FCBAD3",
        "#B83B5E",
        "#6A2C70",
        "#3D5A80",
        "#EE6C4D",
        "#98C1D9",
        "#293241",
    ]

    # Convert string to a more unique hash by using character codes
    # This provides better distribution for similar strings
    str_value = str(value)
    hash_value = 0

    # Create a hash based on character codes and position
    for i, char in enumerate(str_value):
        hash_value += ord(char) * (i + 1) * 31

    # Add length as a factor to differentiate short similar strings
    hash_value += len(str_value) * 13

    # Use modulo to get color index
    color_index = abs(hash_value) % len(colors)

    return colors[color_index]


@register.filter
def get_field_type(category, field_name):
    """Get the type of a custom field from category configuration."""
    if not category or not field_name:
        return None

    root_category = category.get_root_category()
    if not root_category.custom_fields:
        return None

    field_config = root_category.custom_fields.get(field_name, {})
    return field_config.get("type")
