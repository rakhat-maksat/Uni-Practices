class Person:
    species = "Human"   # class variable

    def __init__(self, name, age):
        self.name = name
        self.age = age
        
print(Person.species)
print(p1.species)