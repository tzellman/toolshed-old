from functools import partial
import os, sys, re, fileinput, datetime
from os.path import isdir, isfile, join, splitext

if __name__ == '__main__':

    from argparse import ArgumentParser

    parser = ArgumentParser(description='copyright utilities')
    parser.add_argument("-r", dest='recurse', action='store_true', help="recursively search paths for files")
    parser.add_argument("--ext", metavar='EXTENSION', help="provide file matcher regex", action='append')
#    parser.add_argument("-f", "--file", metavar='PATHS', help="specify one or more paths", nargs='+', required=False, action='append')

    subparsers = parser.add_subparsers(dest='command')
    p = subparsers.add_parser('update-year', help='update the year')
    p.add_argument("--year", metavar='YEAR', help="specify the end year")
    p = subparsers.add_parser('banner', help='add/update banner to files')
    p.add_argument("--banner", metavar='BANNER', help="banner file", required=True)
    p.add_argument("--remove", action="store_true", help="remove existing banners and add new banners at the top")
    p.add_argument("--type", metavar='LANG', choices='java'.split(), help="set the file type", default='java')

    parser.add_argument("paths", metavar='PATHS', help="specify one or more paths", nargs='+')


#    parser.add_argument("--banner", dest='banner', metavar='FILE', help="specify the file that hosts the banner")
#    parser.add_argument("--pattern", dest='pattern', metavar='PATTERN', help="specify the pattern for finding files with a copyright")

    args = parser.parse_args()

    YEAR_PATTERN = re.compile(r'(Copyright\s+(?:[(]C[)])?\s*(?:\d+\s*[-]\s*)?)(\d+)', re.I)
    BANNER_PATTERNS = dict(java=re.compile(r'(/[*][^\n]*\n(?:\s*[*]\s*Copyright[^\n]*\n)(?:\s*[*][^\n]*\n)*\s*[*]/\s*\n)', re.I | re.M))

    def readFile(name):
        try:
            f = open(name)
            return f.read()
        finally:
            if f:
                f.close()

    def writeFile(name, data):
        try:
            f = open(name, 'wb')
            f.write(data)
        finally:
            if f:
                f.close()

    def fileMatch(pattern, name):
        try:
            data = readFile(name)
            return len(pattern.findall(data)) > 0
        except:
            return False

    paths, files = args.paths, []
    if args.recurse:
        while paths:
            p = paths.pop()
            if isdir(p):
                paths.extend(map(lambda x: join(p, x), os.listdir(p)))
            else:
                files.append(p)
    else:
        files = paths

    paths = filter(lambda x: args.ext is None or splitext(x)[1] in args.ext, files)

    if args.command == 'update-year':
        files = filter(partial(fileMatch, YEAR_PATTERN), paths)

        if files:
            year = int(args.year or datetime.datetime.now().year)
            for line in fileinput.input(files, inplace=1):
                line = YEAR_PATTERN.sub(r'\g<1>%d' % year, line)
                sys.stdout.write(line)
            for f in files:
                print 'Updated %s' % f
    elif args.command == 'banner':
        files = filter(partial(fileMatch, BANNER_PATTERNS[args.type]), paths)

        banner = readFile(args.banner)

        for f in files:
            data = readFile(f)
            repl = banner
            if args.remove:
                repl = ''
            data = BANNER_PATTERNS[args.type].sub(repl, data)
            writeFile(f, data)
            print 'Updated %s' % f

        files = paths if args.remove else set(paths).difference(files)
        for f in files:
            writeFile(f, ''.join([banner, readFile(f)]))
            print 'Updated %s' % f


