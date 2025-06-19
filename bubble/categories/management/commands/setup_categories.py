from django.core.management.base import BaseCommand
from django.db import transaction
from bubble.categories.models import Category


class Command(BaseCommand):
    help = 'Populates initial categories for a Wohnprojekt (housing project)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing categories before creating new ones',
        )

    @transaction.atomic
    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write('Clearing existing categories...')
            Category.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('✓ Categories cleared'))

        categories_data = {
            'Möbel': {
                'description': 'Möbel und Einrichtungsgegenstände',
                'subcategories': [
                    ('Tische', 'Esstische, Schreibtische, Couchtische'),
                    ('Stühle', 'Bürostühle, Esszimmerstühle, Hocker'),
                    ('Sofas & Sessel', 'Couches, Sessel, Sitzmöbel'),
                    ('Betten & Matratzen', 'Bettgestelle, Matratzen, Lattenroste'),
                    ('Schränke', 'Kleiderschränke, Kommoden, Regale'),
                    ('Regale & Aufbewahrung', 'Bücherregale, Kallax, Boxen'),
                ]
            },
            'Elektronik': {
                'description': 'Elektronische Geräte und Zubehör',
                'subcategories': [
                    ('Computer & Laptops', 'PCs, Notebooks, Tablets'),
                    ('Smartphones & Tablets', 'Handys, Tablets, E-Reader'),
                    ('Audio & Video', 'Lautsprecher, Kopfhörer, Fernseher'),
                    ('Kabel & Adapter', 'USB-Kabel, HDMI, Adapter'),
                    ('Gaming', 'Konsolen, Spiele, Controller'),
                    ('Zubehör', 'Hüllen, Ladegeräte, Powerbanks'),
                ]
            },
            'Haushaltsgeräte': {
                'description': 'Geräte für Küche und Haushalt',
                'subcategories': [
                    ('Küchengeräte', 'Mixer, Toaster, Kaffeemaschinen'),
                    ('Großgeräte', 'Kühlschränke, Waschmaschinen, Geschirrspüler'),
                    ('Kleingeräte', 'Staubsauger, Bügeleisen, Ventilatoren'),
                    ('Kochgeschirr', 'Töpfe, Pfannen, Backformen'),
                    ('Geschirr & Besteck', 'Teller, Tassen, Bestecksets'),
                ]
            },
            'Bücher & Medien': {
                'description': 'Bücher, Filme und andere Medien',
                'subcategories': [
                    ('Bücher', 'Romane, Sachbücher, Kochbücher'),
                    ('DVDs & Blu-rays', 'Filme, Serien, Dokumentationen'),
                    ('Musik', 'CDs, Vinyl, Kassetten'),
                    ('Zeitschriften', 'Magazine, Comics, Hefte'),
                    ('Spiele', 'Brettspiele, Kartenspiele, Puzzles'),
                ]
            },
            'Kleidung': {
                'description': 'Kleidung und Textilien',
                'subcategories': [
                    ('Damenkleidung', 'Kleider, Hosen, Oberteile'),
                    ('Herrenkleidung', 'Hemden, Hosen, Jacken'),
                    ('Kinderkleidung', 'Baby- und Kinderkleidung'),
                    ('Schuhe', 'Sneaker, Stiefel, Sandalen'),
                    ('Accessoires', 'Taschen, Gürtel, Schals'),
                    ('Textilien', 'Bettwäsche, Handtücher, Vorhänge'),
                ]
            },
            'Pflanzen': {
                'description': 'Pflanzen und Gartenbedarf',
                'subcategories': [
                    ('Zimmerpflanzen', 'Grünpflanzen, Sukkulenten, Kakteen'),
                    ('Kräuter', 'Küchenkräuter, Heilkräuter'),
                    ('Balkonpflanzen', 'Blumen, Gemüsepflanzen'),
                    ('Pflanzgefäße', 'Töpfe, Übertöpfe, Kästen'),
                    ('Gartenzubehör', 'Erde, Dünger, Gießkannen'),
                    ('Samen & Ableger', 'Saatgut, Stecklinge, Ableger'),
                ]
            },
            'Werkzeug': {
                'description': 'Werkzeuge und Baumaterial',
                'subcategories': [
                    ('Handwerkzeug', 'Hammer, Schraubenzieher, Zangen'),
                    ('Elektrowerkzeug', 'Bohrmaschinen, Sägen, Schleifer'),
                    ('Gartenwerkzeug', 'Schaufeln, Rechen, Gartenscheren'),
                    ('Baumaterial', 'Schrauben, Nägel, Kleber'),
                    ('Malerbedarf', 'Pinsel, Rollen, Abdeckmaterial'),
                    ('Messwerkzeug', 'Zollstock, Wasserwaage, Maßband'),
                ]
            },
            'Lebensmittel': {
                'description': 'Lebensmittel und Getränke zum Teilen',
                'subcategories': [
                    ('Haltbare Lebensmittel', 'Konserven, Nudeln, Reis'),
                    ('Selbstgemachtes', 'Marmelade, Eingelegtes, Brot'),
                    ('Getränke', 'Säfte, Tee, Kaffee'),
                    ('Gewürze & Öle', 'Gewürze, Öle, Essig'),
                    ('Überschuss', 'Zu viel gekauft/gekocht'),
                    ('Gartenertrag', 'Obst, Gemüse aus eigenem Anbau'),
                ]
            },
            'Dienstleistungen': {
                'description': 'Angebotene Hilfe und Dienstleistungen',
                'subcategories': [
                    ('Handwerkliche Hilfe', 'Reparaturen, Aufbau, Renovierung'),
                    ('Transport', 'Umzugshilfe, Fahrdienste, Einkaufsfahrten'),
                    ('Betreuung', 'Kinderbetreuung, Haustiersitting'),
                    ('Nachhilfe & Kurse', 'Sprachen, Musik, Computer'),
                    ('Haushaltshilfe', 'Putzen, Bügeln, Kochen'),
                    ('Beratung', 'IT-Support, Rechtsberatung, Finanzberatung'),
                ]
            },
        }

        created_count = 0
        
        for main_cat_name, main_cat_data in categories_data.items():
            main_category, created = Category.objects.get_or_create(
                name=main_cat_name,
                defaults={'description': main_cat_data['description']}
            )
            if created:
                created_count += 1
                self.stdout.write(f'  ✓ Created main category: {main_cat_name}')
            else:
                self.stdout.write(f'  - Main category exists: {main_cat_name}')
            
            for subcat_name, subcat_desc in main_cat_data['subcategories']:
                subcategory, created = Category.objects.get_or_create(
                    name=subcat_name,
                    parent_category=main_category,
                    defaults={'description': subcat_desc}
                )
                if created:
                    created_count += 1
                    self.stdout.write(f'    ✓ Created subcategory: {subcat_name}')
                else:
                    self.stdout.write(f'    - Subcategory exists: {subcat_name}')

        self.stdout.write(
            self.style.SUCCESS(
                f'\n✓ Successfully set up categories. Created {created_count} new categories.'
            )
        )
        
        total_categories = Category.objects.count()
        self.stdout.write(f'Total categories in database: {total_categories}')