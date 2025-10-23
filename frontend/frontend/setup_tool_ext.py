from hashlib import md5

from scrapy.selector import Selector

from .settings import SNAPSHOT_DIR

# Field ID to name mapping
FIELD_ID_TO_NAME = {
    1: 'title',
    2: 'description',
    3: 'link',
    4: 'date'
}

def build_xpath_results(selectors, file_name):
    feed_xpath = selectors[0]
    field_xpathes = selectors[1]

    fpath = "%s/%s" % (SNAPSHOT_DIR, file_name)

    with open(fpath) as f:
        data = f.read()

    html = data.decode('utf-8').split('\n\n', 1)[1]

    feed_result = None
    field_results = {}

    extracted_posts = []

    success = True
    post_elems = None
    try:
        doc = Selector(text=html)
        post_elems = doc.xpath(feed_xpath)
        feed_result = {'count': len(post_elems)}

        if post_elems:
            for elem in post_elems:
                selected_required = True
                extracted_post = {}
                for field_id, xpath_required in field_xpathes.iteritems():
                    xpath, required = xpath_required
                    if not (field_id in field_results):
                        field_results[field_id] = {}
                    xpath = xpath.strip()
                    try:
                        extracts = elem.xpath(xpath).extract()
                        if not required:
                            if extracts:
                                extracted_post[field_id] = u''.join(extracts)
                        else:
                            if not extracts:
                                selected_required = False
                            else:
                                extracted_post[field_id] = u''.join(extracts)
                    except ValueError as ex:
                        success = False
                        field_results[field_id]['error'] = ex.message

                if selected_required:
                    for field_id, xpath_required in field_xpathes.iteritems():
                        xpath, required = xpath_required
                        if not required:
                            if field_id in extracted_post:
                                if 'count' in field_results[field_id]:
                                    field_results[field_id]['count'] += 1
                                else:
                                    field_results[field_id]['count'] = 1
                        else:
                            if 'count' in field_results[field_id]:
                                field_results[field_id]['count'] += 1
                            else:
                                field_results[field_id]['count'] = 1

                    # Convert field IDs to field names
                    extracted_post_named = {}
                    for field_id, value in extracted_post.items():
                        if field_id in FIELD_ID_TO_NAME:
                            extracted_post_named[FIELD_ID_TO_NAME[field_id]] = value
                        else:
                            extracted_post_named[str(field_id)] = value
                    extracted_posts.append(extracted_post_named)
            else:
                for field_id, xpath_required in field_xpathes.iteritems():
                    xpath, required = xpath_required
                    xpath = xpath.strip()
                    try:
                        doc.xpath(xpath).extract()
                    except ValueError as ex:
                        if not (field_id in field_results):
                            field_results[field_id] = {}
                        field_results[field_id]['error'] = ex.message
                        success = False


    except ValueError as ex:
        feed_result = {'error': ex.message}
        success = False

    return [[feed_result, field_results], extracted_posts, success]
