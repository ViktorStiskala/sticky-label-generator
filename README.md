# Sticky label generator

A Python CLI utility for generating customizable sticky labels using XeLaTeX, with support for multiple label
formats and customization of label output using format files. The tool takes input in the form of a .tex file,
and the `--labels` argument can be provided multiple times to allow printing multiple labels on a single sheet.

## Usage

```
Usage: generate-labels [OPTIONS] FORMAT_FILE

Options:
  --skip INTEGER                  Number of labels to skip
  --labels <INTEGER FILENAME>...  Specify the number of labels and the input
                                  file  [required]
  --output_dir DIRECTORY          Output directory for PDF file
  --print-latex                   Print the generated LaTeX code to the
                                  terminal
  --help                          Show this message and exit.

```

## Formats

The utility uses format files, specified in yaml, to specify the output format for XeLaTeX for specific sticky label types.
The format files include information such as the total number of labels, font size, and page margins.
This allows users to create custom output formats for their labels. An example of a format file is shown below:

```yaml
%YAML 1.1
---

generator:
  label_count: 24
  font_size: 10pt

format:
  LabelCols: 3
  LabelRows: 8
  LeftPageMargin: 0mm
  RightPageMargin: 0mm
  TopPageMargin: 3mm
  BottomPageMargin: 3mm

```
