# Ansible Inventory to PDF of Network Diagram

## Prereqs
So obviously you have the `pip install -r requirements.txt` but, if you want a pdf in addition to the html, you also need to install "[wkhtmltopdf](https://wkhtmltopdf.org/downloads.html)" which is what the python package pdfkit is a wrapper for. **You can skip this step if you don't need a pdf and just want the html (in fact you don't even need the `pdfkit` in `requirements.txt` in that case).** You need the wkhtmltopdf binary in your path for pdfkit to convert the html output to a pdf. I think most linux package managers have it, otherwise you can download from source.

## Usage
Run script directly: `py ansible2pdf.py <name_of_file>`\
If you want to import it into another script instead (example in `caller.py`), just call the main function: `ansible2pdf.main()`,\
which expects the name of a yaml file (specifically an ansible inventory) as a required argument, the name of the output file as an optional argument, and a labelling option (see below) as an optional argument.

## About labels on the network diagram
By default, the names of the hosts listed in the ansible inventory are used. These can get a little too long for the circles, however, so there is an option to just use numerical indices instead (supply "indices" as the third argument). There is actually an even further option to customize completely what happens to the labels (supply "custom" as the third argument), but this requires you to write a function yourself and reassign the  `custom_labeler()` function with it. In this case, you would have to `import ansible2pdf` and then `ansible2pdf.custom_labeler = your_function(label: str)` before calling `ansible2pdf.main()`; see `caller.py` for an example. **You <u>cannot</u> use the `from ansible2pdf import` syntax for custom_labeler!**

### Examples included in this directory based on the included example.yaml