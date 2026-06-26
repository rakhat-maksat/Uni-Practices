import re

# 1
print("1:", bool(re.fullmatch(r"ab*", "abbb")))

# 2
print("2:", bool(re.fullmatch(r"ab{2,3}", "abb")))

# 3
text3 = "hello_world test_var invalid_Var"
print("3:", re.findall(r"\b[a-z]+_[a-z]+\b", text3))

# 4
text4 = "Hello world Test ABC"
print("4:", re.findall(r"\b[A-Z][a-z]+\b", text4))

# 5 
print("5:", bool(re.fullmatch(r"a.*b", "axxxb")))

# 6
text6 = "Hello, world. Python is cool"
print("6:", re.sub(r"[ ,\.]", ":", text6))

# 7
def snake_to_camel(text):
    return re.sub(r"_([a-z])", lambda x: x.group(1).upper(), text)

print("7:", snake_to_camel("hello_world_example"))

# 8
text8 = "HelloWorldPython"
print("8:", re.findall(r"[A-Z][^A-Z]*", text8))

# 9
text9 = "HelloWorldPython"
print("9:", re.sub(r"(?<!^)([A-Z])", r" \1", text9))

# 10
def camel_to_snake(text):
    return re.sub(r"(?<!^)([A-Z])", r"_\1", text).lower()

print("10:", camel_to_snake("helloWorldExample"))