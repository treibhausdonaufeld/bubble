import { BrowseNav } from '@/components/browse/BrowseNav';
import { ItemCard } from '@/components/browse/ItemCard';
import { Button } from '@/components/ui/button';
import { useItems } from '@/hooks/useItems';
import { type ItemCategoryFilter } from '@/hooks/types';
import { type Status402Enum } from '@/services/django';
import { type ConditionEnum } from '@/services/django';
import { useLanguage } from '@/contexts/LanguageContext';
import { ChevronLeft, ChevronRight } from 'lucide-react';
import { useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';

type BrowseItemsPageFilters = {
  status?: Status402Enum | Status402Enum[];
  minSalePrice?: number;
  minRentalPrice?: number;
  maxSalePrice?: number;
};

const PAGE_SIZE = 20;
// by default, show 'new' and 'used' items, don't show 'broken' items
const DEFAULT_CONDITIONS: ConditionEnum[] = [0, 1];

const Index = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { t } = useLanguage();
  const params = new URLSearchParams(location.search);
  const typeParam = params.get('type');
  const searchQuery = params.get('search') || undefined;
  const pageParam = params.get('page');
  const currentPage = pageParam ? parseInt(pageParam, 10) : 1;
  let itemFilters: BrowseItemsPageFilters | undefined;
  if (typeParam === 'buy') {
    itemFilters = { minSalePrice: 0 };
  } else if (typeParam === 'rent') {
    itemFilters = { minRentalPrice: 0 };
  } else if (typeParam === 'wanted') {
    itemFilters = { maxSalePrice: -0.001 };
  }

  const [selectedCategory, setSelectedCategory] = useState<ItemCategoryFilter>('all');
  const [selectedConditions, setSelectedConditions] = useState<ConditionEnum[]>(DEFAULT_CONDITIONS);

  let conditions: ConditionEnum[] | undefined;
  if (typeParam === 'buy' && selectedConditions.length > 0) {
    conditions = selectedConditions;
  }

  const itemsQuery = useItems({
    category: selectedCategory === 'all' ? undefined : selectedCategory,
    conditions: conditions,
    search: searchQuery,
    page: currentPage,
    status: itemFilters?.status,
    minSalePrice: itemFilters?.minSalePrice,
    minRentalPrice: itemFilters?.minRentalPrice,
    maxSalePrice: itemFilters?.maxSalePrice,
  });

  const handlePageChange = (newPage: number) => {
    const newParams = new URLSearchParams(location.search);
    newParams.set('page', String(newPage));
    navigate(`/?${newParams.toString()}`);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  if (itemsQuery.error) {
    return (
      <main className="container mx-auto px-4 py-8">
        <div className="text-center">
          <p className="text-destructive">{t('common.loadingError')}</p>
        </div>
      </main>
    );
  }

  if (itemsQuery.isLoading) {
    return (
      <main className="container mx-auto px-4 py-8">
        <div className="text-center">
          <p className="text-destructive">{t('index.loadingItems')}</p>
        </div>
      </main>
    );
  }

  if (itemsQuery.isSuccess) {
    const totalPages = Math.ceil(itemsQuery.data.pagination.count / PAGE_SIZE);

    return (
      <main className="container mx-auto px-4 py-4">
        <div className="space-y-4">
          <BrowseNav
            selectedConditions={selectedConditions}
            selectedCategory={selectedCategory}
            onSelectedConditionsChange={setSelectedConditions}
            onSelectedCategoryChange={setSelectedCategory}
          />

          <div className="space-y-6">
            <div className="flex items-center justify-between">
              <h2 className="text-2xl font-bold text-foreground">
                {searchQuery
                  ? t('index.searchResults').replace('{query}', searchQuery)
                  : selectedCategory === 'all'
                    ? t('index.allItems')
                    : t('index.categoryItems').replace('{category}', selectedCategory)}
              </h2>
              <div className="text-sm text-muted-foreground">
                {t('index.itemsFound').replace('{count}', String(itemsQuery.data.pagination.count))}
              </div>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
            {itemsQuery.data.items.length === 0 ? (
              <div className="col-span-full text-center py-8">
                <p>{t('index.noItemsFound')}</p>
              </div>
            ) : (
              itemsQuery.data.items.map(item => (
                <ItemCard
                  key={item.id}
                  id={item.id}
                  title={item.name}
                  description={item.description || ''}
                  category={item.category}
                  condition={
                    item.condition === 0 ? 'new' : item.condition === 1 ? 'used' : 'broken'
                  }
                  status={item.status}
                  listingType="sell" // Django API doesn't have listing_type in list view, default to sell
                  salePrice={item.sale_price ? parseFloat(item.sale_price) : undefined}
                  salePriceCurrency={item.sale_price_currency}
                  rentalPrice={item.rental_price ? parseFloat(item.rental_price) : undefined}
                  rentalPriceCurrency={item.rental_price_currency}
                  location="Location not set"
                  imageUrl={item.first_image || '/placeholder.svg'}
                  owner={item.user}
                  createdAt={item.created_at}
                  isFavorited={false}
                />
              ))
            )}
          </div>

          {/* Pagination Controls */}
          {totalPages > 1 && (
            <div className="flex items-center justify-center gap-2 pt-8">
              <Button
                variant="outline"
                size="sm"
                onClick={() => handlePageChange(currentPage - 1)}
                disabled={currentPage === 1}
              >
                <ChevronLeft className="h-4 w-4 mr-1" />
                {t('index.previous')}
              </Button>

              <div className="flex items-center gap-2">
                {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                  let pageNum: number;
                  if (totalPages <= 5) {
                    pageNum = i + 1;
                  } else if (currentPage <= 3) {
                    pageNum = i + 1;
                  } else if (currentPage >= totalPages - 2) {
                    pageNum = totalPages - 4 + i;
                  } else {
                    pageNum = currentPage - 2 + i;
                  }

                  return (
                    <Button
                      key={pageNum}
                      variant={currentPage === pageNum ? 'default' : 'outline'}
                      size="sm"
                      onClick={() => handlePageChange(pageNum)}
                    >
                      {pageNum}
                    </Button>
                  );
                })}
              </div>

              <Button
                variant="outline"
                size="sm"
                onClick={() => handlePageChange(currentPage + 1)}
                disabled={currentPage === totalPages}
              >
                {t('index.next')}
                <ChevronRight className="h-4 w-4 ml-1" />
              </Button>
            </div>
          )}
        </div>
      </main>
    );
  }
};

export default Index;
