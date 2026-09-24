import csv
from io import StringIO
from html import escape

def export_rows(rows, kind):
    output = StringIO(newline="")
    writer = csv.writer(output, delimiter="\t" if kind == "anki" else ",", lineterminator="\n")
    if kind == "anki":
        output.write("#separator:Tab\n#html:true\n#columns:Japanese\tReading\tEnglish\tNotes\n")
    else:
        writer.writerow(["Japanese", "Reading", "English", "Notes"])
    for row in rows:
        values = [row.jp, row.reading, row.en, row.notes]
        if kind == "anki": values = [escape(v).replace("\n", "<br>") for v in values]
        else: values = [("'"+v if v.lstrip().startswith(("=", "+", "-", "@")) else v) for v in values]
        writer.writerow(values)
    return output.getvalue().encode("utf-8-sig" if kind == "csv" else "utf-8")
