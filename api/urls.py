# from django.conf.urls import url
# # from rest_framework import routers
#
#

from django.conf.urls import url
from rest_framework import permissions
from rest_framework.urlpatterns import format_suffix_patterns
from api import views
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

schema_view = get_schema_view(
   openapi.Info(
      title="Snippets API",
      default_version='v1',
      description="Test description",
      terms_of_service="https://www.google.com/policies/terms/",
      contact=openapi.Contact(email="contact@snippets.local"),
      license=openapi.License(name="BSD License"),
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    url(r'^swagger/$', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    url(r'^redoc/$', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    url(r'^article/$',
        views.ArticleList.as_view()),
    url(r'^article/gtin/(?P<gtin>[0-9]+)/$',
        views.ArticleGtin.as_view()),
    url(r'^article/name/(?P<product_name>.+)/$',
        views.ArticleProductName.as_view()),
    url(r'^article/add/$',
        views.ArticleAdd.as_view()),
    url(r'^article/image/gtin/(?P<gtin>[0-9]+)/$',
        views.ArticleImageGtin.as_view()),
    url(r'^article/image/add/$',
        views.ArticleImageAdd.as_view()),
    url(r'^merchantarticle/$',
        views.MerchantArticleList.as_view()),
    url(r'^merchantarticle/add/$',
        views.MerchantArticleAdd.as_view()),
    url(r'^merchantarticle/nameandexternalid/' +
        '(?P<merchant_name>.+)/(?P<external_id>[0-9]+)/$',
        views.MerchantArticleGet.as_view()),
    url(r'^merchantarticle/consumergtin/' +
        '(?P<gtin>[0-9]+)/$',
        views.MerchantArticleByGtin.as_view()),
    url(r'^merchantarticle/merchantnameandgtin/' +
        '(?P<merchant_name>.+)/(?P<gtin>[0-9]+)/$',
        views.MerchantArticleNameAndGtin.as_view()),
    url(r'^product/$',
        views.ProductList.as_view()),
    url(r'^product/gtin/(?P<gtin>[0-9]+)/$',
        views.ProductGtin.as_view()),
    url(r'^product/productid/(?P<product_id>[0-9]+)/$',
        views.ProductId.as_view()),
    url(r'^tags/list/all/$',
        views.TagList.as_view()),
    url(r'^tags/list/type/id/(?P<tagtypeid>[0-9]+)/$',
        views.TagList.as_view()),
]

urlpatterns = format_suffix_patterns(urlpatterns)
