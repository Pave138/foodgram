from rest_framework.pagination import PageNumberPagination

PAGINATION_PAGE_SIZE = 10


class FoodgramApiPagination(PageNumberPagination):
    page_size = PAGINATION_PAGE_SIZE
    page_size_query_param = 'limit'
