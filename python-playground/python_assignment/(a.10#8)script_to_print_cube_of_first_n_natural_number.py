# script to print cubes of first n natural number.
n = int(input("enter a natural number:"))
i = 1
while i <= n:
    cube = (i * i * i)
    print(cube, end=',')
    i += 1