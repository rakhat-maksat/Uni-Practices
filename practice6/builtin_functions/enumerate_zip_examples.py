# enumerate() and zip()
fruits  = ["apple", "banana", "cherry"]
prices  = [1.2, 0.5, 3.0]
in_stock = [True, False, True]

print("\n3. enumerate() and zip()")
print("   enumerate:")
for i, fruit in enumerate(fruits, start=1):
    print(f"   {i}. {fruit}")

print("   zip (2 iterables):")
for fruit, price in zip(fruits, prices):
    print(f"   {fruit}: ${price}")

print("   zip (3 iterables):")
for fruit, price, stock in zip(fruits, prices, in_stock):
    status = "✔" if stock else "✘"
    print(f"   {status} {fruit}: ${price}")