import { useToast } from '@/hooks/use-toast';
import { useAuth } from '@/hooks/useAuth';
import {
  itemsDestroy,
  itemsList,
  itemsPartialUpdate,
  StatusEnum,
  type PaginatedItemListList,
} from '@/services/django';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

export const useMyItems = (page?: number) => {
  const { user } = useAuth();

  return useQuery<PaginatedItemListList>({
    queryKey: ['my-items', user?.id, page],
    queryFn: async () => {
      if (!user) throw new Error('User not authenticated');
      const response = await itemsList({
        query: {
          user: Number(user.id),
          page: page,
        },
      });
      return response.data;
    },
    enabled: !!user,
  });
};

export const useUpdateItemStatus = () => {
  const queryClient = useQueryClient();
  const { user } = useAuth();
  const { toast } = useToast();

  return useMutation({
    mutationFn: async ({ itemId, status }: { itemId: string; status: StatusEnum }) => {
      const response = await itemsPartialUpdate({
        path: { uuid: itemId },
        body: { status },
      });

      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['my-items', user?.id] });
      toast({
        title: 'Status Updated',
        description: 'The item status has been successfully updated.',
      });
    },
    onError: (error: Error) => {
      toast({
        title: 'Error Updating Status',
        description: error.message || 'Failed to update item status',
        variant: 'destructive',
      });
    },
  });
};

export const useDeleteItem = () => {
  const queryClient = useQueryClient();
  const { user } = useAuth();
  const { toast } = useToast();

  return useMutation({
    mutationFn: async (itemId: string) => {
      if (!user) throw new Error('User not authenticated');
      const response = await itemsDestroy({
        path: { uuid: itemId },
      });

      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['my-items', user?.id] });
      toast({
        title: 'Item Deleted',
        description: 'The item has been successfully deleted.',
      });
    },
    onError: (error: Error) => {
      toast({
        title: 'Error Deleting Item',
        description: error.message,
        variant: 'destructive',
      });
    },
  });
};
