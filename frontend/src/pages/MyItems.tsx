import { Header } from '@/components/layout/Header';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from '@/components/ui/alert-dialog';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardFooter, CardHeader } from '@/components/ui/card';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { useLanguage } from '@/contexts/LanguageContext';
import { useToast } from '@/hooks/use-toast';
import { useAuth } from '@/hooks/useAuth';
import { useDeleteItem, useMyItems, useUpdateItemStatus } from '@/hooks/useMyItems';
import { formatPrice } from '@/lib/currency';
import { cn } from '@/lib/utils';
import { Status402Enum } from '@/services/django';
import { Edit3, Eye, Grid3X3, List, MoreHorizontal, Plus, Trash2 } from 'lucide-react';
import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';

const MyItems = () => {
  const { user, loading } = useAuth();
  const navigate = useNavigate();
  const { t } = useLanguage();
  const { toast } = useToast();
  const { data: myItemsData, isLoading } = useMyItems();
  const items = myItemsData?.results || [];
  const updateStatusMutation = useUpdateItemStatus();
  const deleteItemMutation = useDeleteItem();

  // Helper function to get the correct edit URL based on item category
  const getEditUrl = (item: any) => {
    return item.category === 'books' ? `/edit-book/${item.id}` : `/edit-item/${item.id}`;
  };

  // View mode state with localStorage persistence
  const [viewMode, setViewMode] = useState<'list' | 'cards'>('list');

  useEffect(() => {
    const savedViewMode = localStorage.getItem('myItemsViewMode') as 'list' | 'cards' | null;
    if (savedViewMode) {
      setViewMode(savedViewMode);
    }
  }, []);

  const toggleViewMode = (mode: 'list' | 'cards') => {
    setViewMode(mode);
    localStorage.setItem('myItemsViewMode', mode);
  };

  const handleDeleteItem = (itemId: string) => {
    deleteItemMutation.mutate(itemId);
  };

  const handleStatusChange = async (
    itemId: string,
    newStatus: 'draft' | 'available' | 'reserved' | 'rented' | 'sold',
  ) => {
    // Map string status to Status402Enum number
    let statusEnum: Status402Enum;
    switch (newStatus) {
      case 'draft':
        statusEnum = 0;
        break;
      case 'available':
        statusEnum = 2;
        break;
      case 'reserved':
        statusEnum = 3;
        break;
      case 'rented':
        statusEnum = 4;
        break;
      case 'sold':
        statusEnum = 5;
        break;
      default:
        statusEnum = 0;
    }

    updateStatusMutation.mutate({ itemId, status: statusEnum });
  };

  const getStatusColor = (status: Status402Enum) => {
    switch (status) {
      case 0:
        return 'bg-muted text-muted-foreground'; // draft
      case 1:
        return 'bg-info text-info-foreground'; // processing
      case 2:
        return 'bg-success text-success-foreground'; // available
      case 3:
        return 'bg-warning text-warning-foreground'; // reserved
      case 4:
        return 'bg-primary text-primary-foreground'; // rented
      case 5:
        return 'bg-destructive text-destructive-foreground'; // sold
      default:
        return 'bg-muted text-muted-foreground';
    }
  };

  const getStatusText = (status: Status402Enum) => {
    switch (status) {
      case 0:
        return t('status.draft');
      case 1:
        return t('status.processing');
      case 2:
        return t('status.available');
      case 3:
        return t('status.reserved');
      case 4:
        return t('status.rented');
      case 5:
        return t('status.sold');
      default:
        return 'Unknown';
    }
  };

  if (loading || isLoading) {
    return (
      <div className="min-h-screen bg-background">
        <Header />
        <div className="container mx-auto px-4 py-8">
          <div className="text-center">{t('common.loading')}</div>
        </div>
      </div>
    );
  }

  if (!user) {
    navigate('/auth');
    return null;
  }

  return (
    <div className="min-h-screen bg-background">
      <Header />

      <div className="container mx-auto px-4 py-8">
        <div className="flex items-center justify-between mb-8">
          <h1 className="text-3xl font-bold text-foreground">{t('myItems.title')}</h1>
          <div className="flex items-center gap-4">
            {/* View Mode Toggle */}
            <div className="flex items-center gap-1 border rounded-lg p-1">
              <Button
                variant={viewMode === 'list' ? 'default' : 'ghost'}
                size="sm"
                onClick={() => toggleViewMode('list')}
                className="h-8 w-8 p-0"
              >
                <List className="h-4 w-4" />
              </Button>
              <Button
                variant={viewMode === 'cards' ? 'default' : 'ghost'}
                size="sm"
                onClick={() => toggleViewMode('cards')}
                className="h-8 w-8 p-0"
              >
                <Grid3X3 className="h-4 w-4" />
              </Button>
            </div>

            <Button onClick={() => navigate('/create-item')} className="gap-2">
              <Plus className="h-4 w-4" />
              {t('myItems.createItem')}
            </Button>
          </div>
        </div>

        {items.length === 0 ? (
          <div className="text-center py-12">
            <div className="max-w-md mx-auto">
              <div className="mb-4">
                <div className="w-24 h-24 mx-auto mb-4 rounded-full bg-gradient-subtle flex items-center justify-center">
                  <Plus className="h-12 w-12 text-muted-foreground" />
                </div>
              </div>
              <h3 className="text-xl font-semibold text-foreground mb-2">{t('myItems.noItems')}</h3>
              <p className="text-muted-foreground mb-6">{t('myItems.createFirst')}</p>
              <Button onClick={() => navigate('/create-item')} className="gap-2">
                <Plus className="h-4 w-4" />
                {t('myItems.createItem')}
              </Button>
            </div>
          </div>
        ) : viewMode === 'list' ? (
          <div className="rounded-lg border">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-20">Image</TableHead>
                  <TableHead>Title</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Category</TableHead>
                  <TableHead>Price</TableHead>
                  <TableHead>Created</TableHead>
                  <TableHead className="w-20">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {items.map(item => {
                  const primaryImage = item.first_image;

                  return (
                    <TableRow
                      key={item.id}
                      className="cursor-pointer hover:bg-muted/50"
                      onClick={() => navigate(getEditUrl(item))}
                    >
                      <TableCell>
                        <div className="w-12 h-12 rounded-lg overflow-hidden">
                          {primaryImage ? (
                            <img
                              src={primaryImage}
                              alt={item.name}
                              className="h-full w-full object-cover"
                            />
                          ) : (
                            <div className="flex h-full w-full items-center justify-center bg-gradient-subtle">
                              <Plus className="h-4 w-4 text-muted-foreground" />
                            </div>
                          )}
                        </div>
                      </TableCell>
                      <TableCell>
                        <div className="font-medium max-w-48 truncate">{item.name}</div>
                        {item.description && (
                          <div className="text-sm text-muted-foreground truncate max-w-48">
                            {item.description}
                          </div>
                        )}
                      </TableCell>
                      <TableCell onClick={e => e.stopPropagation()}>
                        <Select
                          value={item.status.toString()}
                          onValueChange={value => {
                            const statusMap: Record<
                              string,
                              'draft' | 'available' | 'reserved' | 'rented' | 'sold'
                            > = {
                              '0': 'draft',
                              '2': 'available',
                              '3': 'reserved',
                              '4': 'rented',
                              '5': 'sold',
                            };
                            handleStatusChange(item.id, statusMap[value] || 'draft');
                          }}
                          disabled={updateStatusMutation.isPending}
                        >
                          <SelectTrigger className="w-32">
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="0">{t('status.draft')}</SelectItem>
                            <SelectItem value="2">{t('status.available')}</SelectItem>
                            <SelectItem value="3">{t('status.reserved')}</SelectItem>
                            <SelectItem value="4">{t('status.rented')}</SelectItem>
                            <SelectItem value="5">{t('status.sold')}</SelectItem>
                          </SelectContent>
                        </Select>
                      </TableCell>
                      <TableCell>
                        <Badge variant="outline" className="text-xs">
                          {t(`categories.${item.category}`)}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <div className="text-sm font-medium">
                          {item.sale_price && (
                            <div className="flex items-center gap-1">
                              {formatPrice(item.sale_price, item.sale_price_currency)}
                            </div>
                          )}
                          {item.rental_price && (
                            <div className="flex items-center gap-1">
                              {formatPrice(item.rental_price, item.rental_price_currency)}
                              {t('time.perHour')}
                            </div>
                          )}
                        </div>
                      </TableCell>
                      <TableCell>
                        <div className="text-sm text-muted-foreground">
                          {new Date(item.created_at).toLocaleDateString()}
                        </div>
                      </TableCell>
                      <TableCell onClick={e => e.stopPropagation()}>
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button variant="ghost" size="icon" className="h-8 w-8">
                              <MoreHorizontal className="h-4 w-4" />
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end">
                            <DropdownMenuItem onClick={() => navigate(`/item/${item.id}`)}>
                              <Eye className="h-4 w-4 mr-2" />
                              View
                            </DropdownMenuItem>
                            <DropdownMenuItem onClick={() => navigate(getEditUrl(item))}>
                              <Edit3 className="h-4 w-4 mr-2" />
                              Edit
                            </DropdownMenuItem>
                            <DropdownMenuSeparator />
                            <AlertDialog>
                              <AlertDialogTrigger asChild>
                                <DropdownMenuItem
                                  onSelect={e => e.preventDefault()}
                                  className="text-destructive focus:text-destructive"
                                >
                                  <Trash2 className="h-4 w-4 mr-2" />
                                  Delete
                                </DropdownMenuItem>
                              </AlertDialogTrigger>
                              <AlertDialogContent>
                                <AlertDialogHeader>
                                  <AlertDialogTitle>Are you absolutely sure?</AlertDialogTitle>
                                  <AlertDialogDescription>
                                    This action cannot be undone. This will permanently delete your
                                    item and remove its data from our servers.
                                  </AlertDialogDescription>
                                </AlertDialogHeader>
                                <AlertDialogFooter>
                                  <AlertDialogCancel>Cancel</AlertDialogCancel>
                                  <AlertDialogAction
                                    onClick={() => handleDeleteItem(item.id)}
                                    className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
                                  >
                                    Delete
                                  </AlertDialogAction>
                                </AlertDialogFooter>
                              </AlertDialogContent>
                            </AlertDialog>
                          </DropdownMenuContent>
                        </DropdownMenu>
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {items.map(item => {
              return (
                <Card key={item.id} className="overflow-hidden">
                  {/* Image */}
                  <div
                    className="aspect-[4/3] overflow-hidden cursor-pointer"
                    onClick={() => navigate(getEditUrl(item))}
                  >
                    {item.first_image ? (
                      <img
                        src={item.first_image}
                        alt={item.name}
                        className="h-full w-full object-cover"
                      />
                    ) : (
                      <div className="flex h-full w-full items-center justify-center bg-gradient-subtle">
                        <div className="text-center text-muted-foreground">
                          <Plus className="mx-auto h-12 w-12 mb-2" />
                          <p className="text-sm">No image</p>
                        </div>
                      </div>
                    )}
                  </div>

                  <CardHeader className="pb-3">
                    <div className="flex items-center justify-between">
                      <h3
                        className="font-semibold text-foreground line-clamp-1 cursor-pointer hover:underline"
                        onClick={() => navigate(getEditUrl(item))}
                      >
                        {item.name}
                      </h3>
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button variant="ghost" size="icon">
                            <MoreHorizontal className="h-4 w-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          <DropdownMenuItem onClick={() => navigate(`/item/${item.id}`)}>
                            <Eye className="h-4 w-4 mr-2" />
                            View
                          </DropdownMenuItem>
                          <DropdownMenuItem onClick={() => navigate(getEditUrl(item))}>
                            <Edit3 className="h-4 w-4 mr-2" />
                            Edit
                          </DropdownMenuItem>
                          <DropdownMenuSeparator />
                          <AlertDialog>
                            <AlertDialogTrigger asChild>
                              <DropdownMenuItem
                                onSelect={e => e.preventDefault()}
                                className="text-destructive focus:text-destructive"
                              >
                                <Trash2 className="h-4 w-4 mr-2" />
                                Delete
                              </DropdownMenuItem>
                            </AlertDialogTrigger>
                            <AlertDialogContent>
                              <AlertDialogHeader>
                                <AlertDialogTitle>Are you absolutely sure?</AlertDialogTitle>
                                <AlertDialogDescription>
                                  This action cannot be undone. This will permanently delete your
                                  item and remove its data from our servers.
                                </AlertDialogDescription>
                              </AlertDialogHeader>
                              <AlertDialogFooter>
                                <AlertDialogCancel>Cancel</AlertDialogCancel>
                                <AlertDialogAction
                                  onClick={() => handleDeleteItem(item.id)}
                                  className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
                                >
                                  Delete
                                </AlertDialogAction>
                              </AlertDialogFooter>
                            </AlertDialogContent>
                          </AlertDialog>
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </div>

                    <div className="flex items-center gap-2">
                      <Badge className={cn(getStatusColor(item.status), 'text-xs')}>
                        {getStatusText(item.status)}
                      </Badge>
                      <Badge variant="outline" className="text-xs">
                        {t(`categories.${item.category}`)}
                      </Badge>
                    </div>
                  </CardHeader>

                  <CardContent className="pb-3">
                    <p className="text-sm text-muted-foreground line-clamp-2 mb-3">
                      {item.description}
                    </p>

                    {/* Price */}
                    <div className="text-lg font-semibold text-primary">
                      <div className="text-sm space-y-1">
                        {item.sale_price && (
                          <div className="flex items-center gap-1">
                            {formatPrice(item.sale_price, item.sale_price_currency)} (sale)
                          </div>
                        )}
                        {item.rental_price && (
                          <div className="flex items-center gap-1">
                            {formatPrice(item.rental_price, item.rental_price_currency)} (rental)
                          </div>
                        )}
                      </div>
                    </div>
                  </CardContent>

                  <CardFooter className="pt-0">
                    <div className="w-full space-y-2">
                      <div className="text-xs text-muted-foreground">{t('myItems.status')}</div>
                      <Select
                        value={item.status.toString()}
                        onValueChange={value => {
                          const statusMap: Record<
                            string,
                            'draft' | 'available' | 'reserved' | 'rented' | 'sold'
                          > = {
                            '0': 'draft',
                            '2': 'available',
                            '3': 'reserved',
                            '4': 'rented',
                            '5': 'sold',
                          };
                          handleStatusChange(item.id, statusMap[value] || 'draft');
                        }}
                        disabled={updateStatusMutation.isPending}
                      >
                        <SelectTrigger className="w-full">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="0">{t('status.draft')}</SelectItem>
                          <SelectItem value="2">{t('status.available')}</SelectItem>
                          <SelectItem value="3">{t('status.reserved')}</SelectItem>
                          <SelectItem value="4">{t('status.rented')}</SelectItem>
                          <SelectItem value="5">{t('status.sold')}</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  </CardFooter>
                </Card>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
};

export default MyItems;
