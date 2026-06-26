from functools import reduce

numbers = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

# map() and filter()
squared   = list(map(lambda x: x**2, numbers))
evens     = list(filter(lambda x: x % 2 == 0, numbers))
odd_cubes = list(map(lambda x: x**3, filter(lambda x: x % 2 != 0, numbers)))

print("1. map() and filter()")
print(f"   Squared:    {squared}")
print(f"   Evens:      {evens}")
print(f"   Odd cubes:  {odd_cubes}")

# reduce()
total   = reduce(lambda acc, x: acc + x, numbers)
product = reduce(lambda acc, x: acc * x, numbers)
maximum = reduce(lambda acc, x: acc if acc > x else x, numbers)

print("\n2. reduce()")
print(f"   Sum:     {total}")
print(f"   Product: {product}")
print(f"   Max:     {maximum}")
