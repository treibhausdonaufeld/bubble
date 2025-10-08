from django.views.generic import DetailView, ListView

from .models import Room


class RoomListView(ListView):
    model = Room
    template_name = "rooms/room_list.html"
    context_object_name = "rooms"
    paginate_by = 12


class RoomDetailView(DetailView):
    model = Room
    template_name = "rooms/room_detail.html"
    context_object_name = "room"
