import { ImageManager } from '@/components/items/ImageManager';
import {
  BasicFields,
  CategoryConditionFields,
  PricingFields,
} from '@/components/items/ItemFormFields';
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
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import { Progress } from '@/components/ui/progress';
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
import { useMyItem } from '@/hooks/useMyItem';
import { imagesAPI } from '@/services/custom/images';
import {
  CategoryEnum,
  ConditionEnum,
  Image,
  imagesPartialUpdate,
  itemsAiDescribeUpdate,
  itemsAiImageUpdate,
  PatchedItemWritable,
  RentalPeriodEnum,
  Status402Enum,
} from '@/services/django';
import { useQueryClient } from '@tanstack/react-query';
import { ArrowLeft, CheckCircle, Loader, Sparkles } from 'lucide-react';
import { useEffect, useRef, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';

const EditItem = () => {
  // CSP-compliant event handlers
  const handleBackClick = () => {
    navigate(-1);
  };

  const handleClearImages = () => {
    setImages([]);
  };

  const handleRentalPeriodChange = (value: RentalPeriodEnum) => {
    setFormData({ ...formData, rental_period: value });
  };
  const { user } = useAuth();
  const navigate = useNavigate();
  const { toast } = useToast();
  const { t, language } = useLanguage();
  const { itemUuid: editItemUuid } = useParams<{ itemUuid: string }>();
  const queryClient = useQueryClient();

  const { data: item, isLoading: loadingItem, error } = useMyItem(editItemUuid);
  const updateItemMutation = useUpdateItem();

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
    category: '' as CategoryEnum | '',
    condition: '' as ConditionEnum | '',
    status: '' as Status402Enum | '',
    sale_price: '',
    rental_price: '',
    rental_period: '' as RentalPeriodEnum | '',
    rental_self_service: false,
    rental_open_end: false,
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

  const conditions: { value: ConditionEnum; key: string }[] = [
    { value: 0, key: 'new' },
    { value: 1, key: 'used' },
    { value: 2, key: 'broken' },
  ];

  const statuses: { value: Status402Enum; label: string }[] = [
    { value: 0, label: 'Draft' },
    { value: 2, label: 'Available' },
    { value: 3, label: 'Reserved' },
    { value: 4, label: 'Rented' },
    { value: 5, label: 'Sold' },
  ];

  // Load existing item data if editing
  useEffect(() => {
    if (item && editItemUuid) {
      setFormData({
        name: item.name || '',
        description: item.description || '',
        category: item.category || '',
        condition: item.condition !== undefined ? item.condition : '',
        status: item.status !== undefined ? item.status : '',
        sale_price: item.sale_price?.toString() || '',
        rental_price: item.rental_price?.toString() || '',
        rental_period: (item.rental_period as RentalPeriodEnum) || '',
        rental_self_service:
          item.rental_self_service !== undefined ? item.rental_self_service : false,
        rental_open_end: item.rental_open_end !== undefined ? item.rental_open_end : false,
      });

      // Use Django images directly without transformation
      if (item.images && Array.isArray(item.images)) {
        setExistingImages(item.images);
      }
      // Adjust textarea height to match loaded content
      setTimeout(() => adjustDescriptionHeight(), 0);
    }
  }, [item, editItemUuid]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (intervalRef.current) {
        window.clearInterval(intervalRef.current);
      }
    };
  }, []);

  // Handle error
  if (error) {
    toast({
      title: 'Error',
      description: 'Failed to load item data.',
      variant: 'destructive',
    });
    navigate('/');
    return null;
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!user) {
      toast({
        title: 'Error',
        description: 'You must be logged in to update an item.',
        variant: 'destructive',
      });
      return;
    }

    // Validate required fields
    if (!formData.name || !formData.category || formData.condition === '') {
      toast({
        title: 'Missing Information',
        description: 'Please fill in all required fields.',
        variant: 'destructive',
      });
      return;
    }

    // Prevent both sale and rental price from being set
    if (formData.sale_price !== '' && formData.rental_price !== '') {
      toast({
        title: t('editItem.invalidPricingTitle'),
        description: t('editItem.invalidPricingDescription'),
        variant: 'destructive',
      });
      return;
    }

    if (!editItemUuid) {
      toast({
        title: 'Error',
        description: 'Item UUID is required for editing.',
        variant: 'destructive',
      });
      return;
    }

    setLoading(true);

    try {
      const itemData = {
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
      };

      await updateItemMutation.mutateAsync({
        itemUuid: editItemUuid,
        data: itemData,
      });

      // Navigate to my items page
      navigate('/my-items');
    } catch (error) {
      console.error('Error updating item:', error);
      // Error toast is handled by the mutation
    } finally {
      setLoading(false);
    }
  };

  const handlePublish = async () => {
    if (!user) {
      toast({
        title: 'Error',
        description: 'You must be logged in to publish an item.',
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

    // Prevent both sale and rental price from being set when publishing
    if (formData.sale_price !== '' && formData.rental_price !== '') {
      toast({
        title: t('editItem.invalidPricingTitle'),
        description: t('editItem.invalidPricingDescription'),
        variant: 'destructive',
      });
      return;
    }

    if (!editItemUuid) {
      toast({
        title: 'Error',
        description: 'Item UUID is required for publishing.',
        variant: 'destructive',
      });
      return;
    }

    setLoading(true);

    try {
      const itemData: PatchedItemWritable = {
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
      };

      await updateItemMutation.mutateAsync({
        itemUuid: editItemUuid,
        data: itemData,
      });

      toast({
        title: 'Success',
        description: 'Item published successfully!',
      });

      // Navigate to my items page
      navigate('/my-items');
    } catch (error) {
      console.error('Error publishing item:', error);
      toast({
        title: 'Error',
        description: 'Failed to publish item. Please try again.',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  const uploadImages = async () => {
    if (!editItemUuid) {
      toast({
        title: 'Error',
        description: 'Item UUID is required for AI processing.',
        variant: 'destructive',
      });
      return;
    }

    if (images.length === 0) {
      toast({
        title: 'No Images',
        description: 'Please upload at least one image to use AI processing.',
        variant: 'destructive',
      });
      return;
    }

    setProcessingState('uploading');
    setProgress(10);

    try {
      // Upload new images if any and collect returned Image objects
      const uploadedImages = [] as Image[];
      for (let i = 0; i < images.length; i++) {
        const file = images[i];
        try {
          // Upload image via Django API
          const created = await imagesAPI.createImage({
            item: editItemUuid,
            original: file.file,
            ordering: i,
          });
          uploadedImages.push(created);
          setProgress(10 + Math.round(((i + 1) * 90) / images.length));
        } catch (error) {
          console.error('Error uploading image:', error);
          throw error;
        }
      }

      // Merge newly uploaded images into existingImages and set ordering sequentially
      if (uploadedImages.length > 0) {
        const merged = [...existingImages, ...uploadedImages].map((img, idx) => ({
          ...img,
          ordering: idx,
        }));

        setExistingImages(merged);

        // Persist ordering for all images to backend
        try {
          await Promise.all(
            merged.map(img =>
              imagesPartialUpdate({
                path: { id: img.id },
                body: { ordering: img.ordering },
              }),
            ),
          );
        } catch (err) {
          console.error('Failed to persist image ordering after upload', err);
        }
      }

      // Clear uploaded images and notify ImageManager to clear its local preview state
      setImages([]); // Clear uploaded images
      // bump token so ImageManager clears its internal newImages state
      setResetNewImagesToken(prev => (prev === undefined ? 1 : prev + 1));
      setProcessingState('idle');
      setProgress(0);
    } catch (error) {
      console.error('Error uploading images:', error);
    }
  };

  // Auto-upload newly selected images immediately when in edit mode
  useEffect(() => {
    // Only auto-upload when editing an existing item (we need an item UUID)
    if (!editItemUuid) return;
    // Don't trigger during AI operations or if already uploading/processing
    if (aiProcessing) return;
    if (processingState !== 'idle') return;
    // Only run when there are new images pending upload
    if (images.length === 0) return;

    // Start upload
    // Note: uploadImages clears `images` on success, so this effect won't loop.
    void uploadImages();
  }, [images, editItemUuid, aiProcessing, processingState]);

  const getProcessingMessage = () => {
    switch (processingState) {
      case 'uploading':
        return t('editItem.uploadingImages');
      case 'processing':
        return t('editItem.aiProcessing');
      case 'completed':
        return t('editItem.processingCompleted');
      case 'error':
        return t('editItem.processingError');
      default:
        return '';
    }
  };

  const adjustDescriptionHeight = () => {
    if (descriptionRef.current) {
      descriptionRef.current.style.height = 'auto';
      descriptionRef.current.style.height = descriptionRef.current.scrollHeight + 5 + 'px';
    }
  };

  const handleAiProcess = async () => {
    if (!editItemUuid) {
      toast({
        title: 'Error',
        description: 'Item UUID is required for AI processing.',
        variant: 'destructive',
      });
      return;
    }

    setAiProcessing(true);

    try {
      const aiResult = await itemsAiDescribeUpdate({
        path: { id: editItemUuid },
      });
      const data = aiResult.data;

      // Update form data with AI-generated content
      setFormData(prevData => ({
        ...prevData,
        name: data.name || prevData.name,
        description: data.description || prevData.description,
        category: (data.category as CategoryEnum) || prevData.category,
        sale_price: data.sale_price?.toString() || prevData.sale_price,
      }));

      // Ensure textarea resizes after AI update
      setTimeout(() => adjustDescriptionHeight(), 0);

      toast({
        title: 'AI Processing Complete',
        description: 'Item details have been automatically updated based on the images.',
      });
    } catch (error) {
      console.error('Error processing with AI:', error);
      toast({
        title: 'AI Processing Failed',
        description: 'Failed to process item with AI. Please try again.',
        variant: 'destructive',
      });
    } finally {
      setAiProcessing(false);
    }
  };

  const handleAiImageGenerate = async () => {
    if (!editItemUuid) {
      toast({
        title: 'Error',
        description: 'Item UUID is required for AI processing.',
        variant: 'destructive',
      });
      return;
    }

    if (!formData.name && !formData.description) {
      toast({
        title: 'Missing Information',
        description: 'Please provide a name or description to generate an image.',
        variant: 'destructive',
      });
      return;
    }

    setAiProcessing(true);

    try {
      await itemsAiImageUpdate({
        path: { id: editItemUuid },
        body: {
          name: formData.name,
          description: formData.description,
        },
      });

      toast({
        title: 'AI Image Generation Complete',
        description: 'A new image has been generated based on the item details.',
      });

      // Invalidate the query to refetch item data
      await queryClient.invalidateQueries({ queryKey: ['item', editItemUuid] });
    } catch (error) {
      console.error('Error generating image with AI:', error);
      toast({
        title: 'AI Image Generation Failed',
        description: 'Failed to generate image with AI. Please try again.',
        variant: 'destructive',
      });
    } finally {
      setAiProcessing(false);
    }
  };

  if (loadingItem) {
    return (
      <div className="min-h-screen bg-background">
        <Header />
        <div className="container mx-auto py-8">
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
      <div className="container mx-auto py-8 space-y-6">
        {/* Back Button */}
        <Button variant="ghost" onClick={handleBackClick} className="mb-6 gap-2">
          <ArrowLeft className="h-4 w-4" />
          {t('common.back')}
        </Button>

        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle>{editItemUuid ? t('itemDetail.editItem') : t('editItem.name')}</CardTitle>
              <div className="flex gap-2">
                {editItemUuid &&
                  (existingImages.length > 0 ? (
                    <AlertDialog>
                      <AlertDialogTrigger asChild>
                        <Button
                          type="button"
                          variant="outline"
                          disabled={aiProcessing}
                          className="gap-2"
                        >
                          <Sparkles className={`h-4 w-4 ${aiProcessing ? 'animate-spin' : ''}`} />
                          {aiProcessing ? t('editItem.aiMagicProcessing') : t('editItem.aiMagic')}
                        </Button>
                      </AlertDialogTrigger>
                      <AlertDialogContent>
                        <AlertDialogHeader>
                          <AlertDialogTitle>{t('editItem.aiMagicWarningTitle')}</AlertDialogTitle>
                          <AlertDialogDescription>
                            {t('editItem.aiMagicWarningDescription')}
                          </AlertDialogDescription>
                        </AlertDialogHeader>
                        <AlertDialogFooter>
                          <AlertDialogCancel>
                            {t('editItem.aiMagicWarningCancel')}
                          </AlertDialogCancel>
                          <AlertDialogAction onClick={handleAiProcess}>
                            {t('editItem.aiMagicWarningContinue')}
                          </AlertDialogAction>
                        </AlertDialogFooter>
                      </AlertDialogContent>
                    </AlertDialog>
                  ) : (
                    <Button
                      type="button"
                      variant="outline"
                      disabled={
                        aiProcessing ||
                        (!formData.name && !formData.description) ||
                        images.length < 1
                      }
                      className="gap-2"
                      onClick={handleAiImageGenerate}
                    >
                      <Sparkles className={`h-4 w-4 ${aiProcessing ? 'animate-spin' : ''}`} />
                      {aiProcessing ? t('editItem.aiMagicProcessing') : t('editItem.aiMagic')}
                    </Button>
                  ))}
                {formData.status === 0 && editItemUuid && (
                  <Button
                    type="button"
                    variant="default"
                    onClick={handlePublish}
                    disabled={loading || updateItemMutation.isPending || aiProcessing}
                    className="gap-2"
                  >
                    {t('editItem.publish')}
                  </Button>
                )}
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-6">
              {/* Image Upload and AI Processing Section */}
              <Card className="border-dashed">
                <CardContent className="space-y-4">
                  <ImageManager
                    onImagesChange={setImages}
                    onExistingImagesChange={setExistingImages}
                    existingImages={existingImages}
                    maxImages={16}
                    isEditing={!aiProcessing}
                    resetNewImagesToken={resetNewImagesToken}
                  />

                  {images.length > 0 && (
                    <div className="flex items-center gap-2">
                      <Badge variant="secondary" className="gap-1">
                        <CheckCircle className="h-3 w-3" />
                        {images.length} new image
                        {images.length !== 1 ? 's' : ''} ready to upload
                      </Badge>
                    </div>
                  )}

                  {/* Processing State */}
                  {processingState !== 'idle' && (
                    <div className="space-y-3 p-4 bg-muted/50 rounded-lg">
                      <div className="flex items-center gap-2">
                        <Loader className="h-4 w-4 animate-spin" />
                        <span className="text-sm font-medium">{getProcessingMessage()}</span>
                      </div>
                      <Progress value={progress} className="w-full" />
                    </div>
                  )}
                </CardContent>
              </Card>

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

                  // If switching to books, persist change first then navigate
                  if (category === 'books' && editItemUuid) {
                    try {
                      await updateItemMutation.mutateAsync({
                        itemUuid: editItemUuid,
                        data: { category: category as CategoryEnum },
                      });
                      navigate(`/edit-book/${editItemUuid}`);
                    } catch (err) {
                      console.error('Error updating category before switching to EditBook:', err);
                      toast({
                        title: t('editItem.updateErrorTitle'),
                        description: (err as any)?.message || t('editItem.updateErrorDescription'),
                        variant: 'destructive',
                      });
                    }
                  }
                }}
              />

              <PricingFields
                formData={formData}
                setFormData={setFormData}
                disabled={aiProcessing}
              />

              <div className="flex items-end justify-between gap-4 pt-4">
                {/* Status field */}
                <div className="flex-1 max-w-xs space-y-2">
                  <Label htmlFor="status" className="text-sm">
                    {t('editItem.status')}
                  </Label>
                  <Select
                    value={formData.status.toString()}
                    onValueChange={value =>
                      setFormData({
                        ...formData,
                        status: parseInt(value) as Status402Enum,
                      })
                    }
                    disabled={aiProcessing}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder={t('editItem.selectStatus')} />
                    </SelectTrigger>
                    <SelectContent>
                      {statuses.map(status => (
                        <SelectItem key={status.value} value={status.value.toString()}>
                          {t(`status.${status.label.toLowerCase()}`)}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <div className="flex gap-2">
                  <Button
                    type="submit"
                    disabled={loading || updateItemMutation.isPending || aiProcessing}
                  >
                    {loading || updateItemMutation.isPending
                      ? t('common.saving')
                      : editItemUuid
                        ? t('common.save')
                        : t('editItem.listItem')}
                  </Button>

                  {formData.status === 0 && (
                    <Button
                      type="button"
                      variant="default"
                      onClick={handlePublish}
                      disabled={loading || updateItemMutation.isPending || aiProcessing}
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

export default EditItem;
