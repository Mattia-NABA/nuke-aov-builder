"""
Test script for AOV Builder - Nuke 17.0v1 - WORKING
"""

import nuke
import re
from collections import defaultdict

# ===== CONFIG =====
AOV_CATEGORIES = {
    'DIFFUSE': ['diffuse_direct', 'diffuse_indirect', 'diffuse*'],
    'SPECULAR': ['specular_direct', 'specular_indirect', 'specular*'],
    'TRANSMISSION': ['transmission_direct', 'transmission_indirect', 'transmission*'],
    'SSS': ['sss_direct', 'sss_indirect', 'sss*'],
    'VOLUME': ['volume*', 'volumetric*'],
    'EMISSION': ['emission*'],
}

MERGE_TYPE = 'plus'
CREATE_BACKDROPS = True

DOT_X_OFFSET = 180
SHUFFLE_X_OFFSET = 360
CATEGORY_SPACING = 620
SHUFFLE_SPACING = 140
VERTICAL_CATEGORY_SPACING = 220
BACKDROP_PADDING_X = 100
BACKDROP_PADDING_TOP = 100
BACKDROP_PADDING_BOTTOM = 120
SHUFFLE_BACKDROP_PADDING_X = 45
SHUFFLE_BACKDROP_PADDING_TOP = 45
SHUFFLE_BACKDROP_PADDING_BOTTOM = 55

# ===== UTILITY FUNCTIONS =====
def match_pattern(aov, pattern):
    """Check whether an AOV matches a pattern."""
    if '*' in pattern:
        regex_pattern = pattern.replace('*', '.*')
        return re.match(f'^{regex_pattern}$', aov) is not None
    return aov == pattern

def classify_aovs(aov_list):
    """Classify AOVs into categories."""
    aov_groups = defaultdict(list)
    classified = set()
    unknown_aovs = []

    for category, patterns in AOV_CATEGORIES.items():
        for aov in aov_list:
            if aov in classified:
                continue
            for pattern in patterns:
                if match_pattern(aov, pattern):
                    aov_groups[category].append(aov)
                    classified.add(aov)
                    break

    unknown_aovs = [aov for aov in aov_list if aov not in classified]
    return aov_groups, unknown_aovs

def print_summary(aov_groups, unknown_aovs):
    """Print the AOV summary."""
    print("\n" + "="*50)
    print("AOV BUILDER - SUMMARY")
    print("="*50)
    
    for category in sorted(aov_groups.keys()):
        aovs = aov_groups[category]
        if aovs:
            print(f"\n{category} ({len(aovs)})")
            for aov in aovs:
                print(f"  - {aov}")
    
    if unknown_aovs:
        print(f"\nUNKNOWN ({len(unknown_aovs)})")
        for aov in unknown_aovs:
            print(f"  - {aov}")
    
    print("\n" + "="*50 + "\n")

# ===== NODE CREATION =====
def create_dot(input_node, xpos, ypos):
    """Create a Dot to distribute the Read node neatly."""
    dot = nuke.nodes.Dot(inputs=[input_node])
    dot.setXYpos(xpos, ypos)
    return dot

def create_shuffle(aov_name, input_node, xpos, ypos):
    """Create a Shuffle2 node to extract an AOV."""
    shuffle = nuke.nodes.Shuffle2(inputs=[input_node])
    shuffle.knob('in1').setValue(aov_name)
    shuffle.knob('name').setValue(f'Shuffle_{aov_name}')
    shuffle.setXYpos(xpos, ypos)
    return shuffle

def create_merge(category, input_nodes, xpos, ypos):
    """Create a Merge node to combine AOVs."""
    if len(input_nodes) == 1:
        return input_nodes[0]
    
    merge = nuke.nodes.Merge2(inputs=[input_nodes[0], input_nodes[1]])
    merge.knob('operation').setValue(MERGE_TYPE)
    merge.knob('name').setValue(f'Merge_{category}')
    
    for i in range(2, len(input_nodes)):
        merge = nuke.nodes.Merge2(inputs=[merge, input_nodes[i]])
        merge.knob('operation').setValue(MERGE_TYPE)
    
    merge.setXYpos(xpos, ypos)
    return merge

def create_backdrop(label, nodes, padding_x, padding_top, padding_bottom, z_order):
    """Create a Backdrop around the nodes."""
    if not nodes:
        return None
    
    min_x = min(node.xpos() for node in nodes)
    max_x = max(node.xpos() + node.screenWidth() for node in nodes)
    min_y = min(node.ypos() for node in nodes)
    max_y = max(node.ypos() + node.screenHeight() for node in nodes)
    
    # Use BackdropNode for Nuke 17
    backdrop = nuke.nodes.BackdropNode(
        xpos=min_x - padding_x,
        ypos=min_y - padding_top,
        bdwidth=max_x - min_x + (padding_x * 2),
        bdheight=max_y - min_y + padding_top + padding_bottom,
        z_order=z_order
    )
    backdrop.knob('label').setValue(label)
    
    return backdrop

# ===== MAIN =====
def build_aov_network_manual():
    """Build the AOV network - Manual version."""
    print("\n[START] AOV Builder v0.1")
    
    selected = nuke.selectedNodes()
    if not selected:
        nuke.message("Select a multilayer Read node")
        return
    
    read_node = selected[0]
    print(f"[INFO] Selected node: {read_node.name()}")
    
    if read_node.Class() != 'Read':
        nuke.message("The selected node is not a Read node")
        return
    
    # Ask the user to enter the AOVs manually
    aov_input = nuke.getInput(
        "Enter comma-separated AOVs:\n(e.g. diffuse_direct, diffuse_indirect, specular_direct)",
        "diffuse_direct, diffuse_indirect, specular_direct, specular_indirect"
    )
    
    if not aov_input:
        return
    
    # Parse the input
    aov_list = [aov.strip() for aov in aov_input.split(',')]
    aov_list = [aov for aov in aov_list if aov]
    
    print(f"[INFO] Entered AOVs: {aov_list}")
    
    # Classify
    aov_groups, unknown_aovs = classify_aovs(aov_list)
    print_summary(aov_groups, unknown_aovs)
    
    if not aov_groups:
        nuke.message("No AOVs classified")
        return
    
    # Build the network
    print("[BUILD] Starting network creation...")
    xpos = read_node.xpos()
    start_y = read_node.ypos() + 220
    category_y = start_y
    category_outputs = []
    
    for category in sorted(aov_groups.keys()):
        aov_list_cat = aov_groups[category]
        if not aov_list_cat:
            continue
        
        print(f"[BUILD] Creating {category} with {len(aov_list_cat)} AOVs...")
        
        dot_nodes = []
        shuffle_nodes = []
        for index, aov in enumerate(aov_list_cat):
            branch_y = category_y + (index * SHUFFLE_SPACING)
            dot = create_dot(read_node, xpos, branch_y)
            dot_nodes.append(dot)
            shuffle = create_shuffle(aov, dot, xpos + SHUFFLE_X_OFFSET, branch_y)
            shuffle_nodes.append(shuffle)

            create_backdrop(
                aov.upper(),
                [dot, shuffle],
                SHUFFLE_BACKDROP_PADDING_X,
                SHUFFLE_BACKDROP_PADDING_TOP,
                SHUFFLE_BACKDROP_PADDING_BOTTOM,
                -1
            )
        
        merge_y = int(round(category_y + (len(shuffle_nodes) * SHUFFLE_SPACING) + 100))
        merge = create_merge(category, shuffle_nodes, xpos + SHUFFLE_X_OFFSET, merge_y)
        category_outputs.append(merge)
        
        if CREATE_BACKDROPS:
            all_nodes = dot_nodes + shuffle_nodes + [merge]
            create_backdrop(
                category,
                all_nodes,
                BACKDROP_PADDING_X,
                BACKDROP_PADDING_TOP,
                BACKDROP_PADDING_BOTTOM,
                -2
            )
        
        category_y = merge_y + VERTICAL_CATEGORY_SPACING
    
    if category_outputs:
        beauty = create_merge('BEAUTY', category_outputs, xpos + SHUFFLE_X_OFFSET, category_y)
        print(f"\n[SUCCESS] Network created!")
        print(f"[SUCCESS] Categories: {len(aov_groups)}")
        print(f"[SUCCESS] Nodes created successfully")

# Esegui
build_aov_network_manual()