import argparse

import analyzer
import fs
import gdrive
import minisites

parser = argparse.ArgumentParser(
    prog='minisites analyzer',
    description='analyzer students websites')

parser.add_argument('path')
parser.add_argument('-s', '--section')
parser.add_argument('-t', '--tag')

if __name__ == '__main__':
    args = parser.parse_args()

    print("Opening Google Sheet")
    gdrive.open_spreadsheet("SNT 2023-2024 - Minisites")
    print("Google Sheet is open")

    runner = analyzer.Runner()
    runner.add_task(minisites.ListFilesTask())
    # runner.add_task(minisites.ProjetNameTask(), 'LIV_4')
    # runner.add_task(minisites.ExtractAuthorsTask())
    # runner.add_task(minisites.CountHTMLFilesTask(), 'EQUIPE_3')
    # runner.add_task(minisites.CountCSSFilesTask(), 'CSS')
    runner.add_task(minisites.CheckIndexTask(), 'CODE_1')
    runner.add_task(minisites.HyperlinkScoreTask(), 'CODE_2')
    runner.add_task(minisites.ImageScoreTask(), 'CODE_3')
    runner.add_task(minisites.HTMLScoreTask(), 'CODE_4')
    runner.add_task(minisites.CSSScoreTask(), 'CODE_5')

    pupil_dirs = fs.get_pupil_dirs(args.path)
    if args.section is not None:
        pupil_dirs = [item for item in pupil_dirs if item[0] == args.section]

    for pupil_dir in pupil_dirs:
        runner.run(pupil_dir)

    runner.report()
    gdrive.commit()
