import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Textarea } from '@/components/ui/textarea';
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip';
import { useLanguage } from '@/contexts/LanguageContext';
import { CategoryEnum, ConditionEnum, RentalPeriodEnum, Status402Enum } from '@/services/django';

interface BasicFieldsProps {
  formData: {
    name: string;
    description: string;
  };
  setFormData: (data: any) => void;
  disabled?: boolean;
  descriptionRef?: React.RefObject<HTMLTextAreaElement>;
}

export const BasicFields = ({
  formData,
  setFormData,
  disabled,
  descriptionRef,
}: BasicFieldsProps) => {
  const { t } = useLanguage();

  return (
    <>
      <div className="space-y-2">
        <Label htmlFor="name">{t('editItem.name')} *</Label>
        <Input
          id="name"
          type="text"
          placeholder={t('editItem.enterName')}
          value={formData.name}
          onChange={e => setFormData({ ...formData, name: e.target.value })}
          disabled={disabled}
          required
        />
      </div>

      <div className="space-y-2">
        <Label htmlFor="description">{t('editItem.description')}</Label>
        <Textarea
          id="description"
          ref={descriptionRef}
          placeholder={t('editItem.enterDescription')}
          value={formData.description}
          onChange={e => setFormData({ ...formData, description: e.target.value })}
          disabled={disabled}
          className="min-h-[100px]"
        />
      </div>
    </>
  );
};

interface CategoryConditionFieldsProps {
  formData: {
    category: CategoryEnum | '';
    condition: ConditionEnum | '';
  };
  setFormData: (data: any) => void;
  disabled?: boolean;
  categories: CategoryEnum[];
  onCategoryChange?: (category: CategoryEnum) => void;
}

export const CategoryConditionFields = ({
  formData,
  setFormData,
  disabled,
  categories,
  onCategoryChange,
}: CategoryConditionFieldsProps) => {
  const { t } = useLanguage();

  const conditions = [
    { value: 0, key: 'new' },
    { value: 1, key: 'used' },
    { value: 2, key: 'broken' },
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      <div className="space-y-2">
        <Label htmlFor="category">{t('editItem.category')} *</Label>
        <Select
          value={formData.category}
          onValueChange={(value: CategoryEnum) => {
            setFormData({ ...formData, category: value });
            onCategoryChange?.(value);
          }}
          disabled={disabled}
          required
        >
          <SelectTrigger>
            <SelectValue placeholder={t('editItem.selectCategory')} />
          </SelectTrigger>
          <SelectContent>
            {categories.map(category => (
              <SelectItem key={category} value={category}>
                {t(`categories.${category}`)}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <div className="space-y-2">
        <Label htmlFor="condition">{t('editItem.condition')} *</Label>
        <Select
          value={formData.condition.toString()}
          onValueChange={value =>
            setFormData({
              ...formData,
              condition: parseInt(value) as ConditionEnum,
            })
          }
          disabled={disabled}
          required
        >
          <SelectTrigger>
            <SelectValue placeholder={t('editItem.selectCondition')} />
          </SelectTrigger>
          <SelectContent>
            {conditions.map(condition => (
              <SelectItem key={condition.value} value={condition.value.toString()}>
                {t(`condition.${condition.key}`)}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>
    </div>
  );
};

interface PricingFieldsProps {
  formData: {
    sale_price: string;
    rental_price: string;
    rental_period: RentalPeriodEnum | '';
    rental_self_service: boolean;
    rental_open_end: boolean;
  };
  setFormData: (data: any) => void;
  disabled?: boolean;
}

export const PricingFields = ({ formData, setFormData, disabled }: PricingFieldsProps) => {
  const { t } = useLanguage();

  return (
    <>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label htmlFor="sale_price">{t('editItem.salePrice')}</Label>
          <Tooltip>
            <TooltipTrigger asChild>
              <Input
                id="sale_price"
                type="number"
                step="1.00"
                placeholder={t('editItem.saleDisabledPlaceholder')}
                value={formData.sale_price}
                onChange={e =>
                  setFormData({
                    ...formData,
                    sale_price: e.target.value,
                  })
                }
                disabled={disabled || formData.rental_price !== ''}
              />
            </TooltipTrigger>
            {formData.rental_price !== '' && (
              <TooltipContent>{t('editItem.saleDisablesRental')}</TooltipContent>
            )}
          </Tooltip>
        </div>

        <div className="space-y-2">
          <Label htmlFor="rental_price">{t('editItem.rentalPrice')}</Label>
          <Tooltip>
            <TooltipTrigger asChild>
              <Input
                id="rental_price"
                type="number"
                step="1.00"
                placeholder={t('editItem.rentalDisabledPlaceholder')}
                value={formData.rental_price}
                onChange={e =>
                  setFormData({
                    ...formData,
                    rental_price: e.target.value,
                  })
                }
                disabled={disabled || formData.sale_price !== ''}
              />
            </TooltipTrigger>
            {formData.sale_price !== '' && (
              <TooltipContent>{t('editItem.rentalDisablesSale')}</TooltipContent>
            )}
          </Tooltip>
        </div>
      </div>

      {/* Rental-specific fields - only visible when rental_price is set */}
      {formData.rental_price !== '' && (
        <div className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="rental_period">{t('editItem.rentalPeriod')}</Label>
              <Select
                value={formData.rental_period}
                onValueChange={(value: RentalPeriodEnum) =>
                  setFormData({ ...formData, rental_period: value })
                }
                disabled={disabled}
              >
                <SelectTrigger>
                  <SelectValue placeholder={t('editItem.selectRentalPeriod')} />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="h">{t('rentalPeriod.h')}</SelectItem>
                  <SelectItem value="d">{t('rentalPeriod.d')}</SelectItem>
                  <SelectItem value="w">{t('rentalPeriod.w')}</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label className="text-sm">{t('editItem.rentalOptions')}</Label>
              <div className="flex flex-col gap-2">
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={formData.rental_self_service}
                    onChange={e =>
                      setFormData({
                        ...formData,
                        rental_self_service: e.target.checked,
                      })
                    }
                    disabled={disabled}
                  />
                  <span className="text-sm">{t('editItem.rentalSelfService')}</span>
                </label>

                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={formData.rental_open_end}
                    onChange={e =>
                      setFormData({
                        ...formData,
                        rental_open_end: e.target.checked,
                      })
                    }
                    disabled={disabled}
                  />
                  <span className="text-sm">{t('editItem.rentalOpenEnd')}</span>
                </label>
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  );
};

interface StatusFieldProps {
  formData: {
    status: Status402Enum | '';
  };
  setFormData: (data: any) => void;
  disabled?: boolean;
}

export const StatusField = ({ formData, setFormData, disabled }: StatusFieldProps) => {
  const { t } = useLanguage();

  const statuses = [
    { value: 0, label: 'draft' },
    { value: 1, label: 'archived' },
    { value: 2, label: 'available' },
    { value: 3, label: 'pending' },
    { value: 4, label: 'sold' },
    { value: 5, label: 'rented' },
  ];

  return (
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
        disabled={disabled}
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
  );
};
