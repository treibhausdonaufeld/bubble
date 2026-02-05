import { FormEvent } from 'react';
import { CategoryFilter } from './CategoryFilter';
import { ItemCategoryFilter } from '@/hooks/types';
import { ConditionEnum } from '@/services/django';
import { ConditionFilter } from './ConditionFilter';

type FilterOptions = {
  category?: ItemCategoryFilter;
  conditions?: ConditionEnum[];
};

type FilterFormProps = {
  filters: FilterOptions;
  onFiltersChange: (value: FilterOptions) => void;
};

export const FilterForm = ({ filters, onFiltersChange }: FilterFormProps) => {
  return (
    <form onSubmit={event => event.preventDefault()} className="space-y-8">
      <CategoryFilter
        selectedCategory={filters.category || 'all'}
        onCategoryChange={value => {
          onFiltersChange({ ...filters, category: value });
        }}
      />
      <ConditionFilter
        selectedConditions={filters.conditions || []}
        onConditionsChange={value => {
          onFiltersChange({ ...filters, conditions: value });
        }}
      />
    </form>
  );
};
