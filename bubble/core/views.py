from django.http import JsonResponse
from django.shortcuts import redirect
from django.utils.translation import gettext as _
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST


@require_POST
@csrf_exempt
def set_theme(request):
    """
    Set the user's theme preference.
    """
    theme = request.POST.get("theme", "auto")

    # Validate theme value
    if theme not in ["light", "dark", "auto"]:
        theme = "auto"

    # Store theme in session
    request.session["theme"] = theme

    # Return JSON response for AJAX requests
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return JsonResponse(
            {
                "success": True,
                "theme": theme,
                "message": _("Theme updated successfully"),
            }
        )

    # Redirect for regular form submissions
    next_url = request.POST.get("next", request.headers.get("referer", "/"))
    return redirect(next_url)
