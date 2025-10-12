import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { useLanguage } from '@/contexts/LanguageContext';
import { useCreateBooking } from '@/hooks/useBookings';
import { formatPrice } from '@/lib/currency';
import { useEffect, useState } from 'react';

interface BookingDialogProps {
  itemUuid: string;
  itemName: string;
  salePrice?: string | null;
  salePriceCurrency?: string;
  rentalPrice?: string | null;
  rentalPriceCurrency?: string;
  buttonSize?: 'default' | 'sm' | 'lg' | 'icon';
  buttonClassName?: string;
  triggerLabel?: string;
  disabled?: boolean;
  preselectedStartDate?: Date;
  preselectedEndDate?: Date;
  controlledOpen?: boolean;
  onControlledOpenChange?: (open: boolean) => void;
}

export const BookingDialog = ({
  itemUuid,
  itemName,
  salePrice,
  salePriceCurrency,
  rentalPrice,
  rentalPriceCurrency,
  buttonSize = 'lg',
  buttonClassName = 'w-full md:w-auto',
  preselectedStartDate,
  preselectedEndDate,
  triggerLabel,
  disabled = false,
  controlledOpen,
  onControlledOpenChange,
}: BookingDialogProps) => {
  const { t } = useLanguage();
  const createBookingMutation = useCreateBooking();
  const [internalOpen, setInternalOpen] = useState(false);
  const isRental = rentalPrice != null;
  const isControlled =
    typeof controlledOpen !== 'undefined' && typeof onControlledOpenChange === 'function';
  const dialogOpen = isControlled ? controlledOpen! : internalOpen;
  const setDialogOpen = (val: boolean) => {
    if (isControlled) {
      onControlledOpenChange!(val);
    } else {
      setInternalOpen(val);
    }
  };
  const [offerPrice, setOfferPrice] = useState('');
  const [timeFrom, setTimeFrom] = useState('');
  const [timeTo, setTimeTo] = useState('');

  // Calculate total price based on time period
  const calculateTotalPrice = (): string => {
    if (!isRental || !timeFrom || !timeTo || rentalPrice == null) {
      return isRental ? rentalPrice || '' : salePrice || '';
    }

    const start = new Date(timeFrom);
    const end = new Date(timeTo);
    const hours = (end.getTime() - start.getTime()) / (1000 * 60 * 60);

    if (hours <= 0) {
      return rentalPrice;
    }

    const hourlyRate = parseFloat(rentalPrice);
    const total = hourlyRate * hours;
    return total.toFixed(2);
  };

  // Set default price when dialog opens or dates change
  useEffect(() => {
    if (dialogOpen) {
      const defaultPrice = calculateTotalPrice();
      setOfferPrice(defaultPrice);
    }
  }, [dialogOpen, isRental, rentalPrice, salePrice, timeFrom, timeTo]);

  // Set preselected dates when they change
  useEffect(() => {
    if (preselectedStartDate) {
      // Format date for datetime-local input (YYYY-MM-DDTHH:mm)
      // This maintains the user's local timezone
      const year = preselectedStartDate.getFullYear();
      const month = String(preselectedStartDate.getMonth() + 1).padStart(2, '0');
      const day = String(preselectedStartDate.getDate()).padStart(2, '0');
      const hours = String(preselectedStartDate.getHours()).padStart(2, '0');
      const minutes = String(preselectedStartDate.getMinutes()).padStart(2, '0');
      setTimeFrom(`${year}-${month}-${day}T${hours}:${minutes}`);
    }
    if (preselectedEndDate) {
      const year = preselectedEndDate.getFullYear();
      const month = String(preselectedEndDate.getMonth() + 1).padStart(2, '0');
      const day = String(preselectedEndDate.getDate()).padStart(2, '0');
      const hours = String(preselectedEndDate.getHours()).padStart(2, '0');
      const minutes = String(preselectedEndDate.getMinutes()).padStart(2, '0');
      setTimeTo(`${year}-${month}-${day}T${hours}:${minutes}`);
    }
  }, [preselectedStartDate, preselectedEndDate]);

  // Recalculate price when dates change
  useEffect(() => {
    if (isRental && timeFrom && timeTo) {
      const calculatedPrice = calculateTotalPrice();
      setOfferPrice(calculatedPrice);
    }
  }, [timeFrom, timeTo]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    // Validation
    if (offerPrice === '' || offerPrice === null) {
      return;
    }

    if (isRental && (!timeFrom || !timeTo)) {
      return;
    }

    try {
      await createBookingMutation.mutateAsync({
        item: itemUuid,
        offer: offerPrice,
        time_from: isRental ? timeFrom : null,
        time_to: isRental ? timeTo : null,
        status: 1, // Pending status
      });

      // Reset form and close dialog
      setOfferPrice('');
      setTimeFrom('');
      setTimeTo('');
      setDialogOpen(false);
    } catch (error) {
      // Error is handled by the mutation hook
    }
  };
  return (
    <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
      <DialogTrigger asChild>
        <Button
          size={buttonSize}
          className={`${buttonClassName} ${disabled ? 'opacity-50 cursor-not-allowed' : ''}`}
          disabled={createBookingMutation.isPending || disabled}
        >
          {triggerLabel ?? (isRental ? t('booking.bookNow') : t('itemDetail.buyNow'))}
        </Button>
      </DialogTrigger>

      <DialogContent>
        <form onSubmit={handleSubmit}>
          <DialogHeader>
            <DialogTitle>{isRental ? t('booking.bookNow') : t('itemDetail.buyNow')}</DialogTitle>
            <DialogDescription>
              {t('booking.createBookingDescription').replace('{itemName}', itemName)}
            </DialogDescription>
          </DialogHeader>

          <div className="grid gap-4 py-4">
            {/* Original Price Display */}
            <div className="space-y-1">
              {isRental && rentalPrice != null ? (
                <p className="text-base">
                  <span className="font-medium">{t('booking.listedRentalPrice')}:</span>{' '}
                  {formatPrice(rentalPrice, rentalPriceCurrency)} {t('time.perHour')}
                </p>
              ) : salePrice != null ? (
                <p className="text-base">
                  <span className="font-medium">{t('booking.listedPrice')}:</span>{' '}
                  {formatPrice(salePrice, salePriceCurrency)}
                </p>
              ) : null}
            </div>

            {/* Rental Duration - only show if item has rental price */}
            {isRental && (
              <>
                <div className="space-y-2">
                  <Label htmlFor="timeFrom">
                    {t('booking.rentalStart')} *
                    <span className="ml-1 text-xs text-muted-foreground">(24h)</span>
                  </Label>
                  <Input
                    id="timeFrom"
                    type="datetime-local"
                    step="3600"
                    value={timeFrom}
                    onChange={e => setTimeFrom(e.target.value)}
                    required
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="timeTo">
                    {t('booking.rentalEnd')} *
                    <span className="ml-1 text-xs text-muted-foreground">(24h)</span>
                  </Label>
                  <Input
                    id="timeTo"
                    type="datetime-local"
                    step="3600"
                    value={timeTo}
                    onChange={e => setTimeTo(e.target.value)}
                    required
                    min={timeFrom}
                  />
                </div>
              </>
            )}

            {/* Calculated Total Price (editable) */}
            <div className="space-y-2">
              <Label htmlFor="offer">
                {isRental ? t('booking.totalPrice') : t('booking.purchaseOffer')} *
              </Label>
              {isRental &&
                timeFrom &&
                timeTo &&
                (() => {
                  const start = new Date(timeFrom);
                  const end = new Date(timeTo);
                  const hours = (end.getTime() - start.getTime()) / (1000 * 60 * 60);
                  if (hours > 0) {
                    return (
                      <p className="text-sm text-muted-foreground">
                        {hours} {hours === 1 ? t('time.hour') : t('time.hours')}
                      </p>
                    );
                  }
                  return null;
                })()}
              <Input
                id="offer"
                type="number"
                step="0.01"
                placeholder={t('booking.enterYourOffer')}
                value={offerPrice}
                onChange={e => setOfferPrice(e.target.value)}
                required
              />
            </div>
          </div>

          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => setDialogOpen(false)}
              disabled={createBookingMutation.isPending}
            >
              {t('common.cancel')}
            </Button>
            <Button type="submit" disabled={createBookingMutation.isPending}>
              {createBookingMutation.isPending
                ? t('common.submitting')
                : t('booking.submitRequest')}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
};
