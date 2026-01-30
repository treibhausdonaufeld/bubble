import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { useLanguage } from '@/contexts/LanguageContext';
import { cn } from '@/lib/utils';
import {
  BookOpen,
  Car,
  ChefHat,
  Dumbbell,
  Flower2,
  Gamepad2,
  Grid3x3,
  MoreHorizontal,
  Shirt,
  Smartphone,
  Sofa,
  Wrench,
} from 'lucide-react';
import { useState } from 'react';

const categories = [
  { id: '', name: 'All Items', icon: Grid3x3 },
  { id: 'electronics', name: 'Electronics', icon: Smartphone },
  { id: 'tools', name: 'Tools', icon: Wrench },
  { id: 'furniture', name: 'Furniture', icon: Sofa },
  { id: 'books', name: 'Books', icon: BookOpen },
  { id: 'sports', name: 'Sports', icon: Dumbbell },
  { id: 'clothing', name: 'Clothing', icon: Shirt },
  { id: 'kitchen', name: 'Kitchen', icon: ChefHat },
  { id: 'garden', name: 'Garden', icon: Flower2 },
  { id: 'toys', name: 'Toys', icon: Gamepad2 },
  { id: 'vehicles', name: 'Vehicles', icon: Car },
  { id: 'rooms', name: 'Rooms', icon: Sofa },
  { id: 'other', name: 'Other', icon: MoreHorizontal },
];

interface CategoryFilterProps {
  selectedCategory: string;
  onCategoryChange: (category: string) => void;
}

export const CategoryFilter = ({ selectedCategory, onCategoryChange }: CategoryFilterProps) => {
  const [showAll, setShowAll] = useState(false);
  const { t } = useLanguage();

  const getCategoryName = (id: string) => {
    switch (id) {
      case '':
        return t('categories.all');
      case 'electronics':
        return t('categories.electronics');
      case 'tools':
        return t('categories.tools');
      case 'furniture':
        return t('categories.furniture');
      case 'books':
        return t('categories.books');
      case 'sports':
        return t('categories.sports');
      case 'clothing':
        return t('categories.clothing');
      case 'kitchen':
        return t('categories.kitchen');
      case 'garden':
        return t('categories.garden');
      case 'toys':
        return t('categories.toys');
      case 'vehicles':
        return t('categories.vehicles');
      case 'rooms':
        return t('categories.rooms');
      case 'other':
        return t('categories.other');
      default:
        return id;
    }
  };

  const visibleCategories = showAll ? categories : categories.slice(0, 8);

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-foreground">Categories</h3>
        <Badge variant="secondary" className="animate-bounce-gentle">
          {categories.length - 1} available
        </Badge>
      </div>

      <div className="flex flex-wrap gap-2">
        {visibleCategories.map(category => {
          const Icon = category.icon;
          const isSelected = selectedCategory === category.id;

          return (
            <Button
              key={category.id}
              variant={isSelected ? 'community' : 'ghost'}
              size="sm"
              onClick={() => onCategoryChange(category.id)}
              className={cn(
                'gap-2 transition-all duration-300',
                isSelected ? 'shadow-glow scale-105' : 'hover:scale-105 hover:shadow-medium',
              )}
            >
              <Icon className="h-4 w-4" />
              <span className="hidden sm:inline">{getCategoryName(category.id)}</span>
            </Button>
          );
        })}

        {!showAll && categories.length > 8 && (
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setShowAll(true)}
            className="gap-2 text-muted-foreground hover:text-foreground"
          >
            <MoreHorizontal className="h-4 w-4" />
            <span className="hidden sm:inline">More</span>
          </Button>
        )}
      </div>
    </div>
  );
};
