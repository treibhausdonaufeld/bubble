import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Textarea } from '@/components/ui/textarea';
import { useLanguage } from '@/contexts/LanguageContext';
import { CategoryEnum, ConditionEnum, RentalPeriodEnum, Status402Enum } from '@/services/django';
import { useEffect, useState } from 'react';

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
            if (value) {
              setFormData({ ...formData, category: value });
              onCategoryChange?.(value);
            }
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
            value
              ? setFormData({
                  ...formData,
                  condition: parseInt(value) as ConditionEnum,
                })
              : null
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
  const [pricingOption, setPricingOption] = useState<'sell' | 'rent' | ''>('sell');

  useEffect(() => {
    if (formData.rental_price) {
      setPricingOption('rent');
    } else {
      setPricingOption('sell');
    }
  }, [formData.sale_price, formData.rental_price]);

  const handleOptionChange = (value: 'sell' | 'rent') => {
    setPricingOption(value);
    if (value === 'sell') {
      setFormData({
        ...formData,
        rental_price: '',
        rental_period: 'h',
        rental_self_service: false,
        rental_open_end: false,
      });
    } else if (value === 'rent') {
      setFormData({
        ...formData,
        sale_price: '',
      });
    }
  };

  return (
    <>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label>{t('editItem.pricingModel')}</Label>
          <RadioGroup
            value={pricingOption}
            onValueChange={handleOptionChange}
            className="flex gap-4"
            disabled={disabled}
          >
            <div className="flex items-center space-x-2">
              <RadioGroupItem value="sell" id="sell" />
              <Label htmlFor="sell">{t('editItem.sell')}</Label>
            </div>
            <div className="flex items-center space-x-2">
              <RadioGroupItem value="rent" id="rent" />
              <Label htmlFor="rent">{t('editItem.rent')}</Label>
            </div>
          </RadioGroup>
        </div>

        {(pricingOption === 'sell' || !!formData.sale_price) && (
          <div className="space-y-2">
            <Label htmlFor="sale_price">{t('editItem.salePrice')}</Label>
            <Input
              id="sale_price"
              type="number"
              step="1.00"
              placeholder={t('editItem.enterSalePrice')}
              value={formData.sale_price}
              onChange={e =>
                setFormData({
                  ...formData,
                  sale_price: e.target.value,
                })
              }
              disabled={disabled}
              required
            />
          </div>
        )}

        {(pricingOption === 'rent' || !!formData.rental_price) && (
          <div className="space-y-2">
            <Label htmlFor="rental_price">{t('editItem.rentalPrice')}</Label>
            <Input
              id="rental_price"
              type="number"
              step="1.00"
              placeholder={t('editItem.enterRentalPrice')}
              value={formData.rental_price}
              onChange={e =>
                setFormData({
                  ...formData,
                  rental_price: e.target.value,
                })
              }
              disabled={disabled}
              required
            />
          </div>
        )}
      </div>
      {(pricingOption === 'rent' || !!formData.rental_price) && (
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
                required
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
    { value: 1, label: 'processing' },
    { value: 2, label: 'available' },
    { value: 3, label: 'reserved' },
    { value: 4, label: 'rented' },
    { value: 5, label: 'sold' },
  ];

  return (
    <div className="flex-1 max-w-xs space-y-2">
      <Label htmlFor="status" className="text-sm">
        {t('editItem.status')}
      </Label>
      <Select
        value={formData.status.toString()}
        onValueChange={value =>
          value !== ''
            ? setFormData({
                ...formData,
                status: parseInt(value) as Status402Enum,
              })
            : null
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
