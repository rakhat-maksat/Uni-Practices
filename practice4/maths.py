import math

# 1
gradus = int(input("Input degree: "))
radian = gradus * math.pi / 180
print(f"Output radian: {radian:.6f}")

# 2
h = int(input("Height: "))
first = int(input("Base, first value: "))
second = int(input("Base, second value: "))
ans = (first + second) / 2 * h
print(f"Expected Output: {ans}")

# 3
n = int(input("Input number of sides: "))
a = int(input("Input the length of a side: "))
ans = int((n * a**2) / (4 * math.tan(math.pi / n)))
print(f"The area of the polygon is: {ans}")

# 4
l = float(input("Length of base: "))
h = float(input("Height of parallelogram: "))
ans = l * h
print(f"Expected Output: {ans}")