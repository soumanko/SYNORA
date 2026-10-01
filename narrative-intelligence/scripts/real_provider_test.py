"""
Real-provider validation script for the Forge revision pipeline.
Runs one complete Draft 0 -> Draft 1 cycle and reports:
  - Actual feature values before/after
  - Targeted vs incidental changes
  - Direction match results
  - Intent preservation results

Does NOT retry on quota errors. Reports BLOCKED_BY_PROVIDER_QUOTA if unavailable.
"""
import os
import sys
import json

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.routes.forge import generate_story, GenerateRequest


def main():
    # Check if provider is configured
    if not os.getenv("GEMINI_API_KEY") and not os.getenv("OPENAI_API_KEY") and not os.getenv("ANTHROPIC_API_KEY"):
        print("REAL_PROVIDER_TEST = BLOCKED_BY_PROVIDER_QUOTA")
        return
    
    print("=" * 70)
    print("FORGE REVISION VALIDATION — REAL PROVIDER RUN")
    print("=" * 70)
    
    req = GenerateRequest(
        prompt="Write a short mystery scene about a student who discovers an unlocked room in an empty university building.",
        genre="Mystery",
        tone="Suspenseful",
        pov="Third-person limited",
        length=200,
        constraints=[]
    )
    
    try:
        response = generate_story(req)
    except Exception as e:
        if "quota" in str(e).lower() or "429" in str(e):
            print("REAL_PROVIDER_TEST = BLOCKED_BY_PROVIDER_QUOTA")
        else:
            print(f"REAL_PROVIDER_TEST = FAILED: {e}")
        return
    
    print(f"\nStatus: {response['status']}")
    if "error" in response:
        print(f"Error: {response['error']}")
        return
    
    # --- REVISION HISTORY ---
    print("\n" + "=" * 70)
    print("REVISION HISTORY")
    print("=" * 70)
    
    for entry in response.get("revision_history", []):
        version = entry["version"]
        content = entry["content"]
        wc = len(content.split())
        print(f"\n--- {version} (word count: {wc}) ---")
        print(content[:200] + ("..." if len(content) > 200 else ""))
    
    # --- REVISION PLAN ---
    plan = response.get("revision_plan", {})
    print("\n" + "=" * 70)
    print("REVISION PLAN")
    print("=" * 70)
    if plan.get("interventions"):
        for i, inv in enumerate(plan["interventions"]):
            print(f"\n  Intervention {i+1}:")
            print(f"    Target: {inv['target']['feature_id']} ({inv['target']['feature_name']})")
            print(f"    Direction: {inv.get('direction', 'N/A')}")
            print(f"    Reason: {inv['diagnostic_reason']}")
            print(f"    Instruction: {inv['revision_instruction']}")
    else:
        print("  No interventions planned.")
    
    print(f"\n  Revision Summary: {response.get('revision_summary', 'N/A')}")
    
    # --- REVISION EFFECT ---
    print("\n" + "=" * 70)
    print("REVISION EFFECT EVALUATION")
    print("=" * 70)
    
    effect = response.get("revision_effect", {})
    
    if effect.get("status") == "unavailable":
        print(f"  UNAVAILABLE: {effect.get('reason')}")
    else:
        print(f"\n  Summary: {json.dumps(effect.get('summary', {}), indent=4)}")
        
        print("\n  TARGETED CHANGES:")
        for tc in effect.get("targeted_changes", []):
            print(f"    Feature: {tc['feature_id']} ({tc['feature_name']})")
            print(f"      Type: {tc['feature_type']}")
            if tc.get("comparison_type") == "numeric":
                print(f"      Before: {tc.get('before')}")
                print(f"      After: {tc.get('after')}")
                print(f"      Delta: {tc.get('delta')}")
                print(f"      Direction observed: {tc.get('direction_observed')}")
                print(f"      Direction match: {tc.get('direction_match')}")
            elif tc.get("comparison_type") == "categorical":
                print(f"      Before: {tc.get('before')}")
                print(f"      After: {tc.get('after')}")
                print(f"      Changed: {tc.get('changed')}")
                print(f"      Direction match: {tc.get('direction_match')}")
            elif tc.get("comparison_type") == "set":
                print(f"      Before: {tc.get('before')}")
                print(f"      After: {tc.get('after')}")
                print(f"      Added: {tc.get('added')}")
                print(f"      Removed: {tc.get('removed')}")
                print(f"      Retained: {tc.get('retained')}")
            else:
                print(f"      Status: {tc.get('status')}")
                if tc.get('reason'):
                    print(f"      Reason: {tc.get('reason')}")
        
        print("\n  INCIDENTAL CHANGES:")
        for ic in effect.get("incidental_changes", []):
            print(f"    Feature: {ic['feature_id']} ({ic['feature_name']})")
            if ic.get("comparison_type") == "numeric":
                print(f"      Delta: {ic.get('delta')}")
            elif ic.get("comparison_type") == "set":
                print(f"      Added: {ic.get('added')}, Removed: {ic.get('removed')}")
            elif ic.get("comparison_type") == "categorical":
                print(f"      Before: {ic.get('before')} -> After: {ic.get('after')}")
        
        if not effect.get("incidental_changes"):
            print("    (none)")
        
        print(f"\n  UNCHANGED FEATURES: {len(effect.get('unchanged_features', []))}")
        
        print("\n  DIRECTIONAL SUCCESS:")
        for ds in effect.get("directional_success", []):
            print(f"    {ds['feature_id']}: {ds['direction_match']}")
    
    # --- INTENT PRESERVATION ---
    print("\n" + "=" * 70)
    print("INTENT PRESERVATION EVALUATION")
    print("=" * 70)
    
    ip = response.get("intent_preservation", {})
    for check_name, check_result in ip.items():
        if isinstance(check_result, dict):
            status = check_result.get("status", "unknown")
            method = check_result.get("method", "")
            print(f"\n  {check_name}: {status}")
            if method:
                print(f"    method: {method}")
            # Print additional details for specific checks
            if check_name == "word_count":
                print(f"    requested: {check_result.get('requested_length')}")
                print(f"    actual: {check_result.get('actual_length')}")
            elif check_name == "named_entities" and check_result.get("preserved_in_draft_1"):
                print(f"    preserved: {check_result.get('preserved_in_draft_1')}")
                if check_result.get("missing_from_draft_1"):
                    print(f"    missing: {check_result.get('missing_from_draft_1')}")
    
    print("\n" + "=" * 70)
    print("VALIDATION COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()
