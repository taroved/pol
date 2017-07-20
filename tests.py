from lxml import etree
import sys
import requests

from feed import element_to_unicode

def element_to_string(element):
    if isinstance(element, basestring): # attribute
        return element

    s = [element.text] if element.text else []
    for sub_element in element:
        s.append(etree.tostring(sub_element))
    return ''.join(s)

def test1_get_inner_html():
    root = etree.fromstring('<a>1<b>2</b>3<c>4</c>5</a>')
    assert element_to_unicode(root, 'utf-8') == u'1<b>2</b>3<c>4</c>5'

ids = [1,2,3,5,6,54,100,101,113,118,123,124,131,132,133,134,135,136,137,138,139,140,141,142,143,144,145,146,147,148,149,150,151,152,153,154,155,156,157,158,159,160,161,162,163,166,167]
domain = "politepol.com"

def parse_feed(text):
    ch = etree.fromstring(text).xpath('/rss/channel')
    title = ch[0].xpath('title')[0].text
    items = ch[0].xpath('item')
    return [title.encode('utf-8'), items]

def crawl(extention):
    number = 0
    for id in ids:
        print "ID: %s (%s of %s)" % (id, number, len(ids))
        r = requests.get("http://%s/feed/%s" % (domain, id))
        text = r.text.encode('utf-8')
        with open("tests/%s.%s" % (id, extention), 'w') as f:
            f.write(text)
        title, items = parse_feed(text)
        print "Title: %s" % title
        print "Items count: %s" % len(items)
        number += 1

def diff(ext1, ext2):
    diff = []
    number = 0
    for id in ids:
        print "ID: %s" % (id,)
        text1 = None
        with open("tests/%s.%s" % (id, ext1), 'r') as f:
            text1 = f.read()
        text2 = None
        with open("tests/%s.%s" % (id, ext2), 'r') as f:
            text2 = f.read()
	
	if text1 == text2:
            print "Identical"
        else:
            diff.append(id)
            posts_diff = 0
            with open("tests/%s.diff" % (id,), 'w') as f:
		title1, items1 = parse_feed(text1)
		title2, items2 = parse_feed(text2)
		if title1 != title2:
                    print "Different titles"
                    f.write("<<<<<<<<<<<<<<< Different titles >>>>>>>>>>>>>>>\n")
                    f.write(">>>>>>>>>>>>>>> %s.%s  <<<<<<<<<<<<<\n" % (id, ext1))
                    f.write(title1 + "\n")
                    f.write(">>>>>>>>>>>>>>> %s.%s  <<<<<<<<<<<<<\n" % (id, ext2))
                    f.write(title2 + "\n")
                posts1 = {}
                posts2 = {}
                if len(items1) != len(items2):
                    print "Different post count: %s vs %s" % (len(items1), len(item2))
                    f.write("<< Different posts count: %s.%s:%s vs %s.%s:%s >>\n" % (id, ext1, len(items1), id, ext2, len(item2)))
                for post in items1:
                    posts1[element_to_string(post)] = True
                for post in items2:
                    posts2[element_to_string(post)] = True
                
                for post in items1:
                    if not (element_to_string(post) in posts2):
                        posts_diff += 1
                        f.write("<<<<<<<<<<<<<<< Different posts (%s) >>>>>>>>>>>>>>>\n" % posts_diff)
                        f.write(">>>>>>>>>>>>>>> %s.%s  <<<<<<<<<<<<<\n" % (id, ext1))
                        f.write(element_to_string(post) + "\n")
                        f.write(">>>>>>>>>>>>>>> %s.%s  <<<<<<<<<<<<<\n" % (id, ext2))
                        f.write("*** Not found ***\n")
  
                for post in items2:
                    if not (element_to_string(post) in posts1):
                        posts_diff += 1
                        f.write("<<<<<<<<<<<<<<< Different posts (%s) >>>>>>>>>>>>>>>\n" % posts_diff)
                        f.write(">>>>>>>>>>>>>>> %s.%s  <<<<<<<<<<<<<\n" % (id, ext1))
                        f.write("*** Not found ***\n")
                        f.write(">>>>>>>>>>>>>>> %s.%s  <<<<<<<<<<<<<\n" % (id, ext2))
                        f.write(element_to_string(post) + "\n")
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
      if len(sys.argv) == 4:
          diff(sys.argv[2], sys.argv[3])
      else:
          raise Exception("Invalid argument count for diff")
   else:
      raise Exception("Unsupported operation %s" % sys.argv[1])
else:
   raise Exception("Invaid argument count")

print 'All tests are OK'
