from alerts import SustainedAlert, top_processes, format_top

# Test 1: 10 readings above 80 in a row should fire exactly once, on the 10th reading
det = SustainedAlert(threshold=80, seconds=10)
print("Test 1:", [det.update(85) for _ in range(10)])

# Test 2: the same episode continuing should NOT fire again
print("Test 2 (continues):", [det.update(85) for _ in range(3)])

# Test 3: a dip below the limit resets the streak, then a new 10 readings fire again
det2 = SustainedAlert(threshold=80, seconds=10)
values = [85, 85, 40] + [85] * 10
print("Test 3:", [det2.update(v) for v in values])

# Test 4: the top-process snapshot (takes about 1 second)
print("Top processes:", format_top(top_processes()))