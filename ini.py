class Profile():
    def __init__(self,name,surname,grade):
        self.name = name
        self.surname = surname
        self.grade = grade
    def __str__(self):
        return self.name
a = Profile('njwa','dlamini','ten')
print(a.surname)