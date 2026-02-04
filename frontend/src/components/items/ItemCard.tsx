import { BookingDialog } from '@/components/items/BookingDialog';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardFooter } from '@/components/ui/card';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import { useLanguage } from '@/contexts/LanguageContext';
import { useAuth } from '@/hooks/useAuth';
import { formatPrice } from '@/lib/currency';
import { cn } from '@/lib/utils';
import { Status402Enum } from '@/services/django';
import { Clock, ShoppingCart } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { getStatusColor, getStatusLabel } from './status';
import { convertLineBreaks } from '@/lib/convertLineBreaks';

interface ItemCardProps {
  id: string;
  title?: string;
  description: string;
  category?: string;
  condition: 'new' | 'used' | 'broken';
  listingType: 'sell' | 'rent' | 'both';
  salePrice?: number;
  salePriceCurrency?: string | null;
  rentalPrice?: number;
  rentalPriceCurrency?: string | null;
  rentalPeriod?: 'hourly' | 'daily' | 'weekly';
  location: string;
  imageUrl?: string;
  ownerAvatar?: string;
  createdAt: string;
  isFavorited?: boolean;
  ownerId?: string;
  owner?: string;
  status?: Status402Enum | null;
}

export const ItemCard = ({
  id,
  title,
  description,
  category,
  condition,
  listingType,
  salePrice,
  salePriceCurrency,
  rentalPrice,
  rentalPriceCurrency,
  location,
  imageUrl,
  ownerAvatar,
  createdAt,
  isFavorited = false,
  owner,
  status,
}: ItemCardProps) => {
  const navigate = useNavigate();
  const { user } = useAuth();
  const { t } = useLanguage();

  const isOwner = user && owner && user.id === owner;

  const handleMessageOwner = () => {
    if (!user) {
      navigate('/auth');
      return;
    }

    // Contact functionality removed - navigate to item details instead
    navigate(`/item/${id}`);
  };

  const conditionColors = {
    new: 'bg-success text-success-foreground',
    used: 'bg-warning text-warning-foreground',
    broken: 'bg-destructive text-destructive-foreground',
  };

  const typeColors = {
    sell: 'bg-primary text-primary-foreground',
    rent: 'bg-accent text-accent-foreground',
    both: 'bg-gradient-warm text-white',
  };

  return (
    <Card
      className="group overflow-hidden transition-all duration-300 hover:shadow-strong hover:scale-105 border-border animate-fade-in cursor-pointer"
      onClick={() => navigate(`/item/${id}`)}
    >
      {/* Image Section */}
      <div className="relative aspect-4/3 overflow-hidden">
        {imageUrl ? (
          <img
            src={imageUrl}
            alt={title}
            className="h-full w-full object-cover transition-transform duration-300 group-hover:scale-110"
          />
        ) : (
          <div className="flex h-full w-full items-center justify-center bg-gradient-subtle">
            <div className="text-center text-muted-foreground">
              <ShoppingCart className="mx-auto h-12 w-12 mb-2" />
              <p className="text-sm">{t('item.noImage')}</p>
            </div>
          </div>
        )}

        {/* Overlay badges */}
        <div className="absolute top-3 left-3 flex gap-2">
          {/* Status badge (shows available/reserved/sold/...) */}
          {typeof status !== 'undefined' && status !== null ? (
            <Badge className={cn(getStatusColor(status), 'text-xs shadow-medium')}>
              {getStatusLabel(status) ? t(`status.${getStatusLabel(status)}`) : ''}
            </Badge>
          ) : null}
        </div>

        {/* Price overlay */}
        <div className="absolute bottom-3 right-3">
          <div className="rounded-lg bg-background/90 backdrop-blur-xs px-3 py-1 shadow-medium">
            {salePrice !== undefined && (
              <div className="flex items-center gap-1 text-sm font-semibold">
                {formatPrice(salePrice, salePriceCurrency)}
              </div>
            )}
            {rentalPrice !== undefined && (
              <div className="flex items-center gap-1 text-sm font-semibold">
                {formatPrice(rentalPrice, rentalPriceCurrency)} {t('time.perHour')}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Content Section */}
      <CardContent className="p-4 space-y-3">
        <div>
          <h3 className="font-semibold text-foreground line-clamp-1 group-hover:text-primary transition-colors">
            {title}
          </h3>
          <p className="text-sm text-muted-foreground line-clamp-2 mt-1">
            {convertLineBreaks(description)}
          </p>
        </div>

        <div className="flex items-center justify-between text-xs text-muted-foreground">
          <div className="flex items-center gap-1">
            <Clock className="h-3 w-3" />
            <span>{new Date(createdAt).toLocaleDateString()}</span>
          </div>
        </div>
      </CardContent>

      {/* Actions */}
      <CardFooter
        className="p-4 pt-0 flex gap-2"
        onClick={e => {
          e.stopPropagation();
        }}
      >
        <TooltipProvider>
          <Tooltip>
            <TooltipTrigger asChild>
              <div className="flex flex-1 gap-2">
                {(() => {
                  const buyingAllowed = status === 2 || status === 3; // 2 = available, 3 = reserved
                  const isRentable = rentalPrice !== undefined && rentalPrice !== null;

                  if (isRentable) {
                    // For rentals, navigate to item detail and open/scroll to the booking calendar
                    return (
                      <Button
                        size="sm"
                        className="w-full"
                        onClick={e => {
                          e.stopPropagation();
                          if (!user) {
                            navigate('/auth');
                            return;
                          }
                          navigate(`/item/${id}#booking`);
                        }}
                        disabled={(isOwner && !!salePrice) || !user}
                      >
                        {t('itemDetail.rentNow')}
                      </Button>
                    );
                  }

                  return (
                    <BookingDialog
                      itemUuid={id}
                      itemName={title}
                      salePrice={salePrice?.toString()}
                      salePriceCurrency={salePriceCurrency || undefined}
                      rentalPriceCurrency={rentalPriceCurrency || undefined}
                      buttonSize="sm"
                      buttonClassName="w-full"
                      triggerLabel={isRentable ? t('booking.bookNow') : t('itemDetail.buyNow')}
                      disabled={
                        (isOwner && !!salePrice) || !user || (!isRentable && !buyingAllowed)
                      }
                    />
                  );
                })()}
              </div>
            </TooltipTrigger>
            {(!user || isOwner) && (
              <TooltipContent>
                <p>{!user ? t('auth.loginRequired') : t('item.cannotMessageSelf')}</p>
              </TooltipContent>
            )}
          </Tooltip>
        </TooltipProvider>
      </CardFooter>
    </Card>
  );
};
