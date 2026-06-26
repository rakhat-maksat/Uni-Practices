with open("sample_data.txt", "a") as file:
    file.write("\nMes que un club")

with open("sample_data.txt") as file:
    print(file.read())