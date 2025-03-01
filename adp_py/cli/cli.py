"""
@ai-metadata {
    "domain": "command-line-interface",
    "description": "Command-line interface for ADP tools",
    "dependencies": ["../core/parser.py", "../core/schema.py", "../core/graph.py"]
}
"""

import os
import sys
import json
import click
import logging
from typing import List, Dict, Any, Optional
from rich.console import Console
from rich.table import Table
from rich.syntax import Syntax
from rich.panel import Panel

from adp_py.core.parser import ADPParser, ParsedFile, CodeScope
from adp_py.core.schema import ADPSchema, load_schema, get_default_schema, register_schema
from adp_py.core.graph import GraphBuilder, KnowledgeGraph, NodeType, EdgeType


console = Console()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("adp")


@click.group()
@click.version_option()
def cli():
    """AI Documentation Protocol (ADP) command-line tools."""
    pass


@cli.command()
@click.argument('path', type=click.Path(exists=True))
@click.option('--recursive/--no-recursive', default=True, help='Recursively scan directories')
@click.option('--output', '-o', type=click.Path(), help='Output file for results (JSON format)')
@click.option('--schema', '-s', type=click.Path(exists=True), help='Custom schema file to use for validation')
def scan(path: str, recursive: bool, output: Optional[str], schema: Optional[str]):
    """
    Scan a file or directory for ADP metadata.
    
    PATH is the file or directory to scan.
    """
    try:
        if schema:
            schema_obj = load_schema(schema)
            parser = ADPParser(schema_name=schema_obj.name)
        else:
            parser = ADPParser()
        
        if os.path.isfile(path):
            console.print(f"Scanning file: [bold blue]{path}[/bold blue]")
            parsed_files = [parser.parse_file(path)]
        else:
            console.print(f"Scanning directory: [bold blue]{path}[/bold blue]")
            parsed_files = parser.parse_directory(path, recursive=recursive)
        
        # Count metadata blocks by scope
        scope_counts = {scope.value: 0 for scope in CodeScope}
        total_blocks = 0
        
        for parsed_file in parsed_files:
            for metadata_block in parsed_file.metadata_blocks:
                scope_counts[metadata_block.scope] += 1
                total_blocks += 1
        
        # Display summary
        console.print(f"\n[bold green]Found {total_blocks} metadata blocks in {len(parsed_files)} files[/bold green]\n")
        
        if total_blocks > 0:
            table = Table(title="Metadata Distribution")
            table.add_column("Scope", style="cyan")
            table.add_column("Count", style="magenta")
            table.add_column("Percentage", style="green")
            
            for scope, count in scope_counts.items():
                if count > 0:
                    percentage = (count / total_blocks) * 100
                    table.add_row(scope, str(count), f"{percentage:.1f}%")
            
            console.print(table)
            
            # Display file details
            console.print("\n[bold]Files with metadata:[/bold]")
            files_table = Table()
            files_table.add_column("File", style="blue")
            files_table.add_column("Blocks", style="magenta")
            
            for parsed_file in parsed_files:
                if parsed_file.has_metadata:
                    files_table.add_row(
                        parsed_file.file_path, 
                        str(len(parsed_file.metadata_blocks))
                    )
            
            console.print(files_table)
        
        # Save results to file if specified
        if output:
            result = {
                "summary": {
                    "total_files": len(parsed_files),
                    "total_blocks": total_blocks,
                    "scope_counts": scope_counts
                },
                "files": [
                    {
                        "path": pf.file_path,
                        "blocks": [
                            {
                                "metadata": block.metadata,
                                "scope": block.scope,
                                "line": block.line_number
                            }
                            for block in pf.metadata_blocks
                        ]
                    }
                    for pf in parsed_files if pf.has_metadata
                ]
            }
            
            with open(output, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2)
            
            console.print(f"\nResults saved to: [bold]{output}[/bold]")
    
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        sys.exit(1)


@cli.command()
@click.argument('file_path', type=click.Path(exists=True))
@click.option('--schema', '-s', type=click.Path(exists=True), help='Custom schema file for validation')
def validate(file_path: str, schema: Optional[str]):
    """
    Validate ADP metadata in a file against the schema.
    
    FILE_PATH is the file to validate.
    """
    try:
        if schema:
            schema_obj = load_schema(schema)
            parser = ADPParser(schema_name=schema_obj.name)
        else:
            parser = ADPParser()
        
        parsed_file = parser.parse_file(file_path)
        
        if not parsed_file.has_metadata:
            console.print(f"[yellow]No ADP metadata found in {file_path}[/yellow]")
            return
        
        console.print(f"Validating [bold blue]{file_path}[/bold blue]")
        
        valid_count = 0
        invalid_count = 0
        
        for metadata_block in parsed_file.metadata_blocks:
            is_valid = parser.validate_metadata(metadata_block.metadata)
            
            if is_valid:
                valid_count += 1
                console.print(f"  [green]✓[/green] Line {metadata_block.line_number} ({metadata_block.scope}): Valid metadata")
            else:
                invalid_count += 1
                errors = parser.get_validation_errors(metadata_block.metadata)
                console.print(f"  [red]✗[/red] Line {metadata_block.line_number} ({metadata_block.scope}): Invalid metadata")
                for error in errors:
                    console.print(f"    - {error}")
        
        if invalid_count == 0:
            console.print(f"\n[bold green]All {valid_count} metadata blocks are valid![/bold green]")
        else:
            console.print(f"\n[bold]Summary:[/bold] {valid_count} valid, {invalid_count} invalid")
    
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        sys.exit(1)


@cli.command()
@click.argument('path', type=click.Path(exists=True))
@click.option('--output', '-o', type=click.Path(), required=True, help='Output file for the graph visualization')
@click.option('--format', '-f', type=click.Choice(['png', 'svg', 'pdf']), default='png', help='Output format')
@click.option('--engine', '-e', type=click.Choice(['graphviz', 'matplotlib']), default='graphviz', 
              help='Visualization engine to use')
@click.option('--recursive/--no-recursive', default=True, help='Recursively scan directories')
def visualize(path: str, output: str, format: str, engine: str, recursive: bool):
    """
    Generate a knowledge graph visualization from ADP metadata.
    
    PATH is the file or directory to process.
    """
    try:
        parser = ADPParser()
        builder = GraphBuilder()
        
        console.print(f"Building knowledge graph from: [bold blue]{path}[/bold blue]")
        
        if os.path.isfile(path):
            parsed_file = parser.parse_file(path)
            if parsed_file.has_metadata:
                builder.add_file(parsed_file)
        else:
            parsed_files = parser.parse_directory(path, recursive=recursive)
            for parsed_file in parsed_files:
                if parsed_file.has_metadata:
                    builder.add_file(parsed_file)
        
        graph = builder.graph
        
        # Display summary
        console.print(f"\n[bold green]Knowledge Graph:[/bold green]")
        console.print(f"  Nodes: {len(graph.nodes)}")
        console.print(f"  Edges: {len(graph.edges)}")
        
        # Node type distribution
        node_types = {}
        for node_id, node in graph.nodes.items():
            if node.type not in node_types:
                node_types[node.type] = 0
            node_types[node.type] += 1
        
        console.print("\n[bold]Node Types:[/bold]")
        for node_type, count in node_types.items():
            console.print(f"  {node_type}: {count}")
        
        # Generate visualization
        if engine == 'graphviz':
            console.print(f"\nGenerating Graphviz visualization...")
            graph.visualize_graphviz(output_path=output, format=format)
        else:
            console.print(f"\nGenerating Matplotlib visualization...")
            if format != 'png':
                console.print("[yellow]Note: Matplotlib engine only supports PNG format[/yellow]")
            graph.visualize_matplotlib(output_path=output)
        
        console.print(f"[bold green]✓[/bold green] Visualization saved to: [bold]{output}[/bold]")
    
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        sys.exit(1)


@cli.command()
@click.argument('output_path', type=click.Path())
def create_schema(output_path: str):
    """
    Create a new ADP schema template file.
    
    OUTPUT_PATH is where to save the schema file.
    """
    try:
        # Get the default schema
        schema = get_default_schema()
        
        # Save it to the specified path
        schema.save(output_path)
        
        console.print(f"[bold green]✓[/bold green] Schema template saved to: [bold]{output_path}[/bold]")
        console.print("\nYou can now edit this file to customize the schema for your project.")
    
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        sys.exit(1)


@cli.command()
@click.argument('file_path', type=click.Path(exists=True))
@click.option('--language', '-l', help='Force language (py, js, ts, java, cs)')
def show(file_path: str, language: Optional[str]):
    """
    Display ADP metadata in a file with syntax highlighting.
    
    FILE_PATH is the file to display.
    """
    try:
        parser = ADPParser()
        parsed_file = parser.parse_file(file_path)
        
        if not parsed_file.has_metadata:
            console.print(f"[yellow]No ADP metadata found in {file_path}[/yellow]")
            return
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        console.print(f"[bold blue]ADP Metadata in {file_path}[/bold blue]\n")
        
        for metadata_block in parsed_file.metadata_blocks:
            console.print(f"[bold]Block at line {metadata_block.line_number} ({metadata_block.scope}):[/bold]")
            
            # Pretty-print the metadata
            json_str = json.dumps(metadata_block.metadata, indent=2)
            syntax = Syntax(json_str, "json", theme="monokai", line_numbers=True)
            console.print(Panel(syntax))
    
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        sys.exit(1)


@cli.command()
@click.argument('file_path', type=click.Path(exists=True))
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose debug output')
def debug(file_path: str, verbose: bool):
    """
    Debug parse operations for a file.
    
    FILE_PATH is the file to debug parse.
    """
    try:
        if verbose:
            logger.setLevel(logging.DEBUG)
            logging.getLogger("adp_py").setLevel(logging.DEBUG)
        
        parser = ADPParser()
        
        console.print(f"[bold]Debug parsing of:[/bold] {file_path}")
        console.print("\n[bold]File content:[/bold]")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            console.print(content)
        
        console.print("\n[bold]Parsing file...[/bold]")
        parsed_file = parser.parse_file(file_path)
        
        if parsed_file.has_metadata:
            console.print(f"\n[bold green]✓[/bold green] Found {len(parsed_file.metadata_blocks)} metadata blocks")
            
            for i, metadata_block in enumerate(parsed_file.metadata_blocks):
                console.print(f"\n[bold]Block {i+1} at line {metadata_block.line_number} ({metadata_block.scope}):[/bold]")
                json_str = json.dumps(metadata_block.metadata, indent=2)
                console.print(json_str)
        else:
            console.print("\n[bold red]✗[/bold red] No metadata blocks found")
            console.print("\n[bold]Common issues:[/bold]")
            console.print("  - Incorrect comment format (expected: @ai-metadata { ... })")
            console.print("  - Invalid JSON syntax in metadata")
            console.print("  - Unsupported file type")
    
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        if verbose:
            import traceback
            console.print(traceback.format_exc())
        sys.exit(1)


@cli.command()
@click.argument('path', type=click.Path(exists=True))
@click.option('--output', '-o', type=click.Path(), default="adp_knowledge_graph.html", 
              help='Output HTML file for the interactive visualization')
@click.option('--title', '-t', default="ADP Knowledge Graph", 
              help='Title for the visualization')
@click.option('--recursive/--no-recursive', default=True, help='Recursively scan directories')
def interactive(path: str, output: str, title: str, recursive: bool):
    """
    Generate an interactive HTML visualization of the knowledge graph.
    
    PATH is the file or directory to process.
    
    This creates an HTML file with a modern, interactive visualization powered by
    Cytoscape.js that can be opened in any web browser. The visualization includes:
    
    - Interactive node dragging, zooming, and panning
    - Multiple layout options (hierarchical, concentric, force-directed)
    - Search functionality for nodes and metadata
    - Detailed tooltips showing all node and edge metadata
    - Highlighting of connected nodes and edges
    """
    try:
        parser = ADPParser()
        builder = GraphBuilder()
        
        console.print(f"Building knowledge graph from: [bold blue]{path}[/bold blue]")
        
        if os.path.isfile(path):
            parsed_file = parser.parse_file(path)
            if parsed_file.has_metadata:
                builder.add_file(parsed_file)
        else:
            parsed_files = parser.parse_directory(path, recursive=recursive)
            for parsed_file in parsed_files:
                if parsed_file.has_metadata:
                    builder.add_file(parsed_file)
        
        graph = builder.graph
        
        # Display summary
        console.print(f"\n[bold green]Knowledge Graph:[/bold green]")
        console.print(f"  Nodes: {len(graph.nodes)}")
        console.print(f"  Edges: {len(graph.edges)}")
        
        # Node type distribution
        node_types = {}
        for node_id, node in graph.nodes.items():
            node_type = node.type.value if hasattr(node.type, 'value') else node.type
            if node_type not in node_types:
                node_types[node_type] = 0
            node_types[node_type] += 1
        
        console.print("\n[bold]Node Types:[/bold]")
        for node_type, count in sorted(node_types.items()):
            console.print(f"  {node_type}: {count}")
        
        # Generate interactive visualization
        console.print(f"\nGenerating interactive visualization...")
        output_path = graph.visualize_interactive(output_path=output, title=title)
        
        console.print(f"[bold green]✓[/bold green] Interactive visualization saved to: [bold]{output_path}[/bold]")
        console.print(f"Open this file in your web browser to view the interactive graph.")
    
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        sys.exit(1)


if __name__ == '__main__':
    cli() 