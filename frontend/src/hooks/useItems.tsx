import { publicItemsList, type Status402Enum } from '@/services/django';
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
}: {
  category?: ItemCategory;
  search?: string;
  page?: number;
  status?: Status402Enum | Status402Enum[];
  minSalePrice?: number;
  minRentalPrice?: number;
  maxSalePrice?: number;
} = {}) => {
  const normalizedStatus =
    status === undefined ? undefined : Array.isArray(status) ? status : [status];
  const statusKey = normalizedStatus?.join(',');

  return useQuery({
    queryKey: [
      'items',
      { category, search, page, status: statusKey, minSalePrice, minRentalPrice, maxSalePrice },
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
