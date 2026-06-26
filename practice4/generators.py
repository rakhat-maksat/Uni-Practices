# 1
def square(n):
    for i in range(n+1):
        yield i * i

n = int(input())
for num in square(n):
    print(num)

# 2
def even(n):
    for i in range(n+1):
        if i % 2 == 0:
            yield i

n = int(input())
evens = even(n)
print(",".join(str(num) for num in evens))


# 3
def num(n):
    for i in range(n+1):
        if i % 3 == 0 and i % 4 == 0:
            yield i

n = int(input())
nums = num(n)
for x in nums:
    print(x, end = " ")


# 4
def square(a, b):
    for i in range(a, b + 1):
        yield i * i

a, b = map(int, input().split())
squares = square(a, b)
for x in squares:
    print(x, end = " ")


# 5
def down(n):
    for i in range(n, -1, -1):
        yield i 

n = int(input())
nums = down(n)
for num in nums:
    print(num, end = " ")