import urllib
import json

from django.views.decorators.csrf import ensure_csrf_cookie
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse

from .forms import IndexForm
from .settings import DOWNLOADER_PAGE_URL

from .setup_tool import get_selection_tag_ids

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

@ensure_csrf_cookie
def setup(request):
    if request.method == 'GET' and 'url' in request.GET:
        external_page_url = DOWNLOADER_PAGE_URL + urllib.quote(request.GET['url'], safe='')
        return render(request, 'frontend/setup.html', {'external_page_url': external_page_url})

    return HttpResponse('Url is required')

def setup_generate_selected_ids(request):
    if request.method == 'POST':
        obj = json.loads(request.body)
        html_json = obj['html']
        item_names = obj['names']

        return HttpResponse(json.dumps(get_selection_tag_ids(item_names, html_json)))
