import { useLanguage } from '@/contexts/LanguageContext';
import { useToast } from '@/hooks/use-toast';
import {
  bookingsCreate,
  bookingsList,
  bookingsPartialUpdate,
  bookingsRetrieve,
  type BookingWritable,
  type PatchedBooking,
} from '@/services/django';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

export const useBookings = () => {
  return useQuery({
    queryKey: ['bookings'],
    queryFn: async () => {
      const response = await bookingsList();
      return response.data;
    },
  });
};

export const useBooking = (uuid?: string) => {
  return useQuery({
    queryKey: ['bookings', uuid],
    queryFn: async () => {
      if (!uuid) throw new Error('Booking UUID is required');
      const response = await bookingsRetrieve({ path: { uuid } });
      return response.data;
    },
    enabled: !!uuid,
  });
};

export const useCreateBooking = () => {
  const { toast } = useToast();
  const { t } = useLanguage();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: BookingWritable) => {
      const response = await bookingsCreate({ body: data });
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['bookings'] });
      toast({
        title: t('booking.successTitle'),
        description: t('booking.successCreated'),
      });
    },
    onError: (error: any) => {
      console.error('Error creating booking:', error);
      toast({
        title: t('common.error'),
        description: error?.non_field_errors[0] || t('booking.errorCreate'),
        variant: 'destructive',
      });
    },
  });
};

export const useUpdateBooking = () => {
  const { toast } = useToast();
  const { t } = useLanguage();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ uuid, data }: { uuid: string; data: PatchedBooking }) => {
      const response = await bookingsPartialUpdate({
        path: { uuid },
        body: data,
      });
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['bookings'] });
      toast({
        title: t('booking.successTitle'),
        description: t('booking.successUpdated'),
      });
    },
    onError: (error: any) => {
      console.error('Error updating booking:', error);
      toast({
        title: t('common.error'),
        description: error?.message || t('booking.errorUpdate'),
        variant: 'destructive',
      });
    },
  });
};
