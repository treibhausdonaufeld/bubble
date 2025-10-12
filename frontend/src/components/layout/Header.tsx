import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Input } from '@/components/ui/input';
import { useLanguage } from '@/contexts/LanguageContext';
import { useAuth } from '@/hooks/useAuth';
import { useUnreadMessages } from '@/hooks/useMessages';

import { cn } from '@/lib/utils';
import { useTheme } from '@/providers/theme-provider';
import { Languages, LogOut, Moon, NotebookPen, Plus, Search, Sun, User } from 'lucide-react';
import { useEffect, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';

export const Header = () => {
  const [isSearchFocused, setIsSearchFocused] = useState(false);
  const { theme, setTheme } = useTheme();
  const { user, signOut, loading } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const { data: unreadMessages } = useUnreadMessages();

  const { language, setLanguage, t } = useLanguage();

  const unreadCount = unreadMessages?.count || 0;

  const toggleTheme = () => {
    setTheme(theme === 'dark' ? 'light' : 'dark');
  };

  const handleSignOut = async () => {
    await signOut();
    navigate('/');
  };

  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    const params = new URLSearchParams(location.search);
    const q = params.get('search') || '';
    setSearchTerm(q);
  }, [location.search]);

  // Debounced search
  useEffect(() => {
    const timer = setTimeout(() => {
      if (searchTerm && searchTerm.trim() !== '') {
        navigate(`/?search=${encodeURIComponent(searchTerm.trim())}`);
      } else if (searchTerm === '') {
        // Only clear if we're on a search page
        const params = new URLSearchParams(location.search);
        if (params.has('search')) {
          navigate('/');
        }
      }
    }, 500);

    return () => clearTimeout(timer);
  }, [searchTerm, navigate, location.search]);

  const handleSearchSubmit = (term: string) => {
    if (term && term.trim() !== '') {
      navigate(`/?search=${encodeURIComponent(term.trim())}`);
    } else {
      navigate('/');
    }
  };

  return (
    <header className="sticky top-0 z-50 border-b border-border bg-background/80 backdrop-blur-md">
      <div className="container mx-auto px-4 py-3">
        <div className="flex items-center justify-between gap-4">
          {/* Logo */}
          <div className="flex items-center gap-3 cursor-pointer" onClick={() => navigate('/')}>
            <div className="flex h-10 w-10 items-center justify-center rounded-lg overflow-hidden">
              <img src="/icon-192.png" alt="bubble logo" className="h-10 w-10 object-cover" />
            </div>
            <div className="hidden sm:block">
              <h1 className="text-xl font-bold text-foreground">bubble</h1>
              <p className="text-xs text-muted-foreground">Community Network</p>
            </div>
          </div>

          {/* Search Bar */}
          <div className="flex-1 max-w-lg">
            <div
              className={cn('relative transition-all duration-300', isSearchFocused && 'scale-105')}
            >
              <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                placeholder={t('header.search')}
                className="pl-10 shadow-soft focus:shadow-medium transition-shadow"
                value={searchTerm}
                onChange={e => setSearchTerm(e.target.value)}
                onKeyDown={e => {
                  if (e.key === 'Enter') {
                    handleSearchSubmit(searchTerm);
                  }
                }}
                onFocus={() => setIsSearchFocused(true)}
                onBlur={() => setIsSearchFocused(false)}
              />
            </div>
          </div>

          {/* Actions */}
          <div className="flex items-center gap-2">
            {/* Language Toggle */}
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button
                  variant="ghost"
                  size="icon"
                  className="hover:scale-110 transition-transform"
                >
                  <Languages className="h-5 w-5" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent
                align="end"
                className="w-32 bg-background border border-border z-50"
              >
                <DropdownMenuItem
                  onClick={() => setLanguage('en')}
                  className={cn('cursor-pointer', language === 'en' && 'bg-accent')}
                >
                  🇺🇸 English
                </DropdownMenuItem>
                <DropdownMenuItem
                  onClick={() => setLanguage('de')}
                  className={cn('cursor-pointer', language === 'de' && 'bg-accent')}
                >
                  🇩🇪 Deutsch
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>

            {/* Theme Toggle */}
            <Button
              variant="ghost"
              size="icon"
              onClick={toggleTheme}
              className="hover:scale-110 transition-transform"
            >
              {theme === 'dark' ? <Sun className="h-5 w-5" /> : <Moon className="h-5 w-5" />}
            </Button>

            {user && (
              <>
                {/* Bookings */}
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={() => navigate('/bookings')}
                  className="hover:scale-110 transition-transform relative"
                  title={t('header.myBookings')}
                >
                  <NotebookPen className="h-5 w-5" />
                  {unreadCount > 0 && (
                    <Badge
                      variant="destructive"
                      className="absolute -top-1 -right-1 h-5 min-w-[20px] px-1 text-xs"
                    >
                      {unreadCount}
                    </Badge>
                  )}
                </Button>

                {/* Add Item */}
                <Button
                  variant="community"
                  size="sm"
                  className="gap-2"
                  onClick={() => navigate('/create-item')}
                >
                  <Plus className="h-4 w-4" />
                  <span className="hidden sm:inline">{t('header.shareItem')}</span>
                </Button>
              </>
            )}

            {user ? (
              <>
                {/* Profile Dropdown */}
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button variant="outline" size="icon" className="relative">
                      <Avatar className="w-5 h-5">
                        <AvatarFallback className="text-xs">
                          {user.email?.charAt(0).toUpperCase()}
                        </AvatarFallback>
                      </Avatar>
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent
                    align="end"
                    className="w-56 bg-background border border-border z-50"
                  >
                    <DropdownMenuItem
                      className="flex items-center"
                      onClick={() => navigate('/profile')}
                    >
                      <User className="w-4 h-4 mr-2" />
                      {t('header.myProfile')}
                    </DropdownMenuItem>
                    <DropdownMenuItem
                      className="flex items-center"
                      onClick={() => navigate('/my-items')}
                    >
                      <Plus className="w-4 h-4 mr-2" />
                      {t('header.myItems')}
                    </DropdownMenuItem>
                    <DropdownMenuSeparator />
                    <DropdownMenuItem
                      className="flex items-center text-destructive focus:text-destructive"
                      onClick={handleSignOut}
                    >
                      <LogOut className="w-4 h-4 mr-2" />
                      {t('header.signOut')}
                    </DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>
              </>
            ) : (
              /* Sign In Button */
              <Button
                variant="community"
                size="sm"
                onClick={() => navigate('/auth')}
                className="gap-2"
              >
                <User className="h-4 w-4" />
                <span className="hidden sm:inline">{t('header.signIn')}</span>
              </Button>
            )}
          </div>
        </div>
      </div>
    </header>
  );
};
