from __future__ import annotations
import json
from typing import List

# Node Class.
class Node():
    def  __init__(self,
                  keys     : List[int] = None,
                  values   : List[str] = None,
                  children : List[Node] = None,
                  parent   : Node = None):
        self.keys     = keys
        self.values   = values
        self.children = children
        self.parent   = parent
        self.k        = len(keys)
        self.c        = 0

class Btree():
    def  __init__(self,
                  m    : int  = None,
                  root : Node = None):
        self.m    = m
        self.root = root

    def dump(self) -> str:
        def _to_dict(node) -> dict:
            return {
                "keys": node.keys,
                "values": node.values,
                "children": [(_to_dict(child) if child is not None else None) for child in node.children]
            }
        if self.root == None:
            dict_repr = {}
        else:
            dict_repr = _to_dict(self.root)
        return json.dumps(dict_repr,indent=2)

    # Insert
    def insert(self, key: int, value: str):
        # Insert into an empty tree
        if self.root is None:
            self.root = Node([key], [value], [None, None])
            return
        
        # Find the index to insert the key/value and or the
        # index to recurse down further for searching
        i = 0
        while i < self.root.k and key > self.root.keys[i]:
            i += 1

        # If the level of leaves is reached then attempt to insert
        # Otherwise recurse to the appropriate level
        if self.root.c == 0:
            self.root.keys.insert(i, key)
            self.root.values.insert(i, value)
            self.root.k += 1
            self.root.children = [None] * (self.root.k + 1)

            # If the insert causes an overfull node then restructure
            if self.root.k > self.m - 1:
                self.restructure_insert()
            return

        # Recurse down the b-tree
        Btree(self.m, self.root.children[i]).insert(key, value)
        # If the parent is overfull then we restructure it
        if self.root.k > self.m - 1:
            self.restructure_insert()

    # Delete
    def delete(self, key: int):
        # Find the index of the key/value to delete and or 
        # the index to recurse down further for searching
        i = 0
        while i < self.root.k and key > self.root.keys[i]:
            i += 1
        # Check whether we have found the key to delete
        if i < self.root.k and self.root.keys[i] == key:
            if self.root.c == 0: # Child node
                # Remove the key/value if it exists at a child
                self.root.keys.remove(self.root.keys[i])
                self.root.values.remove(self.root.values[i])
                self.root.k -= 1
                self.root.children = [None] * (self.root.k + 1)
            else: # Internal node
                # Find inorder predecessor to replace the current key/value
                k, v = Btree(self.m, self.root.children[i + 1]).inorder_successor()
                self.root.keys[i] = k
                self.root.values[i] = v
                # Delete the inorder successor from its leaf node
                Btree(self.m, self.root.children[i + 1]).delete(k)
        else:
            Btree(self.m, self.root.children[i]).delete(key)
        # Restructure if the keys are below the minimum
        min_keys = 1 if not self.root.parent else (self.m / 2) - 1 if self.m % 2 == 0 else int((self.m / 2) + 1) - 1
        if self.root.k < min_keys:
            self.restructure_delete()
        return

    # Search
    def search(self, key: int) -> List[int]:
        # Build a list containing the child indicies followed from the root
        # to the target key with the value append at the end
        def search_list(tree: Btree, key: int):
            # Find the index that corresponds to the target key
            i = 0
            while i < tree.root.k and key > tree.root.keys[i]:
                i += 1

            if i < tree.root.k and tree.root.keys[i] == key:
                return [tree.root.values[i]]
            
            child = Btree(tree.m, tree.root.children[i])
            return [i] + search_list(child, key)
        
        return json.dumps(search_list(self, key))

    # -------------------------------------------------- #
    # ----------------- Helper Methods ----------------- #
    # -------------------------------------------------- #

    # Restructure Insert
    def restructure_insert(self):
        can_rotate_left, can_rotate_right, s = self.can_rotate_insert()

        if can_rotate_left:
            T = self.root.k + self.root.parent.children[s - 1].k
            N = T / 2 if T % 2 == 0 else int((T / 2) + 1)
            # Perform a left rotation until number of keys is ceil T/2
            while self.root.k > N:
                self.rotate_left(0, s, s - 1)
        elif can_rotate_right:
            T = self.root.k + self.root.parent.children[s + 1].k
            N = T / 2 if T % 2 == 0 else int((T / 2) + 1)
            # Perform a rotation rotation until number of keys is ceil T/2
            while self.root.k > N:
                self.rotate_right(self.root.k - 1, s, s + 1)
        else: # Split on the root if rotations are not possible
            self.split()

    # Restructure Delete
    def restructure_delete(self):
        can_rotate_left, can_rotate_right, s = self.can_rotate_delete()
        if can_rotate_right:
            T = self.root.k + self.root.parent.children[s - 1].k
            N = int(T / 2)# if T % 2 == 0 else int(T / 2)
            # Perform a left rotation until number of keys is floor T/2
            while self.root.k < N:
                self.rotate_right(self.root.parent.children[s - 1].k - 1, s - 1, s)
        elif can_rotate_left:
            T = self.root.k + self.root.parent.children[s + 1].k
            N = int(T / 2)# if T % 2 == 0 else int(T / 2)
            # Perform a left rotation until number of keys is floor T/2
            while self.root.k < N:
                self.rotate_left(0, s + 1, s)
        else: # Merge on the root if rotations are not possible
            self.merge()

    # Rotation checker for insert
    def can_rotate_insert(self) -> List[bool, bool, int]:
        # Rotation is not possible without a root
        if self.root.parent is None:
            return False, False , -1
        
        # Find the index for the overfull node in the parent's children list
        i = 0
        while i < self.root.parent.c and self.root.parent.children[i].k < self.m:
            i += 1

        can_rotate_left = i - 1 >= 0 and self.root.parent.children[i - 1].k < self.m - 1
        can_rotate_right = i + 1 < self.root.parent.c and self.root.parent.children[i + 1].k < self.m - 1

        return [can_rotate_left, can_rotate_right, i]
    
    # Rotation checker for delete
    def can_rotate_delete(self) -> List[bool, bool, int]:
        # Rotation is not possible without a root
        if self.root.parent is None:
            return False, False , -1
        
        # Find the index for the underfull node in the parent's children list
        i = 0
        min_keys = int(self.m / 2) - 1 if self.m % 2 == 0 else int((self.m / 2) + 1) - 1
        while i < self.root.parent.c and self.root.parent.children[i].k > min_keys - 1:
            i += 1

        can_rotate_left = i + 1 < self.root.parent.c and self.root.parent.children[i + 1].k > min_keys
        can_rotate_right = i - 1 >= 0 and self.root.parent.children[i - 1].k > min_keys

        return [can_rotate_left, can_rotate_right, i]

    # Left rotation
    def rotate_left(self, key_idx: int, src_idx: int, dest_idx: int):
        # Parent of the node being rotated
        parent = self.root.parent

        # Store the keys and values to be rotated
        key = parent.children[src_idx].keys[key_idx]
        val = parent.children[src_idx].values[key_idx]

        # Parent index is the current subtree's index minus one
        parent_key = parent.keys[src_idx - 1]
        parent_val = parent.values[src_idx - 1]

        # Move the key/value from the original node to the root
        parent.keys[src_idx - 1] = key
        parent.values[src_idx - 1] = val

        # Delete the key/value from the original node
        parent.children[src_idx].keys.pop(key_idx)
        parent.children[src_idx].values.pop(key_idx)
        parent.children[src_idx].k -= 1

        # Move the parent key/value to the left adjacent child
        # Parent key/value always go to the end of the list
        parent.children[dest_idx].keys.insert(parent.children[dest_idx].k, parent_key)
        parent.children[dest_idx].values.insert(parent.children[dest_idx].k, parent_val)
        parent.children[dest_idx].k += 1

        # The subtree of the original node moves to the left adjacent child
        # It will always be inserted at the end of the list of children in the
        # adjacent child
        if parent.children[src_idx].children[0]:
            subtree = parent.children[src_idx].children[0]
            parent.children[src_idx].children.pop(0)
            parent.children[src_idx].c -= 1
            parent.children[dest_idx].children.insert(parent.children[dest_idx].c, subtree)
            parent.children[dest_idx].children[parent.children[dest_idx].c].parent = parent.children[dest_idx]
            parent.children[dest_idx].c += 1

        if self.root.c == 0:
            parent.children[src_idx].children = [None] * (parent.children[src_idx].k + 1)
            parent.children[dest_idx].children = [None] * (parent.children[dest_idx].k + 1)

        for child in parent.children:
            child.parent = parent

    # Right rotation
    def rotate_right(self, key_idx: int, src_idx: int, dest_idx: int):
        # Parent of the node being rotated
        parent = self.root.parent

        # Store the keys and values to be rotated
        key = parent.children[src_idx].keys[key_idx]
        val = parent.children[src_idx].values[key_idx]
        
        # Parent index is the current subtree's index
        parent_key = parent.keys[src_idx]
        parent_val = parent.values[src_idx]

        # Move the key/value from the original node to the root
        parent.keys[src_idx] = key
        parent.values[src_idx] = val

        # Delete the key/value from the original node
        parent.children[src_idx].keys.pop(key_idx)
        parent.children[src_idx].values.pop(key_idx)
        parent.children[src_idx].k -= 1

        # Move the parent key/value to the right adjacent child
        # Parent key/value always go to the front of the list
        parent.children[dest_idx].keys.insert(0, parent_key)
        parent.children[dest_idx].values.insert(0, parent_val)
        parent.children[dest_idx].k += 1

        # The subtree of the original node moves to the right adjacent child
        # It will always be inserted to the front of the list of children in the
        # adjacent child
        if parent.children[src_idx].children[parent.children[src_idx].c - 1]:
            # The node key being rotated may not always have a child
            subtree = parent.children[src_idx].children[parent.children[src_idx].c - 1]
            parent.children[src_idx].children.pop(parent.children[src_idx].c - 1)
            parent.children[src_idx].c -= 1
            parent.children[dest_idx].children.insert(0, subtree)
            parent.children[dest_idx].children[0].parent = parent.children[dest_idx]
            parent.children[dest_idx].c += 1

        if self.root.c == 0:
            parent.children[src_idx].children = [None] * (parent.children[src_idx].k + 1)
            parent.children[dest_idx].children = [None] * (parent.children[dest_idx].k + 1)

        for child in parent.children:
            child.parent = parent

    # Split
    def split(self):
        # Store median key and value
        num_keys = self.root.k
        m_idx = int(num_keys / 2) - 1 if num_keys % 2 == 0 else int((num_keys - 1) / 2)
        m = self.root.keys[m_idx]
        v = self.root.values[m_idx]

        # Keys left of the median are a new node
        left_keys = self.root.keys[:m_idx]
        left_values = self.root.values[:m_idx]
        left_children = [None] * (m_idx + 1) if self.root.c == 0 else self.root.children[:m_idx+1]
        left_node = Node(left_keys, left_values, left_children)
        left_node.c = 0 if self.root.c == 0 else len(left_children)
        # Update children parent references
        i = 0
        while i < left_node.c:
            left_node.children[i].parent = left_node
            i += 1
        
        # Keys right of the median are a new node
        right_keys = self.root.keys[m_idx+1:]
        right_values = self.root.values[m_idx+1:]
        right_children = [None] * (len(right_keys) + 1) if self.root.c == 0 else self.root.children[m_idx+1:]
        right_node = Node(right_keys, right_values, right_children)
        right_node.c = 0 if self.root.c == 0 else len(right_children)
        # Update children parent references
        i = 0
        while i < right_node.c:
            right_node.children[i].parent = right_node
            i += 1

        # Perform split routine
        if self.root.parent is None:
            root = Node([m], [v], [left_node, right_node])
            # Update key count and children count
            root.c = 2
            # Update the root for the left and right node
            left_node.parent = root
            right_node.parent = root
            self.root = root
            for child in root.children:
                child.parent = root
        else:
            parent = self.root.parent
            
            # Move the median key/value from the original node to the parent
            i = 0
            while i < parent.k and m > parent.keys[i]:
                i += 1
            parent.keys.insert(i, m)
            parent.values.insert(i, v)
            parent.k += 1
            
            # Delete the median element from the original node
            parent.children[i].keys.pop(m_idx)
            parent.children[i].values.pop(m_idx)
            parent.children[i].k -= 1

            # Delete the original node from the parent subtree
            parent.children.pop(i)

            # Add the new left and right children to the list of children
            parent.children.insert(i, left_node)
            parent.children.insert(i + 1, right_node)
            parent.c += 1

            # Update the parent for the children
            for child in parent.children:
                child.parent = parent

    # Merge
    def merge(self):
        # Shrink the height of the tree if no root exists
        # The single child becomes the new root
        i = 0
        if not self.root.parent:
            self.root = self.root.children[i]
            self.root.parent = None
            return

        parent = self.root.parent

        # Find the index of the current subtree
        min_keys = int(self.m / 2) - 1 if self.m % 2 == 0 else int((self.m / 2) + 1) - 1
        while i < parent.c and parent.children[i].k > min_keys - 1:
            i += 1

        merged_keys = self.root.keys
        merged_vals = self.root.values
        merged_children = []
        if i - 1 >= 0: # Merge left
            sep_key = parent.keys[i - 1]
            sep_val = parent.values[i - 1]

            # Delete demoted key/value form the parent
            parent.keys.pop(i - 1)
            parent.values.pop(i - 1)

            # Merge the current node with the left node
            merged_keys = parent.children[i - 1].keys + [sep_key] + merged_keys
            merged_vals = parent.children[i - 1].values + [sep_val] + merged_vals
            merged_children = [None] * (len(merged_keys) + 1) if self.root.c == 0 else parent.children[i - 1].children + self.root.children
            
            # Delete the merged nodes from the parent
            parent.children.pop(i - 1)
            parent.children.pop(i - 1)
        else: # Merge right
            sep_key = parent.keys[i]
            sep_val = parent.values[i]

            # Delete demoted key/value form the parent
            parent.keys.pop(i)
            parent.values.pop(i)

            # Merge the current node with the right node
            merged_keys = merged_keys + [sep_key] + parent.children[i + 1].keys
            merged_vals = merged_vals + [sep_val] + parent.children[i + 1].values
            merged_children = [None] * (len(merged_keys) + 1) if self.root.c == 0 else self.root.children + parent.children[i + 1].children

            # Delete the merged nodes from the parent
            parent.children.pop(i)
            parent.children.pop(i)
        
        # The root losses one key and one child
        parent.k -= 1
        parent.c -= 1
        
        merged_node = Node(merged_keys, merged_vals, merged_children, self.root.parent)
        merged_node.c = 0 if self.root.c == 0 else len(merged_children)

        # Insert the merged node into the correct position
        parent.children.insert(i - 1, merged_node) if i - 1 >= 0 else parent.children.insert(i, merged_node)
        
        # Update the parent for the merged children
        if merged_node.c > 0:
            for c in merged_children:
                c.parent = merged_node

        # Update the parent for the children
        for child in parent.children:
            child.parent = parent

    def inorder_successor(self) -> tuple[int,str]:
        if self.root.c == 0:
            return self.root.keys[0], self.root.values[0]
    
        child = Btree(self.m, self.root.children[0])
        return child.inorder_successor()