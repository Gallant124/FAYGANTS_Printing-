import win32print

printer_name = "EPSON L3250 Series"

printer = win32print.OpenPrinter(printer_name)

job = win32print.StartDocPrinter(
    printer,
    1,
    ("FAYGANTS Printer Test", None, "RAW")
)

win32print.StartPagePrinter(printer)

win32print.WritePrinter(
    printer,
    b"FAYGANTS PRINTING SYSTEM\n"
    b"Printer connection test successful!\n"
)

win32print.EndPagePrinter(printer)
win32print.EndDocPrinter(printer)
win32print.ClosePrinter(printer)

print("Print job sent successfully!")