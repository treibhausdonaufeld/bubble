import { ItemCard } from '@/components/items/ItemCard';
import { CategoryFilter } from '@/components/layout/CategoryFilter';
import { Header } from '@/components/layout/Header';
import { HeroSection } from '@/components/layout/HeroSection';
import { Button } from '@/components/ui/button';
import { useAuth } from '@/hooks/useAuth';
import { useItems } from '@/hooks/useItems';
import { ChevronLeft, ChevronRight } from 'lucide-react';
import { useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';

// Mock data for initial demonstration
const mockItems = [
  {
    id: '1',
    title: 'Professional Drill Set',
    description: 'Complete drill set with various bits. Perfect for home improvement projects.',
    category: 'tools',
    condition: 'used' as const,
    listingType: 'both' as const,
    salePrice: 45,
    rentalPrice: 8,
    rentalPeriod: 'daily' as const,
    location: 'Downtown, 2km away',
    imageUrl: 'https://images.unsplash.com/photo-1581091226825-a6a2a5aee158?w=400&h=300&fit=crop',
    ownerName: 'Sarah M.',
    ownerRating: 4.8,
    createdAt: '2 days ago',
    isFavorited: false,
  },
  {
    id: '2',
    title: 'MacBook Pro 13-inch',
    description:
      'Excellent condition laptop, perfect for work or study. Includes charger and case.',
    category: 'electronics',
    condition: 'used' as const,
    listingType: 'sell' as const,
    salePrice: 899,
    location: 'City Center, 1.5km away',
    imageUrl: 'https://images.unsplash.com/photo-1531297484001-80022131f5a1?w=400&h=300&fit=crop',
    ownerName: 'Alex K.',
    ownerRating: 4.9,
    createdAt: '1 day ago',
    isFavorited: true,
  },
  {
    id: '3',
    title: 'Mountain Bike',
    description: 'Great bike for trails and city rides. Recently serviced, ready to go!',
    category: 'sports',
    condition: 'used' as const,
    listingType: 'rent' as const,
    rentalPrice: 15,
    rentalPeriod: 'daily' as const,
    location: 'Park District, 3km away',
    imageUrl: 'https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=400&h=300&fit=crop',
    ownerName: 'Mike R.',
    ownerRating: 4.7,
    createdAt: '3 days ago',
    isFavorited: false,
  },
];

const Index = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const params = new URLSearchParams(location.search);
  const searchQuery = params.get('search') || undefined;
  const pageParam = params.get('page');
  const currentPage = pageParam ? parseInt(pageParam, 10) : 1;

  const [selectedCategory, setSelectedCategory] = useState('');
  const { items, loading, error, pagination } = useItems(
    selectedCategory,
    searchQuery,
    currentPage,
  );
  const { user } = useAuth();

  const handlePageChange = (newPage: number) => {
    const newParams = new URLSearchParams(location.search);
    newParams.set('page', String(newPage));
    navigate(`/?${newParams.toString()}`);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const totalPages = Math.ceil(pagination.count / 20); // Assuming 20 items per page

  if (error) {
    return (
      <div className="min-h-screen bg-background">
        <Header />
        <main className="container mx-auto px-4 py-8">
          <div className="text-center">
            <p className="text-destructive">Error loading items: {error}</p>
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      <Header />
      {!user && <HeroSection />}

      <main className="container mx-auto px-4 py-8">
        <div className="space-y-8">
          <CategoryFilter
            selectedCategory={selectedCategory}
            onCategoryChange={setSelectedCategory}
          />

          <div className="space-y-6">
            <div className="flex items-center justify-between">
              <h2 className="text-2xl font-bold text-foreground">
                {searchQuery
                  ? `Search results for "${searchQuery}"`
                  : selectedCategory === 'all'
                    ? 'All Items'
                    : `${selectedCategory} Items`}
              </h2>
              <div className="text-sm text-muted-foreground">{pagination.count} items found</div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
              {loading ? (
                <div className="col-span-full text-center py-8">
                  <p>Loading items...</p>
                </div>
              ) : items.length === 0 ? (
                <div className="col-span-full text-center py-8">
                  <p>No items found in this category.</p>
                </div>
              ) : (
                items.map(item => (
                  <ItemCard
                    key={item.id}
                    id={item.id}
                    title={item.name}
                    description={item.description || ''}
                    category={item.category}
                    condition={
                      item.condition === 0 ? 'new' : item.condition === 1 ? 'used' : 'broken'
                    }
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
            {!loading && totalPages > 1 && (
              <div className="flex items-center justify-center gap-2 pt-8">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handlePageChange(currentPage - 1)}
                  disabled={currentPage === 1}
                >
                  <ChevronLeft className="h-4 w-4 mr-1" />
                  Previous
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
                        variant={currentPage === pageNum ? 'default' : 'outline-solid'}
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
                  Next
                  <ChevronRight className="h-4 w-4 ml-1" />
                </Button>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
};

export default Index;
