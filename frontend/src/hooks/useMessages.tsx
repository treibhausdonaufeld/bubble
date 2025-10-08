import { useToast } from '@/hooks/use-toast';
import { messagesCreate, messagesList, type MessageWritable } from '@/services/django';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

export const useMessages = (bookingUuid?: string) => {
  const query = useQuery({
    queryKey: ['messages', bookingUuid],
    queryFn: async () => {
      if (!bookingUuid) throw new Error('Booking UUID is required');
      const response = await messagesList({
        query: { booking: bookingUuid },
      });
      return response.data;
    },
    enabled: !!bookingUuid,
  });

  return query;
};

export const useCreateMessage = () => {
  const { toast } = useToast();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: MessageWritable) => {
      const response = await messagesCreate({ body: data });
      return response.data;
    },
    onSuccess: data => {
      // Invalidate messages for this booking
      queryClient.invalidateQueries({ queryKey: ['messages', data.booking] });
      toast({
        title: 'Message sent',
        description: 'Your message has been sent successfully.',
      });
    },
    onError: (error: Error) => {
      toast({
        variant: 'destructive',
        title: 'Failed to send message',
        description: error?.message || 'Failed to send message. Please try again.',
      });
    },
  });
};
