from io import BufferedReader
import struct


def read_file(file_path: str) -> dict[str, str]:
    data = {}

    with open(file_path, 'rb') as file:
        read_int(file, int_type=8, offset=9)

        num_entries = read_int(file, int_type=32, offset=0xC)
        start_offset = read_int(file, int_type=32, offset=0x14)
        row_number = 0

        for i in range(num_entries):
            start_index = read_int(file, int_type=32, offset=0x1C + i * 0xC)
            start_id = read_int(file, int_type=32, offset=0x1C + i * 0xC + 4)
            end_id = read_int(file, int_type=32, offset=0x1C + i * 0xC + 8)

            for id in range(start_id, end_id + 1):
                text_offset = read_int(
                    file,
                    int_type=32,
                    offset=start_offset + (start_index + id - start_id) * 4
                )
                text = str()

                if text_offset > 0:
                    text = read_unicode_string(file, text_offset)
                    text = text.replace('\n', '/n/')

                row_number += 1

                data[str(id)] = text

    return data


def read_int(file: BufferedReader, int_type: int, offset: int) -> int:
    file.seek(offset)

    match int_type:
        case 8:
            size = 1
            format_char = 'b'
        case 32:
            size = 4
            format_char = 'i'

    data = file.read(size)
    return struct.unpack('<' + format_char, data)[0]


def read_unicode_string(file: BufferedReader, offset: int) -> str:
    file.seek(offset)

    max_bytes = 4096
    data = file.read(max_bytes)

    for i in range(0, len(data) - 1, 2):
        if data[i] == 0 and data[i + 1] == 0:
            data = data[:i]
            break

    return data.decode('utf-16-le') if data else ''
