import { publicItemsList, type Status402Enum, type ConditionEnum } from '@/services/django';
import { useQuery } from '@tanstack/react-query';
import { type ItemCategory } from './types';

export const useItems = ({
  category,
  search,
  page,
  status,
  minSalePrice,
  minRentalPrice,
  maxSalePrice,
  conditions,
}: {
  category?: ItemCategory;
  search?: string;
  page?: number;
  status?: Status402Enum | Status402Enum[];
  minSalePrice?: number;
  minRentalPrice?: number;
  maxSalePrice?: number;
  conditions?: ConditionEnum[];
} = {}) => {
  const normalizedStatus =
    status === undefined ? undefined : Array.isArray(status) ? status : [status];
  const statusKey = normalizedStatus?.join(',');
  // sort the array so it can be better used as a key
  const conditionsSorted = conditions && [...conditions].sort();

  return useQuery({
    queryKey: [
      'items',
      {
        category,
        search,
        page,
        status: statusKey,
        minSalePrice,
        minRentalPrice,
        maxSalePrice,
        conditions: conditionsSorted,
      },
    ],
    queryFn: async () => {
      const response = await publicItemsList({
        query: {
          category,
          page: page,
          search: search,
          status: normalizedStatus,
          min_sale_price: minSalePrice,
          min_rental_price: minRentalPrice,
          max_sale_price: maxSalePrice,
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
