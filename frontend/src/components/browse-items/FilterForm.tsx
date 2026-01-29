import { FormEvent } from 'react';
import { CategoryFilter } from './CategoryFilter';
import { ConditionFilter, type ConditionValue } from './ConditionFilter';
import { ItemCategoryFilter } from '@/hooks/types';

type FilterOptions = {
  category?: ItemCategoryFilter;
  conditions?: ConditionValue[];
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
