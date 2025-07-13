import csv

class SlfConversion:
    def csv_to_slf(csv_path, slf_path):
        with open(csv_path, newline='') as f:
            reader = csv.reader(f, delimiter=';')
            headers = next(reader)
            # assume first header is blank or 'Object'
            object_names = []
            matrix = []
            for row in reader:
                if not row: continue
                object_names.append(str(len(object_names)))
                # interpret presence: any non-zero/non-empty → '1', else '0'
                line = []
                for val in row:
                    v = val.strip()
                    line.append('1' if v and v not in ('0','false','False') else '0')
                matrix.append(line)

        attribute_names = headers
        n_objs = len(object_names)
        n_attrs = len(attribute_names)

        with open(slf_path, 'w', newline='') as f:
            f.write('[Lattice]\n')
            f.write(f'{n_objs}\n{n_attrs}\n')
            f.write('[Objects]\n')
            f.writelines(obj + '\n' for obj in object_names)
            f.write('[Attributes]\n')
            f.writelines(attr + '\n' for attr in attribute_names)
            f.write('[relation]\n')
            for row in matrix:
                f.write(' '.join(row) + ' ' + '\n')
