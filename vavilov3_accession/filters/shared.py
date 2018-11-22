from django.db.models import Q


class TermFilterMixin():

    def term_filter(self, qs, _, value):
        return qs.filter(Q(code__icontains=value) |
                         Q(name__icontains=value))
