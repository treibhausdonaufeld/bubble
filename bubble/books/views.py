"""
Views for books app.
"""
import logging
from typing import List

from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db import models
from django.db.models import Q
from django.http import JsonResponse
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib import messages
from django.utils.translation import gettext_lazy as _

from .models import Book, Author, Genre, Location
from .forms import BookForm, BookFilterForm
from .services.embeddings import get_embeddings_service

logger = logging.getLogger(__name__)


class BookListView(ListView):
    model = Book
    template_name = "books/book_list.html"
    context_object_name = "books"
    paginate_by = 15

    def get_queryset(self):
        queryset = (
            Book.objects.for_user(self.request.user)
            .filter(active=True)
            .select_related("user", "location")
            .prefetch_related("authors", "genres")
        )

        # Apply search and filters
        form = BookFilterForm(self.request.GET)
        if form.is_valid():
            search = form.cleaned_data.get("search")
            authors = form.cleaned_data.get("authors")
            genres = form.cleaned_data.get("genres")
            location = form.cleaned_data.get("location")
            year_min = form.cleaned_data.get("year_min")
            year_max = form.cleaned_data.get("year_max")
            sort = form.cleaned_data.get("sort", "newest")

            # Text search across multiple fields
            if search:
                text_queryset = queryset.filter(
                    Q(title__icontains=search)
                    | Q(description__icontains=search)
                    | Q(topic__icontains=search)
                    | Q(authors__name__icontains=search)
                    | Q(genres__name__icontains=search)
                    | Q(user__username__icontains=search)
                    | Q(user__name__icontains=search)
                ).distinct()
                
                # Try vector search if embeddings are available
                try:
                    embeddings_service = get_embeddings_service()
                    search_embedding = embeddings_service.backend.encode(search)
                    
                    if search_embedding and any(x != 0.0 for x in search_embedding):
                        # Combine text search with vector similarity
                        vector_queryset = Book.objects.search_similar(
                            search_embedding, limit=50
                        ).filter(active=True)
                        
                        # Get IDs from both querysets and combine
                        text_ids = set(text_queryset.values_list('id', flat=True))
                        vector_ids = set(vector_queryset.values_list('id', flat=True))
                        combined_ids = text_ids.union(vector_ids)
                        
                        queryset = queryset.filter(id__in=combined_ids)
                        
                        # If sort is by relevance, prioritize vector similarity
                        if sort == 'relevance':
                            queryset = queryset.extra(
                                select={
                                    'similarity_score': f"""
                                    CASE WHEN id IN ({','.join(map(str, vector_ids))}) 
                                    THEN 1 ELSE 0 END
                                    """
                                }
                            ).order_by('-similarity_score', '-date_created')
                        else:
                            queryset = text_queryset
                    else:
                        queryset = text_queryset
                        
                except Exception as e:
                    logger.warning(f"Vector search failed, falling back to text search: {e}")
                    queryset = text_queryset

            # Filter by authors
            if authors:
                queryset = queryset.filter(authors__in=authors).distinct()

            # Filter by genres
            if genres:
                queryset = queryset.filter(genres__in=genres).distinct()

            # Filter by location
            if location:
                queryset = queryset.filter(location=location)

            # Filter by year range
            if year_min:
                queryset = queryset.filter(year__gte=year_min)
            if year_max:
                queryset = queryset.filter(year__lte=year_max)

            # Apply sorting
            if sort == "oldest":
                queryset = queryset.order_by("date_created")
            elif sort == "title":
                queryset = queryset.order_by("title")
            elif sort == "year_new":
                queryset = queryset.order_by("-year")
            elif sort == "year_old":
                queryset = queryset.order_by("year")
            elif sort != "relevance":  # newest (default) - relevance handled above
                queryset = queryset.order_by("-date_created")

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["filter_form"] = BookFilterForm(self.request.GET)
        context["authors"] = Author.objects.all()
        context["genres"] = Genre.objects.all()
        context["locations"] = Location.objects.all()
        return context


class BookDetailView(DetailView):
    model = Book
    template_name = "books/book_detail.html"
    context_object_name = "book"

    def get_queryset(self):
        return (
            Book.objects.for_user(self.request.user)
            .select_related("user", "location")
            .prefetch_related("authors", "genres")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["is_owner"] = (
            self.request.user == self.object.user
            if self.request.user.is_authenticated
            else False
        )
        
        # Get similar books using vector similarity
        if self.object.embedding:
            try:
                similar_books = Book.objects.search_similar(
                    self.object.embedding, limit=5
                ).exclude(id=self.object.id).filter(active=True)[:4]
                context["similar_books"] = similar_books
            except Exception as e:
                logger.warning(f"Failed to get similar books: {e}")
                context["similar_books"] = []
        else:
            context["similar_books"] = []

        return context


class BookCreateView(LoginRequiredMixin, CreateView):
    model = Book
    form_class = BookForm
    template_name = "books/book_form.html"

    def form_valid(self, form):
        form.instance.user = self.request.user
        response = super().form_valid(form)
        messages.success(
            self.request,
            _("Book '%(title)s' has been created successfully.") % {
                'title': self.object.title
            }
        )
        return response

    def get_success_url(self):
        return reverse_lazy("books:detail", kwargs={"pk": self.object.pk})


class BookUpdateView(LoginRequiredMixin, UpdateView):
    model = Book
    form_class = BookForm
    template_name = "books/book_form.html"

    def get_queryset(self):
        return Book.objects.filter(user=self.request.user)

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(
            self.request,
            _("Book '%(title)s' has been updated successfully.") % {
                'title': self.object.title
            }
        )
        return response

    def get_success_url(self):
        return reverse_lazy("books:detail", kwargs={"pk": self.object.pk})


class BookDeleteView(LoginRequiredMixin, DeleteView):
    model = Book
    template_name = "books/book_confirm_delete.html"
    success_url = reverse_lazy("books:list")

    def get_queryset(self):
        return Book.objects.filter(user=self.request.user)

    def form_valid(self, form):
        messages.success(
            self.request,
            _("Book '%(title)s' has been deleted successfully.") % {
                'title': self.object.title
            }
        )
        return super().form_valid(form)


class MyBooksView(LoginRequiredMixin, ListView):
    model = Book
    template_name = "books/my_books.html"
    context_object_name = "books"
    paginate_by = 20

    def get_queryset(self):
        return (
            Book.objects.filter(user=self.request.user)
            .select_related("location")
            .prefetch_related("authors", "genres")
            .order_by("-date_created")
        )


@method_decorator(never_cache, name='dispatch')
class BookSearchAPIView(ListView):
    """API endpoint for book search with JSON response."""
    
    def get(self, request, *args, **kwargs):
        search_query = request.GET.get('q', '').strip()
        limit = min(int(request.GET.get('limit', 10)), 50)
        
        if not search_query:
            return JsonResponse({'books': [], 'count': 0})
        
        try:
            # Get embeddings service
            embeddings_service = get_embeddings_service()
            search_embedding = embeddings_service.backend.encode(search_query)
            
            if search_embedding and any(x != 0.0 for x in search_embedding):
                # Vector search
                books = Book.objects.search_similar(
                    search_embedding, limit=limit
                ).filter(active=True).for_user(request.user)
            else:
                # Fallback to text search
                books = Book.objects.for_user(request.user).filter(
                    Q(title__icontains=search_query) |
                    Q(authors__name__icontains=search_query) |
                    Q(description__icontains=search_query)
                ).distinct()[:limit]
            
            results = []
            for book in books:
                results.append({
                    'id': book.id,
                    'title': book.title,
                    'authors': book.get_authors_display(),
                    'year': book.year,
                    'url': reverse_lazy('books:detail', kwargs={'pk': book.pk})
                })
            
            return JsonResponse({
                'books': results,
                'count': len(results)
            })
            
        except Exception as e:
            logger.error(f"Search API error: {e}")
            return JsonResponse({'error': 'Search failed'}, status=500)
