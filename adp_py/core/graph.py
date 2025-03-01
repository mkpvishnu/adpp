"""
@ai-metadata {
    "domain": "knowledge-graph",
    "description": "Knowledge graph builder for visualizing code relationships using ADP metadata",
    "dependencies": ["parser.py", "schema.py"]
}
"""

import os
import json
from enum import Enum
from typing import Dict, List, Any, Optional, Set, Tuple, Union
from dataclasses import dataclass, field
import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
import graphviz

from adp_py.core.parser import ParsedFile, CodeScope, ADPMetadata
from adp_py.core.schema import get_schema, ADPSchema


class NodeType(str, Enum):
    """Types of nodes in the knowledge graph."""
    SERVICE = "service"
    MODULE = "module"
    CLASS = "class"
    FUNCTION = "function"
    METHOD = "method"
    VARIABLE = "variable"
    FILE = "file"
    DOMAIN = "domain"
    CONCEPT = "concept"
    TEAM = "team"
    TECH_DEBT = "tech_debt"
    PERFORMANCE = "performance"
    DATA = "data"


class EdgeType(str, Enum):
    """Types of edges in the knowledge graph."""
    CONTAINS = "contains"
    USES = "uses"
    DEPENDS_ON = "depends_on"
    CALLS = "calls"
    IMPLEMENTS = "implements"
    EXTENDS = "extends"
    REFERENCES = "references"
    OWNED_BY = "owned_by"
    RELATED_TO = "related_to"
    HAS_TECH_DEBT = "has_tech_debt"
    HAS_PERFORMANCE_ISSUE = "has_performance_issue"
    PROCESSES_DATA = "processes_data"


@dataclass
class Node:
    """A node in the knowledge graph."""
    id: str
    type: Union[NodeType, str]  # Can be either an enum value or a custom string type
    label: str
    short_label: str = None
    attributes: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        type_value = self.type.value if isinstance(self.type, NodeType) else self.type
        return {
            "id": self.id,
            "type": type_value,
            "label": self.label,
            "short_label": self.short_label or self.label,
            "attributes": self.attributes
        }


@dataclass
class Edge:
    """An edge in the knowledge graph."""
    source: str
    target: str
    type: Union[EdgeType, str]  # Can be either an enum value or a custom string type
    attributes: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        type_value = self.type.value if isinstance(self.type, EdgeType) else self.type
        return {
            "source": self.source,
            "target": self.target,
            "type": type_value,
            "attributes": self.attributes
        }


@dataclass
class KnowledgeGraph:
    """Knowledge graph representation of code and its metadata."""
    nodes: Dict[str, Node] = field(default_factory=dict)
    edges: List[Edge] = field(default_factory=list)
    custom_node_types: Set[str] = field(default_factory=set)
    custom_edge_types: Set[str] = field(default_factory=set)
    
    def add_node(self, node: Node) -> None:
        """
        Add a node to the graph.
        
        Args:
            node: The node to add.
        """
        self.nodes[node.id] = node
    
    def add_edge(self, edge: Edge) -> None:
        """
        Add an edge to the graph.
        
        Args:
            edge: The edge to add.
        """
        self.edges.append(edge)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "nodes": [node.to_dict() for node in self.nodes.values()],
            "edges": [edge.to_dict() for edge in self.edges]
        }
    
    def to_json(self, file_path: str) -> None:
        """
        Export the graph to a JSON file.
        
        Args:
            file_path: Path to the output file.
        """
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=2)
    
    def to_networkx(self) -> nx.DiGraph:
        """
        Convert to NetworkX graph.
        
        Returns:
            A NetworkX DiGraph object.
        """
        G = nx.DiGraph()
        
        # Add nodes with attributes
        for node_id, node in self.nodes.items():
            G.add_node(
                node_id,
                label=node.label,
                type=node.type,
                **node.attributes
            )
        
        # Add edges with attributes
        for edge in self.edges:
            G.add_edge(
                edge.source,
                edge.target,
                type=edge.type,
                **edge.attributes
            )
        
        return G
    
    def visualize_matplotlib(self, output_path: str = None, figsize: Tuple[int, int] = (16, 10), 
                            title: str = "ADP Knowledge Graph") -> None:
        """
        Visualize the graph using matplotlib with hierarchical layout.
        
        Args:
            output_path: Path to save the visualization. If None, the graph is displayed.
            figsize: Size of the figure.
            title: Title of the visualization.
        """
        G = self.to_networkx()
        
        # Set node labels to use short_label if available
        node_labels = {}
        for node_id, data in G.nodes(data=True):
            if 'short_label' in self.nodes[node_id].attributes:
                node_labels[node_id] = self.nodes[node_id].attributes['short_label']
            elif hasattr(self.nodes[node_id], 'short_label') and self.nodes[node_id].short_label:
                node_labels[node_id] = self.nodes[node_id].short_label
            else:
                node_labels[node_id] = data.get('label', node_id)
        
        # Create color map for node types
        node_types = {data['type'] for _, data in G.nodes(data=True)}
        colors = plt.cm.tab20(range(len(node_types)))
        color_map = {t: c for t, c in zip(node_types, colors)}
        
        # Get node colors
        node_colors = [color_map[G.nodes[n]['type']] for n in G.nodes]
        
        # Create hierarchical layout based on node types and their relationships
        # Files at the top, then domains, services, classes, functions, variables
        layer_types = {
            "file": 0,
            "domain": 1,
            "service": 2, 
            "team": 2,
            "class": 3,
            "function": 4, 
            "method": 4,
            "variable": 5,
            "tech_debt": 6,
            "performance": 6,
            "data": 6
        }
        
        # Assign positions based on layers
        pos = {}
        nodes_by_layer = {}
        
        # Group nodes by layer
        for node, data in G.nodes(data=True):
            layer = layer_types.get(data['type'], 0)
            if layer not in nodes_by_layer:
                nodes_by_layer[layer] = []
            nodes_by_layer[layer].append(node)
        
        # Calculate maximum width to scale the layout
        max_layer_size = max(len(nodes) for nodes in nodes_by_layer.values()) if nodes_by_layer else 0
        width_scale = max(12, max_layer_size * 1.5)
        
        # Position nodes in each layer
        for layer, nodes in nodes_by_layer.items():
            y = -layer * 2  # Negative to have top-to-bottom layout with more spacing
            for i, node in enumerate(sorted(nodes)):
                # Evenly space nodes horizontally, centered
                x = (i - (len(nodes) - 1) / 2) * (width_scale / max(1, len(nodes)))
                pos[node] = (x, y)
        
        # Apply force-directed adjustments to spread nodes horizontally within layers
        # but maintain the vertical hierarchy
        fixed_y = {}
        for node, (x, y) in pos.items():
            fixed_y[node] = y  # Remember the vertical position
        
        # Apply spring layout only within each layer to avoid edge crossings
        for layer, nodes in nodes_by_layer.items():
            if len(nodes) > 1:
                subgraph = G.subgraph(nodes)
                sub_pos = nx.spring_layout(subgraph, k=2.0, iterations=50, 
                                          pos={n: (pos[n][0], 0) for n in nodes})
                
                # Update x positions while keeping y positions fixed
                for node in nodes:
                    if node in sub_pos:
                        pos[node] = (sub_pos[node][0] * width_scale / 2, fixed_y[node])
        
        # Create high-quality figure with better resolution
        plt.figure(figsize=figsize, dpi=300, facecolor='white')
        
        # Set high quality rendering
        plt.rcParams['figure.dpi'] = 300
        plt.rcParams['savefig.dpi'] = 600
        plt.rcParams['path.simplify'] = True
        plt.rcParams['path.simplify_threshold'] = 1.0
        plt.rcParams['agg.path.chunksize'] = 10000
        
        # Draw nodes with larger size for better visibility
        nx.draw_networkx_nodes(G, pos, node_size=1000, node_color=node_colors, alpha=0.9, 
                               linewidths=2, edgecolors='white')
        
        # Draw edges with colors based on type, using curved edges to reduce overlap
        edge_types = {G.edges[e]['type'] for e in G.edges}
        edge_colors = plt.cm.tab10(range(len(edge_types)))
        edge_color_map = {t: c for t, c in zip(edge_types, edge_colors)}
        
        for edge_type, color in edge_color_map.items():
            edges_of_type = [(u, v) for u, v, data in G.edges(data=True) if data['type'] == edge_type]
            if edges_of_type:
                # Use curved edges with different curvature based on direction
                for u, v in edges_of_type:
                    # Determine if edge goes up or down in the hierarchy
                    source_layer = layer_types.get(G.nodes[u]['type'], 0)
                    target_layer = layer_types.get(G.nodes[v]['type'], 0)
                    
                    # Adjust curvature based on direction and distance
                    if source_layer == target_layer:
                        rad = 0.3  # Horizontal connections get more curve
                    else:
                        rad = 0.1  # Vertical connections get less curve
                    
                    nx.draw_networkx_edges(
                        G, pos, 
                        edgelist=[(u, v)], 
                        edge_color=[color], 
                        width=1.5, 
                        alpha=0.7,
                        connectionstyle=f'arc3,rad={rad}',
                        arrowsize=15
                    )
        
        # Draw labels with better positioning and fonts
        nx.draw_networkx_labels(
            G, 
            {k: (v[0], v[1] - 0.3) for k, v in pos.items()},  # Offset labels below nodes
            labels=node_labels,
            font_size=10, 
            font_family='sans-serif',
            font_weight='bold',
            bbox=dict(facecolor='white', alpha=0.7, edgecolor='none', pad=0.5)
        )
        
        # Create legend for node types
        node_patches = [plt.Line2D([0], [0], marker='o', color='w', markerfacecolor=color_map[nt], 
                                  markersize=10, label=f'Node: {nt}') for nt in node_types]
        
        # Create legend for edge types
        edge_patches = [plt.Line2D([0], [0], color=edge_color_map[et], lw=2, label=f'Edge: {et}') 
                        for et in edge_types]
        
        plt.legend(handles=node_patches + edge_patches, loc='upper right', bbox_to_anchor=(1.15, 1))
        
        plt.title(title)
        plt.axis('off')
        
        if output_path:
            plt.savefig(output_path, bbox_inches='tight', dpi=600, format='png', 
                       pad_inches=0.2, transparent=False)
            plt.close()
        else:
            plt.show()
    
    def visualize_graphviz(self, output_path: str = None, format: str = 'png') -> None:
        """
        Visualize the graph using Graphviz.
        
        Args:
            output_path: Path to save the visualization. If None, returns the Graphviz object.
            format: Output format (png, svg, pdf, etc.).
        
        Returns:
            The Graphviz object if output_path is None.
        """
        import tempfile
        import shutil
        import re
        
        # Create Graphviz graph
        dot = graphviz.Digraph(
            comment='ADP Knowledge Graph',
            # Use hierarchical layout
            graph_attr={
                'rankdir': 'TB',        # Top to bottom layout
                'concentrate': 'true',  # Merge edges
                'overlap': 'scale',     # Scale to avoid overlap
                'splines': 'true',      # Use curved edges
                'nodesep': '0.5',       # Increase node separation
                'ranksep': '0.75',      # Increase rank separation
                'fontname': 'Arial',
                'fontsize': '14',
                'bgcolor': 'white',
                'ratio': 'fill',
                'size': '12,8',
                'dpi': '600'            # High DPI for better quality
            },
            node_attr={
                'fontname': 'Arial',
                'fontsize': '12',
                'shape': 'box',
                'style': 'filled,rounded',
                'margin': '0.2,0.1',
                'penwidth': '1.5'
            },
            edge_attr={
                'fontname': 'Arial',
                'fontsize': '10',
                'fontcolor': '#555555',
                'penwidth': '1.5',
                'arrowsize': '0.8'
            }
        )
        
        # Node type colors
        type_colors = {
            "service": '#1f77b4',  # blue
            "module": '#ff7f0e',   # orange
            "class": '#2ca02c',    # green
            "function": '#d62728', # red
            "method": '#9467bd',   # purple
            "variable": '#8c564b', # brown
            "file": '#e377c2',     # pink
            "domain": '#7f7f7f',   # grey
            "concept": '#bcbd22',  # olive
            "team": '#17becf',     # cyan
            "tech_debt": '#000000', # black
            "performance": '#ff9896', # light red
            "data": '#aec7e8',     # light blue
        }
        
        # Helper function to sanitize node IDs for Graphviz
        def sanitize_id(node_id):
            # Replace any characters that could cause issues in Graphviz
            safe_id = re.sub(r'[^a-zA-Z0-9_]', '_', node_id)
            # Ensure it starts with a letter
            if safe_id and not safe_id[0].isalpha():
                safe_id = 'n' + safe_id
            return safe_id
        
        # Map original node IDs to sanitized IDs
        node_id_map = {node_id: sanitize_id(node_id) for node_id in self.nodes.keys()}
        
        # Create subgraphs for each type to improve clustering
        for node_type in set(node.type for node in self.nodes.values()):
            with dot.subgraph(name=f'cluster_{node_type}') as c:
                c.attr(label=node_type.capitalize(), 
                       style='filled,rounded', 
                       fillcolor='#f8f8f8', 
                       fontsize='16',
                       color='#dddddd')
                
                # Add nodes of this type to the subgraph
                for node_id, node in self.nodes.items():
                    if node.type == node_type:
                        # Get the appropriate color for this node type
                        color = type_colors.get(node.type, '#aaaaaa')
                        
                        # Use short_label if available
                        display_label = node.short_label if node.short_label else node.label
                        
                        # Set shape based on node type
                        shape = 'box'
                        if node.type == 'file':
                            shape = 'folder'
                        elif node.type in ['class', 'function', 'method']:
                            shape = 'ellipse' 
                        elif node.type in ['domain', 'service']:
                            shape = 'hexagon'
                        elif node.type == 'tech_debt':
                            shape = 'diamond'
                        
                        # Add node with styling using sanitized ID
                        c.node(
                            node_id_map[node_id],
                            label=display_label,
                            fillcolor=color,
                            fontcolor='white' if node.type in ['tech_debt', 'service'] else 'black',
                            shape=shape,
                            penwidth='1.5'
                        )
        
        # Edge type styling with better colors and styles
        edge_styles = {
            "contains": {'color': '#0077cc', 'style': 'solid', 'weight': '10'},  # Strong blue
            "uses": {'color': '#009900', 'style': 'solid', 'weight': '5'},       # Green
            "depends_on": {'color': '#cc0000', 'style': 'solid', 'weight': '8'},  # Red
            "calls": {'color': '#9900cc', 'style': 'solid', 'weight': '5'},      # Purple
            "implements": {'color': '#ff6600', 'style': 'dashed', 'weight': '3'}, # Orange
            "extends": {'color': '#996633', 'style': 'dashed', 'weight': '3'},   # Brown
            "references": {'color': '#666666', 'style': 'dotted', 'weight': '1'}, # Grey
            "owned_by": {'color': '#000000', 'style': 'dashed', 'weight': '3'},  # Black
            "related_to": {'color': '#888888', 'style': 'dotted', 'weight': '1'}, # Grey
            "has_tech_debt": {'color': '#ff0000', 'style': 'bold', 'weight': '2'}, # Red
            "has_performance_issue": {'color': '#ff9900', 'style': 'bold', 'weight': '2'}, # Orange
            "processes_data": {'color': '#0099cc', 'style': 'dashed', 'weight': '2'}, # Blue
        }
        
        # Add edges with styling using sanitized IDs
        for edge in self.edges:
            style = edge_styles.get(edge.type, {'color': '#000000', 'style': 'solid', 'weight': '1'})
            try:
                dot.edge(
                    node_id_map[edge.source], 
                    node_id_map[edge.target], 
                    label=edge.type, 
                    color=style['color'], 
                    style=style['style'],
                    penwidth='1.5',
                    weight=style['weight'],
                    arrowsize='0.8'
                )
            except KeyError:
                # Skip edges if nodes don't exist in the map
                continue
        
        if output_path:
            # Use a temporary file for rendering
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.gv')
            temp_name = temp_file.name
            temp_file.close()
            
            try:
                # First attempt: render the graph with default settings but high DPI in graph attributes
                rendered_file = dot.render(temp_name, format=format, cleanup=True)
                
                # Copy the rendered file to the desired output path
                shutil.copy(rendered_file, output_path)
                
                # Clean up temporary files
                try:
                    os.remove(rendered_file)
                    os.remove(temp_name)
                except:
                    pass
            except Exception as e:
                print(f"Error generating Graphviz visualization: {e}")
                # Fallback to matplotlib rendering
                self.visualize_matplotlib(output_path)
        
        return dot

    def to_cytoscape_json(self) -> Dict[str, Any]:
        """
        Convert to Cytoscape.js compatible JSON format with support for custom types.
        
        Returns:
            A dictionary with elements in Cytoscape.js format.
        """
        elements = []
        
        # Node type colors (modern palette)
        type_colors = {
            # Default node types
            NodeType.SERVICE.value: "#3498db",    # bright blue
            NodeType.MODULE.value: "#e74c3c",     # bright red
            NodeType.CLASS.value: "#2ecc71",      # bright green
            NodeType.FUNCTION.value: "#9b59b6",   # purple
            NodeType.METHOD.value: "#8e44ad",     # dark purple
            NodeType.VARIABLE.value: "#f1c40f",   # yellow
            NodeType.FILE.value: "#1abc9c",       # turquoise
            NodeType.DOMAIN.value: "#34495e",     # dark blue
            NodeType.CONCEPT.value: "#95a5a6",    # light gray
            NodeType.TEAM.value: "#16a085",       # green
            NodeType.TECH_DEBT.value: "#e67e22",  # orange
            NodeType.PERFORMANCE.value: "#d35400", # dark orange
            NodeType.DATA.value: "#3498db",       # blue
        }
        
        # Generate colors for any custom node types
        import colorsys
        import random
        
        # Add custom node types to the colors dictionary
        if self.custom_node_types:
            num_custom_types = len(self.custom_node_types)
            if num_custom_types > 0:
                # Generate evenly distributed colors in HSV space
                for i, custom_type in enumerate(sorted(self.custom_node_types)):
                    h = i / float(num_custom_types + 1)
                    s = 0.7
                    v = 0.95
                    r, g, b = colorsys.hsv_to_rgb(h, s, v)
                    color = "#{:02x}{:02x}{:02x}".format(int(r * 255), int(g * 255), int(b * 255))
                    type_colors[custom_type] = color
        
        # Generate nodes with classes and styling
        for node_id, node in self.nodes.items():
            # Get node type as string
            node_type = node.type.value if isinstance(node.type, NodeType) else node.type
            
            node_data = {
                "id": node_id,
                "label": node.label,
                "short_label": node.short_label or node.label,
                "type": node_type,
            }
            
            # Include all attributes as data for tooltips
            # Process nested attributes more flexibly
            self._add_attributes_to_data(node_data, node.attributes)
            
            # Create node with styling based on type
            elements.append({
                "data": node_data,
                "classes": node_type
            })
        
        # Generate edges with classes and styling
        edge_types = set()
        for edge in self.edges:
            # Get edge type as string
            edge_type = edge.type.value if isinstance(edge.type, EdgeType) else edge.type
            edge_types.add(edge_type)
            
            edge_data = {
                "id": f"{edge.source}-{edge_type}-{edge.target}",
                "source": edge.source,
                "target": edge.target,
                "type": edge_type
            }
            
            # Include attributes
            self._add_attributes_to_data(edge_data, edge.attributes)
            
            elements.append({
                "data": edge_data,
                "classes": edge_type
            })
        
        # Generate colors for any edge types that don't have predefined colors
        edge_colors = {
            EdgeType.CONTAINS.value: '#3498db',
            EdgeType.USES.value: '#2ecc71',
            EdgeType.DEPENDS_ON.value: '#e74c3c',
            EdgeType.CALLS.value: '#9b59b6',
            EdgeType.IMPLEMENTS.value: '#f39c12',
            EdgeType.EXTENDS.value: '#d35400',
            EdgeType.REFERENCES.value: '#7f8c8d',
            EdgeType.OWNED_BY.value: '#2c3e50',
            EdgeType.RELATED_TO.value: '#95a5a6',
            EdgeType.HAS_TECH_DEBT.value: '#e67e22',
            EdgeType.HAS_PERFORMANCE_ISSUE.value: '#d35400',
            EdgeType.PROCESSES_DATA.value: '#3498db',
        }
        
        # Add custom edge types to the edge colors dictionary
        for edge_type in edge_types:
            if edge_type not in edge_colors:
                # Generate a random color for this edge type
                h = random.random()
                s = 0.7
                v = 0.95
                r, g, b = colorsys.hsv_to_rgb(h, s, v)
                color = "#{:02x}{:02x}{:02x}".format(int(r * 255), int(g * 255), int(b * 255))
                edge_colors[edge_type] = color
        
        return {
            "elements": elements, 
            "type_colors": type_colors,
            "edge_colors": edge_colors,
            "custom_node_types": list(self.custom_node_types),
            "custom_edge_types": list(self.custom_edge_types)
        }
    
    def _add_attributes_to_data(self, data_dict: Dict[str, Any], attributes: Dict[str, Any], prefix: str = "attr_") -> None:
        """
        Recursively add attributes to the data dictionary.
        
        Args:
            data_dict: The data dictionary to add attributes to.
            attributes: The attributes to add.
            prefix: Prefix for attribute keys.
        """
        for key, value in attributes.items():
            if isinstance(value, (str, int, float, bool)) or value is None:
                data_dict[f"{prefix}{key}"] = value
            elif isinstance(value, dict):
                # For nested dictionaries, flatten with underscore notation
                for sub_key, sub_value in value.items():
                    if isinstance(sub_value, (str, int, float, bool)) or sub_value is None:
                        data_dict[f"{prefix}{key}_{sub_key}"] = sub_value
                    elif isinstance(sub_value, dict):
                        # If it's a nested dictionary, use recursive call
                        self._add_attributes_to_data(data_dict, {f"{key}_{sub_key}": sub_value}, prefix)
                    elif isinstance(sub_value, list) and all(isinstance(item, (str, int, float, bool)) for item in sub_value):
                        data_dict[f"{prefix}{key}_{sub_key}"] = ", ".join(str(item) for item in sub_value)
            elif isinstance(value, list):
                if all(isinstance(item, (str, int, float, bool)) for item in value):
                    # If all items are simple types, join as string
                    data_dict[f"{prefix}{key}"] = ", ".join(str(item) for item in value)
                elif all(isinstance(item, dict) for item in value):
                    # If items are dictionaries, process each separately
                    for i, item in enumerate(value):
                        item_key = f"{key}_{i+1}"
                        for item_subkey, item_value in item.items():
                            if isinstance(item_value, (str, int, float, bool)) or item_value is None:
                                data_dict[f"{prefix}{item_key}_{item_subkey}"] = item_value

    def visualize_interactive(self, output_path: str = None, title: str = "ADP Knowledge Graph") -> None:
        """
        Create an interactive visualization using Cytoscape.js.
        
        Args:
            output_path: Path to save the HTML file. If None, a default path is used.
            title: Title of the visualization.
        """
        if not output_path:
            output_path = "adp_knowledge_graph.html"
        
        # Get data in cytoscape format
        graph_data = self.to_cytoscape_json()
        
        # Generate HTML template with embedded Cytoscape.js
        html_template = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{title}</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 0;
            background-color: #f9f9f9;
            color: #333;
        }}
        #cy {{
            width: 100%;
            height: 85vh;
            display: block;
            background-color: #ffffff;
            border-radius: 8px;
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        }}
        .header {{
            padding: 15px 20px;
            background-color: #34495e;
            color: white;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid #2c3e50;
        }}
        .controls {{
            padding: 10px 20px;
            background-color: #ecf0f1;
            border-bottom: 1px solid #ddd;
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            align-items: center;
        }}
        button, select {{
            padding: 8px 12px;
            border: none;
            border-radius: 4px;
            background-color: #3498db;
            color: white;
            cursor: pointer;
            font-size: 14px;
            transition: background-color 0.2s;
        }}
        button:hover {{
            background-color: #2980b9;
        }}
        .search-container {{
            display: flex;
            align-items: center;
            margin-left: auto;
        }}
        #search {{
            padding: 8px 12px;
            border: 1px solid #ddd;
            border-radius: 4px;
            margin-right: 5px;
            width: 200px;
        }}
        .legend {{
            position: absolute;
            top: 70px;
            right: 20px;
            background-color: rgba(255, 255, 255, 0.9);
            border-radius: 8px;
            padding: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            z-index: 1000;
            max-height: 80vh;
            overflow-y: auto;
            font-size: 12px;
            width: 200px;
        }}
        .legend-item {{
            display: flex;
            align-items: center;
            margin-bottom: 5px;
        }}
        .legend-color {{
            width: 16px;
            height: 16px;
            margin-right: 8px;
            border-radius: 3px;
        }}
        .tooltip {{
            position: absolute;
            background-color: #fff;
            border-radius: 8px;
            padding: 15px;
            box-shadow: 0 3px 14px rgba(0,0,0,0.25);
            max-width: 400px;
            z-index: 1001;
            font-size: 13px;
            display: none;
            pointer-events: none;
            overflow-y: auto;
            max-height: 60vh;
            transition: opacity 0.2s;
        }}
        .tooltip h3 {{
            margin-top: 0;
            margin-bottom: 8px;
            font-size: 16px;
            border-bottom: 1px solid #eee;
            padding-bottom: 8px;
            color: #2c3e50;
        }}
        .tooltip h4 {{
            margin: 12px 0 6px 0;
            font-size: 14px;
            color: #2980b9;
            border-bottom: 1px dashed #eee;
            padding-bottom: 4px;
        }}
        .tooltip p {{
            margin: 4px 0;
            display: flex;
            align-items: baseline;
        }}
        .tooltip-label {{
            font-weight: 600;
            display: inline-block;
            min-width: 100px;
            color: #555;
            flex-shrink: 0;
        }}
        .tooltip-value {{
            word-break: break-word;
            flex-grow: 1;
        }}
        .badge {{
            display: inline-block;
            background-color: #3498db;
            color: white;
            padding: 2px 6px;
            border-radius: 3px;
            font-size: 11px;
            margin-right: 5px;
            font-weight: normal;
        }}
        .section-title {{
            font-weight: 600;
            margin-top: 10px;
            margin-bottom: 5px;
            color: #555;
        }}
        .metadata-section {{
            margin-left: 10px;
            padding-left: 10px;
            border-left: 3px solid #f0f0f0;
        }}
        .edge-tooltip {{
            background-color: #f8f8f8;
            border-left: 4px solid #3498db;
        }}
        #snapshot {{
            margin-left: 10px;
        }}
        #loading {{
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background-color: rgba(255, 255, 255, 0.9);
            padding: 20px;
            border-radius: 5px;
            box-shadow: 0 0 10px rgba(0, 0, 0, 0.2);
            text-align: center;
            z-index: 1000;
            display: none;
        }}
        .spinner {{
            border: 4px solid #f3f3f3;
            border-top: 4px solid #3498db;
            border-radius: 50%;
            width: 30px;
            height: 30px;
            animation: spin 2s linear infinite;
            margin: 0 auto 10px auto;
        }}
        @keyframes spin {{
            0% {{ transform: rotate(0deg); }}
            100% {{ transform: rotate(360deg); }}
        }}
    </style>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/cytoscape/3.25.0/cytoscape.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/dagre/0.8.5/dagre.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/cytoscape-dagre@2.5.0/cytoscape-dagre.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/cytoscape-popper@2.0.0/cytoscape-popper.min.js"></script>
    <script src="https://unpkg.com/file-saver@2.0.5/dist/FileSaver.min.js"></script>
    <script src="https://html2canvas.hertzen.com/dist/html2canvas.min.js"></script>
</head>
<body>
    <div class="header">
        <h2>{title}</h2>
        <div class="search-container">
            <input type="text" id="search" placeholder="Search nodes...">
            <button id="searchBtn">Search</button>
        </div>
    </div>
    <div class="controls">
        <button id="fit">Fit View</button>
        <button id="hierarchical">Hierarchical Layout</button>
        <button id="concentric">Concentric Layout</button>
        <button id="force">Force-Directed Layout</button>
        <select id="filterByType">
            <option value="all">All Node Types</option>
        </select>
        <button id="resetFilter">Reset Filters</button>
        <button id="toggleLegend">Toggle Legend</button>
        <button id="snapshot">Save Image</button>
    </div>
    <div id="cy"></div>
    <div class="legend" id="legend"></div>
    <div class="tooltip" id="tooltip"></div>
    <div id="loading">
        <div class="spinner"></div>
        <div>Processing layout...</div>
    </div>

    <script>
        // Graph data from Python
        const graphData = {json.dumps(graph_data, indent=2)};
        
        // Initialize Cytoscape
        const cy = cytoscape({{
            container: document.getElementById('cy'),
            elements: graphData.elements,
            style: [
                {{
                    selector: 'node',
                    style: {{
                        'label': 'data(short_label)',
                        'text-valign': 'center',
                        'text-halign': 'center',
                        'font-size': '12px',
                        'color': '#fff',
                        'text-outline-width': 1,
                        'text-outline-color': '#555',
                        'background-color': '#888',
                        'border-width': 1,
                        'border-color': '#555',
                        'text-wrap': 'wrap',
                        'text-max-width': '80px'
                    }}
                }},
                {{
                    selector: 'edge',
                    style: {{
                        'curve-style': 'bezier',
                        'target-arrow-shape': 'triangle',
                        'arrow-scale': 0.8,
                        'line-color': '#ccc',
                        'target-arrow-color': '#ccc',
                        'opacity': 0.7,
                        'label': 'data(type)',
                        'font-size': '10px',
                        'text-rotation': 'autorotate',
                        'text-margin-y': '-10px',
                        'text-outline-width': 2,
                        'text-outline-color': '#fff',
                        'color': '#555'
                    }}
                }},
            ],
            layout: {{
                name: 'dagre',
                padding: 30,
                nodeSep: 80,
                rankSep: 100,
                rankDir: 'TB',
                animate: true,
                animationDuration: 500,
                fit: true
            }}
        }});
        
        // Set node colors based on type
        Object.entries(graphData.type_colors).forEach(([type, color]) => {{
            cy.style().selector(`node.${type}`).style({{'background-color': color}}).update();
        }});
        
        // Set edge colors based on type
        Object.entries(graphData.edge_colors).forEach(([type, color]) => {{
            cy.style().selector(`edge.${type}`).style({{
                'line-color': color, 
                'target-arrow-color': color
            }}).update();
        }});
        
        // Add style for highlighted elements
        cy.style()
            .selector('node.highlight')
            .style({{
                'border-width': 3,
                'border-color': '#ff0',
                'border-style': 'double'
            }})
            .selector('node.semitransparent')
            .style({{
                'opacity': 0.3
            }})
            .selector('edge.highlight')
            .style({{
                'width': 4,
                'line-color': '#ff0',
                'target-arrow-color': '#ff0',
                'opacity': 1
            }})
            .selector('edge.semitransparent')
            .style({{
                'opacity': 0.1
            }})
            .selector('node:selected')
            .style({{
                'border-width': 3,
                'border-color': '#ff0',
                'border-style': 'double'
            }})
            .selector('edge:selected')
            .style({{
                'width': 4,
                'line-color': '#ff0',
                'target-arrow-color': '#ff0'
            }})
            .update();
        
        // Add node types to filter dropdown
        const nodeTypes = [...new Set(graphData.elements
            .filter(el => el.data.type)
            .map(el => el.data.type))];
            
        const filterSelect = document.getElementById('filterByType');
        nodeTypes.sort().forEach(type => {{
            const option = document.createElement('option');
            option.value = type;
            option.textContent = type.charAt(0).toUpperCase() + type.slice(1).replace(/_/g, ' ');
            filterSelect.appendChild(option);
        }});
        
        // Create legend
        function createLegend() {{
            const legend = document.getElementById('legend');
            legend.innerHTML = '<h3>Node Types</h3>';
            
            // Add entries for known node types and any custom ones
            const allNodeTypes = nodeTypes;
            
            allNodeTypes.sort().forEach(type => {{
                const color = graphData.type_colors[type] || '#888';
                
                if (cy.nodes('.' + type).length > 0) {{
                    const item = document.createElement('div');
                    item.className = 'legend-item';
                    
                    const colorBox = document.createElement('div');
                    colorBox.className = 'legend-color';
                    colorBox.style.backgroundColor = color;
                    
                    const label = document.createElement('span');
                    label.textContent = type.charAt(0).toUpperCase() + type.slice(1).replace(/_/g, ' ');
                    
                    item.appendChild(colorBox);
                    item.appendChild(label);
                    legend.appendChild(item);
                }}
            }});
            
            legend.innerHTML += '<h3>Edge Types</h3>';
            const edgeTypes = [...new Set(cy.edges().map(e => e.data('type')))];
            
            edgeTypes.sort().forEach(type => {{
                const color = graphData.edge_colors[type] || '#ccc';
                
                const item = document.createElement('div');
                item.className = 'legend-item';
                
                const colorBox = document.createElement('div');
                colorBox.className = 'legend-color';
                colorBox.style.backgroundColor = color;
                
                const label = document.createElement('span');
                label.textContent = type.replace(/_/g, ' ');
                
                item.appendChild(colorBox);
                item.appendChild(label);
                legend.appendChild(item);
            }});
        }}
        
        createLegend();
        
        // Helper function to format attribute keys for display
        function formatAttributeKey(key) {{
            // Remove attr_ prefix and replace underscores with spaces
            return key.replace(/^attr_/, '')
                     .replace(/_/g, ' ')
                     // Capitalize first letter of each word
                     .replace(/(\b\w)/g, match => match.toUpperCase());
        }}
        
        // Group metadata attributes by category
        function groupMetadataAttributes(data) {{
            const groups = {{
                // Core properties that should appear at the top
                core: [],
                // Known categories
                domain: [],
                service: [],
                dependencies: [],
                tech_debt: [],
                performance: [],
                data: [],
                // Everything else goes here
                other: []
            }};
            
            // Get all attribute keys (those starting with attr_)
            const attributes = Object.entries(data).filter(([key]) => key.startsWith('attr_'));
            
            attributes.forEach(([key, value]) => {{
                const cleanKey = key.replace(/^attr_/, '');
                
                // Check which group this attribute belongs to
                if (cleanKey === 'domain' || cleanKey === 'description') {{
                    groups.core.push([key, value]);
                }} else if (cleanKey.startsWith('tech_debt') || 
                           cleanKey.startsWith('techDebt') || 
                           cleanKey.startsWith('tech-debt')) {{
                    groups.tech_debt.push([key, value]);
                }} else if (cleanKey.startsWith('performance')) {{
                    groups.performance.push([key, value]);
                }} else if (cleanKey.startsWith('data') || 
                           cleanKey.startsWith('dataHandling') || 
                           cleanKey.startsWith('data-handling')) {{
                    groups.data.push([key, value]);
                }} else if (cleanKey.startsWith('service') || 
                           cleanKey.startsWith('serviceBoundary') ||
                           cleanKey.startsWith('service-boundary')) {{
                    groups.service.push([key, value]);
                }} else if (cleanKey === 'dependencies' || 
                           cleanKey.startsWith('depends_on') || 
                           cleanKey.startsWith('imports') ||
                           cleanKey.startsWith('requires')) {{
                    groups.dependencies.push([key, value]);
                }} else {{
                    groups.other.push([key, value]);
                }}
            }});
            
            return groups;
        }}
        
        // Tooltip for node metadata
        function showNodeTooltip(node, event) {{
            const tooltip = document.getElementById('tooltip');
            const data = node.data();
            
            let content = `<h3>${{data.label}}</h3>`;
            content += `<p><span class="tooltip-label">Type:</span> <span class="badge">${{data.type}}</span></p>`;
            
            // Group and organize the metadata
            const groups = groupMetadataAttributes(data);
            
            // Add core properties first
            if (groups.core.length > 0) {{
                groups.core.forEach(([key, value]) => {{
                    const attrName = formatAttributeKey(key);
                    const valueDisplay = typeof value === 'string' && value.length > 100 ? 
                                      value.substring(0, 100) + '...' : value;
                    content += `<p><span class="tooltip-label">${{attrName}}:</span> <span class="tooltip-value">${{valueDisplay}}</span></p>`;
                }});
            }}
            
            // Add each metadata group
            const groupLabels = {{
                domain: 'Domain',
                service: 'Service',
                dependencies: 'Dependencies',
                tech_debt: 'Technical Debt',
                performance: 'Performance',
                data: 'Data Handling',
                other: 'Other Metadata'
            }};
            
            Object.entries(groups).forEach(([groupName, attributes]) => {{
                // Skip the core group (already processed) and empty groups
                if (groupName === 'core' || attributes.length === 0) return;
                
                content += `<h4>${{groupLabels[groupName]}}</h4>`;
                content += '<div class="metadata-section">';
                
                attributes.forEach(([key, value]) => {{
                    const attrName = formatAttributeKey(key);
                    const valueDisplay = typeof value === 'string' && value.length > 100 ? 
                                      value.substring(0, 100) + '...' : value;
                    content += `<p><span class="tooltip-label">${{attrName}}:</span> <span class="tooltip-value">${{valueDisplay}}</span></p>`;
                }});
                
                content += '</div>';
            }});
            
            tooltip.innerHTML = content;
            tooltip.style.left = `${{event.renderedPosition.x + 10}}px`;
            tooltip.style.top = `${{event.renderedPosition.y + 10}}px`;
            tooltip.style.display = 'block';
            
            // Adjust tooltip position if it goes off screen
            const tooltipRect = tooltip.getBoundingClientRect();
            const viewportWidth = window.innerWidth;
            const viewportHeight = window.innerHeight;
            
            if (tooltipRect.right > viewportWidth) {{
                tooltip.style.left = `${{event.renderedPosition.x - tooltipRect.width - 10}}px`;
            }}
            
            if (tooltipRect.bottom > viewportHeight) {{
                tooltip.style.top = `${{event.renderedPosition.y - tooltipRect.height - 10}}px`;
            }}
        }}
        
        function showEdgeTooltip(edge, event) {{
            const tooltip = document.getElementById('tooltip');
            const data = edge.data();
            
            let content = `<h3>Relationship: ${{data.type.replace(/_/g, ' ')}}</h3>`;
            content += `<p><span class="tooltip-label">From:</span> <span class="tooltip-value">${{edge.source().data('short_label')}}</span></p>`;
            content += `<p><span class="tooltip-label">To:</span> <span class="tooltip-value">${{edge.target().data('short_label')}}</span></p>`;
            
            // Add additional metadata if present
            const attributes = Object.entries(data).filter(([key]) => key.startsWith('attr_'));
            if (attributes.length > 0) {{
                content += '<h4>Metadata</h4>';
                content += '<div class="metadata-section">';
                attributes.forEach(([key, value]) => {{
                    const attrName = formatAttributeKey(key);
                    content += `<p><span class="tooltip-label">${{attrName}}:</span> <span class="tooltip-value">${{value}}</span></p>`;
                }});
                content += '</div>';
            }}
            
            tooltip.innerHTML = content;
            tooltip.className = 'tooltip edge-tooltip';
            tooltip.style.left = `${{event.renderedPosition.x + 10}}px`;
            tooltip.style.top = `${{event.renderedPosition.y + 10}}px`;
            tooltip.style.display = 'block';
            
            // Adjust tooltip position if it goes off screen
            const tooltipRect = tooltip.getBoundingClientRect();
            const viewportWidth = window.innerWidth;
            const viewportHeight = window.innerHeight;
            
            if (tooltipRect.right > viewportWidth) {{
                tooltip.style.left = `${{event.renderedPosition.x - tooltipRect.width - 10}}px`;
            }}
            
            if (tooltipRect.bottom > viewportHeight) {{
                tooltip.style.top = `${{event.renderedPosition.y - tooltipRect.height - 10}}px`;
            }}
        }}
        
        function hideTooltip() {{
            const tooltip = document.getElementById('tooltip');
            tooltip.style.display = 'none';
            tooltip.className = 'tooltip'; // Reset tooltip class
        }}
        
        // Highlight connected elements
        function highlightConnectedElements(node) {{
            // Reset all elements
            cy.elements().removeClass('highlight semitransparent');
            
            // If no node is selected, clear highlight
            if (!node) return;
            
            // Get connected edges and nodes
            const connectedEdges = node.connectedEdges();
            const connectedNodes = connectedEdges.connectedNodes();
            
            // Add the original node to the connected nodes
            const allConnected = connectedNodes.union(node);
            
            // Highlight connected elements
            allConnected.addClass('highlight');
            connectedEdges.addClass('highlight');
            
            // Make all other elements semi-transparent
            cy.elements().not(allConnected.union(connectedEdges)).addClass('semitransparent');
        }}
        
        // Event listeners
        cy.on('mouseover', 'node', function(evt) {{
            showNodeTooltip(evt.target, evt);
        }});
        
        cy.on('mouseover', 'edge', function(evt) {{
            showEdgeTooltip(evt.target, evt);
        }});
        
        cy.on('mouseout', function() {{
            hideTooltip();
        }});
        
        cy.on('tap', 'node', function(evt) {{
            highlightConnectedElements(evt.target);
        }});
        
        cy.on('tap', function(evt) {{
            if (evt.target === cy) {{
                // Clicked on background, clear highlights
                cy.elements().removeClass('highlight semitransparent');
                hideTooltip();
            }}
        }});
        
        // Layout buttons
        document.getElementById('fit').addEventListener('click', function() {{
            cy.fit();
        }});
        
        document.getElementById('hierarchical').addEventListener('click', function() {{
            document.getElementById('loading').style.display = 'block';
            setTimeout(() => {{
                cy.layout({{
                    name: 'dagre',
                    rankDir: 'TB',
                    nodeSep: 80,
                    rankSep: 100,
                    padding: 30,
                    animate: true,
                    animationDuration: 800
                }}).run();
                
                setTimeout(() => {{
                    document.getElementById('loading').style.display = 'none';
                }}, 900);
            }}, 50);
        }});
        
        document.getElementById('concentric').addEventListener('click', function() {{
            document.getElementById('loading').style.display = 'block';
            setTimeout(() => {{
                cy.layout({{
                    name: 'concentric',
                    concentric: function(node) {{
                        // More important nodes in the center
                        const typeRank = {{
                            'domain': 10,
                            'service': 9,
                            'team': 8,
                            'file': 7,
                            'class': 6,
                            'function': 5,
                            'method': 4,
                            'variable': 3,
                            'tech_debt': 2,
                            'performance': 2,
                            'data': 1
                        }};
                        return typeRank[node.data('type')] || 0;
                    }},
                    levelWidth: function() {{ return 1; }},
                    animate: true,
                    animationDuration: 800
                }}).run();
                
                setTimeout(() => {{
                    document.getElementById('loading').style.display = 'none';
                }}, 900);
            }}, 50);
        }});
        
        document.getElementById('force').addEventListener('click', function() {{
            document.getElementById('loading').style.display = 'block';
            setTimeout(() => {{
                cy.layout({{
                    name: 'cose',
                    idealEdgeLength: 150,
                    nodeOverlap: 20,
                    refresh: 20,
                    fit: true,
                    padding: 30,
                    randomize: false,
                    componentSpacing: 100,
                    nodeRepulsion: 400000,
                    edgeElasticity: 100,
                    nestingFactor: 5,
                    gravity: 80,
                    numIter: 1000,
                    animate: 'end',
                    animationDuration: 800
                }}).run();
                
                setTimeout(() => {{
                    document.getElementById('loading').style.display = 'none';
                }}, 1000);
            }}, 50);
        }});
        
        // Filter by node type
        document.getElementById('filterByType').addEventListener('change', function() {{
            const selectedType = this.value;
            
            if (selectedType === 'all') {{
                cy.elements().removeClass('semitransparent');
                return;
            }}
            
            // Filter nodes by selected type
            const selectedNodes = cy.nodes('.' + selectedType);
            const connectedEdges = selectedNodes.connectedEdges();
            
            // Make non-matching elements semi-transparent
            cy.elements().addClass('semitransparent');
            selectedNodes.removeClass('semitransparent');
            connectedEdges.removeClass('semitransparent');
        }});
        
        document.getElementById('resetFilter').addEventListener('click', function() {{
            cy.elements().removeClass('highlight semitransparent');
            document.getElementById('filterByType').value = 'all';
        }});
        
        // Toggle legend
        document.getElementById('toggleLegend').addEventListener('click', function() {{
            const legend = document.getElementById('legend');
            legend.style.display = legend.style.display === 'none' ? 'block' : 'none';
        }});
        
        // Search functionality
        document.getElementById('searchBtn').addEventListener('click', function() {{
            const searchTerm = document.getElementById('search').value.toLowerCase();
            if (!searchTerm) return;
            
            // Reset highlighting
            cy.elements().removeClass('highlight semitransparent');
            
            // Build search index from all node data
            const searchableNodes = cy.nodes().filter(node => {{
                const data = node.data();
                
                // Check label and short_label
                if (data.label.toLowerCase().includes(searchTerm) || 
                    (data.short_label && data.short_label.toLowerCase().includes(searchTerm))) {{
                    return true;
                }}
                
                // Search in all attributes
                for (const [key, value] of Object.entries(data)) {{
                    if (key.startsWith('attr_') && 
                        typeof value === 'string' && 
                        value.toLowerCase().includes(searchTerm)) {{
                        return true;
                    }}
                }}
                
                return false;
            }});
            
            if (searchableNodes.length > 0) {{
                // Highlight matching nodes
                searchableNodes.addClass('highlight');
                
                // Make non-matching elements semi-transparent
                cy.elements().not(searchableNodes).addClass('semitransparent');
                
                // Center the view on the first match
                cy.animate({{
                    fit: {{
                        eles: searchableNodes,
                        padding: 50
                    }},
                    duration: 500
                }});
            }}
        }});
        
        // Also trigger search on Enter key
        document.getElementById('search').addEventListener('keyup', function(event) {{
            if (event.key === 'Enter') {{
                document.getElementById('searchBtn').click();
            }}
        }});
        
        // Save snapshot
        document.getElementById('snapshot').addEventListener('click', function() {{
            // Create a PNG snapshot of the current view
            const png = cy.png({{
                output: 'blob',
                bg: 'white',
                full: false,
                scale: 2,
                quality: 1
            }});
            
            // Save the image
            saveAs(png, 'knowledge_graph.png');
        }});
        
        // Fit the graph to the viewport initially
        cy.ready(() => {{
            cy.fit();
        }});
    </script>
</body>
</html>
        """
        
        # Write HTML file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_template)
        
        print(f"Interactive visualization saved to {output_path}")
        print(f"Open this HTML file in a web browser to view the interactive graph")
        
        return output_path


class GraphBuilder:
    """Builder for creating knowledge graphs from ADP metadata."""
    
    def __init__(self, schema_name: str = None):
        """
        Initialize the graph builder.
        
        Args:
            schema_name: Name of the schema to use. If None, uses the active schema.
        """
        self.graph = KnowledgeGraph()
        self.processed_files = set()
        self.schema = get_schema(schema_name)
        self.custom_node_types = set()
        self.custom_edge_types = set()
    
    def add_file(self, parsed_file: ParsedFile) -> None:
        """
        Add a file to the knowledge graph.
        
        Args:
            parsed_file: The parsed file to add.
        """
        file_path = parsed_file.file_path
        if file_path in self.processed_files:
            return
        
        # Add file node
        file_name = os.path.basename(file_path)
        # Sanitize file path for use as node ID
        sanitized_path = file_path.replace('/', '_').replace('\\', '_')
        file_id = f"file:{sanitized_path}"
        self.graph.add_node(Node(
            id=file_id,
            type=NodeType.FILE,
            label=file_path,
            short_label=file_name,
            attributes={"path": file_path}
        ))
        
        # Process metadata blocks
        for metadata_block in parsed_file.metadata_blocks:
            # Generate a unique ID for the metadata block
            block_id = f"{file_id}:{metadata_block.line_number}"
            
            # Process different scopes
            if metadata_block.scope == "file":
                self._process_metadata(metadata_block, block_id, file_id, file_name, NodeType.FILE)
            elif metadata_block.scope == "class":
                self._process_metadata(metadata_block, block_id, file_id, file_name, NodeType.CLASS)
            elif metadata_block.scope in ["function", "method"]:
                node_type = NodeType.METHOD if metadata_block.scope == "method" else NodeType.FUNCTION
                self._process_metadata(metadata_block, block_id, file_id, file_name, node_type)
            elif metadata_block.scope == "variable":
                self._process_metadata(metadata_block, block_id, file_id, file_name, NodeType.VARIABLE)
        
        self.processed_files.add(file_path)
    
    def _process_metadata(self, metadata_block: ADPMetadata, block_id: str, file_id: str, file_name: str, node_type: NodeType) -> None:
        """
        Process metadata with flexible approach to handle any schema.
        
        Args:
            metadata_block: The metadata block to process.
            block_id: The ID of the metadata block.
            file_id: The ID of the file.
            file_name: The name of the file.
            node_type: The type of node for this metadata.
        """
        metadata = metadata_block.metadata
        print(f"Processing metadata block: {metadata}")
        
        # Create the primary node for this metadata block
        # Use name from metadata if available, otherwise check scope_name, then fallback to default naming
        node_name = metadata.get("name")
        if node_name is not None:
            print(f"Using explicit 'name' from metadata: {node_name}")
        else:
            # Try scope_name as an alternative
            node_name = metadata.get("scope_name")
            if node_name is not None:
                print(f"Using 'scope_name' as alternative: {node_name}")
            else:
                # If both name and scope_name are not available, use default naming
                node_name = f"{node_type.value.capitalize()} in {file_name}"
                print(f"Using default naming convention: {node_name}")
        
        # Generate a unique ID for this node
        node_id = f"{node_type.value}:{block_id}"
        
        # Add node to graph
        self.graph.add_node(Node(
            id=node_id,
            type=node_type,
            label=f"{node_name} ({file_name})",
            short_label=node_name,
            attributes=metadata  # Include all metadata as attributes
        ))
        
        # Connect to file
        if node_type != NodeType.FILE:  # Don't connect file to itself
            self.graph.add_edge(Edge(
                source=file_id,
                target=node_id,
                type=EdgeType.CONTAINS
            ))
        
        # Process connections based on available metadata
        self._process_connections(metadata, node_id, file_id, node_type)
        
        # Process custom node types (domains, concepts, etc.)
        self._process_custom_nodes(metadata, node_id)
    
    def _process_connections(self, metadata: Dict[str, Any], node_id: str, file_id: str, node_type: NodeType) -> None:
        """
        Process connections based on available metadata.
        
        Args:
            metadata: The metadata dictionary.
            node_id: The ID of the current node.
            file_id: The ID of the file containing this node.
            node_type: The type of current node.
        """
        # Domain connections
        if "domain" in metadata:
            domain_id = f"domain:{metadata['domain']}"
            domain_label = metadata['domain']
            
            # Add domain node if not exists
            if domain_id not in self.graph.nodes:
                self.graph.add_node(Node(
                    id=domain_id,
                    type=NodeType.DOMAIN,
                    label=domain_label,
                    short_label=domain_label
                ))
            
            # Connect node to domain
            self.graph.add_edge(Edge(
                source=node_id,
                target=domain_id,
                type=EdgeType.RELATED_TO
            ))
        
        # Process dependencies (flexible key names)
        for key in ["dependencies", "depends_on", "imports", "requires"]:
            if key in metadata and isinstance(metadata[key], list):
                for dep in metadata[key]:
                    # Create dependency nodes based on type
                    if isinstance(dep, str):
                        # Simple string dependency
                        dep_parts = dep.split('.')
                        if len(dep_parts) > 1:
                            # Likely a module or class
                            dep_type = NodeType.MODULE
                            dep_id = f"module:{dep}"
                        else:
                            # Likely a file
                            dep_type = NodeType.FILE
                            sanitized_dep = dep.replace('/', '_').replace('\\', '_')
                            dep_id = f"file:{sanitized_dep}"
                        
                        dep_name = os.path.basename(dep)
                        
                        # Add dependency node if not exists
                        if dep_id not in self.graph.nodes:
                            self.graph.add_node(Node(
                                id=dep_id,
                                type=dep_type,
                                label=dep,
                                short_label=dep_name
                            ))
                        
                        # Connect node to dependency
                        self.graph.add_edge(Edge(
                            source=node_id,
                            target=dep_id,
                            type=EdgeType.DEPENDS_ON
                        ))
        
        # Process service boundary information (flexible schema)
        for service_key in ["service", "serviceBoundary", "service-boundary", "service_boundary"]:
            if service_key in metadata:
                service_info = metadata[service_key]
                
                # Handle both string and dictionary formats
                if isinstance(service_info, str):
                    service_name = service_info
                    service_data = {}
                elif isinstance(service_info, dict):
                    service_name = service_info.get("service") or service_info.get("name")
                    service_data = service_info
                else:
                    continue
                
                if service_name:
                    service_id = f"service:{service_name}"
                    
                    # Add service node if not exists
                    if service_id not in self.graph.nodes:
                        self.graph.add_node(Node(
                            id=service_id,
                            type=NodeType.SERVICE,
                            label=service_name,
                            short_label=service_name,
                            attributes=service_data
                        ))
                    
                    # Connect node to service
                    self.graph.add_edge(Edge(
                        source=node_id,
                        target=service_id,
                        type=EdgeType.DEPENDS_ON
                    ))
                    
                    # Process team ownership (several possible key names)
                    team_name = None
                    for team_key in ["teamOwner", "team_owner", "team", "owner"]:
                        if isinstance(service_info, dict) and team_key in service_info:
                            team_name = service_info[team_key]
                            break
                    
                    if team_name:
                        team_id = f"team:{team_name}"
                        
                        # Add team node if not exists
                        if team_id not in self.graph.nodes:
                            self.graph.add_node(Node(
                                id=team_id,
                                type=NodeType.TEAM,
                                label=team_name,
                                short_label=team_name
                            ))
                        
                        # Connect service to team
                        self.graph.add_edge(Edge(
                            source=service_id,
                            target=team_id,
                            type=EdgeType.OWNED_BY
                        ))
        
        # Process class relationships (inheritance, implementation)
        if node_type == NodeType.CLASS:
            # Inheritance (multiple possible key names)
            for extends_key in ["extends", "parent", "inherits", "superclass"]:
                if extends_key in metadata:
                    parent_class = metadata[extends_key]
                    if isinstance(parent_class, str):
                        parent_id = f"class:{parent_class}"
                        
                        # Add parent class node if not exists
                        if parent_id not in self.graph.nodes:
                            self.graph.add_node(Node(
                                id=parent_id,
                                type=NodeType.CLASS,
                                label=parent_class,
                                short_label=parent_class
                            ))
                        
                        # Connect class to parent
                        self.graph.add_edge(Edge(
                            source=node_id,
                            target=parent_id,
                            type=EdgeType.EXTENDS
                        ))
            
            # Interface implementation (multiple possible key names)
            for implements_key in ["implements", "interfaces"]:
                if implements_key in metadata and isinstance(metadata[implements_key], list):
                    for interface in metadata[implements_key]:
                        interface_id = f"class:{interface}"
                        
                        # Add interface node if not exists
                        if interface_id not in self.graph.nodes:
                            self.graph.add_node(Node(
                                id=interface_id,
                                type=NodeType.CLASS,
                                label=interface,
                                short_label=interface,
                                attributes={"is_interface": True}
                            ))
                        
                        # Connect class to interface
                        self.graph.add_edge(Edge(
                            source=node_id,
                            target=interface_id,
                            type=EdgeType.IMPLEMENTS
                        ))
        
        # Process function/method relationships
        if node_type in [NodeType.FUNCTION, NodeType.METHOD]:
            # Function calls (multiple possible key names)
            for calls_key in ["calls", "invokes", "uses_functions"]:
                if calls_key in metadata and isinstance(metadata[calls_key], list):
                    for called_fn in metadata[calls_key]:
                        if isinstance(called_fn, str):
                            # Simple string function reference
                            called_id = f"function:{called_fn}"
                            
                            # Add called function node if not exists
                            if called_id not in self.graph.nodes:
                                self.graph.add_node(Node(
                                    id=called_id,
                                    type=NodeType.FUNCTION,
                                    label=called_fn,
                                    short_label=called_fn
                                ))
                            
                            # Connect function to called function
                            self.graph.add_edge(Edge(
                                source=node_id,
                                target=called_id,
                                type=EdgeType.CALLS
                            ))
    
    def _process_custom_nodes(self, metadata: Dict[str, Any], node_id: str) -> None:
        """
        Process custom node types from metadata.
        
        Args:
            metadata: The metadata dictionary.
            node_id: The ID of the current node.
        """
        # Generic approach to handle any known metadata categories
        known_categories = {
            # Category name: (node type, edge type, node prefix)
            "tech_debt": (NodeType.TECH_DEBT, EdgeType.HAS_TECH_DEBT, "tech_debt"),
            "techDebt": (NodeType.TECH_DEBT, EdgeType.HAS_TECH_DEBT, "tech_debt"),
            "tech-debt": (NodeType.TECH_DEBT, EdgeType.HAS_TECH_DEBT, "tech_debt"),
            "performance": (NodeType.PERFORMANCE, EdgeType.HAS_PERFORMANCE_ISSUE, "perf"),
            "data_handling": (NodeType.DATA, EdgeType.PROCESSES_DATA, "data"),
            "dataHandling": (NodeType.DATA, EdgeType.PROCESSES_DATA, "data"),
            "data-handling": (NodeType.DATA, EdgeType.PROCESSES_DATA, "data"),
        }
        
        # Process each known category if present in metadata
        for category_key, (node_type, edge_type, prefix) in known_categories.items():
            if category_key in metadata:
                category_data = metadata[category_key]
                
                # Handle both list and dictionary formats
                if isinstance(category_data, list):
                    for index, item in enumerate(category_data):
                        self._add_custom_node(node_id, item, node_type, edge_type, f"{prefix}:{index}")
                elif isinstance(category_data, dict):
                    self._add_custom_node(node_id, category_data, node_type, edge_type, prefix)
        
        # Look for any custom properties in the schema and create nodes/edges as appropriate
        schema_properties = self.schema.schema.get("properties", {})
        for prop_name, prop_spec in schema_properties.items():
            # Skip properties we've already handled
            if prop_name in known_categories or prop_name in ["domain", "dependencies", "name", "service"]:
                continue
                
            # Check if the property is in the metadata
            if prop_name in metadata:
                prop_value = metadata[prop_name]
                
                # Handle objects that might represent entities
                if isinstance(prop_value, dict) and "name" in prop_value:
                    # This looks like an entity with a name
                    entity_name = prop_value["name"]
                    entity_type = prop_name.replace("_", "-").replace(" ", "-")
                    
                    # Register custom node type
                    if entity_type not in [t.value for t in NodeType]:
                        self.custom_node_types.add(entity_type)
                    
                    # Create custom node
                    entity_id = f"{entity_type}:{entity_name}"
                    if entity_id not in self.graph.nodes:
                        self.graph.add_node(Node(
                            id=entity_id,
                            type=entity_type,  # Use string for custom type
                            label=entity_name,
                            short_label=entity_name,
                            attributes=prop_value
                        ))
                    
                    # Create relationship
                    relationship_type = f"has_{entity_type}"
                    if relationship_type not in [t.value for t in EdgeType]:
                        self.custom_edge_types.add(relationship_type)
                    
                    self.graph.add_edge(Edge(
                        source=node_id,
                        target=entity_id,
                        type=relationship_type  # Use string for custom type
                    ))
    
    def _add_custom_node(self, parent_id: str, data: Dict[str, Any], node_type: NodeType, edge_type: EdgeType, prefix: str) -> None:
        """
        Add a custom node based on metadata.
        
        Args:
            parent_id: The ID of the parent node.
            data: The data for the custom node.
            node_type: The type of node.
            edge_type: The type of edge to connect parent and custom node.
            prefix: Prefix for the custom node ID.
        """
        # Determine label based on data content
        label = None
        for key in ["name", "issue", "title", "type", "consideration", "dataType"]:
            if key in data and isinstance(data[key], str):
                label = data[key]
                break
        
        if not label:
            # Use node type as fallback label
            label = node_type.value.replace("_", " ").capitalize()
        
        # Create unique ID for this custom node
        custom_id = f"{parent_id}:{prefix}"
        
        # Add custom node
        self.graph.add_node(Node(
            id=custom_id,
            type=node_type,
            label=label,
            short_label=label,
            attributes=data
        ))
        
        # Connect parent to custom node
        self.graph.add_edge(Edge(
            source=parent_id,
            target=custom_id,
            type=edge_type
        ))
    
    def build_from_parsed_files(self, parsed_files: List[ParsedFile]) -> KnowledgeGraph:
        """
        Build a knowledge graph from parsed files.
        
        Args:
            parsed_files: List of parsed files.
        
        Returns:
            The built knowledge graph.
        """
        for parsed_file in parsed_files:
            self.add_file(parsed_file)
        
        return self.graph 