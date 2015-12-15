

def build_xpathes(item_tag_ids, html_json):
    shared_tag_stack = [];

def build_parent_stack(html_json, tag_id):
    tag_stack = []

    def walk_by_tag(tag):
        if (tag[1]['tag-id'] == tag_id):
            return True
        else:
            for subtag in tag[2]:
                if walk_by_tag(subtag):
                    tag_stack.append(subtag)
                    return True
            return False
    
    walk_by_tag(html_json)
    return list(reversed(tag_stack))

def find_tags_by_tag_names(html_json, parent_tag_names):

    tag_ids = []

    def walk_by_tag(tag):
        depth = len(tag_ids)
        if tag[0] == parent_tag_names[depth]:
            if depth == len(parent_tag_names)-1: # is a tie
                tag_ids.append(tag[1]['tag-id'])
            elif depth < len(parent_tag_names):
                for subtag in tag[2]:
                    walk_by_tag(subtag)
    return tag_ids

# allusion to xpath
class PathItem:
    go_parent = False
    go_child_tag = None
    child_index = None

def _build_path(stack, target_stack):
    fork = None
    for fork_i in xrange(0, len(stack)):
        if stack[fork_i] == target_stack[fork_i]:
            fork = stack[fork_i]
        else:
            break
     
    path = []
    for i in xrange(fork_i, len(stack)):
        path.append(PathItem(go_parent=True))

    for i in xrange(fork_i, len(target_stack)-1):
        tag = target_stack[i]
        tag_name = tag[0]
        parent = target_stack[i-1]
        children = parent[2]
        idx = 0
        for j in xrange(0, len(children)):
            if children[j][0] == tag_name:
                idx += 1
                if children[j] == tag:
                    break
        path.append(PathItem(go_child_tag=tag_name, child_index=idx))
        
    return path
    

def get_selection_tag_ids(item_tag_ids, html_json):
    parent_stacks = {}

    import pdb; pdb.set_trace()
    # buld parent stacks for every item name
    for name in item_tag_ids:
        tag_id = item_tag_ids[name]
        parent_stacks[name] = build_parent_stack(html_json, tag_id)

    # get first item and get his path
    first_name, parent_stack = parent_stacks.popitem()
    parent_tag_names = [tag[0] for tag in parent_stack]

    # find tags for first item
    tags = find_tags_by_tag_names(html_json, parent_tag_names)

    # get pathes for another items
    selection_pathes = {}
    for name in parent_stacks:
        selection_pathes[name] = _build_path(parent_stack, parent_stacks[name])

    # get selection ids
    selection_ids = [name:[] for name in item_tag_ids]
    for source_tag in tags:
        ids = []
        for name in selection_pathes:
            tag = _find_tag(html_json, source_tag, selection_path[name])
            if tag is not None:
                ids[name] = tag[T_ATTRS]['tag-id'])
            else
                ids = None
                break
        if ids is not None:
            selection_ids[first_name].append(source_tag[T_ATTRS]['tag-id'])
            for name in selection_pathes:
                selection_ids[name].append(ids[name])

    return selection_ids

    return { name: tag_ids }
