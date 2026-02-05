import { ConditionEnum, publicItemsList } from '@/services/django';
import { useQuery } from '@tanstack/react-query';
import { type ItemCategory } from './types';

export const useItems = ({
  category,
  search,
  page,
  conditions,
}: {
  category?: ItemCategory;
  search?: string;
  page?: number;
  conditions?: ConditionEnum[];
} = {}) => {
  // sort the array so it can be better used as a key
  const conditionsSorted = conditions && [...conditions].sort();
  return useQuery({
    queryKey: ['items', { category, search, page, conditions: conditionsSorted }],
    queryFn: async () => {
      const response = await publicItemsList({
        query: {
          category,
          page: page,
          search: search,
          conditions: conditionsSorted,
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
