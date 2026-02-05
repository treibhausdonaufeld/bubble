import { publicItemsList } from '@/services/django';
import { useQuery } from '@tanstack/react-query';
import { type ItemCategory } from './types';

export const useItems = ({
  category,
  search,
  page,
}: { category?: ItemCategory; search?: string; page?: number } = {}) => {
  return useQuery({
    queryKey: ['items', { category, search, page }],
    queryFn: async () => {
      const response = await publicItemsList({
        query: {
          category,
          page: page,
          search: search,
        },
      });
      return {
        items: response.data.results || [],
        pagination: {
          count: response.data.count,
          next: response.data.next ?? null,
          previous: response.data.previous ?? null,
        },
      };
    },
  });
};
