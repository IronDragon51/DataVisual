import requests
import networkx as nx
import holoviews as hv
import pandas as pd  # Add import for pandas
from holoviews.operation.datashader import datashade
from holoviews import opts

hv.extension('bokeh')

# Amboss API configuration
API_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ2ZXJzaW9uIjowLjEsImlhdCI6MTcxOTA3ODI0NiwiZXhwIjoxNzIxNjcwMjQ2LCJpc3MiOiJhcGkuYW1ib3NzLnNwYWNlIiwic3ViIjoiNTQ1NTVmOWItZDhjOS00OGYzLWFiMjQtYjM2NzFhMTRiYTEyIn0.9tMtcJA1EnDgh2Ckp1tZbB8oWUoniWQzRWI_-qOgczg'
API_URL = 'https://api.amboss.space/graphql'

# GraphQL query for fetching node and channel data
query = """
{
  nodes {
    pub_key
    channels {
      capacity
      node1_pub
      node2_pub
    }
  }
}
"""

# Request headers including the API key
headers = {
    'Content-Type': 'application/json',
    'Authorization': f'Bearer {API_KEY}'
}

# Fetch Bitcoin Lightning Network Data from Amboss
response = requests.post(API_URL, json={'query': query}, headers=headers)

# Check the response status code and content
print(f"Response Status Code: {response.status_code}")

try:
    response_json = response.json()
    if 'data' in response_json and 'nodes' in response_json['data']:
        nodes_data = response_json['data']['nodes']
    else:
        raise KeyError('data or nodes not found in response')
except (requests.exceptions.JSONDecodeError, KeyError) as e:
    print("Error decoding JSON or accessing data: ", e)
    nodes_data = []

# Use mock data if API data is invalid
if not nodes_data:
    print("Using mock data due to invalid API response.")
    mock_data = [
        {"pub_key": "A", "channels": [{"node1_pub": "A", "node2_pub": "B", "capacity": 1000}]},
        {"pub_key": "B", "channels": [{"node1_pub": "B", "node2_pub": "C", "capacity": 1500}]},
        {"pub_key": "C", "channels": [{"node1_pub": "C", "node2_pub": "A", "capacity": 2000}]}
    ]
    nodes_data = mock_data

# Print nodes_data to debug
print("Nodes Data:")
print(nodes_data)

# Prepare the Data
def create_network_graph(data):
    G = nx.Graph()
    for node in data:
        channels = node.get('channels', [])  # Use .get() to handle missing 'channels' gracefully
        for channel in channels:
            G.add_edge(channel['node1_pub'], channel['node2_pub'], weight=channel['capacity'])
    return G

G = create_network_graph(nodes_data)

# Print graph details to debug
print("Graph Details:")
print(G.nodes)
print(G.edges)

# Create Visualization
def draw_network(G):
    # Extract positions for each node
    pos = nx.spring_layout(G, scale=2)
    nodes = hv.Nodes(pd.DataFrame.from_dict(dict(G.nodes(data=True)), orient='index', columns=['index', 'x', 'y']))
    edges = hv.Graph(((G.edges(), nodes)))

    # Customize the plot
    opts.defaults(
        opts.Graph(node_color='index', node_size=10, edge_line_width='weight', edge_color='weight', width=800, height=800, tools=['hover'])
    )

    # Use datashader to handle large graphs efficiently
    shaded_graph = datashade(edges, normalization='log', cmap='viridis', line_width=2)
    return shaded_graph

# Check if nodes_data is not empty before creating visualization
if nodes_data:
    graph = draw_network(G)
    hv.save(graph, 'lightning_network.html', backend='bokeh')
else:
    print("No data available to visualize")
