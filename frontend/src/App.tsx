import { Toaster as Sonner } from '@/components/ui/sonner';
import { Toaster } from '@/components/ui/toaster';
import { TooltipProvider } from '@/components/ui/tooltip';
import { LanguageProvider } from '@/contexts/LanguageContext';
import { AuthProvider } from '@/hooks/useAuth';
import { NotificationProvider } from '@/providers/NotificationProvider';
import { ThemeProvider } from '@/providers/theme-provider';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter, Route, Routes } from 'react-router-dom';
import { configureApiClient } from './config/apiClient';
import Auth from './pages/Auth';
import Bookings from './pages/Bookings';
import CreateItem from './pages/CreateItem';
import EditBook from './pages/EditBook';
import EditItem from './pages/EditItem';
import Index from './pages/Index';
import ItemDetail from './pages/ItemDetail';
import MyItems from './pages/MyItems';
import NotFound from './pages/NotFound';
import Profile from './pages/Profile';

const queryClient = new QueryClient();

// Configure the API client once at startup
configureApiClient();

const App = () => (
  <QueryClientProvider client={queryClient}>
    <ThemeProvider defaultTheme="system" storageKey="bubble-theme">
      <LanguageProvider>
        <AuthProvider>
          <NotificationProvider>
            <TooltipProvider>
              <Toaster />
              <Sonner />
              <BrowserRouter>
                <Routes>
                  <Route path="/" element={<Index />} />
                  <Route path="/auth" element={<Auth />} />
                  <Route path="/create-item" element={<CreateItem />} />
                  <Route path="/edit-item/:itemUuid" element={<EditItem />} />
                  <Route path="/edit-book/:itemUuid" element={<EditBook />} />
                  <Route path="/item/:itemUuid" element={<ItemDetail />} />
                  <Route path="/my-items" element={<MyItems />} />
                  <Route path="/profile" element={<Profile />} />
                  <Route path="/bookings" element={<Bookings />} />
                  {/* ADD ALL CUSTOM ROUTES ABOVE THE CATCH-ALL "*" ROUTE */}
                  <Route path="*" element={<NotFound />} />
                </Routes>
              </BrowserRouter>
            </TooltipProvider>
          </NotificationProvider>
        </AuthProvider>
      </LanguageProvider>
    </ThemeProvider>
  </QueryClientProvider>
);

export default App;
