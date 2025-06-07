
import React, { useMemo } from 'react';
import { WorkflowStep } from '../../types';
// For a more complex visualization, consider libraries like react-flow-renderer or d3.
// This is a simplified textual/basic SVG representation.

interface DAGViewProps {
  steps: WorkflowStep[];
}

interface Node {
  id: string;
  label: string;
  x: number;
  y: number;
  width: number;
  height: number;
}

interface Edge {
  id: string;
  source: string;
  target: string;
}

const DAGView: React.FC<DAGViewProps> = ({ steps }) => {
  const { nodes, edges, maxWidth, maxHeight } = useMemo(() => {
    if (!steps || steps.length === 0) {
      return { nodes: [], edges: [], maxWidth: 0, maxHeight: 0 };
    }

    const stepMap = new Map(steps.map(step => [step.id, step]));
    const nodesArr: Node[] = [];
    const edgesArr: Edge[] = [];

    // Simple layout: group by dependency level
    const levels: string[][] = [];
    const stepToLevel: { [key: string]: number } = {};

    let currentLevelSteps = steps.filter(s => !s.dependencies || s.dependencies.length === 0);
    let level = 0;

    while (currentLevelSteps.length > 0) {
      levels[level] = currentLevelSteps.map(s => s.id);
      currentLevelSteps.forEach(s => stepToLevel[s.id] = level);
      
      const nextLevelSteps = new Set<WorkflowStep>();
      steps.forEach(s => {
        if (s.dependencies && s.dependencies.every(dep => stepToLevel[dep] < level +1)) {
            if (stepToLevel[s.id] === undefined) { // not yet placed
                 let maxDepLevel = -1;
                 s.dependencies.forEach(dep => {
                     if(stepToLevel[dep] !== undefined) maxDepLevel = Math.max(maxDepLevel, stepToLevel[dep]);
                 });
                 if(maxDepLevel === level){ // if all dependencies are in current or previous levels
                    nextLevelSteps.add(s);
                 }
            }
        }
      });
      // A bit more robust: find steps whose dependencies are ALL in placed levels
      const allPlacedStepIds = new Set(Object.keys(stepToLevel));
      const potentialNextLevelSteps = steps.filter(s => !allPlacedStepIds.has(s.id) && s.dependencies.every(depId => allPlacedStepIds.has(depId)));

      currentLevelSteps = potentialNextLevelSteps;
      level++;
      if (level > steps.length) break; // prevent infinite loop for cyclic or broken deps
    }
    
    // If levels are not well-formed (e.g. cycles or unassigned), fall back to simple list
    if (Object.keys(stepToLevel).length !== steps.length) {
        steps.forEach((s, i) => {
            if (stepToLevel[s.id] === undefined) stepToLevel[s.id] = levels.length > 0 ? levels.length : 0; // Put remaining in new level
            if(!levels[stepToLevel[s.id]]) levels[stepToLevel[s.id]] = [];
            if(!levels[stepToLevel[s.id]].includes(s.id)) levels[stepToLevel[s.id]].push(s.id);
        });
    }


    const NODE_WIDTH = 150;
    const NODE_HEIGHT = 60;
    const X_SPACING = 80;
    const Y_SPACING = 60;
    let currentMaxWidth = 0;

    levels.forEach((levelSteps, lvlIdx) => {
      const y = lvlIdx * (NODE_HEIGHT + Y_SPACING) + Y_SPACING / 2;
      levelSteps.forEach((stepId, stepIdxInLvl) => {
        const x = stepIdxInLvl * (NODE_WIDTH + X_SPACING) + X_SPACING / 2;
        const step = stepMap.get(stepId);
        if (step) {
          nodesArr.push({ id: step.id, label: step.name, x, y, width: NODE_WIDTH, height: NODE_HEIGHT });
          currentMaxWidth = Math.max(currentMaxWidth, x + NODE_WIDTH);

          step.dependencies.forEach(depId => {
            edgesArr.push({ id: `${depId}-${step.id}`, source: depId, target: step.id });
          });
        }
      });
    });
    
    const finalMaxHeight = levels.length * (NODE_HEIGHT + Y_SPACING);

    return { nodes: nodesArr, edges: edgesArr, maxWidth: currentMaxWidth, maxHeight: finalMaxHeight };
  }, [steps]);

  if (steps.length === 0) {
    return <p className="text-gray-400">No steps to visualize.</p>;
  }

  const getNodeById = (id: string) => nodes.find(n => n.id === id);

  return (
    <div className="overflow-auto p-4 bg-gray-800 rounded-lg">
      <svg width={Math.max(maxWidth, 400)} height={Math.max(maxHeight, 200)} className="min-w-full">
        <defs>
          <marker
            id="arrowhead"
            markerWidth="10"
            markerHeight="7"
            refX="0"
            refY="3.5"
            orient="auto"
          >
            <polygon points="0 0, 10 3.5, 0 7" fill="#9ca3af" /> {/* gray-400 */}
          </marker>
        </defs>
        {edges.map(edge => {
          const sourceNode = getNodeById(edge.source);
          const targetNode = getNodeById(edge.target);
          if (!sourceNode || !targetNode) return null;
          
          const x1 = sourceNode.x + sourceNode.width / 2;
          const y1 = sourceNode.y + sourceNode.height;
          const x2 = targetNode.x + targetNode.width / 2;
          const y2 = targetNode.y;

          // Simple straight line, adjust for arrowhead
          const length = Math.sqrt((x2-x1)*(x2-x1) + (y2-y1)*(y2-y1));
          const arrowOffset = 10; // arrowhead size
          const targetXAdjusted = x2 - arrowOffset * (x2-x1)/length;
          const targetYAdjusted = y2 - arrowOffset * (y2-y1)/length;


          return (
            <line
              key={edge.id}
              x1={x1}
              y1={y1}
              x2={targetXAdjusted}
              y2={targetYAdjusted}
              stroke="#6b7280" // gray-500
              strokeWidth="2"
              markerEnd="url(#arrowhead)"
            />
          );
        })}
        {nodes.map(node => (
          <g key={node.id} transform={`translate(${node.x}, ${node.y})`}>
            <rect
              width={node.width}
              height={node.height}
              rx="8"
              fill="#2d3748" // gray-800, but Tailwind uses #1f2937 for bg-gray-800, maybe use #374151 (gray-700) for contrast
              stroke="#4b5563" // gray-600
              strokeWidth="1"
            />
            <text
              x={node.width / 2}
              y={node.height / 2}
              textAnchor="middle"
              dominantBaseline="central"
              fill="#e5e7eb" // gray-200
              fontSize="12px"
              fontWeight="medium"
              className="select-none"
            >
              {node.label.length > 20 ? node.label.substring(0,18) + '...' : node.label}
            </text>
             <title>{node.label} (ID: {node.id})</title> {/* Tooltip */}
          </g>
        ))}
      </svg>
    </div>
  );
};

export default DAGView;
