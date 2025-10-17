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
import { useUpdateBooking } from '@/hooks/useBookings';
import { useEffect, useState } from 'react';

interface Props {
  booking: any; // Booking type from API
}

const BookingEditDialog = ({ booking }: Props) => {
  const { t } = useLanguage();
  const updateBooking = useUpdateBooking();
  const [open, setOpen] = useState(false);

  const isRental = !!booking?.item_details?.rental_price;
  const [timeFrom, setTimeFrom] = useState<string>(booking?.time_from || '');
  const [timeTo, setTimeTo] = useState<string>(booking?.time_to || '');
  const [offer, setOffer] = useState<string>(booking?.offer ?? '');

  useEffect(() => {
    if (open) {
      setTimeFrom(booking?.time_from || '');
      setTimeTo(booking?.time_to || '');
      setOffer(booking?.offer ?? '');
    }
  }, [open, booking]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await updateBooking.mutateAsync({
        id: booking.id,
        data: {
          offer: offer === '' ? null : offer,
          time_from: timeFrom === '' ? null : timeFrom,
          time_to: timeTo === '' ? null : timeTo,
        },
      });
      setOpen(false);
    } catch (err) {
      // handled by hook
    }
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button size="sm" variant="outline">
          {t('bookings.editBooking')}
        </Button>
      </DialogTrigger>
      <DialogContent>
        <form onSubmit={handleSubmit}>
          <DialogHeader>
            <DialogTitle>{t('bookings.editBooking')}</DialogTitle>
            <DialogDescription>{t('bookings.editBookingDescription')}</DialogDescription>
          </DialogHeader>

          <div className="grid gap-4 py-4">
            {isRental && (
              <>
                <div className="space-y-2">
                  <Label htmlFor="timeFrom">{t('booking.rentalStart')}</Label>
                  <Input
                    id="timeFrom"
                    type="datetime-local"
                    value={timeFrom}
                    onChange={e => setTimeFrom(e.target.value)}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="timeTo">{t('booking.rentalEnd')}</Label>
                  <Input
                    id="timeTo"
                    type="datetime-local"
                    value={timeTo}
                    onChange={e => setTimeTo(e.target.value)}
                  />
                </div>
              </>
            )}

            <div className="space-y-2">
              <Label htmlFor="offer">{t('booking.enterYourOffer')}</Label>
              <Input
                id="offer"
                type="number"
                step="0.01"
                value={offer ?? ''}
                onChange={e => setOffer(e.target.value)}
              />
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setOpen(false)}>
              {t('common.cancel')}
            </Button>
            <Button type="submit" disabled={updateBooking.isPending}>
              {t('bookings.update')}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
};

export default BookingEditDialog;
