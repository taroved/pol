import urllib

from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse

from .forms import IndexForm
from .settings import DOWNLOADER_PAGE_URL

def index(request):
    if request.method == 'GET' and 'url' in request.GET:
        form = IndexForm(request.GET)
        if form.is_valid():
            val = URLValidator()
            try:
                val(request.GET['url'])
            except ValidationError, e:
                form.add_error('url', 'Invalid url')
            else:
                return HttpResponseRedirect('%s?url=%s' % (reverse('setup'), urllib.quote(request.GET['url'].encode('utf8'))))
    else:
        form = IndexForm()

    return render(request, 'frontend/index.html', {'form': form})


def setup(request):
    if request.method == 'GET' and 'url' in request.GET:
        external_page_url = DOWNLOADER_PAGE_URL + urllib.quote(request.GET['url'], safe='')
        return render(request, 'frontend/setup.html', {'external_page_url': external_page_url})

    return HttpResponse('Url is required')

