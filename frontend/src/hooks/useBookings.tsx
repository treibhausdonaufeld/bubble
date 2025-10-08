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
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: BookingWritable) => {
      const response = await bookingsCreate({ body: data });
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['bookings'] });
      toast({
        title: 'Success',
        description: 'Booking request created successfully!',
      });
    },
    onError: (error: any) => {
      console.error('Error creating booking:', error);
      toast({
        title: 'Error',
        description: error?.message || 'Failed to create booking request. Please try again.',
        variant: 'destructive',
      });
    },
  });
};

export const useUpdateBooking = () => {
  const { toast } = useToast();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ uuid, data }: { uuid: string; data: PatchedBooking }) => {
      const response = await bookingsPartialUpdate({ path: { uuid }, body: data });
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['bookings'] });
      toast({
        title: 'Success',
        description: 'Booking updated successfully!',
      });
    },
    onError: (error: any) => {
      console.error('Error updating booking:', error);
      toast({
        title: 'Error',
        description: error?.message || 'Failed to update booking. Please try again.',
        variant: 'destructive',
      });
    },
  });
};
