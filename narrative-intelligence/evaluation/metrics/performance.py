from typing import Dict, Any

def calculate_performance(run_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extracts latency, LLM calls, and estimated tokens from run data.
    """
    # Assuming start and end times are ISO strings
    from datetime import datetime
    
    try:
        start = datetime.fromisoformat(run_data.get("started_at", "").replace('Z', '+00:00'))
        end = datetime.fromisoformat(run_data.get("completed_at", "").replace('Z', '+00:00'))
        total_runtime = (end - start).total_seconds()
    except ValueError:
        total_runtime = None
        
    return {
        "total_runtime_seconds": total_runtime,
        "generation_latency": None, # If recorded in details
        "analysis_latency": None,
        "revision_latency": None,
        "llm_calls": len(run_data.get("drafts", [])) + len(run_data.get("revision_history", [])), 
        "input_tokens": "unavailable",
        "output_tokens": "unavailable",
        "total_tokens": "unavailable",
        "estimated_cost": "unavailable"
    }
