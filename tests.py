from lxml import etree

from feed import element_to_string

def test1_get_inner_html():
    root = etree.fromstring('<a>1<b>2</b>3<c>4</c>5</a>')
    assert element_to_string(root) == '1<b>2</b>3<c>4</c>5'

test1_get_inner_html()

print 'All tests are OK'
