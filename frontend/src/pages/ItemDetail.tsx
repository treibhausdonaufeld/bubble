import { BookingDialog } from '@/components/items/BookingDialog';
import { RentalCalendar } from '@/components/items/RentalCalendar';
import { Header } from '@/components/layout/Header';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from '@/components/ui/alert-dialog';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  Carousel,
  CarouselContent,
  CarouselItem,
  CarouselNext,
  CarouselPrevious,
} from '@/components/ui/carousel';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import { useLanguage } from '@/contexts/LanguageContext';
import { useAuth } from '@/hooks/useAuth';
import { useItem } from '@/hooks/useItem';
import { useDeleteItem } from '@/hooks/useMyItems';
import { formatPrice } from '@/lib/currency';
import { formatDistanceToNow } from 'date-fns';
import { ArrowLeft, Calendar, Edit3, Trash2, X } from 'lucide-react';
import { useMemo, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';

const ItemDetail = () => {
  const { itemUuid } = useParams<{ itemUuid: string }>();
  const navigate = useNavigate();
  const { user } = useAuth();
  const { t } = useLanguage();
  const { data: item, isLoading, error } = useItem(itemUuid);
  const deleteItemMutation = useDeleteItem();
  const [showAllImages, setShowAllImages] = useState(false);
  const [selectedStartDate, setSelectedStartDate] = useState<Date | undefined>();
  const [selectedEndDate, setSelectedEndDate] = useState<Date | undefined>();
  const [showBookingDialog, setShowBookingDialog] = useState(false);

  const handleDateRangeSelect = (start: Date, end: Date) => {
    setSelectedStartDate(start);
    setSelectedEndDate(end);
  };

  const handleBookNowFromCalendar = (start: Date, end: Date) => {
    setSelectedStartDate(start);
    setSelectedEndDate(end);
    setShowBookingDialog(true);
  };

  const isOwner = useMemo(() => {
    if (!user || !item) return false;
    // The user's ID from the auth hook is a UUID string.
    // The item.user from the Django API is also a UUID string.
    return item.user === user.id;
  }, [user, item]);

  const handleDelete = async () => {
    if (!item) return;
    await deleteItemMutation.mutateAsync(item.uuid, {
      onSuccess: () => {
        navigate('/my-items');
      },
    });
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-background">
        <Header />
        <div className="container mx-auto px-4 py-8">
          <div className="text-center">{t('common.loading')}</div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-background text-center py-10">
        <p className="text-destructive">{error.message}</p>
        <Button asChild className="mt-4">
          <Link to="/">Back to Home</Link>
        </Button>
      </div>
    );
  }

  if (!item) {
    return (
      <div className="min-h-screen bg-background text-center py-10">
        <p>Item not found.</p>
        <Button asChild className="mt-4">
          <Link to="/">Back to Home</Link>
        </Button>
      </div>
    );
  }

  const {
    name,
    description,
    category,
    condition,
    sale_price,
    sale_price_currency,
    rental_price,
    rental_price_currency,
    created_at,
    images,
  } = item;

  const conditionMap: Record<number, string> = {
    0: t('condition.new'),
    1: t('condition.used'),
    2: t('condition.broken'),
  };

  return (
    <div className="min-h-screen bg-background">
      <Header />
      <div className="container mx-auto max-w-4xl px-4 py-8">
        <Button variant="ghost" onClick={() => navigate(-1)} className="mb-4">
          <ArrowLeft className="mr-2 h-4 w-4" />
          Back
        </Button>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          {/* Image Carousel */}
          <div className="relative">
            <Carousel className="w-full">
              <CarouselContent>
                {images.map((image, index) => (
                  <CarouselItem key={index}>
                    <img
                      src={image.original}
                      alt={`${name} ${index + 1}`}
                      className="w-full h-auto object-cover rounded-lg cursor-pointer"
                      onClick={() => setShowAllImages(true)}
                    />
                  </CarouselItem>
                ))}
              </CarouselContent>
              <CarouselPrevious className="left-2" />
              <CarouselNext className="right-2" />
            </Carousel>
          </div>

          {/* Item Details */}
          <div className="space-y-6">
            <div className="space-y-2">
              <div className="flex flex-wrap items-center gap-4">
                <Badge>{t(`categories.${category}`)}</Badge>
                <Badge variant="secondary">{conditionMap[condition]}</Badge>
              </div>
              <h1 className="text-3xl font-bold">{name}</h1>
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <Calendar className="h-4 w-4" />
                <span>
                  Listed{' '}
                  {formatDistanceToNow(new Date(created_at), {
                    addSuffix: true,
                  })}
                </span>
              </div>
            </div>

            <div className="space-y-4">
              {sale_price && (
                <p className="text-2xl font-bold">{formatPrice(sale_price, sale_price_currency)}</p>
              )}
              {rental_price && (
                <p className="text-xl font-semibold">
                  {formatPrice(rental_price, rental_price_currency)} {t('time.perHour')}
                </p>
              )}
            </div>

            <p className="text-muted-foreground">{description}</p>

            {/* Action Buttons */}
            <div className="flex items-center gap-2 pt-4">
              {/* Owner controls: edit & delete */}
              {isOwner && (
                <>
                  <Button asChild variant="outline">
                    <Link to={`/edit-item/${item.uuid}`}>
                      <Edit3 className="mr-2 h-4 w-4" /> Edit
                    </Link>
                  </Button>
                  <AlertDialog>
                    <AlertDialogTrigger asChild>
                      <Button variant="destructive">
                        <Trash2 className="mr-2 h-4 w-4" /> Delete
                      </Button>
                    </AlertDialogTrigger>
                    <AlertDialogContent>
                      <AlertDialogHeader>
                        <AlertDialogTitle>Are you sure?</AlertDialogTitle>
                        <AlertDialogDescription>
                          This action cannot be undone. This will permanently delete your item.
                        </AlertDialogDescription>
                      </AlertDialogHeader>
                      <AlertDialogFooter>
                        <AlertDialogCancel>Cancel</AlertDialogCancel>
                        <AlertDialogAction onClick={handleDelete}>Delete</AlertDialogAction>
                      </AlertDialogFooter>
                    </AlertDialogContent>
                  </AlertDialog>
                </>
              )}

              {/* Booking dialog: show for non-owners, and also show for owners when item is rentable */}
              {(!isOwner || !!rental_price) && (
                <div className={isOwner ? 'ml-2' : ''}>
                  <TooltipProvider>
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <div>
                          <BookingDialog
                            itemUuid={item.uuid}
                            itemName={name}
                            salePrice={sale_price}
                            salePriceCurrency={sale_price_currency}
                            rentalPrice={rental_price}
                            rentalPriceCurrency={rental_price_currency}
                            preselectedStartDate={selectedStartDate}
                            preselectedEndDate={selectedEndDate}
                            controlledOpen={showBookingDialog}
                            onControlledOpenChange={setShowBookingDialog}
                            disabled={!user || (isOwner && !!sale_price && !rental_price)}
                          />
                        </div>
                      </TooltipTrigger>
                      {!user && (
                        <TooltipContent>
                          <p>{t('auth.loginRequired')}</p>
                        </TooltipContent>
                      )}
                    </Tooltip>
                  </TooltipProvider>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Rental Calendar - Only show for rental items */}
        {rental_price && user && (
          <div className="mt-8">
            <RentalCalendar
              itemUuid={itemUuid}
              onDateRangeSelect={handleDateRangeSelect}
              selectedStart={selectedStartDate}
              selectedEnd={selectedEndDate}
              onBookNow={handleBookNowFromCalendar}
            />
          </div>
        )}
      </div>

      {/* Full-screen image viewer */}
      {showAllImages && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-80"
          onClick={() => setShowAllImages(false)}
        >
          <div
            className="relative w-full h-full max-w-4xl max-h-4xl"
            onClick={e => e.stopPropagation()}
          >
            <Carousel className="w-full h-full">
              <CarouselContent>
                {images.map((image, index) => (
                  <CarouselItem key={index}>
                    <div
                      className="flex items-center justify-center h-full cursor-pointer"
                      onClick={() => setShowAllImages(false)}
                    >
                      <img
                        src={image.original}
                        alt={`${name} ${index + 1}`}
                        className="max-w-full max-h-full object-contain"
                      />
                    </div>
                  </CarouselItem>
                ))}
              </CarouselContent>
              <CarouselPrevious className="left-4 bg-background/80 hover:bg-background" />
              <CarouselNext className="right-4 bg-background/80 hover:bg-background" />
            </Carousel>
            <Button
              variant="ghost"
              size="icon"
              className="absolute top-4 right-4 text-white hover:bg-white/20"
              onClick={() => setShowAllImages(false)}
            >
              <X className="h-6 w-6" />
            </Button>
          </div>
        </div>
      )}
    </div>
  );
};

export default ItemDetail;
