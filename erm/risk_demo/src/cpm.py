import networkx as nx

def calculate_cpm_end_date(tasks_df, relationships_df):
    G = nx.DiGraph()
    
    # Add Nodes
    for _, row in tasks_df.iterrows():
        G.add_node(row['task_id'], duration=row['duration'], early_finish=0)
        
    # Add Edges
    for _, row in relationships_df.iterrows():
        G.add_edge(row['predecessor'], row['successor'])
        
    # Forward Pass
    for node in nx.topological_sort(G):
        predecessors = list(G.predecessors(node))
        
        if not predecessors:
            # It's a Start Node
            early_start = 0
        else:
            # Early Start is the MAX Early Finish of all predecessors
            early_start = max(G.nodes[p]['early_finish'] for p in predecessors)
            
        # Calculate Early Finish for this node
        G.nodes[node]['early_finish'] = early_start + G.nodes[node]['duration']
    
    # Project End Date is the max of all early finishes
    return max(nx.get_node_attributes(G, 'early_finish').values())