import os
import time

test_file = os.path.abspath("printer_test.txt")

with open(test_file, "w") as f:
    f.write("FAYGANTS PRINTING SYSTEM\n")
    f.write("Windows printing test\n")
    f.write("If you can read this, printing works!\n")

os.startfile(test_file, "print")

print("Windows print command sent.")
print("Check the Epson printer.")
time.sleep(3)