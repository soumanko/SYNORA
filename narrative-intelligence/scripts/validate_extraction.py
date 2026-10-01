"""
Real-provider extraction validation script.
Runs one Core30 extraction against a short text and reports taxonomy validity.
Does NOT retry on quota errors.
"""
import os
import sys
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.taxonomy.taxonomy_loader import TaxonomyLoader
from core.analysis.core30 import Core30Selector
from core.llm_provider import LLMProvider
from core.extraction.dimension_analyzer import FeatureExtractor
from core.extraction.feature_validator import FeatureValidator
from core.taxonomy.schemas import FeatureValue


def main():
    if not os.getenv("GEMINI_API_KEY") and not os.getenv("OPENAI_API_KEY") and not os.getenv("ANTHROPIC_API_KEY"):
        print("REAL_PROVIDER_TEST = BLOCKED_BY_PROVIDER_QUOTA")
        return
    
    print("=" * 70)
    print("EXTRACTION VALIDATION — REAL PROVIDER RUN")
    print("=" * 70)
    
    # Load taxonomy
    taxonomy_loader = TaxonomyLoader(
        taxonomy_path="data/storyscope/taxonomy.json",
        core30_path="data/storyscope/core30_approximation.json"
    )
    taxonomy = taxonomy_loader.load_taxonomy()
    core30_features = taxonomy_loader.load_core30()
    
    core30_ids = {f.id for f in core30_features}
    core_taxonomy = {k: v for k, v in taxonomy.items() if k in core30_ids}
    
    llm_provider = LLMProvider()
    extractor = FeatureExtractor(core_taxonomy, llm_provider)
    validator = FeatureValidator(core_taxonomy)
    
    text = """
    The old bookshop at the corner of Elm Street had been closed for years, but 
    tonight its door stood ajar. Sarah noticed the faint glow spilling onto the wet 
    pavement as she hurried home from the library. She hesitated, clutching her 
    umbrella. The rain dripped from the awning in a steady rhythm. Inside, shadows 
    moved between the shelves. She pushed the door wider. The bell above didn't ring.
    A man sat at the counter, reading. He looked up and smiled as if he'd been 
    expecting her. "You're late," he said.
    """
    
    print(f"\nText length: {len(text.split())} words")
    print("Extracting Core30 features...\n")
    
    try:
        features = extractor.extract_all(text)
    except Exception as e:
        if "quota" in str(e).lower() or "429" in str(e):
            print("REAL_PROVIDER_TEST = BLOCKED_BY_PROVIDER_QUOTA")
        else:
            print(f"EXTRACTION FAILED: {e}")
        return
    
    # Validate
    validated, metadata = validator.validate_feature_vector(features)
    
    stats = metadata["extraction_validation"]
    
    print("=" * 70)
    print("EXTRACTION VALIDATION RESULTS")
    print("=" * 70)
    print(f"\n  Total features attempted: {stats['total_features_attempted']}")
    print(f"  Valid features:           {stats['valid_features']}")
    print(f"  Invalid features:         {stats['invalid_features']}")
    print(f"  Missing features:         {stats['missing_features']}")
    
    invalid_diags = metadata.get("invalid_value_diagnostics", [])
    
    if invalid_diags:
        print(f"\n  INVALID VALUE DIAGNOSTICS ({len(invalid_diags)}):")
        for d in invalid_diags:
            print(f"\n    Feature: {d['feature_id']}")
            print(f"    Raw value: {d.get('raw_value')}")
            print(f"    Error: {d.get('error')}")
            if d.get('invalid_items'):
                print(f"    Invalid items: {d['invalid_items']}")
    else:
        print("\n  No invalid values detected.")
    
    print(f"\n  VALID FEATURES:")
    for fv in validated:
        if fv.value is not None:
            feature_name = core_taxonomy.get(fv.feature_id)
            name = feature_name.name if feature_name else fv.feature_id
            ftype = feature_name.type.value if feature_name else "?"
            print(f"    {fv.feature_id} ({name}) [{ftype}]: {fv.value}")
    
    # Check conformance
    non_null = [fv for fv in validated if fv.value is not None]
    all_conform = True
    for fv in non_null:
        if fv.feature_id in core_taxonomy:
            result = validator.validate_feature(fv)
            if not result.valid:
                all_conform = False
                print(f"\n  ⚠ POST-VALIDATION FAILURE: {fv.feature_id} = {fv.value}")
    
    print(f"\n{'=' * 70}")
    if all_conform:
        print("CONFORMANCE: Every non-null FeatureVector value conforms to taxonomy ✓")
    else:
        print("CONFORMANCE: Some values still do not conform to taxonomy ✗")
    print(f"{'=' * 70}")


if __name__ == "__main__":
    main()
