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

ids = [1,2,3,5,6,8,44,54,99,100,101,103,113,118,120,123,124,131,132,133,134,135,136,137,138,139,140,141,142,143,144,145,146,147,148,149,150,151,152,153,154,155,156,157,158,159,160,161,162,163,165,166,167,168,169,170,171,172,173,174,175,176,177,178,179,180,181,182,183,184,185,186,187,188,189,190,191,192,193,194,195,196,197,198,199,200,201,202,203,204,205,206,207,208,209,210,211,212,213,214,215,216,217,218,219,220,221,222,223,224,225,226,228,229,230,231,232,233,234,235,236,237,238,239,240,241,242,243,244,245,246,247,249,250,251,252,253,255,257,258,259,260,261,262,263,264,265,266,267,268,269,270,271,272,273,274,275,276,277,278,279,280,281,282,283,284,285,286,287,288,289,290,291,292,293,294,295,296,297,298,299,300,301,302,303,304,305,306,307,308,309,310,311,312,313,314,315,316,317,318,319,320,321,322,323,324,325,326,327,328,329,330,331,332,333,334,335,336,337,338,339,340,341,342,343,345,346,347,348,349,350,351,352,353,354,355,356,357,358,359,360,361,362,363,364,365,366,367,368,369,370,371,372,373,374,375,376,377,378,379,380,381,382,383,384,385,386,387,388,389,390,391,392,393,394,395,396,397,398,399,400,401,402,403,404,405,406,407,408,409,410] # 254 timeout 344 pp gatevway timeout
domain = "politepol.com"

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
        title, link, items = parse_feed(text)
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
