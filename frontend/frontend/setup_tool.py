I_TAGNAME = 0
I_ATTRS = 1
I_CHILDREN = 2
I_PARENT = 3 # not in use

def build_xpathes(item_tag_ids, html_json):
    shared_tag_stack = [];

def _get_fork_stack(stacks):
    first = stacks.itervalues().next() # just first stack
    for i in range(0, len(first)):
        tag = first[i]
        for name in stacks:
            if i >= len(stacks[name]) or tag != stacks[name][i]:
                return stacks[name][:i]
    return first
                
def _build_parent_stack(html_json, tag_id):
    tag_stack = []

    def walk_by_tag(tag):
        if (tag[I_ATTRS]['tag-id'] == tag_id):
            return True
        else:
            for subtag in tag[I_CHILDREN]:
                if walk_by_tag(subtag):
                    tag_stack.append(subtag)
                    return True
            return False
    
    walk_by_tag(html_json)
    
    tag_stack.append(html_json)
    
    return list(reversed(tag_stack))

def _find_tags_by_tag_names(html_json, parent_tag_names):
    tags = []

    def walk_by_tag(tag, depth):
        if tag[I_TAGNAME] == parent_tag_names[depth]:
            if depth == len(parent_tag_names)-1: # is a tie
                tags.append(tag)
            elif depth < len(parent_tag_names)-1:
                for subtag in tag[I_CHILDREN]:
                    walk_by_tag(subtag, depth+1)
    walk_by_tag(html_json, 0)
    return tags

# allusion to xpath
class PathItem:
    go_parent = False
    child_tag = None
    child_index = None

    def __init__(self, go_parent=False, child_tag=None, child_index=None):
        self.go_parent = go_parent
        self.child_tag = child_tag
        self.child_index = child_index

    def __repr__(self):
        return '..' if self.go_parent else '%s[%s]' % (self.child_tag, self.child_index+1)


def _build_path(stack):
    path = []
    for i in range(0, len(stack)-1):
        idx = 0
        tag = stack[i]
        search = stack[i+1] 
        for tag_ in tag[I_CHILDREN]:
            if tag_[I_TAGNAME] == search[I_TAGNAME]:
                if tag_ == search:
                    break
                idx += 1
        path.append(PathItem(child_tag=search[I_TAGNAME], child_index=idx))
    return path

def _find_tag(html_json, tag, path):
    for step in path:
        idx = step.child_index
        next = None
        for child in tag[I_CHILDREN]:
            if child[I_TAGNAME] == step.child_tag:
                if idx == 0:
                    next = child
                    break
                idx -= 1
        if next is None:
            return None
        tag = next
    return tag

def get_selection_tag_ids(item_tag_ids, html_json):
    parent_stacks = {}

    # buld parent stacks for every item name
    for name in item_tag_ids:
        tag_id = item_tag_ids[name]
        parent_stacks[name] = _build_parent_stack(html_json, tag_id)
    
    # get fork
    fork_stack = _get_fork_stack(parent_stacks)
    
    # get fork path
    fork_path = [tag[I_TAGNAME] for tag in fork_stack]
    # console log
    print 'Fork path: /'+'/'.join(fork_path)
    # get pathes for items
    fork_len = len(fork_path) - 1
    selection_pathes = {name:_build_path(parent_stacks[name][fork_len:]) for name in parent_stacks}
    # console log
    for name in selection_pathes:
        print name + ': ' + '/'.join([repr(p) for p in selection_pathes[name]])
    # get fork tags
    fork_tags = _find_tags_by_tag_names(html_json, fork_path)

    # get selection ids
    selection_ids = {name:[] for name in selection_pathes}
    for fork_tag in fork_tags:
        ids = {}
        for name in selection_pathes:
            tag = _find_tag(html_json, fork_tag, selection_pathes[name])
            if tag is not None:
                ids[name] = tag[I_ATTRS]['tag-id']
            else:
                ids = None
                break
        if ids is not None:
            for name in selection_pathes:
                selection_ids[name].append(ids[name])

    return selection_ids

def _path_stack_to_xpath(stack):
    stack

def build_xpathes_for_items(item_tag_ids, html_json):
    parent_stacks = {}

    # buld parent stacks for every item name
    for name in item_tag_ids:
        tag_id = item_tag_ids[name]
        parent_stacks[name] = _build_parent_stack(html_json, tag_id)
    
    # get fork
    fork_stack = _get_fork_stack(parent_stacks)
    
    # get fork path
    fork_path = [tag[I_TAGNAME] for tag in fork_stack]

    # get pathes for items
    fork_len = len(fork_path) - 1
    selection_pathes = {name:_build_path(parent_stacks[name][fork_len:]) for name in parent_stacks}

    # build xpathes
    feed_xpath = '/' + '/'.join(fork_path)
    item_xpathes = {}
    for name in selection_pathes:
        if selection_pathes[name]:
            item_xpathes[name] = '/'.join([repr(path_item) for path_item in selection_pathes[name]])
        else:
            item_xpathes[name] = '.'
        item_xpathes[name] += '/child::node()'

    return [feed_xpath, item_xpathes]
