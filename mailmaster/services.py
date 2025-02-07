from django.core.cache import cache

from config.settings import CACHE_ENABLED
from mailmaster.models import NewsLetter


def get_newsletter_from_cache(newsletter_pk):
    """
    Получает данные по рассылкам. Если кеш пуст, получает данные из БД.
    """
    if CACHE_ENABLED:
        key = f"newsletters_list_{newsletter_pk}"
        newsletters_list = cache.get(key)
        if newsletters_list is None:
            newsletters_list = NewsLetter.objects.filter(id=newsletter_pk)
            cache.set(key, newsletters_list)
    else:
        newsletters_list = NewsLetter.objects.filter(id=newsletter_pk)
    return newsletters_list
