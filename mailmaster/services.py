from django.core.cache import cache

from config.settings import CACHE_ENABLED
from mailmaster.models import NewsLetter


def get_newsletter_from_cache():
    """
    Получает данные по рассылкам. Если кеш пуст, получает данные из БД.
    """
    if CACHE_ENABLED:
        key = f"newsletters_list"
        newsletters_list = cache.get(key)
        if newsletters_list is None:
            newsletters_list = NewsLetter.objects.all()
            cache.set(key, newsletters_list)
    else:
        newsletters_list = NewsLetter.objects.all()
    return newsletters_list
