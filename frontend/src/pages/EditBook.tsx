import { BarcodeScanner } from '@/components/items/BarcodeScanner';
import { ImageManager } from '@/components/items/ImageManager';
import {
  BasicFields,
  CategoryConditionFields,
  PricingFields,
  StatusField,
} from '@/components/items/ItemFormFields';
import { Header } from '@/components/layout/Header';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { useLanguage } from '@/contexts/LanguageContext';
import { useToast } from '@/hooks/use-toast';
import { useAuth } from '@/hooks/useAuth';
import { useUpdateItem } from '@/hooks/useCreateItem';
import {
  Author,
  BookWritable,
  CategoryEnum,
  ConditionEnum,
  Genre,
  Image,
  Publisher,
  RentalPeriodEnum,
  Shelf,
  Status402Enum,
} from '@/services/django';
import {
  authorsList,
  booksPartialUpdate,
  booksRetrieve,
  genresList,
  publishersList,
  shelvesList,
} from '@/services/django/sdk.gen';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { ArrowLeft, Loader } from 'lucide-react';
import { useEffect, useRef, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';

const EditBook = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const { toast } = useToast();
  const { t, language } = useLanguage();
  const { itemUuid: editItemUuid } = useParams<{ itemUuid: string }>();
  const queryClient = useQueryClient();

  const {
    data: book,
    isLoading: loadingBook,
    error,
  } = useQuery({
    queryKey: ['book', editItemUuid],
    queryFn: async () => {
      if (!editItemUuid) throw new Error('No book UUID provided');
      const response = await booksRetrieve({ path: { uuid: editItemUuid } });
      return response.data;
    },
    enabled: !!editItemUuid,
  });

  const updateBookMutation = useMutation({
    mutationFn: async (data: { uuid: string; body: BookWritable }) => {
      const response = await booksPartialUpdate({
        path: { uuid: data.uuid },
        body: data.body,
      });
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['book', editItemUuid] });
      queryClient.invalidateQueries({ queryKey: ['my-items'] });
      toast({
        title: t('editItem.updateSuccessTitle'),
        description: t('editItem.updateSuccessDescription'),
      });
    },
    onError: (error: any) => {
      console.error('Error updating book:', error);
      toast({
        title: t('editItem.updateErrorTitle'),
        description: error?.message || t('editItem.updateErrorDescription'),
        variant: 'destructive',
      });
    },
  });

  // Item update mutation (used when switching category away from books)
  const updateItemMutation = useUpdateItem();

  // Fetch authors, genres, publishers, shelves
  const { data: authorsData } = useQuery({
    queryKey: ['authors'],
    queryFn: async () => {
      const response = await authorsList();
      return response.data;
    },
  });

  const { data: genresData } = useQuery({
    queryKey: ['genres'],
    queryFn: async () => {
      const response = await genresList();
      return response.data;
    },
  });

  const { data: publishersData } = useQuery({
    queryKey: ['publishers'],
    queryFn: async () => {
      const response = await publishersList();
      return response.data;
    },
  });

  const { data: shelvesData } = useQuery({
    queryKey: ['shelves'],
    queryFn: async () => {
      const response = await shelvesList();
      return response.data;
    },
  });

  const authors = authorsData?.results || [];
  const genres = genresData?.results || [];
  const publishers = publishersData?.results || [];
  const shelves = shelvesData?.results || [];

  const [loading, setLoading] = useState(false);
  const [aiProcessing, setAiProcessing] = useState(false);
  const [images, setImages] = useState<{ url: string; file: File }[]>([]);
  const [existingImages, setExistingImages] = useState<Image[]>([]);
  const [resetNewImagesToken, setResetNewImagesToken] = useState<number | undefined>(undefined);
  const [processingState, setProcessingState] = useState<
    'idle' | 'uploading' | 'processing' | 'completed' | 'error'
  >('idle');
  const [progress, setProgress] = useState(0);
  const intervalRef = useRef<number | null>(null);
  const descriptionRef = useRef<HTMLTextAreaElement | null>(null);

  const [formData, setFormData] = useState({
    name: '',
    description: '',
    category: 'books' as CategoryEnum,
    condition: '' as ConditionEnum | '',
    status: '' as Status402Enum | '',
    sale_price: '',
    rental_price: '',
    rental_period: '' as RentalPeriodEnum | '',
    rental_self_service: false,
    rental_open_end: false,
    // Book-specific fields
    isbn: '',
    year: '',
    topic: '',
    author_uuids: [] as string[],
    genre_uuids: [] as string[],
    verlag_uuid: '',
    shelf_uuid: '',
  });

  const categories: CategoryEnum[] = [
    'electronics',
    'furniture',
    'clothing',
    'books',
    'sports',
    'tools',
    'kitchen',
    'garden',
    'toys',
    'vehicles',
    'rooms',
    'other',
  ];

  // Load existing book data
  useEffect(() => {
    if (book) {
      setFormData({
        name: book.name || '',
        description: book.description || '',
        category: (book.category as CategoryEnum) || 'books',
        condition: book.condition !== undefined ? (book.condition as ConditionEnum) : '',
        status: book.status !== undefined ? (book.status as Status402Enum) : '',
        sale_price: book.sale_price || '',
        rental_price: book.rental_price || '',
        rental_period: (book.rental_period as RentalPeriodEnum) || '',
        rental_self_service: book.rental_self_service || false,
        rental_open_end: book.rental_open_end || false,
        isbn: book.isbn || '',
        year: book.year?.toString() || '',
        topic: book.topic || '',
        author_uuids: book.authors?.map(a => a.uuid) || [],
        genre_uuids: book.genres?.map(g => g.uuid) || [],
        verlag_uuid: book.verlag?.uuid || '',
        shelf_uuid: book.shelf?.uuid || '',
      });

      if (book.images) {
        setExistingImages(book.images);
      }
    }
  }, [book]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!user) {
      toast({
        title: 'Error',
        description: 'You must be logged in to update a book.',
        variant: 'destructive',
      });
      return;
    }

    if (!editItemUuid) {
      toast({
        title: 'Error',
        description: 'Book UUID is required.',
        variant: 'destructive',
      });
      return;
    }

    setLoading(true);

    try {
      const bookData: BookWritable = {
        name: formData.name,
        description: formData.description,
        category: formData.category as CategoryEnum,
        condition: formData.condition as ConditionEnum,
        status: formData.status !== '' ? (formData.status as Status402Enum) : undefined,
        sale_price: formData.sale_price === '' ? null : formData.sale_price,
        rental_price: formData.rental_price === '' ? null : formData.rental_price,
        rental_period:
          formData.rental_price === ''
            ? undefined
            : (formData.rental_period as RentalPeriodEnum | undefined),
        rental_self_service:
          formData.rental_price === '' ? undefined : formData.rental_self_service,
        rental_open_end: formData.rental_price === '' ? undefined : formData.rental_open_end,
        isbn: formData.isbn,
        year: formData.year === '' ? null : parseInt(formData.year),
        topic: formData.topic,
        author_uuids: formData.author_uuids.length > 0 ? formData.author_uuids : undefined,
        genre_uuids: formData.genre_uuids.length > 0 ? formData.genre_uuids : undefined,
        verlag_uuid: formData.verlag_uuid || null,
        shelf_uuid: formData.shelf_uuid || null,
      };

      await updateBookMutation.mutateAsync({
        uuid: editItemUuid,
        body: bookData,
      });

      navigate('/my-items');
    } catch (error) {
      console.error('Error updating book:', error);
    } finally {
      setLoading(false);
    }
  };

  const handlePublish = async () => {
    if (!user || !editItemUuid) {
      toast({
        title: 'Error',
        description: 'You must be logged in and have a valid book ID.',
        variant: 'destructive',
      });
      return;
    }

    // Validate required fields
    if (!formData.name || !formData.category || formData.condition === '') {
      toast({
        title: 'Missing Information',
        description: 'Please fill in all required fields before publishing.',
        variant: 'destructive',
      });
      return;
    }

    if (formData.sale_price !== '' && formData.rental_price !== '') {
      toast({
        title: t('editItem.invalidPricingTitle'),
        description: t('editItem.invalidPricingDescription'),
        variant: 'destructive',
      });
      return;
    }

    setLoading(true);

    try {
      const bookData: BookWritable = {
        name: formData.name,
        description: formData.description,
        category: formData.category as CategoryEnum,
        condition: formData.condition as ConditionEnum,
        status: 2, // Set to Available
        sale_price: formData.sale_price === '' ? null : formData.sale_price,
        rental_price: formData.rental_price === '' ? null : formData.rental_price,
        rental_period:
          formData.rental_price === ''
            ? undefined
            : (formData.rental_period as RentalPeriodEnum | undefined),
        rental_self_service:
          formData.rental_price === '' ? undefined : formData.rental_self_service,
        rental_open_end: formData.rental_price === '' ? undefined : formData.rental_open_end,
        isbn: formData.isbn,
        year: formData.year === '' ? null : parseInt(formData.year),
        topic: formData.topic,
        author_uuids: formData.author_uuids.length > 0 ? formData.author_uuids : undefined,
        genre_uuids: formData.genre_uuids.length > 0 ? formData.genre_uuids : undefined,
        verlag_uuid: formData.verlag_uuid || null,
        shelf_uuid: formData.shelf_uuid || null,
      };

      await updateBookMutation.mutateAsync({
        uuid: editItemUuid,
        body: bookData,
      });

      toast({
        title: t('editItem.publishSuccessTitle'),
        description: t('editItem.publishSuccessDescription'),
      });

      navigate('/my-items');
    } catch (error) {
      console.error('Error publishing book:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async () => {
    // Implementation similar to EditItem if needed
  };

  if (loadingBook) {
    return (
      <div className="min-h-screen bg-background">
        <Header />
        <div className="container mx-auto py-8 flex items-center justify-center">
          <Loader className="h-8 w-8 animate-spin" />
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-background">
        <Header />
        <div className="container mx-auto py-8">
          <Card>
            <CardContent className="pt-6">
              <p className="text-destructive">Error loading book: {(error as Error).message}</p>
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      <Header />
      <div className="container mx-auto py-8 space-y-6">
        <div className="flex items-center justify-between">
          <Button variant="ghost" onClick={() => navigate(-1)} className="gap-2">
            <ArrowLeft className="h-4 w-4" />
            {t('common.back')}
          </Button>
          <h1 className="text-2xl font-bold">{t('editItem.editBook')}</h1>
        </div>

        {/* Images Card */}
        <Card>
          <CardHeader>
            <CardTitle>{t('editItem.images')}</CardTitle>
          </CardHeader>
          <CardContent>
            <ImageManager
              onImagesChange={setImages}
              onExistingImagesChange={setExistingImages}
              existingImages={existingImages}
              maxImages={16}
              isEditing={!aiProcessing}
              resetNewImagesToken={resetNewImagesToken}
            />
          </CardContent>
        </Card>

        {/* Book Details Form */}
        <Card>
          <CardHeader>
            <CardTitle>{t('editItem.bookDetails')}</CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-6">
              <BasicFields
                formData={formData}
                setFormData={setFormData}
                disabled={aiProcessing}
                descriptionRef={descriptionRef}
              />

              <CategoryConditionFields
                formData={formData}
                setFormData={setFormData}
                categories={categories}
                onCategoryChange={async category => {
                  // Update local state immediately
                  setFormData(prev => ({ ...prev, category: category as CategoryEnum }));

                  // If switching away from books, persist the change first, then navigate
                  if (category !== 'books' && editItemUuid) {
                    try {
                      await updateItemMutation.mutateAsync({
                        itemUuid: editItemUuid,
                        data: { category: category as CategoryEnum },
                      });
                      navigate(`/edit-item/${editItemUuid}`);
                    } catch (err) {
                      console.error('Error updating category before switching to EditItem:', err);
                      toast({
                        title: t('editItem.updateErrorTitle'),
                        description: (err as any)?.message || t('editItem.updateErrorDescription'),
                        variant: 'destructive',
                      });
                    }
                  }
                }}
              />

              {/* Book-specific fields */}
              {/* ISBN, Year, Topic - compact row */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="isbn">{t('editItem.isbn')}</Label>
                  <div className="flex gap-2">
                    <Input
                      id="isbn"
                      type="text"
                      placeholder={t('editItem.enterIsbn')}
                      value={formData.isbn}
                      onChange={e => setFormData({ ...formData, isbn: e.target.value })}
                      disabled={aiProcessing}
                      className="flex-1"
                    />
                    <BarcodeScanner
                      onScan={code => setFormData({ ...formData, isbn: code })}
                      title={t('editItem.scanIsbn')}
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="year">{t('editItem.year')}</Label>
                  <Input
                    id="year"
                    type="number"
                    placeholder={t('editItem.enterYear')}
                    value={formData.year}
                    onChange={e => setFormData({ ...formData, year: e.target.value })}
                    disabled={aiProcessing}
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="topic">{t('editItem.topic')}</Label>
                  <Input
                    id="topic"
                    type="text"
                    placeholder={t('editItem.enterTopic')}
                    value={formData.topic}
                    onChange={e => setFormData({ ...formData, topic: e.target.value })}
                    disabled={aiProcessing}
                  />
                </div>
              </div>

              {/* Authors and Genres - 2 column row */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="authors">{t('editItem.authors')}</Label>
                  <Select
                    value={formData.author_uuids.join(',')}
                    onValueChange={value => {
                      const uuids = value ? value.split(',').filter(Boolean) : [];
                      setFormData({ ...formData, author_uuids: uuids });
                    }}
                    disabled={aiProcessing}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder={t('editItem.selectAuthors')} />
                    </SelectTrigger>
                    <SelectContent>
                      {authors?.map((author: Author) => (
                        <SelectItem key={author.uuid} value={author.uuid}>
                          {author.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="genres">{t('editItem.genres')}</Label>
                  <Select
                    value={formData.genre_uuids.join(',')}
                    onValueChange={value => {
                      const uuids = value ? value.split(',').filter(Boolean) : [];
                      setFormData({ ...formData, genre_uuids: uuids });
                    }}
                    disabled={aiProcessing}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder={t('editItem.selectGenres')} />
                    </SelectTrigger>
                    <SelectContent>
                      {genres?.map((genre: Genre) => (
                        <SelectItem key={genre.uuid} value={genre.uuid}>
                          {genre.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>

              {/* Publisher and Shelf - 2 column row */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="publisher">{t('editItem.publisher')}</Label>
                  <Select
                    value={formData.verlag_uuid}
                    onValueChange={value => setFormData({ ...formData, verlag_uuid: value })}
                    disabled={aiProcessing}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder={t('editItem.selectPublisher')} />
                    </SelectTrigger>
                    <SelectContent>
                      {publishers?.map((publisher: Publisher) => (
                        <SelectItem key={publisher.uuid} value={publisher.uuid}>
                          {publisher.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="shelf">{t('editItem.shelf')}</Label>
                  <Select
                    value={formData.shelf_uuid}
                    onValueChange={value => setFormData({ ...formData, shelf_uuid: value })}
                    disabled={aiProcessing}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder={t('editItem.selectShelf')} />
                    </SelectTrigger>
                    <SelectContent>
                      {shelves?.map((shelf: Shelf) => (
                        <SelectItem key={shelf.uuid} value={shelf.uuid}>
                          {shelf.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <PricingFields
                formData={formData}
                setFormData={setFormData}
                disabled={aiProcessing}
              />

              <div className="flex items-end justify-between gap-4 pt-4">
                <StatusField
                  formData={formData}
                  setFormData={setFormData}
                  disabled={aiProcessing}
                />

                <div className="flex gap-2">
                  <Button
                    type="submit"
                    disabled={loading || updateBookMutation.isPending || aiProcessing}
                  >
                    {loading || updateBookMutation.isPending
                      ? t('common.saving')
                      : t('common.save')}
                  </Button>

                  {formData.status === 0 && (
                    <Button
                      type="button"
                      variant="default"
                      onClick={handlePublish}
                      disabled={loading || updateBookMutation.isPending || aiProcessing}
                      className="gap-2"
                    >
                      {t('editItem.publish')}
                    </Button>
                  )}
                </div>
              </div>
            </form>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default EditBook;
