import re

with open('tests/test_intent_preservation.py', 'r') as f:
    c = f.read()

c = re.sub(r'result\["(pov|word_count|genre|constraints|named_entities|tone|semantic_plot_consistency)"\]', r'result.details["\1"]', c)

with open('tests/test_intent_preservation.py', 'w') as f:
    f.write(c)
