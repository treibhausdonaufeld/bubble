import { Button } from '@/components/ui/button';
import { useLanguage } from '@/contexts/LanguageContext';
import { cn } from '@/lib/utils';
import { CheckCircle2, Circle } from 'lucide-react';

export type ConditionValue = 0 | 1 | 2;

export interface ConditionOption {
  value: ConditionValue;
  label: string;
}

const conditions: ConditionOption[] = [
  { value: 0, label: 'New' },
  { value: 1, label: 'Used' },
  { value: 2, label: 'Broken' },
];

interface ConditionFilterProps {
  selectedConditions: ConditionValue[];
  onConditionsChange: (conditions: ConditionValue[]) => void;
}

export const ConditionFilter = ({
  selectedConditions,
  onConditionsChange,
}: ConditionFilterProps) => {
  const { t } = useLanguage();

  const getConditionName = (value: ConditionValue) => {
    switch (value) {
      case 0:
        return t('condition.new');
      case 1:
        return t('condition.used');
      case 2:
        return t('condition.broken');
      default:
        return value;
    }
  };

  const toggleCondition = (condition: ConditionValue) => {
    const newConditions = selectedConditions.includes(condition)
      ? selectedConditions.filter(c => c !== condition)
      : [...selectedConditions, condition];
    onConditionsChange(newConditions);
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-foreground">{t('index.condition')}</h3>
      </div>

      <div className="flex flex-wrap gap-2">
        {conditions.map(condition => {
          const isSelected = selectedConditions.includes(condition.value);
          const Icon = isSelected ? CheckCircle2 : Circle;

          return (
            <Button
              key={condition.value}
              variant={isSelected ? 'community' : 'outline'}
              size="sm"
              onClick={() => toggleCondition(condition.value)}
              className={cn(
                'gap-2 transition-all duration-300',
                isSelected ? 'shadow-glow scale-105' : 'hover:scale-105 hover:shadow-medium',
              )}
            >
              <Icon className="h-4 w-4" />
              <span className="hidden sm:inline">{getConditionName(condition.value)}</span>
            </Button>
          );
        })}
      </div>
    </div>
  );
};
