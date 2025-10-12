import { BookingDialog } from '@/components/items/BookingDialog';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardFooter } from '@/components/ui/card';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import { useLanguage } from '@/contexts/LanguageContext';
import { useAuth } from '@/hooks/useAuth';
import { formatPrice } from '@/lib/currency';
import { cn } from '@/lib/utils';
import { Clock, MessageCircle, ShoppingCart } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

interface ItemCardProps {
  id: string;
  title: string;
  description: string;
  category: string;
  condition: 'new' | 'used' | 'broken';
  listingType: 'sell' | 'rent' | 'both';
  salePrice?: number;
  salePriceCurrency?: string | null;
  rentalPrice?: number;
  rentalPriceCurrency?: string | null;
  rentalPeriod?: 'hourly' | 'daily' | 'weekly';
  location: string;
  imageUrl?: string;
  ownerName: string;
  ownerAvatar?: string;
  ownerRating: number;
  createdAt: string;
  isFavorited?: boolean;
  ownerId?: string;
  username?: string;
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
  ownerName,
  ownerAvatar,
  ownerRating,
  createdAt,
  isFavorited = false,
  username,
}: ItemCardProps) => {
  const navigate = useNavigate();
  const { user } = useAuth();
  const { t } = useLanguage();

  const isOwner = user && username && user.username === username;

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
      <div className="relative aspect-[4/3] overflow-hidden">
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
          <Badge className={cn(conditionColors[condition], 'text-xs shadow-medium')}>
            {t(`condition.${condition}`)}
          </Badge>
          {/* Sale / Rent badge */}
          {salePrice ? (
            <Badge className={cn(typeColors['sell'], 'text-xs shadow-medium')}>
              {t('item.price.sale')}
            </Badge>
          ) : null}
          {rentalPrice ? (
            <Badge className={cn(typeColors['rent'], 'text-xs shadow-medium')}>
              {t('item.price.rent')}
            </Badge>
          ) : null}
        </div>

        {/* Favorite button */}
        {/* <Button
          variant="ghost"
          size="icon"
          className="absolute top-3 right-3 h-8 w-8 rounded-full bg-background/80 backdrop-blur-sm hover:bg-background/90 transition-all duration-300"
        >
          <Heart className={cn(
            "h-4 w-4 transition-colors",
            isFavorited ? "fill-destructive text-destructive" : "text-muted-foreground"
          )} />
        </Button> */}

        {/* Price overlay */}
        <div className="absolute bottom-3 right-3">
          <div className="rounded-lg bg-background/90 backdrop-blur-sm px-3 py-1 shadow-medium">
            {salePrice && (
              <div className="flex items-center gap-1 text-sm font-semibold">
                {formatPrice(salePrice, salePriceCurrency)}
              </div>
            )}
            {rentalPrice && (
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
          <p className="text-sm text-muted-foreground line-clamp-2 mt-1">{description}</p>
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
                <BookingDialog
                  itemUuid={id}
                  itemName={title}
                  salePrice={salePrice?.toString()}
                  salePriceCurrency={salePriceCurrency || undefined}
                  rentalPrice={rentalPrice?.toString()}
                  rentalPriceCurrency={rentalPriceCurrency || undefined}
                  buttonSize="sm"
                  buttonClassName="w-full"
                  triggerLabel={
                    salePrice && !rentalPrice ? t('itemDetail.buyNow') : t('booking.bookNow')
                  }
                  disabled={(isOwner && !!salePrice) || !user}
                />

                <Button
                  variant="outline"
                  size="sm"
                  className="flex-1 gap-2"
                  onClick={e => {
                    e.stopPropagation();
                    handleMessageOwner();
                  }}
                  disabled={isOwner || !user}
                >
                  <MessageCircle className="h-4 w-4" />
                  {t('item.messageOwner')}
                </Button>
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
