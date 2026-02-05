import { Button } from '@/components/ui/button';
import { useLanguage } from '@/contexts/LanguageContext';
import { cn } from '@/lib/utils';
import type { ConditionEnum } from '@/services/django/types.gen';
import { CheckCircle2, Circle } from 'lucide-react';

const CONDITIONS: ConditionEnum[] = [0, 1, 2];

interface ConditionFilterProps {
  selectedConditions: ConditionEnum[];
  onConditionsChange: (conditions: ConditionEnum[]) => void;
}

export const ConditionFilter = ({
  selectedConditions,
  onConditionsChange,
}: ConditionFilterProps) => {
  const { t } = useLanguage();

  const getConditionName = (value: ConditionEnum) => {
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

  const toggleCondition = (condition: ConditionEnum) => {
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
        {CONDITIONS.map(condition => {
          const isSelected = selectedConditions.includes(condition);
          const Icon = isSelected ? CheckCircle2 : Circle;

          return (
            <Button
              key={condition}
              variant={isSelected ? 'community' : 'outline'}
              size="sm"
              onClick={() => toggleCondition(condition)}
              className={cn(
                'gap-2 transition-all duration-300',
                isSelected ? 'shadow-glow scale-105' : 'hover:scale-105 hover:shadow-medium',
              )}
            >
              <Icon className="h-4 w-4" />
              <span className="hidden sm:inline">{getConditionName(condition)}</span>
            </Button>
          );
        })}
      </div>
    </div>
  );
};
