import re

def fix(filename):
    with open(filename, 'r') as f:
        c = f.read()

    c = c.replace('failed_checks=[])', 'failed_checks=[], details={})')
    c = c.replace('failed_checks=["pov"])', 'failed_checks=["pov"], details={})')

    with open(filename, 'w') as f:
        f.write(c)

fix('tests/test_quality_gate.py')
fix('tests/test_forge_orchestrator.py')
