from django.core.management.base import BaseCommand

from bubble.categories.models import ItemCategory


class Command(BaseCommand):
    help = (
        "Creates an example category with conditional fields to demonstrate the feature"
    )

    def handle(self, *args, **options):
        # Create or update the Electronics category with conditional fields
        electronics, created = ItemCategory.objects.get_or_create(
            name="Elektronik",
            parent_category=None,
            defaults={
                "description": "Elektronische Geräte mit bedingten Feldern",
                "emoji": "💻",
            },
        )

        # Define custom fields with conditional logic
        electronics.custom_fields = {
            "device_type": {
                "type": "choice",
                "label": "Gerätetyp",
                "choices": [
                    {"key": "laptop", "value": "Laptop"},
                    {"key": "desktop", "value": "Desktop PC"},
                    {"key": "smartphone", "value": "Smartphone"},
                    {"key": "tablet", "value": "Tablet"},
                    {"key": "other", "value": "Sonstiges"},
                ],
                "required": True,
            },
            # Computer-specific fields (laptop AND desktop)
            "screen_size": {
                "type": "choice",
                "label": "Bildschirmgröße",
                "choices": [
                    "13 Zoll",
                    "14 Zoll",
                    "15 Zoll",
                    "17 Zoll",
                    "21 Zoll",
                    "24 Zoll",
                    "27 Zoll",
                    "32 Zoll",
                ],
                "required": False,
                "depending": "device_type",
                "depending_values": [
                    "laptop",
                    "desktop",
                ],  # Shows for both laptop AND desktop
            },
            "ram": {
                "type": "choice",
                "label": "RAM",
                "choices": ["4GB", "8GB", "16GB", "32GB", "64GB"],
                "required": False,
                "depending": "device_type",
                "depending_values": [
                    "laptop",
                    "desktop",
                ],  # Shows for both laptop AND desktop
            },
            "processor": {
                "type": "text",
                "label": "Prozessor",
                "required": False,
                "depending": "device_type",
                "depending_values": [
                    "laptop",
                    "desktop",
                ],  # Shows for both laptop AND desktop
            },
            # Mobile device fields (smartphone AND tablet)
            "storage": {
                "type": "choice",
                "label": "Speicher",
                "choices": ["32GB", "64GB", "128GB", "256GB", "512GB", "1TB"],
                "required": False,
                "depending": "device_type",
                "depending_values": [
                    "smartphone",
                    "tablet",
                ],  # Shows for smartphone OR tablet
            },
            "mobile_network": {
                "type": "choice",
                "label": "Mobilfunk",
                "choices": ["Nur WiFi", "4G", "5G"],
                "required": False,
                "depending": "device_type",
                "depending_values": [
                    "smartphone",
                    "tablet",
                ],  # Shows for smartphone OR tablet
            },
            # Laptop-only field
            "battery_life": {
                "type": "choice",
                "label": "Akkulaufzeit",
                "choices": [
                    "< 4 Stunden",
                    "4-8 Stunden",
                    "8-12 Stunden",
                    "> 12 Stunden",
                ],
                "required": False,
                "depending": "device_type",
                "depending_values": ["laptop"],  # Only for laptops
            },
            # Common field for all devices
            "condition": {
                "type": "choice",
                "label": "Zustand",
                "choices": [
                    {"key": "new", "value": "Neu"},
                    {"key": "like_new", "value": "Wie neu"},
                    {"key": "good", "value": "Gut"},
                    {"key": "fair", "value": "Akzeptabel"},
                ],
                "required": True,
                "default": "good",  # Default to "Gut"
            },
            "accessories": {
                "type": "textarea",
                "label": "Zubehör",
                "required": False,
                "default": "",  # Default to empty string instead of null
            },
            "quantity": {
                "type": "number",
                "label": "Anzahl",
                "required": False,
                "default": 1,  # Default to 1
            },
        }

        electronics.save()

        # Create another example for Clothing with size dependencies
        clothing, created = ItemCategory.objects.get_or_create(
            name="Kleidung",
            parent_category=None,
            defaults={
                "description": "Kleidung mit größenabhängigen Feldern",
                "emoji": "👕",
            },
        )

        clothing.custom_fields = {
            "clothing_type": {
                "type": "choice",
                "label": "Art",
                "choices": [
                    {"key": "shirt", "value": "Oberteil"},
                    {"key": "pants", "value": "Hose"},
                    {"key": "shoes", "value": "Schuhe"},
                    {"key": "accessories", "value": "Accessoires"},
                ],
                "required": True,
            },
            # Size fields that depend on clothing type
            "shirt_size": {
                "type": "choice",
                "label": "Größe",
                "choices": ["XS", "S", "M", "L", "XL", "XXL"],
                "required": True,
                "depending": "clothing_type",
                "depending_value": "shirt",
            },
            "pants_size": {
                "type": "choice",
                "label": "Größe",
                "choices": ["28", "30", "32", "34", "36", "38", "40"],
                "required": True,
                "depending": "clothing_type",
                "depending_value": "pants",
            },
            "shoe_size": {
                "type": "choice",
                "label": "Schuhgröße",
                "choices": ["36", "37", "38", "39", "40", "41", "42", "43", "44", "45"],
                "required": True,
                "depending": "clothing_type",
                "depending_value": "shoes",
            },
            # Common fields
            "brand": {
                "type": "text",
                "label": "Marke",
                "required": False,
            },
            "color": {
                "type": "text",
                "label": "Farbe",
                "required": True,
                "default": "Schwarz",  # Default to "Schwarz" (black)
            },
            "material": {
                "type": "text",
                "label": "Material",
                "required": False,
                "default": "Baumwolle",  # Default to "Baumwolle" (cotton)
            },
        }

        clothing.save()

        self.stdout.write(
            self.style.SUCCESS(
                "\n✓ Successfully created example categories with conditional fields:\n"
                "  - Elektronik: Now with array-based dependencies and default values!\n"
                "    • Screen size, RAM, Processor → Show for both Laptop AND Desktop\n"
                "    • Storage, Mobile network → Show for Smartphone OR Tablet\n"
                "    • Battery life → Shows only for Laptop\n"
                "    • Default values: Condition='Gut', Quantity=1\n"
                "  - Kleidung: Size fields appear based on clothing type\n"
                "    • Default values: Color='Schwarz', Material='Baumwolle'\n\n"
                "Try creating items in these categories to see conditional fields and defaults in action!",
            ),
        )
