from lxml import etree
import sys
import requests
from datetime import datetime

from feed import element_to_unicode

def tostring(el, fields):
    if fields:
        s = ''
        for f in fields:
            for e in el.xpath(f+'/text()'):
                s += e
        return s
    else:
        etree.tostring(el)

def element_to_string(element, fields=None):
    if isinstance(element, basestring): # attribute
        return element

    s = [element.text] if element.text else []
    if fields:
        return tostring(element, fields).encode('utf-8')
    else:
        for sub_element in element:
            s.append(etree.tostring(sub_element))
        return ''.join(s)

def test1_get_inner_html():
    root = etree.fromstring('<a>1<b>2</b>3<c>4</c>5</a>')
    assert element_to_unicode(root, 'utf-8') == u'1<b>2</b>3<c>4</c>5'
ids = [1,54,100,131,134,140,146,159,162,166,168,175,176,183,189,190,192,204,205,226,230,236,244,251,253,260,261,263,271,272,273,275,277,279,280,308,311,312,313,315,316,317,318,327,332,333,334,335,337,338,340,347,350,352,354,355,356,357,358,359,360,361,362,363,369,371,373,376,385,399,402,405,406,410,411,412,422,427,448,467,470,471,472,473,477,479,481,512,514,519,522,523,524,526,527,528,529,532,533,536,538,547,557,587,592,597,598,599,600,606,607,608,615,616,617,618,628,629,641,642,643,645,646,647,648,649,653,658,660,673,676,678,680,681,683,685,704,709,710,717,718,719,728,730,732,735,744,745,746,749,757,758,759,772,776,777,778,779,783,784,785,786,789,790,791,792,793,794,795,797,798,800,801,802,803,804,805,806,807,808,809,810,811,812,813,814,815,816,817,818,819,820,821,822,823,824,825,826,827,828,829,830,831,832,833,835,836,839,840,842,843,844,845,846,847,848,849,850,851,852,853,854,855,861,862,863,864,867,868,869,870,871,872,873,874,875,876,877,878,879,880,881,882,883,884,885,886,889,890,891,893,894,895,896,897,898,899,900,901,902,903,904,905,906,907,908,909,910,911,912,913,914,915,916,917,918,919,920,923,924,926,927,928,929,930,931,933,934,935,936,937,938,939,940,941,942,943,944,947,948,949,950]
domain = "politepol.com"

def parse_feed0(text):
    ch = etree.fromstring(text).xpath('/rss/channel')
    title = ch[0].xpath('title')[0].text
    link = ch[0].xpath('link')[0].text
    items = ch[0].xpath('item')
    return [title, link, items]

def parse_feed(text):
    ch = etree.fromstring(text.encode('utf-8')).xpath('/rss/channel')
    title = ch[0].xpath('title')[0].text
    link = ch[0].xpath('link')[0].text
    items = ch[0].xpath('item')
    return [title, link, items]

def crawl(extention):
    number = 0
    for id in ids:
        print "ID: %s (%s of %s) %s" % (id, number, len(ids), datetime.utcnow())
        r = requests.get("http://%s/feed/%s" % (domain, id))
        #r.encoding = 'utf-8'
        text = r.text.encode('utf-8')
        with open("tests/%s.%s" % (id, extention), 'w') as f:
            f.write(text)
        title, link, items = parse_feed0(text)
        print "Title: %s" % title
        print "Link: %s" % link
        print "Items count: %s" % len(items)
        number += 1

def diff(ext1, ext2, fields):
    diff = []
    number = 0
    for id in ids:
        print "ID: %s" % (id,)
        text1 = None
        with open("tests/%s.%s" % (id, ext1), 'r') as f:
            text1 = f.read().decode('utf-8')
        text2 = None
        with open("tests/%s.%s" % (id, ext2), 'r') as f:
            text2 = f.read().decode('utf-8')

	if text1 == text2:
            print "Identical"
        else:
            diff.append(id)
            posts_diff = 0
            with open("tests/%s.diff" % (id,), 'w') as f:
		title1, link, items1 = parse_feed(text1)
		title2, link, items2 = parse_feed(text2)
		if title1 != title2:
                    print "Different titles"
                    f.write("<<<<<<<<<<<<<<< Different titles >>>>>>>>>>>>>>>\n")
                    f.write(">>>>>>>>>>>>>>> %s.%s  <<<<<<<<<<<<<\n" % (id, ext1))
                    f.write(title1.encode('utf-8') + "\n")
                    f.write(">>>>>>>>>>>>>>> %s.%s  <<<<<<<<<<<<<\n" % (id, ext2))
                    f.write(title2.encode('utf-8') + "\n")
                posts1 = {}
                posts2 = {}
                if len(items1) != len(items2):
                    print "Different post count: %s vs %s" % (len(items1), len(items2))
                    f.write("<< Different posts count: %s.%s:%s vs %s.%s:%s >>\n" % (id, ext1, len(items1), id, ext2, len(items2)))
                for post in items1:
                    posts1[element_to_string(post, fields)] = True
                for post in items2:
                    posts2[element_to_string(post, fields)] = True

                for post in items1:
                    if not (element_to_string(post, fields) in posts2):
                        posts_diff += 1
                        f.write("<<<<<<<<<<<<<<< Different posts (%s) >>>>>>>>>>>>>>>\n" % posts_diff)
                        f.write(">>>>>>>>>>>>>>> %s.%s  <<<<<<<<<<<<<\n" % (id, ext1))
                        #import pdb;pdb.set_trace()
                        f.write(element_to_string(post, fields) + "\n")
                        f.write(">>>>>>>>>>>>>>> %s.%s  <<<<<<<<<<<<<\n" % (id, ext2))
                        f.write("*** Not found ***\n")

                for post in items2:
                    if not (element_to_string(post, fields) in posts1):
                        posts_diff += 1
                        f.write("<<<<<<<<<<<<<<< Different posts (%s) >>>>>>>>>>>>>>>\n" % posts_diff)
                        f.write(">>>>>>>>>>>>>>> %s.%s  <<<<<<<<<<<<<\n" % (id, ext1))
                        f.write("*** Not found ***\n")
                        f.write(">>>>>>>>>>>>>>> %s.%s  <<<<<<<<<<<<<\n" % (id, ext2))
                        f.write(element_to_string(post, fields) + "\n")
            print "Content of files %s.%s and %s.%s is different. Diff: %s.diff" % (id, ext1, id, ext2, id)
            if posts_diff > 0:
                print "Different feeds: %s" % posts_diff  
        number += 1
    if diff > 0:
        print "Different feed ids: %s" % str(diff)

print "Example of usage: python tests.py crawl before politepol.com" 
print str(sys.argv)
if len(sys.argv) == 1:
   test1_get_inner_html()
elif len(sys.argv) > 2:
   if sys.argv[1] == 'crawl':
      if len(sys.argv) == 4:
          domain = sys.argv[3]
          crawl(sys.argv[2])
      else:
          raise Exception("Invalid argument count for crawl")
   elif sys.argv[1] == 'diff':
      if len(sys.argv) >= 4:
          fields = None
          if len(sys.argv) == 5:
              fields = sys.argv[4].split(',')
          diff(sys.argv[2], sys.argv[3], fields)
      else:
          raise Exception("Invalid argument count for diff")
   else:
      raise Exception("Unsupported operation %s" % sys.argv[1])
else:
   raise Exception("Invaid argument count")

print 'All tests are OK'
