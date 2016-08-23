import urllib
import json

from django.views.decorators.csrf import ensure_csrf_cookie
from django.http import HttpResponseRedirect, HttpResponse, HttpResponseBadRequest
from django.shortcuts import render
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse

from .forms import IndexForm
from .settings import DOWNLOADER_PAGE_URL, FEED_PAGE_URL, FEED1_PAGE_URL

from .setup_tool import get_selection_tag_ids, build_xpathes_for_items
from .models import Feed, Field, FeedField

def index(request):
    if request.method == 'GET' and 'url' in request.GET:
        form = IndexForm(request.GET)
        if form.is_valid():
            val = URLValidator()
            try:
                url = request.GET['url']
                if not url.startswith('http'):
                    url = 'http://' + url
                val(url)
            except ValidationError, e:
                form.add_error('url', 'Invalid url')
            else:
                return HttpResponseRedirect('%s?url=%s' % (reverse('setup'), urllib.quote(url.encode('utf8'))))
    else:
        form = IndexForm()

    return render(request, 'frontend/index.html', {'form': form})

@ensure_csrf_cookie
def setup(request):
    if request.method == 'GET' and 'url' in request.GET:
        external_page_url = DOWNLOADER_PAGE_URL + urllib.quote(request.GET['url'], safe='')
        return render(request, 'frontend/setup.html',
                        {
                            'external_page_url': external_page_url,
                            'page_url': request.GET['url']
                        })

    return HttpResponseBadRequest('Url is required')

def _validate_html(html):

    def walk(tag):
        if (len(tag) != 3 or not isinstance(tag[0], basestring) or
                type(tag[1]) is not dict or 'tag-id' not in tag[1] or
                type(tag[2]) is not list):
            return False
        for t in tag[2]:
            if not walk(t):
                return False
        return True

    return walk(html)


def setup_get_selected_ids(request):
    if request.method == 'POST':
        obj = json.loads(request.body)
        if 'html' not in obj or 'fields' not in obj:
            return HttpResponseBadRequest('"html" and "fields" parameters are required')
        html_json = obj['html']
        fields_settings = obj['fields']

        #todo: validate required

        if not _validate_html(html_json):
            return HttpResponseBadRequest('html is invalid')

        return HttpResponse(json.dumps(get_selection_tag_ids(fields_settings, html_json)))

def _create_feed(url, xpathes, fields_settings):
    feed_xpath = xpathes[0]
    field_xpathes = xpathes[1]

    predefined_fields = {'title':1, 'description':2, 'link':3, 'image':4}

    feed = Feed(uri=url, xpath=feed_xpath)
    feed.save()
    for name, field_xpath in field_xpathes.iteritems():
        if name in predefined_fields:
            ff_id = predefined_fields[name]
        else:
            field = Field(name=name)
            field.save()
            ff_id = field.id
        content_type = fields_settings[name][1]
        required = fields_settings[name][2]
        ff = FeedField(feed=feed, field_id=ff_id, xpath=field_xpath, content_type=content_type, required=required)
        ff.save()

    return feed.id

def setup_create_feed(request):
    if request.method == 'POST':
        obj = json.loads(request.body)
        if 'html' not in obj or 'fields' not in obj or 'url' not in obj:
            return HttpResponseBadRequest('"html", "fields" and "url" parameters are required')
        html_json = obj['html']
        fields_settings = obj['fields']
        url = obj['url']

        if not _validate_html(html_json):
            return HttpResponseBadRequest('html is invalid')

        field_tag_ids = {name:v[0] for name, v in fields_settings.iteritems()}

        xpathes = build_xpathes_for_items(field_tag_ids, html_json)

        feed_id = _create_feed(url, xpathes, fields_settings)
 
        return HttpResponse(reverse('preview', args=(feed_id,)))

def preview(request, feed_id):
    if request.method == 'GET': 
        return render(request, 'frontend/preview.html',
                        {
                            'feed_url': FEED_PAGE_URL + feed_id, 
                            'feed1_url': FEED1_PAGE_URL + feed_id, 
                        })
        
    return HttpResponseBadRequest('Only GET method supported')
