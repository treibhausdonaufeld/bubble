import { createContext, ReactNode, useContext, useState } from 'react';

export type Language = 'en' | 'de';

interface LanguageContextType {
  language: Language;
  setLanguage: (lang: Language) => void;
  t: (key: string) => string;
}

const LanguageContext = createContext<LanguageContextType | undefined>(undefined);

const translations = {
  en: {
    // Header
    'header.search': 'Search items in your community...',
    'header.shareItem': 'Share Item',
    'header.signIn': 'Sign In',
    'header.myProfile': 'My Profile',
    'header.myItems': 'My Items',
    'header.myBookings': 'My Bookings',
    'header.signOut': 'Sign Out',

    // Hero Section
    'hero.title': 'Share & Discover in Your Community',
    'hero.subtitle':
      'Connect with neighbors to share, lend, and discover items in your local area. Building stronger communities through sharing.',
    'hero.getStarted': 'Get Started',
    'hero.learnMore': 'Learn More',

    // Auth
    'auth.signIn': 'Sign In',
    'auth.signUp': 'Sign Up',
    'auth.email': 'Email',
    'auth.password': 'Password',
    'auth.confirmPassword': 'Confirm Password',
    'auth.forgotPassword': 'Forgot Password?',
    'auth.noAccount': "Don't have an account?",
    'auth.hasAccount': 'Already have an account?',
    'auth.loginRequired': 'Please log in to book or buy this item',

    // Items
    'item.available': 'Available',
    'item.unavailable': 'Unavailable',
    'item.messageOwner': 'Message',
    'item.category': 'Category',
    'item.condition': 'Condition',
    'item.location': 'Location',
    'item.cannotMessageSelf': 'You cannot message yourself',

    // List Item
    'editItem.title': 'Share an Item',
    'editItem.name': 'Edit Item',
    'editItem.itemName': 'Item Name',
    'editItem.itemNamePlaceholder': 'Enter the name of your item...',
    'editItem.description': 'Description',
    'editItem.descriptionPlaceholder': 'Describe your item, its condition, and any details...',
    'editItem.category': 'Category',
    'editItem.condition': 'Condition',
    'editItem.status': 'Status',
    'editItem.selectCategory': 'Select Category',
    'editItem.selectCondition': 'Select Condition',
    'editItem.selectStatus': 'Select Status',
    'editItem.salePrice': 'Sale Price',
    'editItem.rentalPrice': 'Rental Price',
    'editItem.rentalPeriod': 'Rental Period',
    'editItem.selectRentalPeriod': 'Select Rental Period',
    'editItem.rentalOptions': 'Rental Options',
    'editItem.rentalSelfService': 'Allow self-service rental (no approval required)',
    'editItem.rentalOpenEnd': 'Allow open-ended rental (no return date)',
    'editItem.uploadImages': 'Upload Images',
    'editItem.shareItem': 'Share Item',
    'editItem.listItem': 'List Item',
    'editItem.publish': 'Publish',
    'editItem.aiMagic': 'AI Magic',
    'editItem.aiMagicProcessing': 'Processing...',
    'editItem.aiMagicWarningTitle': 'AI Magic - Data Override Warning',
    'editItem.aiMagicWarningDescription':
      'AI Magic will analyze your images and automatically update the item name, description, category, and price. This may overwrite your existing data. Do you want to continue?',
    'editItem.aiMagicWarningCancel': 'Cancel',
    'editItem.aiMagicWarningContinue': 'Continue',
    'editItem.aiMagicImage': 'Generate Image',

    // Categories
    'categories.all': 'All Categories',
    'categories.electronics': 'Electronics',
    'categories.furniture': 'Furniture',
    'categories.books': 'Books',
    'categories.clothing': 'Clothing',
    'categories.sports': 'Sports',
    'categories.tools': 'Tools',
    'categories.kitchen': 'Kitchen',
    'categories.garden': 'Garden',
    'categories.toys': 'Toys',
    'categories.vehicles': 'Vehicles',
    'categories.rooms': 'Rooms',
    'categories.other': 'Other',

    // Conditions
    'condition.new': 'New',
    'condition.used': 'Used',
    'condition.broken': 'Broken',

    // Item UI
    'item.noImage': 'No image',
    'item.listingType.sell': 'Sell',
    'item.listingType.rent': 'Rent',
    'item.listingType.sellRent': 'Sell/Rent',
    'item.price.sale': 'sale',
    'item.price.rent': 'rent',
    // Time
    'time.hour': 'hour',
    'time.hours': 'hours',
    'time.perHour': '/h',
    // EditItem UI
    'editItem.uploadNewImages': 'Upload new Images',
    'editItem.clearNewImages': 'Clear New Images',
    'editItem.uploadingImages': 'Uploading new images...',
    'editItem.aiProcessing': 'AI is analyzing your images and updating content...',
    'editItem.processingCompleted': 'Processing complete!',
    'editItem.processingError': 'An error occurred during processing.',
    'editItem.saleDisabledPlaceholder': 'Leave empty to disable sale',
    'editItem.rentalDisabledPlaceholder': 'Leave empty to disable rental',
    'editItem.saleDisablesRental': 'Setting a sale price disables rental price',
    'editItem.rentalDisablesSale': 'Setting a rental price disables sale price',
    'editItem.primaryBadge': 'Primary',
    // Image Upload Step
    'imageUpload.title': 'Upload Item Images',
    'imageUpload.description': 'Add photos of your item to help others find and understand it.',
    'imageUpload.imagesUploaded': 'image uploaded',
    'imageUpload.imagesUploadedPlural': 'images uploaded',
    'imageUpload.aiGenerating': 'Generating AI content…',
    'imageUpload.continueWithAI': 'Continue with AI Processing',
    'imageUpload.skipAndContinue': 'Skip AI, Continue Manually',

    // Messages
    'messages.title': 'Messages',
    'messages.noConversations': 'No conversations yet',
    'messages.startConversation': 'Start a conversation by messaging someone about their item!',
    'messages.typeMessage': 'Type a message...',
    'messages.send': 'Send',
    'messages.selectConversation': 'Select a conversation to start messaging',

    // Common
    'common.loading': 'Loading...',
    'common.error': 'Error',
    'common.cancel': 'Cancel',
    'common.save': 'Save',
    'common.saving': 'Saving...',
    'common.delete': 'Delete',
    'common.edit': 'Edit',
    'common.update': 'Update',
    'common.back': 'Back',
    'common.next': 'Next',
    'common.previous': 'Previous',
    'common.submitting': 'Submitting...',

    // Booking
    'booking.bookNow': 'Book Now',
    'booking.createBooking': 'Create Booking Request',
    'booking.createBookingDescription': 'Submit a booking request for {itemName}',
    'booking.purchaseOffer': 'Your Purchase Offer',
    'booking.rentalOffer': 'Your Rental Offer',
    'booking.totalPrice': 'Total Price',
    'booking.listedPrice': 'Listed Price',
    'booking.listedRentalPrice': 'Listed Rental Price',
    'booking.enterYourOffer': 'Enter your offer amount',
    'booking.rentalStart': 'Rental Start Date & Time',
    'booking.rentalEnd': 'Rental End Date & Time',
    'booking.submitRequest': 'Submit Request',
    'booking.successTitle': 'Success',
    'booking.successCreated': 'Booking request created successfully!',
    'booking.errorCreate': 'Failed to create booking request. Please try again.',
    'booking.successUpdated': 'Booking updated successfully!',
    'booking.errorUpdate': 'Failed to update booking. Please try again.',

    // Calendar
    'calendar.selectRentalPeriod': 'Select Rental Period',
    'calendar.time': 'Time',
    'calendar.clickToComplete': 'Click another time slot to complete selection',
    'calendar.selectedPeriod': 'Selected Period',
    'calendar.from': 'From',
    'calendar.to': 'To',
    'calendar.duration': 'Duration',
    'calendar.hours': 'hours',
    'calendar.week': 'Week',
    'calendar.month': 'Month',

    // Bookings Page
    'bookings.title': 'My Bookings',
    'bookings.allBookings': 'All Bookings',
    'bookings.noBookings': 'No bookings yet',
    'bookings.selectBooking': 'Select a booking to view details',
    'bookings.bookingDetails': 'Booking Details',
    'bookings.bookingItem': 'Booking',
    'bookings.unknownItem': 'Unknown Item',
    'bookings.user': 'User',
    'bookings.bookingId': 'Booking ID',
    'bookings.itemId': 'Item ID',
    'bookings.requestFrom': 'Request from',
    'bookings.requestTo': 'Request to',
    'bookings.offerAmount': 'Offer Amount',
    'bookings.counterOffer': 'Counter Offer',
    'bookings.rentalPeriod': 'Rental Period',
    'bookings.noDate': 'No date specified',
    'bookings.accept': 'Accept',
    'bookings.reject': 'Reject',
    'bookings.cancel': 'Cancel Booking',
    'bookings.noMessages': 'No messages yet',
    'bookings.startConversation': 'Start the conversation by sending a message',
    'bookings.messagesComingSoon': 'Messages feature coming soon',
    'bookings.messagesDescription': 'You will be able to chat about bookings here',
    'bookings.typeMessage': 'Type a message...',
    'bookings.messages': 'Messages',
    'bookings.refresh': 'Refresh',
    'bookings.refreshing': 'Refreshing...',
    'bookings.editBooking': 'Edit Booking',
    'bookings.editBookingDescription': 'Edit rental period or offered price for this booking.',
    'bookings.update': 'Update',
    'bookings.counterOfferDialogTitle': 'Make a counter offer',
    'bookings.counterOfferDialogDescription':
      'Enter an alternative price to propose for this booking.',
    'bookings.counterOfferSubmit': 'Submit Counter Offer',
    'bookings.status.pending': 'Pending',
    'bookings.status.cancelled': 'Cancelled',
    'bookings.status.confirmed': 'Confirmed',
    'bookings.status.accepted': 'Accepted',
    'bookings.status.rejected': 'Rejected',
    'bookings.status.completed': 'Completed',
    'bookings.status.unknown': 'Unknown',

    // Item Detail
    'itemDetail.backToItems': 'Back to Items',
    'itemDetail.editItem': 'Edit Item',
    'itemDetail.deleteItem': 'Delete Item',
    'itemDetail.contactOwner': 'Contact Owner',
    'itemDetail.buyNow': 'Buy Now',
    'itemDetail.rentNow': 'Rent Now',
    'itemDetail.itemDetails': 'Item Details',
    'itemDetail.description': 'Description',
    'itemDetail.listed': 'Listed',
    'itemDetail.ownerInfo': 'Owner Information',
    'itemDetail.deleteConfirmTitle': 'Are you sure?',
    'itemDetail.deleteConfirmDescription':
      'This action cannot be undone. This will permanently delete your item.',
    'itemDetail.notFound': 'Item not found',
    'itemDetail.availability': 'Availability',

    // My Items
    'myItems.title': 'My Items',
    'myItems.noItems': 'No items yet',
    'myItems.createFirst': 'Create your first item to get started!',
    'myItems.createItem': 'Create Item',
    'myItems.status': 'Status',
    'myItems.changeStatus': 'Change Status',
    'myItems.statusUpdated': 'Item status updated successfully',

    // Item Status
    'status.draft': 'Draft',
    'status.processing': 'Processing',
    'status.available': 'Available',
    'status.reserved': 'Reserved',
    'status.rented': 'Rented',
    'status.sold': 'Sold',
    // Profile
    'profile.title': 'Profile Settings',
    'profile.manage': 'Manage your profile information and locations',
    'profile.name': 'Name',
    'profile.phone': 'Phone',
    'profile.bio': 'Bio',
    'profile.update': 'Update Profile',
    'profile.updating': 'Updating profile...',
    'editItem.invalidPricingTitle': 'Invalid Pricing',
    'editItem.invalidPricingDescription':
      'Please set either a sale price or a rental price, not both.',
    'rentalPeriod.h': 'Hourly',
    'rentalPeriod.d': 'Daily',
    'rentalPeriod.w': 'Weekly',
    // User labels
    'user.name': 'Name',
    'user.email': 'Email',
  },
  de: {
    // Header
    'header.search': 'Artikel in deiner Community suchen...',
    'header.shareItem': 'Artikel teilen',
    'header.signIn': 'Anmelden',
    'header.myProfile': 'Mein Profil',
    'header.myItems': 'Meine Artikel',
    'header.myBookings': 'Meine Buchungen',
    'header.signOut': 'Abmelden',

    // Hero Section
    'hero.title': 'Teilen & Entdecken in deiner Community',
    'hero.subtitle':
      'Verbinde dich mit Nachbarn, um Artikel in deiner Umgebung zu teilen, zu leihen und zu entdecken. Stärkere Gemeinschaften durch Teilen.',
    'hero.getStarted': 'Loslegen',
    'hero.learnMore': 'Mehr erfahren',

    // Auth
    'auth.signIn': 'Anmelden',
    'auth.signUp': 'Registrieren',
    'auth.email': 'E-Mail',
    'auth.password': 'Passwort',
    'auth.confirmPassword': 'Passwort bestätigen',
    'auth.forgotPassword': 'Passwort vergessen?',
    'auth.noAccount': 'Noch kein Konto?',
    'auth.hasAccount': 'Bereits ein Konto?',
    'auth.loginRequired': 'Bitte melden Sie sich an, um diesen Artikel zu buchen oder zu kaufen',

    // Items
    'item.available': 'Verfügbar',
    'item.unavailable': 'Nicht verfügbar',
    'item.messageOwner': 'Nachricht',
    'item.category': 'Kategorie',
    'item.condition': 'Zustand',
    'item.location': 'Ort',
    'item.cannotMessageSelf': 'Sie können sich nicht selbst eine Nachricht senden',

    // List Item
    'editItem.title': 'Artikel teilen',
    'editItem.name': 'Artikel bearbeiten',
    'editItem.itemName': 'Artikelname',
    'editItem.itemNamePlaceholder': 'Gib den Namen deines Artikels ein...',
    'editItem.description': 'Beschreibung',
    'editItem.saleDisablesRental':
      'Wenn du einen Verkaufspreis setzt, ist der Mietpreis deaktiviert',
    'editItem.rentalDisablesSale':
      'Wenn du einen Mietpreis setzt, ist der Verkaufspreis deaktiviert',
    'editItem.descriptionPlaceholder':
      'Beschreibe deinen Artikel, seinen Zustand und weitere Details...',
    'editItem.category': 'Kategorie',
    'editItem.condition': 'Zustand',
    'editItem.status': 'Status',
    'editItem.selectCategory': 'Kategorie auswählen',
    'editItem.selectCondition': 'Zustand auswählen',
    'editItem.selectStatus': 'Status auswählen',
    'editItem.salePrice': 'Verkaufspreis',
    'editItem.rentalPrice': 'Mietpreis',
    'editItem.rentalPeriod': 'Mietzeitraum',
    'editItem.selectRentalPeriod': 'Mietzeitraum auswählen',
    'editItem.rentalOptions': 'Miet Optionen',
    'editItem.rentalSelfService': 'Selbstbedienung erlauben (keine Genehmigung nötig)',
    'editItem.rentalOpenEnd': 'Offene Miete erlauben (kein Rückgabedatum)',
    'editItem.uploadImages': 'Bilder hochladen',
    'editItem.shareItem': 'Artikel teilen',
    'editItem.listItem': 'Artikel einstellen',
    'editItem.publish': 'Veröffentlichen',
    'editItem.aiMagic': 'KI Magie',
    'editItem.aiMagicProcessing': 'Wird verarbeitet...',
    'editItem.aiMagicWarningTitle': 'KI Magie - Datenüberschreibungswarnung',
    'editItem.aiMagicWarningDescription':
      'KI Magie analysiert deine Bilder und aktualisiert automatisch den Artikelnamen, die Beschreibung, die Kategorie und den Preis. Dies kann deine vorhandenen Daten überschreiben. Möchtest du fortfahren?',
    'editItem.aiMagicWarningCancel': 'Abbrechen',
    'editItem.aiMagicWarningContinue': 'Fortfahren',
    'editItem.aiMagicImage': 'Bild generieren',

    // Categories
    'categories.all': 'Alle Kategorien',
    'categories.electronics': 'Elektronik',
    'categories.furniture': 'Möbel',
    'categories.books': 'Bücher',
    'categories.clothing': 'Kleidung',
    'categories.sports': 'Sport',
    'categories.tools': 'Werkzeuge',
    'categories.kitchen': 'Küche',
    'categories.garden': 'Garten',
    'categories.toys': 'Spielzeug',
    'categories.vehicles': 'Fahrzeuge',
    'categories.rooms': 'Räume',
    'categories.other': 'Sonstiges',

    // Conditions
    'condition.new': 'Neu',
    'condition.used': 'Gebraucht',
    'condition.broken': 'Kaputt',

    // Item UI
    'item.noImage': 'Kein Bild',
    'item.listingType.sell': 'Verkaufen',
    'item.listingType.rent': 'Mieten',
    'item.listingType.sellRent': 'Verkaufen/Mieten',
    'item.price.sale': 'Verkauf',
    'item.price.rent': 'Miete',
    // Time
    'time.hour': 'Stunde',
    'time.hours': 'Stunden',
    'time.perHour': '/h',
    // EditItem UI
    'editItem.uploadNewImages': 'Neue Bilder hochladen',
    'editItem.clearNewImages': 'Neue Bilder löschen',
    'editItem.uploadingImages': 'Lade neue Bilder hoch...',
    'editItem.aiProcessing': 'KI analysiert deine Bilder und aktualisiert Inhalte...',
    'editItem.processingCompleted': 'Verarbeitung abgeschlossen!',
    'editItem.processingError': 'Bei der Verarbeitung ist ein Fehler aufgetreten.',
    'editItem.saleDisabledPlaceholder': 'Verkaufspreis eingeben',
    'editItem.rentalDisabledPlaceholder': 'Mietpreis eingeben',
    'editItem.primaryBadge': 'Hauptbild',
    // Image Upload Step
    'imageUpload.title': 'Bilder des Artikels hochladen',
    'imageUpload.description':
      'Füge Fotos deines Artikels hinzu, damit andere ihn besser finden und verstehen können.',
    'imageUpload.imagesUploaded': 'Bild hochgeladen',
    'imageUpload.imagesUploadedPlural': 'Bilder hochgeladen',
    'imageUpload.aiGenerating': 'KI generiert Inhalte…',
    'imageUpload.continueWithAI': 'Mit KI-Verarbeitung fortfahren',
    'imageUpload.skipAndContinue': 'KI überspringen, manuell fortfahren',

    // Messages
    'messages.title': 'Nachrichten',
    'messages.noConversations': 'Noch keine Unterhaltungen',
    'messages.startConversation':
      'Beginne eine Unterhaltung, indem du jemanden wegen seines Artikels anschreibst!',
    'messages.typeMessage': 'Nachricht eingeben...',
    'messages.send': 'Senden',
    'messages.selectConversation': 'Wähle eine Unterhaltung aus, um zu chatten',

    // Common
    'common.loading': 'Lädt...',
    'common.error': 'Fehler',
    'common.cancel': 'Abbrechen',
    'common.save': 'Speichern',
    'common.saving': 'Speichert...',
    'common.delete': 'Löschen',
    'common.edit': 'Bearbeiten',
    'common.update': 'Aktualisieren',
    'common.back': 'Zurück',
    'common.next': 'Weiter',
    'common.previous': 'Zurück',
    'common.submitting': 'Wird gesendet...',

    // Booking
    'booking.bookNow': 'Jetzt buchen',
    'booking.createBooking': 'Buchungsanfrage erstellen',
    'booking.createBookingDescription': 'Buchungsanfrage für {itemName} einreichen',
    'booking.purchaseOffer': 'Dein Kaufangebot',
    'booking.rentalOffer': 'Dein Mietangebot',
    'booking.totalPrice': 'Gesamtpreis',
    'booking.listedPrice': 'Gelisteter Preis',
    'booking.listedRentalPrice': 'Gelisteter Mietpreis',
    'booking.enterYourOffer': 'Gib deinen Angebotsbetrag ein',
    'booking.rentalStart': 'Mietbeginn Datum & Uhrzeit',
    'booking.rentalEnd': 'Mietende Datum & Uhrzeit',
    'booking.submitRequest': 'Anfrage senden',
    'booking.successTitle': 'Erfolg',
    'booking.successCreated': 'Buchungsanfrage erfolgreich erstellt!',
    'booking.errorCreate':
      'Erstellen der Buchungsanfrage fehlgeschlagen. Bitte versuche es erneut.',
    'booking.successUpdated': 'Buchung erfolgreich aktualisiert!',
    'booking.errorUpdate': 'Aktualisierung der Buchung fehlgeschlagen. Bitte versuche es erneut.',

    // Calendar
    'calendar.selectRentalPeriod': 'Mietzeitraum auswählen',
    'calendar.time': 'Zeit',
    'calendar.clickToComplete': 'Klicke auf ein anderes Zeitfenster, um die Auswahl abzuschließen',
    'calendar.selectedPeriod': 'Ausgewählter Zeitraum',
    'calendar.from': 'Von',
    'calendar.to': 'Bis',
    'calendar.duration': 'Dauer',
    'calendar.hours': 'Stunden',
    'calendar.week': 'Woche',
    'calendar.month': 'Monat',

    // Bookings Page
    'bookings.title': 'Meine Buchungen',
    'bookings.allBookings': 'Alle Buchungen',
    'bookings.noBookings': 'Noch keine Buchungen',
    'bookings.selectBooking': 'Wähle eine Buchung aus, um Details zu sehen',
    'bookings.bookingDetails': 'Buchungsdetails',
    'bookings.bookingItem': 'Buchung',
    'bookings.unknownItem': 'Unbekannter Artikel',
    'bookings.user': 'Benutzer',
    'bookings.bookingId': 'Buchungs-ID',
    'bookings.itemId': 'Artikel-ID',
    'bookings.requestFrom': 'Anfrage von',
    'bookings.requestTo': 'Anfrage an',
    'bookings.offerAmount': 'Angebotsbetrag',
    'bookings.counterOffer': 'Gegenangebot',
    'bookings.rentalPeriod': 'Mietzeitraum',
    'bookings.noDate': 'Kein Datum angegeben',
    'bookings.accept': 'Annehmen',
    'bookings.reject': 'Ablehnen',
    'bookings.cancel': 'Buchung stornieren',
    'bookings.noMessages': 'Noch keine Nachrichten',
    'bookings.startConversation': 'Beginne die Konversation, indem du eine Nachricht sendest',
    'bookings.messagesComingSoon': 'Nachrichtenfunktion kommt bald',
    'bookings.messagesDescription': 'Hier kannst du bald über Buchungen chatten',
    'bookings.typeMessage': 'Nachricht eingeben...',
    'bookings.messages': 'Nachrichten',
    'bookings.refresh': 'Aktualisieren',
    'bookings.refreshing': 'Wird aktualisiert...',
    'bookings.editBooking': 'Buchung bearbeiten',
    'bookings.editBookingDescription':
      'Bearbeite Mietzeitraum oder angebotenen Preis für diese Buchung.',
    'bookings.update': 'Aktualisieren',
    'bookings.status.pending': 'Ausstehend',
    'bookings.status.cancelled': 'Storniert',
    'bookings.status.confirmed': 'Bestätigt',
    'bookings.status.accepted': 'Angenommen',
    'bookings.status.rejected': 'Abgelehnt',
    'bookings.status.completed': 'Abgeschlossen',
    'bookings.status.unknown': 'Unbekannt',

    // Item Detail
    'itemDetail.backToItems': 'Zurück zu Artikeln',
    'itemDetail.editItem': 'Artikel bearbeiten',
    'itemDetail.deleteItem': 'Artikel löschen',
    'itemDetail.contactOwner': 'Besitzer kontaktieren',
    'itemDetail.buyNow': 'Jetzt kaufen',
    'itemDetail.rentNow': 'Jetzt mieten',
    'itemDetail.itemDetails': 'Artikel Details',
    'itemDetail.description': 'Beschreibung',
    'itemDetail.listed': 'Gelistet',
    'itemDetail.ownerInfo': 'Besitzer Informationen',
    'itemDetail.deleteConfirmTitle': 'Bist du sicher?',
    'itemDetail.deleteConfirmDescription':
      'Diese Aktion kann nicht rückgängig gemacht werden. Dieser Artikel wird dauerhaft gelöscht.',
    'itemDetail.notFound': 'Artikel nicht gefunden',
    'itemDetail.availability': 'Verfügbarkeit',

    // My Items
    'myItems.title': 'Meine Artikel',
    'myItems.noItems': 'Noch keine Artikel',
    'myItems.createFirst': 'Erstelle deinen ersten Artikel um loszulegen!',
    'myItems.createItem': 'Artikel erstellen',
    'myItems.status': 'Status',
    'myItems.changeStatus': 'Status ändern',
    'myItems.statusUpdated': 'Artikel Status erfolgreich aktualisiert',

    // Item Status
    'status.draft': 'Entwurf',
    'status.processing': 'In Bearbeitung',
    'status.available': 'Verfügbar',
    'status.reserved': 'Reserviert',
    'status.rented': 'Vermietet',
    'status.sold': 'Verkauft',
    // Profile
    'profile.title': 'Profileinstellungen',
    'profile.manage': 'Verwalte deine Profilinformationen und Orte',
    'profile.name': 'Name',
    'profile.phone': 'Telefon',
    'profile.bio': 'Bio',
    'profile.update': 'Profil aktualisieren',
    'profile.updating': 'Profil wird aktualisiert...',
    'editItem.invalidPricingTitle': 'Ungültige Preisangabe',
    'editItem.invalidPricingDescription':
      'Bitte setze entweder einen Verkaufspreis oder einen Mietpreis, nicht beides.',
    'rentalPeriod.h': 'Stündlich',
    'rentalPeriod.d': 'Täglich',
    'rentalPeriod.w': 'Wöchentlich',
    // User labels
    'user.name': 'Name',
    'user.email': 'E-Mail',
  },
};

export const LanguageProvider = ({ children }: { children: ReactNode }) => {
  const [language, setLanguageState] = useState<Language>(() => {
    const saved = localStorage.getItem('bubble-language');
    return (saved as Language) || 'en';
  });

  const setLanguage = (lang: Language) => {
    setLanguageState(lang);
    localStorage.setItem('bubble-language', lang);
  };

  const t = (key: string): string => {
    return translations[language][key as keyof (typeof translations)['en']] || key;
  };

  return (
    <LanguageContext.Provider value={{ language, setLanguage, t }}>
      {children}
    </LanguageContext.Provider>
  );
};

export const useLanguage = () => {
  const context = useContext(LanguageContext);
  if (context === undefined) {
    throw new Error('useLanguage must be used within a LanguageProvider');
  }
  return context;
};
