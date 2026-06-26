with open("sample_data.txt", "w") as file:
    file.write("Hello world")

file = open("sample_data.txt", "r")
content = file.read()
print(content)