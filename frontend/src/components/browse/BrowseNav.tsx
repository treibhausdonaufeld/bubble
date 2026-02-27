import { buttonVariants } from '@/components/ui/button';
import { useLanguage } from '@/contexts/LanguageContext';
import { ItemCategoryFilter } from '@/hooks/types';
import { cn } from '@/lib/utils';
import { NavLink, useLocation } from 'react-router-dom';
import { ConditionFilter, ConditionValue } from './ConditionFilter';
import { CategoryFilter } from './CategoryFilter';

type BrowseNavProps = {
  selectedCategory: ItemCategoryFilter;
  selectedConditions: ConditionValue[];
  onSelectedCategoryChange: (category: ItemCategoryFilter) => void;
  onSelectedConditionsChange: (conditions: ConditionValue[]) => void;
  className?: string;
};

const browseTabs = [
  { label: 'browse.bookOrRent', type: 'rent' },
  { label: 'browse.buy', type: 'buy' },
  { label: 'browse.wanted', type: 'wanted' },
];

export const BrowseNav = ({
  selectedCategory,
  selectedConditions,
  onSelectedCategoryChange,
  onSelectedConditionsChange,
  className,
}: BrowseNavProps) => {
  const { t } = useLanguage();
  const location = useLocation();
  const params = new URLSearchParams(location.search);
  const activeType = location.pathname === '/' ? params.get('type') : null;

  return (
    <form
      onSubmit={event => event.preventDefault()}
      className={cn(className, 'flex', 'flex-col', 'gap-2')}
    >
      <div className="flex flex-wrap gap-3">
        {browseTabs.map(tab => {
          const isActive = activeType === tab.type;
          const tabParams = new URLSearchParams(location.search);
          tabParams.set('type', tab.type);
          tabParams.delete('page');
          const tabSearch = tabParams.toString();

          return (
            <NavLink
              key={tab.type}
              to={`/?${tabSearch}`}
              className={cn(
                buttonVariants({
                  variant: isActive ? 'default' : 'outline-primary',
                  size: 'sm',
                }),
                'font-semibold',
                isActive ? 'shadow-glow scale-105' : 'hover:scale-105 hover:shadow-medium',
              )}
            >
              {t(tab.label)}
            </NavLink>
          );
        })}
      </div>
      <CategoryFilter
        selectedCategory={selectedCategory}
        onCategoryChange={onSelectedCategoryChange}
      />
      {activeType === 'buy' && (
        <ConditionFilter
          selectedConditions={selectedConditions}
          onConditionsChange={onSelectedConditionsChange}
        />
      )}
    </form>
  );
};
