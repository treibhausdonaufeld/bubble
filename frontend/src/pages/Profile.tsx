import { Header } from '@/components/layout/Header';
import { LocationsList } from '@/components/profile/LocationsList';
import { ProfileForm } from '@/components/profile/ProfileForm';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { useLanguage } from '@/contexts/LanguageContext';
import { MapPin, User } from 'lucide-react';

const Profile = () => {
  const { t } = useLanguage();

  return (
    <div className="min-h-screen bg-background">
      <Header />
      <div className="container mx-auto px-4 py-8 max-w-4xl">
        <div className="mb-8">
          <h1 className="text-3xl font-bold">{t('profile.title')}</h1>
          <p className="text-muted-foreground mt-2">{t('profile.manage')}</p>
        </div>

        <Tabs defaultValue="profile" className="space-y-6">
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="profile" className="flex items-center gap-2">
              <User className="h-4 w-4" />
              {t('profile.title')}
            </TabsTrigger>
            <TabsTrigger value="locations" className="flex items-center gap-2">
              <MapPin className="h-4 w-4" />
              {t('profile.manage')}
            </TabsTrigger>
          </TabsList>

          <TabsContent value="profile">
            <ProfileForm />
          </TabsContent>

          <TabsContent value="locations">
            <LocationsList />
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
};

export default Profile;
