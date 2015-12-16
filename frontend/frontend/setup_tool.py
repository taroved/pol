I_TAGNAME = 0
I_ATTRS = 1
I_CHILDREN = 2
I_PARENT = 3 # not in use

def build_xpathes(item_tag_ids, html_json):
    shared_tag_stack = [];

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
    tag_stack = []

    def walk_by_tag(tag, depth):
        tag_stack.append(tag)
        if tag[I_TAGNAME] == parent_tag_names[depth]:
            if depth == len(parent_tag_names)-1: # is a tie
                tags.append((tag, list(tag_stack)))
            elif depth < len(parent_tag_names)-1:
                for subtag in tag[I_CHILDREN]:
                    walk_by_tag(subtag, depth+1)
        tag_stack.pop()
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


def _build_path(stack, target_stack):
    fork = None
    for fork_i in xrange(0, len(stack)):
        if stack[fork_i] == target_stack[fork_i]:
            fork = stack[fork_i]
        else:
            fork_i -= 1
            break

    path = []
    # shifts to parent; like '..' in xpath
    for i in xrange(fork_i, len(stack)):
        path.append(PathItem(go_parent=True))

    # address by children with indexes; like 'tag[n]' in xpath
    for i in xrange(fork_i, len(target_stack)):
        tag = target_stack[i]
        tag_name = tag[I_TAGNAME]
        parent = target_stack[i-1]
        tags = parent[I_CHILDREN]
        idx = 0
        for tag_ in tags:
            if tag_[I_TAGNAME] == tag_name:
                if tag_ == tag:
                    break
                idx += 1
        path.append(PathItem(child_tag=tag_name, child_index=idx))
        
    return path
   
def _find_tag(html_json, source_tag_info, path):
    tag = source_tag_info[0]
    tag_stack = source_tag_info[1]
    stack_i = len(tag_stack)-1

    for step in path:
        if step.go_parent:
            stack_i -= 1
            tag = tag_stack[stack_i]
        else:
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

    # get first item and get his path
    first_name, parent_stack = parent_stacks.popitem()
    parent_tag_names = [tag[I_TAGNAME] for tag in parent_stack]

    # find tags for first item
    tags = _find_tags_by_tag_names(html_json, parent_tag_names)

    # get pathes for another items
    selection_pathes = {}
    for name in parent_stacks:
        selection_pathes[name] = _build_path(parent_stack, parent_stacks[name])

    # get selection ids
    selection_ids = {name:[] for name in item_tag_ids}
    for tag_info in tags:
        ids = {}
        for name in selection_pathes:
            tag = _find_tag(html_json, tag_info, selection_pathes[name])
            if tag is not None:
                ids[name] = tag[I_ATTRS]['tag-id']
            else:
                ids = None
                break
        if ids is not None:
            selection_ids[first_name].append(tag_info[0][I_ATTRS]['tag-id'])
            for name in selection_pathes:
                selection_ids[name].append(ids[name])

    return selection_ids
