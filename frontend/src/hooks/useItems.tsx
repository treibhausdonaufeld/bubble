import { publicItemsList, type ItemList } from '@/services/django';
import { useEffect, useState } from 'react';

export const useItems = (category?: string, search?: string, page?: number) => {
  const [items, setItems] = useState<ItemList[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [pagination, setPagination] = useState<{
    count: number;
    next: string | null;
    previous: string | null;
  }>({ count: 0, next: null, previous: null });

  useEffect(() => {
    const fetchItems = async () => {
      try {
        setLoading(true);
        setError(null);
        const response = await publicItemsList({
          query: {
            category: category as any,
            page: page,
            search: search,
            published: true,
          },
        });
        setItems(response.data.results || []);
        setPagination({
          count: response.data.count,
          next: response.data.next ?? null,
          previous: response.data.previous ?? null,
        });
      } catch (err) {
        console.error('Error fetching items:', err);
        setError(err instanceof Error ? err.message : 'Failed to fetch items');
        setItems([]);
        setPagination({ count: 0, next: null, previous: null });
      } finally {
        setLoading(false);
      }
    };

    fetchItems();
  }, [category, search, page]);

  const refetch = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await publicItemsList({
        query: {
          category: category as any,
          page: page,
          search: search,
          published: true,
        },
      });
      setItems(response.data.results || []);
      setPagination({
        count: response.data.count,
        next: response.data.next ?? null,
        previous: response.data.previous ?? null,
      });
    } catch (err) {
      console.error('Error refetching items:', err);
      setError(err instanceof Error ? err.message : 'Failed to fetch items');
      setItems([]);
      setPagination({ count: 0, next: null, previous: null });
    } finally {
      setLoading(false);
    }
  };

  return { items, loading, error, refetch, pagination };
};
