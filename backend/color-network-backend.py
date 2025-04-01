# app.py
from flask import Flask, jsonify, request
from flask_cors import CORS
import networkx as nx
import random
import colorsys
import uuid

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Store networks in memory (in production, use a proper database)
networks = {}

class HSLColorNetwork:
    def __init__(self, num_nodes=20, edge_probability=0.2, seed=None):
        """Initialize a random network with HSL colored nodes."""
        if seed is not None:
            random.seed(seed)
            
        self.G = nx.erdos_renyi_graph(n=num_nodes, p=edge_probability, seed=seed)
        
        for node in self.G.nodes():
            hue = random.randint(0, 360)
            saturation = random.randint(50, 100) # Make colours more vibrant
            lightness = random.randint(40, 70) # Make sure they aren't too bright or too dark
            # All personal preferences for the saturation and lightness
            
            self.G.nodes[node]['hsl'] = (hue, saturation, lightness)
            self.G.nodes[node]['color'] = self._hsl_to_hex(hue, saturation, lightness)
    
    def _hsl_to_hex(self, h, s, l):
        """Convert HSL values to hex color string."""
        # Normalize to [0,1] range for colorsys
        h_norm = h / 360.0
        s_norm = s / 100.0
        l_norm = l / 100.0
        
        # Convert HSL to RGB
        r, g, b = colorsys.hls_to_rgb(h_norm, l_norm, s_norm)
        
        # Convert RGB to hex format
        return "#{:02x}{:02x}{:02x}".format(
            int(r * 255),
            int(g * 255),
            int(b * 255)
        )
    
    def update(self, hue_influence=0.1):
        """Update node colors based on their connections."""
        # Store new colors to apply after all calculations (to avoid order effects)
        new_colors = {}
        
        # Update each node's color based on its neighbors
        for node in self.G.nodes():
            neighbors = list(self.G.neighbors(node))
            if not neighbors:
                continue
                
            current_hue, current_sat, current_light = self.G.nodes[node]['hsl']
            
            # Addition of hsl
            neighbor_hue_sum = sum(self.G.nodes[neigh]['hsl'][0] for neigh in neighbors)
            new_hue = ((current_hue + neighbor_hue_sum) * hue_influence) % 360
            
            new_colors[node] = (new_hue, current_sat, current_light)
        
        # Apply all new colors
        for node, (h, s, l) in new_colors.items():
            self.G.nodes[node]['hsl'] = (h, s, l)
            self.G.nodes[node]['color'] = self._hsl_to_hex(h, s, l)
    
    def to_json(self):
        """Convert the network to a JSON-serializable format for the frontend."""
        pos = nx.spring_layout(self.G, seed=42)
        
        nodes = []
        for node, attrs in self.G.nodes(data=True):
            nodes.append({
                'id': str(node),
                'color': attrs['color'],
                'hsl': attrs['hsl'],
                'x': float(pos[node][0]),  # Convert numpy values to native Python types
                'y': float(pos[node][1])
            })
        
        edges = []
        for source, target in self.G.edges():
            edges.append({
                'source': str(source),
                'target': str(target)
            })
        
        return {
            'nodes': nodes,
            'edges': edges
        }

@app.route('/api/networks', methods=['POST'])
def create_network():
    data = request.json
    num_nodes = data.get('num_nodes', 20)
    edge_probability = data.get('edge_probability', 0.2)
    seed = data.get('seed')
    
    network = HSLColorNetwork(num_nodes, edge_probability, seed)
    network_id = str(uuid.uuid4())
    networks[network_id] = network
    
    return jsonify({
        'network_id': network_id,
        'network': network.to_json()
    })

@app.route('/api/networks/<network_id>', methods=['GET'])
def get_network(network_id):
    if network_id not in networks:
        return jsonify({'error': 'Network not found'}), 404
    
    return jsonify({
        'network_id': network_id,
        'network': networks[network_id].to_json()
    })

@app.route('/api/networks/<network_id>/update', methods=['POST'])
def update_network(network_id):
    if network_id not in networks:
        return jsonify({'error': 'Network not found'}), 404
    
    data = request.json
    hue_influence = data.get('hue_influence', 0.1)
    update_mode = data.get('update_mode', 'add')
    
    networks[network_id].update(hue_influence, update_mode)
    
    return jsonify({
        'network_id': network_id,
        'network': networks[network_id].to_json()
    })

if __name__ == '__main__':
    app.run(debug=True)
