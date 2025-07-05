from bubble.categories.models import ItemCategory


def navigation_context(request):
    """
    Provide navigation context to all templates.
    """
    # Get all root categories that have a url_slug
    root_categories = (
        ItemCategory.objects.filter(
            parent_category__isnull=True,
            url_slug__isnull=False,
        )
        .exclude(url_slug="")
        .order_by("ordering", "name")
    )

    # Extract content_type_slug from URL path
    content_type_slug = None
    if request.resolver_match:
        # Get the content_type from URL kwargs
        content_type_slug = request.resolver_match.kwargs.get("content_type")

        # If not in kwargs, try to parse from path
        if not content_type_slug and request.path:
            path_parts = request.path.strip("/").split("/")
            min_path_parts = 2
            if len(path_parts) >= min_path_parts and path_parts[0] == "items":
                content_type_slug = path_parts[1]

    return {
        "root_categories": root_categories,
        "content_type_slug": content_type_slug,
    }
