"""
Custom pagination that wraps results in the unified response envelope.
"""

from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class StandardPagination(PageNumberPagination):
    """Page-based pagination with configurable page size."""

    page_size = 20
    page_size_query_param = 'pageSize'
    max_page_size = 100
    page_query_param = 'page'

    def get_paginated_response(self, data):
        request = self.request
        trace_id = getattr(request, 'trace_id', '-') if request else '-'
        return Response(
            {
                'traceId': trace_id,
                'success': True,
                'data': {
                    'results': data,
                    'pagination': {
                        'count': self.page.paginator.count,
                        'totalPages': self.page.paginator.num_pages,
                        'currentPage': self.page.number,
                        'pageSize': self.get_page_size(request),
                        'next': self.get_next_link(),
                        'previous': self.get_previous_link(),
                    },
                },
            }
        )

    def get_paginated_response_schema(self, schema):
        return {
            'type': 'object',
            'properties': {
                'traceId': {'type': 'string'},
                'success': {'type': 'boolean'},
                'data': {
                    'type': 'object',
                    'properties': {
                        'results': schema,
                        'pagination': {
                            'type': 'object',
                            'properties': {
                                'count': {'type': 'integer'},
                                'totalPages': {'type': 'integer'},
                                'currentPage': {'type': 'integer'},
                                'pageSize': {'type': 'integer'},
                                'next': {'type': 'string', 'nullable': True},
                                'previous': {'type': 'string', 'nullable': True},
                            },
                        },
                    },
                },
            },
        }
