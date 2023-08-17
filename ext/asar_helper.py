import io
import json
import struct
import os


def round_up(i, m):
    """Rounds up ``i`` to the next multiple of ``m``.

    ``m`` is assumed to be a power of two.
    """
    return (i + m - 1) & ~(m - 1)


class AsarHelper:
    @staticmethod
    def extract_asar(asar_path, output_dir):
        """Extract the contents of an .asar file."""
        with open(asar_path, 'rb') as asar_file:
            data_size, header_size, header_object_size, header_string_size = struct.unpack('<4I', asar_file.read(16))
            header_json = asar_file.read(header_string_size).decode('utf-8')

            header = json.loads(header_json)
            base_offset = round_up(16 + header_string_size, 4)

            def extract_file(source, info, destination):
                if 'offset' not in info:
                    return
                asar_file.seek(base_offset + int(info['offset']))
                data = asar_file.read(int(info['size']))
                dest = os.path.join(destination, source)
                os.makedirs(os.path.abspath('/'.join(dest.split(os.path.sep)[:-1])),
                            exist_ok=True)
                with open(dest, 'wb') as f:
                    f.write(data)

            def extract_dir(source, files, destination):
                dest = os.path.abspath(os.path.join(destination, source))
                os.makedirs(dest, exist_ok=True)
                for name, data in files.items():
                    file_path = os.path.abspath(dest + os.path.sep + name)
                    if 'files' in data.keys():
                        extract_dir(file_path, data['files'], output_dir)
                        continue
                    extract_file(file_path, data, dest)

            extract_dir('.', header['files'], output_dir)

    @staticmethod
    def pack_asar(source_dir, asar_path) -> None:
        """Packs a directory to an .asar file
           Disclaimer: A while ago I cloned a repo on GitHub that handles Asar files. I did my best to rewrite all
            the functions, but the pack_asar is from this repo. Unfortunately, I can't remember where I
            got it from, so I don't know who "owns" the method either.
        """
        offset: int = 0
        concatenated_files: bytes = b''

        def _path_to_dict(path) -> dict:
            nonlocal concatenated_files, offset
            result: dict = {'files': {}}

            for cur_file in os.scandir(path):
                if os.path.isdir(cur_file.path):
                    result['files'][cur_file.name] = _path_to_dict(cur_file.path)
                elif cur_file.is_symlink():
                    result['files'][cur_file.name] = {
                        'link': os.path.realpath(cur_file.name)
                    }
                else:
                    if cur_file.name == 'old-core.asar':
                        continue
                    size = cur_file.stat().st_size

                    result['files'][cur_file.name] = {
                        'size': size,
                        'offset': str(offset)
                    }

                    with open(cur_file.path, 'rb') as f_stream:
                        concatenated_files += f_stream.read()

                    offset += size

            return result

        header: dict = _path_to_dict(source_dir)
        header_json: bytes = json.dumps(header, sort_keys=True).encode('utf-8')

        header_string_size: int = len(header_json)
        data_size: int = 4
        aligned_size: int = (header_string_size + data_size - 1) // data_size * data_size
        header_size: int = aligned_size + 8
        header_object_size: int = aligned_size + data_size

        diff: int = aligned_size - header_string_size
        header_json: bytes = header_json + b'\0' * diff if diff else header_json

        fp: io.BytesIO = io.BytesIO()
        fp.write(struct.pack('<4I', data_size, header_size, header_object_size, header_string_size))
        fp.write(header_json)
        fp.write(concatenated_files)

        with open(asar_path, 'wb') as f:
            fp.seek(0)
            f.write(fp.read())
