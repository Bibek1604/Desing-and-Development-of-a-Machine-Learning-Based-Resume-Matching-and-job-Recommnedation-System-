"""Project-wide pagination.

Adds a client-controllable page size on top of DRF's PageNumberPagination,
with a hard upper bound so a client can never request an unbounded page.

Query params:
    ?page=<n>          1-based page number
    ?page_size=<n>     items per page (1..MAX_PAGE_SIZE), default DEFAULT
"""
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class StandardPagination(PageNumberPagination):
    # Default page size comes from settings PAGE_SIZE; clients may override
    # per-request via ?page_size= up to max_page_size.
    page_size_query_param = "page_size"
    max_page_size = 100

    def get_paginated_response(self, data):
        # Keep the familiar DRF shape, plus convenience fields the frontend
        # pager uses (page / num_pages / page_size) — all additive.
        return Response({
            "count":     self.page.paginator.count,
            "num_pages": self.page.paginator.num_pages,
            "page":      self.page.number,
            "page_size": self.get_page_size(self.request),
            "next":      self.get_next_link(),
            "previous":  self.get_previous_link(),
            "results":   data,
        })
