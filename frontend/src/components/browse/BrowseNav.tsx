import { buttonVariants } from '@/components/ui/button';
import { useLanguage } from '@/contexts/LanguageContext';
import { cn } from '@/lib/utils';
import { NavLink, useLocation } from 'react-router-dom';

type BrowseNavProps = {
  className?: string;
};

const browseTabs = [
  { label: 'browse.bookOrRent', type: 'rent' },
  { label: 'browse.buy', type: 'buy' },
  { label: 'browse.wanted', type: 'wanted' },
];

export const BrowseNav = ({ className }: BrowseNavProps) => {
  const { t } = useLanguage();
  const location = useLocation();
  const params = new URLSearchParams(location.search);
  const activeType = location.pathname === '/' ? params.get('type') : null;

  return (
    <nav aria-label="Browse types" className={cn('flex', className)}>
      <div className="flex flex-wrap items-center justify-center gap-3">
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
    </nav>
  );
};
