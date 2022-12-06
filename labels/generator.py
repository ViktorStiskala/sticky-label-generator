from itertools import repeat, chain
from math import ceil

import yaml
import shutil
import subprocess
import tempfile
import typing
from subprocess import CalledProcessError

import click
from datetime import datetime
from pathlib import Path


LATEX_HEADER = '''\
\\documentclass[a4paper,%(font_size)s]{extarticle}
\\usepackage[utf8]{inputenc}
\\usepackage[newdimens]{labels}
\\usepackage{graphicx}

\\usepackage{fontspec}
\\setmainfont{Helvetica}

%(label_params)s

\\LabelInfotrue
%%\\LabelGridtrue

\\begin{document}
\\begin{labels}
'''


class FormatParser:
    REQUIRED_SECTIONS = {'generator', 'format'}

    def __init__(self, conffile: typing.IO):
        config = yaml.safe_load(conffile)

        self.config = config
        self.verify()

    @property
    def label_count(self) -> int:
        return int(self.config['generator']['label_count'])

    @property
    def font_size(self) -> str:
        try:
            return self.config['generator']['font_size']
        except KeyError:
            return '14pt'

    @property
    def labels_format(self) -> str:
        latex = []
        section = self.config['format']
        for key, val in section.items():
            if val is None:
                latex.append(f'\\{key}')
            else:
                latex.append(f'\\{key}={val}')

        return '\n'.join(latex)

    def verify(self):
        sections = set(self.config.keys())
        if not self.REQUIRED_SECTIONS.issubset(sections):  # not all values are present in sections
            raise click.ClickException(f"Missing required sections in format file: {', '.join(self.REQUIRED_SECTIONS)}")

        try:
            assert self.label_count
        except (KeyError, ValueError):
            raise click.ClickException("LabelCount in [generator] is required.")


def generate_content(skip_labels: int, labels_total: int, labels: typing.Tuple[int, typing.IO]) -> typing.Iterator[str]:
    total = skip_labels

    # empty fields
    for i in range(skip_labels):
        yield '\\quad'

    for num_labels, input_f in labels:
        total += num_labels
        content = input_f.read().strip()

        for i in range(num_labels):
            yield content

    # empty fields until end of page
    for i in range(labels_total - (total % labels_total)):
        yield '\\quad'


@click.command()
@click.argument('format_file', type=click.File(), required=True)
@click.option('--skip', type=int, default=0, help='Number of labels to skip')
@click.option('--labels', nargs=2, type=(int, click.File()), multiple=True, required=True, help='Specify the number of labels and the input file')
@click.option('--output_dir', type=click.Path(file_okay=False), default=datetime.today().strftime('%Y-%m-%d'), help='Output directory for PDF file')
@click.option('--print-latex', is_flag=True, help='Print the generated LaTeX code to the terminal')
def generate_labels(labels: typing.Tuple[int, typing.IO], format_file: typing.IO, skip: int, output_dir: typing.Optional[typing.Union[str, Path]], print_latex: bool) -> None:
    format_config = FormatParser(format_file)

    if not isinstance(output_dir, Path):
        output_dir = Path(output_dir)
        output_dir.mkdir(exist_ok=True)

    # Generate LaTeX code for the labels
    latex = LATEX_HEADER % {'font_size': format_config.font_size, 'label_params': format_config.labels_format} + '\n'

    for item in generate_content(skip, format_config.label_count, labels):
        latex += item + '\n\n'

    latex += '\\end{labels}\n'
    latex += '\\end{document}\n'

    # Print the generated LaTeX code to the terminal if the --print-latex flag is set
    if print_latex:
        click.echo(latex)

    with tempfile.TemporaryDirectory() as dirname:
        for show_grid in (False, True):
            latex_file = Path(dirname) / ('labels.tex' if not show_grid else 'grid.tex')

            with open(latex_file, 'w') as f:
                if show_grid:
                    f.write(latex.replace('%\\LabelGridtrue', '\\LabelGridtrue'))
                else:
                    f.write(latex)

            # Execute pdflatex to generate the PDF file
            process = subprocess.run(
                ['xelatex', latex_file],
                input=b'',
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=dirname
            )
            try:
                process.check_returncode()
                # print(process.stdout.decode('utf-8'))
            except CalledProcessError:
                log_file = latex_file.with_suffix('.log')
                if log_file.is_file():
                    with open(log_file, 'r') as f:
                        error_message = f.read()
                raise click.ClickException(f'Latex process ended with error:\n{error_message}')
            else:
                pdf_file = latex_file.with_suffix('.pdf')
                shutil.move(pdf_file, output_dir / pdf_file.name)

            if not show_grid:
                shutil.move(latex_file, output_dir / latex_file.name)


if __name__ == '__main__':
    generate_labels()
