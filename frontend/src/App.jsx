import React, { useCallback, useState } from 'react';
import {
  ReactFlow,
  MiniMap,
  Controls,
  Background,
  useNodesState,
  useEdgesState,
  addEdge,
} from '@xyflow/react';

import '@xyflow/react/dist/style.css';
import axios from 'axios';

const API_URL = "http://localhost:5000/api"

export default function App() {
  const [nodes, setNodes, onNodesChange] = useNodesState(null);
  const [edges, setEdges, onEdgesChange] = useEdgesState(null);
  const [networkId, setNetworkId] = useState(null);

  axios.post(`${API_URL}/networks`, {"seed": 42}, {
    headers: { "Content-Type": "application/json" },
  }).then(function(response) {
    setNetworkId(response.data.networkId)
    setNodes(response.data.network.nodes)
    setEdges(response.data.network.edges)
  })

  console.log(nodes, edges, networkId)

  const onConnect = useCallback(
    (params) => setEdges((eds) => addEdge(params, eds)),
    [setEdges],
  );

  return (
    <div style={{ width: '100vw', height: '100vh' }}>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
      >
        <Controls />
        <MiniMap />
        <Background variant="dots" gap={12} size={1} />
      </ReactFlow>
    </div>
  );
}
