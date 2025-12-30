import { type PublicItemsListData } from '@/services/django';

export type ItemCategory = PublicItemsListData['query']['category'];
export type ItemCategoryFilter = ItemCategory | 'all';
