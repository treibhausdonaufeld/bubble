import { publicItemsList } from '@/services/django';
import { useQuery } from '@tanstack/react-query';
import { type ItemCategory } from './types';
import { ConditionValue } from '@/components/browse-items/ConditionFilter';

export const useItems = ({
  category,
  search,
  page,
  conditions,
}: {
  category?: ItemCategory;
  search?: string;
  page?: number;
  conditions?: ConditionValue[];
} = {}) => {
  return useQuery({
    queryKey: ['items', { category, search, page, conditions }],
    queryFn: async () => {
      const response = await publicItemsList({
        query: {
          category,
          page: page,
          search: search,
          conditions,
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
