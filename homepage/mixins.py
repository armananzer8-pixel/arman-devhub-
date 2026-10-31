
# =====================================
# ARMAN DEVHUB
# DAY 187 - REUSABLE MIXINS
# =====================================

from django.contrib.admin.views.decorators import staff_member_required
from django.utils.decorators import method_decorator


class StaffOnlyMixin:
    """
    Reusable mixin that allows only
    active Django staff members.
    """

    @method_decorator(staff_member_required)
    def dispatch(self, request, *args, **kwargs):

        return super().dispatch(
            request,
            *args,
            **kwargs
        )
