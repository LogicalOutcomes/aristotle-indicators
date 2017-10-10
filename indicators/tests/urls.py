from django.conf.urls import include, url

urlpatterns = [
    url(r'^', include('indicators.urls')),
    url(r'^', include('aristotle_mdr.urls')),
    url(r'^comet/', include('comet.urls', app_name="comet", namespace="comet")),
]
