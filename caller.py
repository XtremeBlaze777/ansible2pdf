import ansible2pdf

ansible2pdf.custom_labeler = lambda x: x + " (custom)"

ansible2pdf.main(
    file = "example.yaml",
    out_file = "caller",
    graph_labeling = "custom"
)